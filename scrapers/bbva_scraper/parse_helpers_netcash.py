import hashlib
import re
import uuid
from collections import OrderedDict
from typing import List, Tuple, Optional

import xlrd

from custom_libs import account_no_format_detector
from custom_libs import convert
from custom_libs import country_code_converter
from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import iban_builder
from project.custom_types import (
    ACCOUNT_NO_TYPE_BBAN, ACCOUNT_NO_TYPE_IBAN, ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT,
    AccountParsed, CheckParsed, MovementParsed, LeasingContractParsed, LeasingFeeParsed
)

__version__ = '1.0.1'
__changelog__ = """
1.0.1
get_movements_parsed_from_json set amount_prev = 0.0 to pass mypy (will be updated on 1st iter)
"""

#  [(title, fields, joiner), ...]
MOV_EXTENDED_DESCRIPTION_KEYS = [
    ('Oficina', ['codOficinaOrigen'], ''),
    ('Fecha de operación', ['fechaContable'], ''),
    ('Fecha valor', ['fechaValor'], ''),
    ('Código', ['codigo', 'descConceptoTx'], ' - '),
    ('Información adicional', ['descConcepto'], ''),

    ('País', ['pais'], ''),
    ('Número de cuenta', ['cuenta'], ''),
    ('Banco', ['banco'], ''),
    ('Divisa', ['divisa'], ''),
    ('Observaciones', ['concepto'], ''),

    # common if no extra 'Importe neto', but we always add it
    ('Importe', ['importe'], ''),
]

# See verify_temp_balances()
MAX_SEQ_LEN_OF_DIFFERENT_CALC_VS_PARSED_TEMPBALANCES = 10


# Fecha de operación: 02/10/2018
# Número de cuenta: ES0501821268840201520111
# Fecha valor: 02/10/2018
# Banco: BANCO BILBAO VIZCAYA ARGENTARIA S.A.
# Código: 0007 - TRANSFERENCIAS
# Divisa: EUR
# Información adicional: TRANSFERENCIAS
# Observaciones: TRANSFERENCIA KOLDO AUTO A MEURI
# Cuenta beneficiario: ES0501821268840201520111
# Nombre beneficiario: MEURI
# Cuenta ordenante: ES**************4409
# Canal: BBVA NETCASH BANCA ELECTRONICA
# Descripción: TRANSFERENCIA KOLDO AUTO A MEURI
# Comisión: 0,00
# Referencia: 18501012007795
# Importe neto: 4.000,00


def _clean_of_null_char(text: str) -> str:
    return text.replace('\x00', '')


def get_accounts_parsed(resp_json: dict) -> List[AccountParsed]:
    """
    {"indProvisional":"",
    "iuc":null,
    "datosSaldos":true,
    "error":null,
    "pais":"ES",
    "saldoContableConsolidado":null,
    "saldoValorConsolidado":null,
    "esFavorita":false,
    "referencia":"20055598",
    "bancoDes":"BANCO BILBAO VIZCAYA ARGENTARIA S.A.",
    "oficinaDes":null,
    "empresaDes":"SUNVISO 16 S.L.",
    "signoSaldoContable":"+", // or null
    "signoSaldoValor":"+", // or null
    "codFormato":"17",
    "numeroAsuntoMostrar":"ES8101820999850201570653",
    "numeroAsunto":"ES8101820999850201570653",
    "bancoAsunto":"1",
    "aliasAsunto":"",
    "divisa":"EUR",
    "saldoContable":"0,00", // or null
    "saldoValor":"0,00",    // or null
    "titular":null,
    "oficinaMidas":null,
    "oficinaHost":null,
    "ordenacion":null,
    "saldoRetenido":null,
    "saldoAutorizado":null,
    "signoSaldoRetenido":null,
    "signoSaldoAutorizado":null,
    "productLevelId":"000010000400056",
    "contractId":null,
    "idProducto":null,
    "descProducto":null}
    """

    accounts_dicts = resp_json['data']['cuentas']  # type: List[dict]

    accounts_parsed = []
    for account_dict in accounts_dicts:
        # can be in IBAN format or BBAN-like format, i.e '41189 00001 16010160904 28EUR'
        account_no = account_dict['numeroAsunto']
        # handle possible none
        if account_dict['saldoContable'] and account_dict['signoSaldoContable']:
            balance = convert.to_float(account_dict['saldoContable'])  # from '2.088,78' or '-12.2344,12'
        else:
            balance = 0.0
        currency = account_dict['divisa']
        country_code = country_code_converter.alpha3_from_alpha2(account_dict['pais'])  # ES-> ESP; FR -> FRA

        account_no_format = account_no_format_detector.detect_account_no_format(account_no)

        # we can convert BBAN to IBAN
        if account_no_format == ACCOUNT_NO_TYPE_BBAN:
            # '41189 00001 16010160904 28EUR' -> '41189000011601016090428'
            account_bban = ''.join(re.findall('\d+', account_no))
            account_iban = iban_builder.build_iban(account_dict['pais'], account_bban)
            account_no_format_converted = ACCOUNT_NO_TYPE_IBAN
        else:
            account_iban = account_no
            account_no_format_converted = account_no_format

        # check own balance and available to detect credit acc
        account_type = (ACCOUNT_TYPE_DEBIT
                        if account_dict['saldoContable'] == account_dict['saldoValor']
                        else ACCOUNT_TYPE_CREDIT)

        organization_title = (account_dict['empresaDes'] or '').strip()

        account_parsed = {
            'account_no': account_iban,
            'organization_title': organization_title,
            'financial_entity_account_id': account_no,
            'balance': balance,
            'currency': currency,
            'account_type': account_type,
            'country_code': country_code,
            'account_no_format': account_no_format_converted
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed_from_excel(content: bytes) -> List[MovementParsed]:
    book = xlrd.open_workbook(file_contents=content)
    sheet = book.sheet_by_index(0)

    movements_parsed = []  # type: List[MovementParsed]
    for row_num in range(15, sheet.nrows):
        cells = sheet.row_values(row_num)
        movement = {}
        movement['operation_date'] = cells[1]  # '17/11/2017'
        movement['value_date'] = cells[2]
        movement['description'] = extract.remove_extra_spaces('{} {}'.format(cells[4], cells[5].strip("'")))
        movement['amount'] = cells[6]
        movement['temp_balance'] = cells[7]

        movements_parsed.append(movement)

    return movements_parsed


def _get_short_and_extended_descriptions(mov_data: dict, should_scrape_ext_descr: bool) -> Tuple[str, str]:
    description_short = extract.remove_extra_spaces(
        '{} {}'.format(mov_data['descConcepto'], mov_data['concepto'])
    )
    description_extended = description_short
    # no extra request required
    if should_scrape_ext_descr:
        for title, fields, joiner in MOV_EXTENDED_DESCRIPTION_KEYS:
            # don't add amount for mov with extra details (?)
            # if title == 'Importe' and mov_data['detalleMovimientoParametroId']:
            #     continue
            vals = [(mov_data.get(field) or '').strip() for field in fields]
            val = joiner.join(vals)
            if val:
                msg = '{}: {}'.format(title, val)
                description_extended += " || {}".format(msg)

    return description_short, description_extended


def mov_parsed_add_extra_details(mov_parsed: MovementParsed,
                                 resp_json: dict) -> Tuple[MovementParsed, bool]:
    """Adds more details from extra resp to already parsed movement:
    - more details extended description
    - receipt pdf download params

    Parses:
    {"success":true,"errorInfo":{"errorCode":"0","errorTitle":null,"errorDescription":"OK","errorKeyTitle":null,
    "errorKeyDescription":null,"debugMessage":null,"debugTrace":null},"data":{"codError":0,"codRetorno":0,
    "descripcion":"OK","detalle":[
    {"clave":"Cuenta beneficiario","tipoClave":"TipoClave","valor":"ES0501821268840201520111","tipoValor":"String"},
    {"clave":"Nombre beneficiario","tipoClave":"TipoClave","valor":"MEURI","tipoValor":"String"},
    {"clave":"Cuenta ordenante","tipoClave":"TipoClave","valor":"ES**************4409","tipoValor":"String"},
    {"clave":"Canal","tipoClave":"TipoClave","valor":"BBVA NETCASH BANCA ELECTRONICA","tipoValor":"String"},
    {"clave":"Descripción","tipoClave":"TipoClave","valor":"TRANSFERENCIA KOLDO AUTO A MEURI","tipoValor":"String"},
    {"clave":"Comisión","tipoClave":"TipoClave","valor":"0,00","tipoValor":"Double"},
    {"clave":"Referencia","tipoClave":"TipoClave","valor":"18501012007795","tipoValor":"String"},
    {"clave":"Importe neto","tipoClave":"TipoClave","valor":"4.000,00","tipoValor":"Double"}
    ],"reutilizarOperacion":false,"ordenReutilizarOperacion":"",
    "detallesPdf":[
        {"clave":"peticionContractId",
        "valor":"0011018218102291642910-RE-ES0182002000000000000000000002321593XXXXXXXXX"}]}}

    :returns: mov_parsed_updated, detalle_is_none
    """
    detalle_is_none = True
    description_extended = mov_parsed['description_extended']

    try:
        mov_data = resp_json['data']
        mov_details = mov_data['detalle']
    except:
        raise Exception(
            "Can't parse extra description (but should). No data/detalle. "
            "Check the resp: {}. ".format(
                resp_json
            )
        )

    # {"success":true,"errorInfo":{"errorCode":"0","errorTitle":null,"errorDescription":"OK","errorKeyTitle":null,
    # "errorKeyDescription":null,"debugMessage":null,"debugTrace":null},"data":{"codError":0,"codRetorno":0,
    # "descripcion":"OK","detalle":[],"reutilizarOperacion":false,"ordenReutilizarOperacion":"","detallesPdf":[]}}
    if mov_details is not None:  # handle possible None
        detalle_is_none = False
        for mov_detail in mov_details:
            title = mov_detail['clave']
            val = extract.remove_extra_spaces(mov_detail['valor'])
            msg = '{}: {}'.format(title, val)
            description_extended += " || {}".format(msg)

    mov_parsed_updated = mov_parsed.copy()
    mov_parsed_updated['description_extended'] = description_extended
    mov_parsed_updated['receipt_params'] = mov_data.get('detallesPdf', [])  # list of dicts
    return mov_parsed_updated, detalle_is_none


def get_movements_parsed_from_json(resp_json: dict, should_scrape_ext_descr: bool) -> List[MovementParsed]:
    """
    Parses
    {"success":true,"errorInfo":{"errorCode":null,"errorTitle":null,"errorDescription":null,
    "errorKeyTitle":null,"errorKeyDescription":null,"debugMessage":null,"debugTrace":null},
    "data":{"cuenta":null,"periodo":null,"importe":null,"conceptos":null,"divisa":null,
    "descCtaIban":"01821268840201520111","descEmpresa":"",
    "descOficina":"","descBanco":"BANCO BILBAO VIZCAYA ARGENTARIA S.A.",
    "paginacionTLSMT016":"81.83","paginacionTLSMT017":"+",
    "ordenacion":"DESC","codError":0,"codRetorno":0,"descripcion":"More records available",

    "movimientos":[

    {"hora":"","indProvisional":"",
    "hayDetalleAmpliado":true,
    "tipoDetalleMovimiento":"Wire transfer",
    "claveAplicacionOrigen":"0011018218102291642910",
    "movementId":"0506",
    "descConceptoTx":"TRANSFERENCIAS                  ",
    "descConcepto":"TRANSFERENCIAS                  ",
    "codOficinaOrigen":"1128",
    "numeroTalon":null,
    "indicadorDH":"H",
    "divisaOrigen":null,
    "codigoMes":null,
    "fechaDocumento":null,
    "identificadorDocumento":"1",
    "bancoProducto":"0182",
    "oficinaProducto":"1128",
    "contrapartidaProducto":null,
    "folioProducto":null,
    "fechaContable":"02/10/2018",
    "fechaValor":"02/10/2018",
    "importe":"4.000,00",
    "saldo":"4.132,70",
    "codigo":"0007",
    "concepto":"TRANSFERENCIA KOLDO AUTO A MEURI",
    "oficina":"",
    "divisa":"EUR",
    "pais":"ES",
    "cuenta":"ES0501821268840201520111",
    "banco":"BANCO BILBAO VIZCAYA ARGENTARIA S.A.",
    "infAdicional":"1128",
    "importeTotal":true,
    "saldoContable":"4.132,70",
    "saldoValor":"4.132,70",
    "claveContable":"",
    "codigoProcedencia":"0102",
    "codRmsoperS":"140000030882201682",
    "detalleMovimientoParametroId":"0011018218102291642910-RE-01821268840201520111",
    "detalleMovimientoParametroFiltro":"(transactionDate==2018-10-02)",
    "referenciaBBVA":null,
    "referenciaCorresponsal":null},

    {"hora":"","indProvisional":"","hayDetalleAmpliado":false,"tipoDetalleMovimiento":null,
    "claveAplicacionOrigen":null,"movementId":"","descConceptoTx":"LIQUIDACIÓN ABONO COMPENSACIÓN  ",
    "descConcepto":"LIQUIDACIÓN ABONO COMPENSACIÓN  ","codOficinaOrigen":"1299","numeroTalon":null,
    "indicadorDH":"D","divisaOrigen":null,"codigoMes":null,"fechaDocumento":null,"identificadorDocumento":"0",
    "bancoProducto":"0182","oficinaProducto":"1299","contrapartidaProducto":null,"folioProducto":null,
    "fechaContable":"27/09/2018","fechaValor":"26/09/2018",
    "importe":"-0,70",
    "saldo":"132,70","codigo":"0173","concepto":"016206-076957034-3","oficina":"","divisa":"EUR","pais":"ES",
    "cuenta":"ES0501821268840201520111","banco":"BANCO BILBAO VIZCAYA ARGENTARIA S.A.","infAdicional":"1299",
    "importeTotal":true,"saldoContable":"132,70","saldoValor":"132,70","claveContable":"","codigoProcedencia":"0136",
    "codRmsoperS":"140000030817351099","detalleMovimientoParametroId":null,"detalleMovimientoParametroFiltro":null,
    "referenciaBBVA":null,"referenciaCorresponsal":null},

    ]
    """

    amount_prev = 0.0  # will be updated on 1st iter, 0.0 to pass mypy
    temp_balance_prev = None  # type: Optional[float]

    movs_data = resp_json['data']['movimientos']
    movements_parsed_desc = []  # type: List[MovementParsed]
    for mov_data in movs_data:
        operation_date = mov_data['fechaContable']  # '17/11/2017'
        value_date = mov_data['fechaValor']  # '17/11/2017'
        description, description_extended = _get_short_and_extended_descriptions(
            mov_data,
            should_scrape_ext_descr
        )
        amount = convert.to_float(mov_data['importe'])

        # See verify_temp_balances()
        temp_balance_parsed = convert.to_float(mov_data['saldo'])
        temp_balance_calc = (
            temp_balance_parsed if temp_balance_prev is None
            else round(temp_balance_prev - amount_prev, 2)
        )
        temp_balance_prev = temp_balance_calc
        amount_prev = amount

        mov_details_params = OrderedDict([
            ('parameroFiltro', mov_data['detalleMovimientoParametroFiltro']),
            ('parametroId', mov_data['detalleMovimientoParametroId']),
            ('tipoDetalleMovimiento', mov_data['tipoDetalleMovimiento'])
        ])

        movement = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': _clean_of_null_char(description),
            'description_extended': _clean_of_null_char(description_extended),
            'amount': amount,
            'temp_balance': temp_balance_calc,
            'temp_balance_parsed': temp_balance_parsed,
            'id': '{}--{}'.format(mov_data['detalleMovimientoParametroId'], uuid.uuid4()),
            'has_extra_details': mov_data['detalleMovimientoParametroId'] is not None,
            'mov_details_params': mov_details_params,
            # for pdf extraction
            'clave_aplicacion_origen_param': mov_data.get('claveAplicacionOrigen') or 'null',
            'may_have_receipt': mov_data.get('identificadorDocumento', '') == '1',
            'amount_str': mov_data['importe'],
            'codigo_param': mov_data['codigo'],
            'observaciones_param': mov_data['concepto'],  # may be with \x00 symbol (used only as req param)
            'mov_raw': mov_data,
        }

        movements_parsed_desc.append(movement)

    return movements_parsed_desc


def replace_temp_balances_calc_by_parsed(movements_parsed: List[MovementParsed]) -> List[MovementParsed]:
    """Replaces temp_balance by temp_balance_parsed for each movement
    Returns a new list, doesn't mutate initial list
    If replaced, usually we expect further ERR_BALANCE_INCONSISTENT_MOVEMENTS
    """
    movements_parsed_replaced = []  # type: List[MovementParsed]
    for mov in movements_parsed:
        m = mov.copy()
        m['temp_balance'] = m['temp_balance_parsed']
        movements_parsed_replaced.append(m)
    return movements_parsed_replaced


def verify_temp_balances(movements_parsed: List[MovementParsed]) -> bool:
    """
    Sometimes there is bank-level inconsistency for balances
        -a a 31211: ES4601822354840201002674: 07/01/2021, movs with amounts 4281.51, 4639.94
        after one of them balance is not changing but after second it changes as both were applied
        Solution: calc balance and validate differences betweed calculated and parsed ones in the end.
        Only intra-day inconsistency is allowed.
        If there will be too many different balances (calc vs parsed) then the scraper will
        set bad parsed balances to inform about inconsistency.
    --
    Compares temp_balance and temp_balance_parsed
    True if:
        number of unequal balances one by one < MAX_SEQ_LEN_OF_DIFFERENT_CALC_VS_PARSED_TEMPBALANCES
        unequal balances inside one date
    """
    seq_of_different_calc_vs_parsed__date_str = ''
    seq_of_different_calc_vs_parsed__len = 0
    for mov in movements_parsed:
        if mov['temp_balance'] == mov['temp_balance_parsed']:
            seq_of_different_calc_vs_parsed__date_str = ''
            seq_of_different_calc_vs_parsed__len = 0
            continue

        # Not equal
        mov_oper_date = mov['operation_date']
        # 1st mov
        if not seq_of_different_calc_vs_parsed__date_str:
            seq_of_different_calc_vs_parsed__date_str = mov_oper_date
            seq_of_different_calc_vs_parsed__len = 1
            continue

        # 2nd or more

        # Got different balances for different dates - bad case.
        if mov_oper_date != seq_of_different_calc_vs_parsed__date_str:
            return False

        seq_of_different_calc_vs_parsed__len += 1
        if seq_of_different_calc_vs_parsed__len > MAX_SEQ_LEN_OF_DIFFERENT_CALC_VS_PARSED_TEMPBALANCES:
            return False
    # Check final seq (if got it)
    return seq_of_different_calc_vs_parsed__len <= MAX_SEQ_LEN_OF_DIFFERENT_CALC_VS_PARSED_TEMPBALANCES


def parse_checks_from_html(resp_text: str) -> List[CheckParsed]:
    check_htmls = re.findall('(?si)<tr><td class="bgfila2?">.*?</tr>', resp_text)

    checks_parsed = []
    for check_html in check_htmls:
        fields = re.findall('(?si)<td.*?>(.*?)</td>', check_html)
        fls = [extract.remove_tags(field) for field in fields]
        details_link = extract.re_first_or_blank('(?si)<a href="(.*?)"', fields[0])
        # handle ['<p class="txtdato2">No existen registros</p>']
        if not details_link:
            continue

        fls[0] = details_link

        hashbase = 'BBVA{}{}{}{}'.format(
            fls[2],
            fls[5],
            fls[3],
            fls[4]
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()

        has_details = True

        state = fls[8].upper()
        amount = convert.to_float(fls[4])

        state = fls[8].upper()
        if fls[8].upper() in ['ABONADO', 'CREDITADO']:
            state = 'ABONADO'
        elif fls[8].upper() in ['TRANSMITIDO', 'TRANSMITIDO BANCO', 'TRANSMÈS BANC']:
            state = 'TRANSMITIDO'
        elif fls[8].upper() in ['DEVOLVIDO', 'DEVUELTO']:
            state = 'DEVUELTO'
            amount = -amount

        checks_parsed.append({
            'details_link': fls[0].replace('amp;', ''),
            'capture_date': fls[1],
            'check_number': fls[2],
            'charge_account': fls[3],
            'amount': amount,
            'expiration_date': fls[5],
            'doc_code': fls[6],
            'stamped': bool(fls[7].lower() == "si"),
            'state': state,
            'has_details': has_details,
            'keyvalue': keyvalue,
            'charge_cif': '',
            'image_link': None,
            'image_content': None
        })

    return checks_parsed


def check_parsed_add_details(check_parsed: CheckParsed, resp_text: str) -> CheckParsed:
    check_parsed['charge_cif'] = extract.remove_tags(
        extract.re_first_or_blank('(?si)Observaciones:(.*?)</tr>', resp_text))
    check_parsed['image_link'] = extract.re_first_or_blank('(?si)class=\'contenedorImagen.*?src="(.*?)"', resp_text)
    check_parsed['image_content'] = None

    return check_parsed


def get_leasing_companies_from_html_resp(resp_text: str) -> List[dict]:
    # <option value='005286707'>A48455299 </option>
    results = re.findall('(?si)<option value=\'(\d+?)\'>(.+?) </option>', resp_text)

    companies_data = []
    for r in results:
        companies_data.append({"cif": r[1], "id": r[0]})

    return companies_data


def get_leasing_contracts_from_html_resp(resp_text: str) -> List[LeasingContractParsed]:
    # arrayDatos[0]=["LEASING MOBILIARIO","182","90","501","1635164","2017-03-28","2020-03-28","68465,00","0",""];
    fields = re.findall(
        '(?si)arrayDatos\[(\d+?)\]=\["(.*?)","(\d+?)","(\d+?)","(\d+?)",'
        '"(\d+?)","(.*?)","(.*?)","(.*?)","(\d+?)","(.*?)"];',
        resp_text
    )

    leasing_contracts_parsed = []
    for f in fields:
        post_data = {'idx': f[0], 'bank': f[2], 'office': f[3], 'control': f[4], 'folio': f[5], 'depcode': f[9]}
        office = f[3].zfill(4)
        # 0182-0090-0501-00000001655739
        contract_reference = "{}-{}-{}-{}".format(f[2].zfill(4), f[3].zfill(4), f[4].zfill(4), f[5].zfill(14))
        contract_date = date_funcs.convert_date_to_db_format(f[6])
        expiration_date = date_funcs.convert_date_to_db_format(f[7])
        amount = convert.to_float(f[8])

        hashbase = 'BBVA{}{}{}'.format(
            contract_reference,
            contract_date,
            amount  # capital
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()

        contract_parsed = {
            'office': office,
            'contract_reference': contract_reference,
            'amount': amount,
            'contract_date': contract_date,
            'expiration_date': expiration_date,
            'keyvalue': keyvalue,
            'has_details': True,
            'post_data': post_data
        }
        leasing_contracts_parsed.append(contract_parsed)

    return leasing_contracts_parsed


def get_leasing_contract_details_from_html_resp(
        resp_text: str,
        contract_parsed: LeasingContractParsed) -> LeasingContractParsed:
    n_data = re.findall(r'(?si)var\sdatoTxt.*?=\'(.*?)\'', resp_text)
    t_data = re.findall(r'(?si)<p class="txtdato">\s*(.*?)</p>', resp_text.replace('\t', '').replace('\n', ''))

    """
    DAF: all the contract data extracted from the page:
    n_data = ['68465,00', '0,00', '0,00', '0,00', '68465,00', '0,00', '21,00000000', '1,40000000', '854,42', '1033,85', '1,55846500', 'N']
    t_data = ['<script>document.write(contrato)</script> ', 'A48455299 &nbsp; &nbsp; &nbsp; &nbsp;ESERGUI DISTESER S.L.    ',
     'APLAZADO', 'FIJO', 'CUOTA NETA CONSTANTE ', '36 ', 'MENSUAL ', 'NATURAL', '36', 'PREPAGABLE', '40000,00', '',
     '0  ', '']
    """

    contract_parsed['fees_quantity'] = int(t_data[8])
    contract_parsed['amount'] = convert.to_float(n_data[0])
    contract_parsed['taxes'] = convert.to_float(n_data[6])
    contract_parsed['residual_value'] = convert.to_float(t_data[10])
    contract_parsed['initial_interest'] = convert.to_float(n_data[7])
    contract_parsed['current_interest'] = contract_parsed['initial_interest']  # DAF:???
    # contract_parsed['tae'] = convert.to_float(n_data[10])  #T.A.E

    return contract_parsed


def get_leasing_fees_parsed_from_excel(
        content: bytes,
        contract_parsed: LeasingContractParsed) -> List[LeasingFeeParsed]:
    book = xlrd.open_workbook(file_contents=content)
    sheet = book.sheet_by_index(0)

    leasing_fees_parsed = []  # type: List[LeasingFeeParsed]
    for row_num in range(11, sheet.nrows):
        # DAF: cells = ['', '1', '28-03-2017', '+774,45', '+774,45', '+79,97', '+0,00', '854,42', '+179,42', '+1033,84', '+67690,55', 'CUOTA']
        cells = sheet.row_values(row_num)
        fee_parsed = {}  # type: LeasingFeeParsed

        operational_date = date_funcs.convert_date_to_db_format(cells[2].replace('-', '/'))  # '17-11-2017'
        hashbase = 'BBVA{}/{}-{}-{}-{}'.format(
            contract_parsed['contract_reference'],
            cells[1],  # fee_number
            operational_date,  # operational_date
            cells[9],  # fee_amount
            cells[10],  # pending_repayment
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()

        fee_parsed['fee_reference'] = "{}/{}".format(contract_parsed['contract_reference'], cells[1])
        fee_parsed['fee_number'] = cells[1]
        fee_parsed['operational_date'] = operational_date
        fee_parsed['currency'] = 'EUR'  # DAF: warn with this
        fee_parsed['financial_repayment'] = convert.to_float(cells[4])
        fee_parsed['financial_performance'] = convert.to_float(cells[5])
        fee_parsed['insurance_amount'] = convert.to_float(cells[6])  # seguro, always 0.00
        fee_parsed['fee_type'] = cells[11]
        fee_parsed['amount'] = convert.to_float(cells[7])  # cuota neta
        fee_parsed['taxes_amount'] = convert.to_float(cells[8])  # impuesto
        fee_parsed['fee_amount'] = convert.to_float(cells[9])  # cuota bruta
        fee_parsed['pending_repayment'] = convert.to_float(cells[10])  # capital vivo
        fee_parsed['state'] = ''
        fee_parsed['keyvalue'] = keyvalue
        fee_parsed['statement_id'] = None
        fee_parsed['contract_id'] = None

        leasing_fees_parsed.append(fee_parsed)

    return leasing_fees_parsed
