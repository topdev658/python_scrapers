import re
import traceback
import uuid
from collections import OrderedDict
from datetime import datetime
from typing import List, Dict

from custom_libs import convert
from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project import settings as project_settings
from project.custom_types import MovementParsed, AccountParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT
from .parse_helpers_regular import MOV_EXTENDED_DESCRIPTION_FIELDS

__version__ = '2.1.0'
__changelog__ = """
2.1.0
get_accounts_parsed:
    get balance and currency from extra column if exists
2.0.0
now supports extended descriptions and receipts:
get_description_extended
get_movs_receipts_req_params
mov value_date from req_params
1.1.0
decsr_w_mas_datos (like in parse_helpers_regular)
"""

SPANISH_MONTH_TO_NUM = {
    'Ene': '01',
    'Feb': '02',
    'Mar': '03',
    'Abr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Ago': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dic': '12',

}


def get_account_parsed_one_acc(resp_text: str, numero_quenta_param: str) -> AccountParsed:
    """Parses 5_resp_accs_202012_family_oneacc.html
    Caixa returns a special layout for if there is only one account
    -a 6923, STIN SA
    """
    account_no = extract.re_first_or_blank(r'(?si)<a[^>]*>\s*(ES[\d\s]+)', resp_text).replace(' ', '')
    # '179.419,49 €'
    balance_str = extract.re_first_or_blank(
        r'(?si)Saldo actual\s*</div>\s*<div[^>]*>(.*?)<',
        resp_text
    ).strip()
    balance = convert.to_float(balance_str)
    currency = convert.to_currency_code(balance_str.split()[1])
    account_parsed = {
        'account_no': account_no,
        'account_alias': '',  # emresas compat
        'balance': balance,
        'account_type': ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT,
        'currency': currency,
        'refval_simple_numero_cuenta_param': numero_quenta_param,  # only for recent movss
        'account_page_ix': 0,
        'is_private_view': True  # scraped from Particulares view
    }
    return account_parsed


def get_accounts_parsed(logger: ScrapeLogger, resp_text: str, page_ix: int) -> List[AccountParsed]:
    # from dev_regular/5_resp_accs_202012_family.html
    # -a 16556, FRANCISCO DE ASIS RIPOLL SOGAS

    accounts_parsed = []  # type: List[AccountParsed]

    # Necessary to extract movements
    # tablaDatosInformacionCuenta = new Array("p6DpzbyOCGynoOnNvI4IbAAAAWep6Y00YJn1r8ShJUA", "", "")
    numero_cuenta_params = [
        v.strip('"')
        for v in extract.re_first_or_blank(
            r'(?si)tablaDatosInformacionCuenta\s*=\s*new\s+Array\((.*?)\)',
            resp_text
        ).split(',')
    ]

    accounts_htmls = re.findall(r'(?si)<tr class="table-row--for_link">.*?</tr>', resp_text)
    if numero_cuenta_params != [""] and not accounts_htmls:
        # Handle special layout for one-acc contract
        account_parsed = get_account_parsed_one_acc(
            resp_text,
            numero_cuenta_params[0]
        )
        return [account_parsed]
    # Increase with each iteration
    # but if got blank refval_simple_numero_cuenta_param
    # then increase more
    numero_cuenta_ix = 0
    for acc_ix, acc_html in enumerate(accounts_htmls):
        cells = re.findall('(?si)<td.*?</td>', acc_html)
        if len(cells) != 4:
            continue

        # ES6321005858740200009275
        # use ES\d+ to avoid ES2321005376447200000795DÓLARUSA:+154.642,19
        account_no = extract.re_first_or_blank(r'ES[\d\s]+', cells[0]).replace(' ', '')

        if not account_no:
            logger.error("acc ix {}: can't get account_no or account_alias. Skip. RESPONSE PART\n{}".format(
                acc_ix,
                acc_html
            ))
            numero_cuenta_ix += 1
            continue

        # Handle case when list contains blank vals
        # due to end of subtype of accounts
        # -u 149727 -a 6033 company VIA CELERE DESARROLLOS INMOBILIARIOS: before ES73 2100 9135 0722 0015 7114
        # -u 242841 -a 12802
        # -a 6025, -a 7214 foreign currency USD
        # -a 7214 - acc alias, no iban
        while True:
            if numero_cuenta_ix >= len(numero_cuenta_params):
                logger.error("{}: can't get numero_quenta_param: ix={} >= len of {}. "
                             "Skip account".format(account_no, numero_cuenta_ix, numero_cuenta_params))
                return accounts_parsed

            numero_quenta_param = numero_cuenta_params[numero_cuenta_ix]
            if numero_quenta_param:
                break
            numero_cuenta_ix += 1

        try:
            # All accounts have value for 'cells[2]' with balance and currency in EUR.
            # Only some accounts, have value for 'cells[1]' with different balance and currency
            # cells[1] = 13.91 USD / cells[2] = 12.97 EUR
            # Movements currency matches 'cells[1]' currency when 'cells[1]' has value
            balance_1 = extract.remove_tags(cells[1])
            balance_2 = extract.remove_tags(cells[2])
            balance_str = balance_2 if balance_1 == '' else balance_1
            balance = convert.to_float(balance_str)
            currency = convert.to_currency_code(balance_str.split()[1])
        except Exception as _e:
            logger.error("{}: can't parse. HANDLED EXCEPTION:\n{}\n. Skip. RESPONSE PART\n{}".format(
                account_no,
                traceback.format_exc(),
                acc_html
            ))
            numero_cuenta_ix += 1
            continue

        if not currency or len(currency) != 3:
            logger.error("{}: can't parse currency. Skip. RESPONSE PART\n{}".format(
                account_no,
                acc_html
            ))
            numero_cuenta_ix += 1
            continue

        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

        account_parsed = {
            'account_no': account_no,
            'account_alias': '',  # if can't get account_no
            # IMPORTANT: we use balance_available for credit accs (equal to balance if debit acc)
            'balance': balance,
            'account_type': account_type,
            'currency': currency,
            'refval_simple_numero_cuenta_param': numero_quenta_param,  # only for recent movs
            # For accounts from page_ix > 0 account_page_ix will be 0 ALWAYS (top in the dropdown)
            # but for accounts from first page its ix in dropdown will be as at the page
            # It used to filter by dates
            'account_page_ix': acc_ix if page_ix == 0 else 0,
            'is_private_view': True  # scraped from Particulares
        }
        accounts_parsed.append(account_parsed)
        numero_cuenta_ix += 1

    return accounts_parsed


def req_recent_movs_params(account_parsed: AccountParsed) -> OrderedDict:
    # from enviar() js func
    req_params = OrderedDict([
        ('PN', 'GCT'),
        ('PE', '100'),
        ('ORIGEN_INVOCACION', 'GCT11'),
        ('INFORMACION_CUENTA', account_parsed['refval_simple_numero_cuenta_param']),
    ])
    return req_params


def is_particulares_accounts(resp_text: str) -> bool:
    return 'p-CT__accounts__head__left__left__inner__data' in resp_text


def get_movs_next_page_clave_continuacion_bus_param(resp_text: str) -> str:
    return extract.re_first_or_blank('"claveContinuacionMovAjax", "(.*?)"', resp_text)


def get_account_no_from_movs_page(resp_text: str) -> str:
    """Parses dev_regular/6-1_recent_movs_particulares.html
    To use in validator"""
    # For OLD (before 202101)
    # acc_htmls = re.findall(r'(?si)<label\s+class="c-carsel__item".*?</label>', resp_text)
    # selected_account_no = ''
    # for acc_html in acc_htmls:
    #     if '<input type="radio" name="p-CT__accounts" checked' in acc_html:
    #         selected_account_no = extract.text_wo_scripts_and_tags(extract.re_first_or_blank(
    #             '(?si)<div class="p-CT__accounts__head__left__left__inner__data">(.*?)</div>',
    #             acc_html
    #         ))
    #         break
    selected_account_no = extract.re_first_or_blank(
        '(?si)<div class="uPV_color--gray400">(.*?)</div>',
        resp_text
    )
    account_no = re.sub(r'\s', '', selected_account_no)
    return account_no


def get_refval_particulares_params(resp_text: str) -> dict:
    # it looks like these values will overwrite initial vals
    refval_params = {
        'REFVAL_SIMPLE_NUMERO_CUENTA': extract.form_param(
            resp_text,
            'REFVAL_SIMPLE_NUMERO_CUENTA'
        ),
        'REFVAL_SIMPLE_CUENTA': extract.form_param(
            resp_text,
            'REFVAL_SIMPLE_CUENTA'
        )
    }
    return refval_params


def req_movs_filter_by_dates_params(
        refval_params: dict,
        date_from: str,
        date_to: str) -> OrderedDict:
    req_params = OrderedDict([
        ('PN', 'GCT'),
        ('PE', '102'),
        ('OPERACION_NUEVO_EXTRACTO', 'MOVIMIENTOS_BUSQUEDA_AVANZADA'),
        ('CLICK_ORIG', 'FLX_GCT_100'),
        # ('FLAG_PE', 'E'),
        ('FLUJO', "GCT,100,180:GFI,7,'"),  # fixed value, but may be changed
        ('CLAVE_CONTINUACION_SUM', '  000000000000000000000000000 0000000'),
        ('FECHA_INICIAL', ''),
        ('ORDEN_MOVIMIENTOS', 'R'),
        ('FEC_INI_BUS', date_funcs.convert_to_ymd(date_from)),  # '20180101'
        ('FEC_FIN_BUS', date_funcs.convert_to_ymd(date_to)),  # '20181230'
        ('FILTRO_ABIERTO', 'S'),
        ('ID_TABLA', 'TablaBean02'),
        ('TIPO_CUENTAS', 'VIG'),
        # 'lZkCMwQriBOVmQIzBCuIEwAAAWgARULCerw5JiVuqfE'
        ('REFVAL_SIMPLE_NUMERO_CUENTA', refval_params['REFVAL_SIMPLE_NUMERO_CUENTA']),
        ('CLAU_CONTINUACIO_MOV', '40' * 50),
        ('TIPO_FECHA', 'F'),
        ('IMPMIN', '000000000000000'),
        ('IMPMAX', '999999999999999'),
        ('TIPMOV', ''),
        ('TXT_BUSCAR', ''),
        ('RESULT_FILTRADO', 'S'),
        ('AGREGADA', 'N'),
    ])
    return req_params


def req_movs_next_page_params(
        resp_text: str,
        refval_params: dict,
        date_from: str,
        date_to: str) -> OrderedDict:
    clave_continuaton_param = get_movs_next_page_clave_continuacion_bus_param(resp_text)

    req_params = OrderedDict([
        ('PN', 'GCT'),
        ('PE', '102'),
        ('OPERACION_NUEVO_EXTRACTO', 'MOVIMIENTOS_BUSQUEDA_AVANZADA'),
        ('CLICK_ORIG', 'PAG_GCT_102'),
        ('ID_TABLA', 'TablaBean02PaginacionPlus'),
        ('TIPO_CUENTAS', 'VIG'),
        # 'lZkCMwQriBOVmQIzBCuIEwAAAWgARULCerw5JiVuqfE'
        ('REFVAL_SIMPLE_NUMERO_CUENTA', refval_params['REFVAL_SIMPLE_NUMERO_CUENTA']),
        ('SALDO_ACTUAL', '000000000000000'),
        ('SALDO_RETENIDO', '000000000000000'),
        ('SIGNO_SALDO_ACTUAL', '+'),
        ('SIGNO_SALDO_RETENIDO', '+'),
        ('AGREGADA', 'N'),
        ('RESULT_FILTRADO', 'S'),
        ('TIPO_FECHA', 'F'),
        ('CLAVE_CONTINUACION_BUS', clave_continuaton_param),
        ('CLAU_CONTINUACIO_MOV', clave_continuaton_param),
        ('CLAVE_CONTINUACION_AGR', ''),
        ('TXT_BUSCAR', ''),
        ('FEC_INI_BUS', date_funcs.convert_to_ymd(date_from)),  # '20180101'
        ('FEC_FIN_BUS', date_funcs.convert_to_ymd(date_to)),  # '20181230'
        ('IMPMIN', '000000000000000'),
        ('IMPMAX', '999999999999999'),
        ('ORDEN_MOVIMIENTOS_BA', 'R'),
        ('CLAVE_CONTINUACION_BA', clave_continuaton_param),
    ])
    return req_params


def _convert_spanish_date(date_raw: str) -> str:
    """Converts '25 Ene 2020' to '25/01/2020"""
    # '24 Ene 2020' -> '24 01 2020' -> '24/01/2020'
    d, m, y = re.sub(r'\s+', '/', date_raw.strip()).split('/')
    m_num = SPANISH_MONTH_TO_NUM[m]
    return '/'.join([d, m_num, y])


def get_description_extended(logger: ScrapeLogger,
                             fin_ent_account_id: str,
                             resp_text: str,
                             movement_parsed: MovementParsed) -> str:
    """Extracts the description_extended from mov details resp with the rules described below.
    Fields:
    a. Concepto
    b. Concepto específico
    c. Remitente
    d. Referencia 2
    e. Otras caracteristicas
    f. Concepto informado por el ordenante
    g. Codigo identificacion del ordenante
    h. Concepto transferencia
    i. [NEW since 2019-06-02] Oficina
    The fields must be concatenated to be inserted in ExtendedDescription as you are doing in BBVA. They must be
    concatenated in the order above.
    If a field does not appear in the Detail of the movement,
     it must also be included in the ExtendedDescription as
    "|| ||", so that the ExtendedDescription format will always be the same, whether the fields appear or not.

    Parses
    <div class="c-form-group c-form-group--vertical margin--bottom-normal">
        <label class="c-form-group__label c-form-group__label--text">
            Remitente
        </label>
        <span class="c-form-group__text">
            625271284
        </span>
    </div>

    """
    description_extended = movement_parsed['description']

    els = re.findall(
        r'(?si)div class="c-form-group\s+c-form-group--vertical.*?label\s+class="c-form-group__label.*?'
        '<span class="c-form-group__text".*?</div>',
        resp_text
    )
    fields_vals = {}  # type: Dict[str, str]
    for el in els:
        try:
            label = extract.remove_tags(extract.re_first_or_blank(
                '(?si)<label class="c-form-group__label c-form-group__label--text">.*?</label>',
                el
            ))
            val = extract.remove_tags(extract.re_first_or_blank(
                '(?si)<span class="c-form-group__text">.*?</span>',
                el
            ))
            fields_vals[label] = val
        except Exception as _e:
            logger.error(
                "{}: can't parse extended description: HANDLED EXCEPTION\n{}\n"
                "---\ntr html:\n{}\nUse short (default) description as description_extended".format(
                    fin_ent_account_id,
                    traceback.format_exc(),
                    el
                ))
            return description_extended

    for title in MOV_EXTENDED_DESCRIPTION_FIELDS:
        val = fields_vals.get(title, '')
        msg = '{}: {}'.format(title, val).strip() if val else ''
        description_extended += ' || {}'.format(msg).rstrip()

    # Get 'oficina' field and add to description_extended
    # it can be
    # 'Oficina'
    # 'Oficina Caixabank origen'
    # 'Oficina origen'
    # '... Oficina ... '
    for k, v in fields_vals.items():
        if 'oficina' in k.lower():
            msg = 'Oficina: {}'.format(extract.remove_extra_spaces(v)).strip()
            description_extended += ' || {}'.format(msg)
            break
    else:
        description_extended += ' ||'  # no office info found

    return description_extended


def get_movs_receipts_req_params(mov_details_req_params: dict) -> OrderedDict:
    receipt_req_params = OrderedDict([
        ('PN', 'GCT'),
        ('PE', '106'),
        ('FLAG_RESULTADO_NUEVO_EXTRACTO', 'DETALLE'),
        ('CLICK_ORIG', 'EOC_GCT_100'),
        ('TIPO_IMPRESION', 'PDF'),
        # 'F_YwKF0EA~8X9jAoXQQD7wAAAX0OuY_cPAyH4mYJnG8'
        ('REFVAL_SIMPLE_NUMERO_CUENTA', mov_details_req_params['REFVAL_SIMPLE_NUMERO_CUENTA']),
        ('NUMERO_MOVIMIENTO', mov_details_req_params['NUMERO_MOVIMIENTO']),  # '0014127'
        ('FECHA_CONTABLE', mov_details_req_params['FECHA_CONTABLE']),  # '2021314'
        ('CLAVE_DETALLE_3496', mov_details_req_params['CLAVE_DETALLE_3496']),  # 'D_3496_8'
        ('CLAVE_CONTINUACION_DETALLE_3496', ' 000000000000000000000000000 0000000'),
        ('TIPO_CUENTAS', 'VIG'),
        ('NUMERO_SUBMOVIMIENTO', ''),
        ('PRINT_DETALLE', 'PDFDET')
    ])

    return receipt_req_params


def _get_mov_details_req_params(row: str, refval_params: dict) -> dict:
    # OrderedDict([('PN', 'GCT'),
    #              ('PE', '103'),
    #              ('NUMERO_MOVIMIENTO', '0014112'),
    #              ('FECHA_CONTABLE', '2021313'),
    #              ('INDICADOR_COMUNICADOS', 'N'),
    #              ('CLOPWW', '046'),
    #              ('SUBCLO', '00000'),
    #              ('IMPORTE_COM', '000000000447658'),
    #              ('SIGNO_IMPORTE_COM', '-'),  # scraped '' - it's ok
    #              ('MONEDA_COM', 'EUR'),
    #              ('SALDO_ACTUAL', '000000039951432'),
    #              ('SIGNO_SALDO_ACTUAL', '+'),  # scraped '' - it's ok
    #              ('FECHA_VALOR', '09112021'),  # available in the list, can be parsed
    #              ('INDICA_SALDO', 'NNNN'),
    #              ('TIPO_BUSQUEDA', '05'),
    #              ('FECHA_COM', '09112021'),
    #              ('TIPO_COMUNICADO', '00000'),
    #              ('DESC_COMUNICADO', 'CANAL+OCIO+EUROPA'),
    #              ('REMITENTE', 'B47506811001'),
    #              ('NUMERO_RECIBO', '049433700102881'),   OR '000000000000000'
    #              ('OPCION_OPERACION', 'LISTACLOP'),
    #              ('CLICK_ORIG', 'FLX_GCT_100'),
    #              ('CLAVE_ANTERIOR', '++000000000000000000000000000+0000000'),
    #              ('CLAVE_CONTINUACION_SUM',
    #               '  000000000000000000000000000 0000000'),
    #              ('CLAVE_CONTINUACION_DETALLE_3496',
    #               '  000000000000000000000000000 0000000'),
    #              ('CLAVE_DETALLE_3496', 'D_3496_0'),
    #              ('NUMERO_SUBMOVIMIENTO', ''),
    #              ('TIPO_CUENTAS', 'VIG'),
    #              ('APLICACION_ORIGEN', 'CIA'),
    #              ('REFVAL_SIMPLE_NUMERO_CUENTA',
    #               'uxd8rmtPMAi7F3yua08wCAAAAX0GX0yoI75OK6iEjSs'),  # todo add then
    #              ('REFVAL_SIMPLE_CUENTA',
    #               'uxd8rmqS3tm7F3yuapLe2QAAAX0GX0yo~RVakHIPDJ8'),  # todo add then
    #              ('ID_DETALLE', 'idDettimeLine0014112')])
    det_req_params = extract.req_params_as_ord_dict(
        extract.re_first_or_blank('data-p-ct__movement_id="(.*?)"', row)
    )
    id_detalle_param = extract.re_first_or_blank('"p-CT__line__details__content_container" id="(.*?)"', row)
    det_req_params['ID_DETALLE'] = id_detalle_param
    det_req_params['REFVAL_SIMPLE_NUMERO_CUENTA'] = refval_params['REFVAL_SIMPLE_NUMERO_CUENTA']
    det_req_params['REFVAL_SIMPLE_CUENTA'] = refval_params['REFVAL_SIMPLE_CUENTA']
    return det_req_params


def get_movements_parsed(logger: ScrapeLogger,
                         fin_ent_account_id: str,
                         resp_text: str,
                         refval_params: dict) -> List[MovementParsed]:
    """Parses dev/7-1_movs_filtered_particulares.html"""

    movements_parsed_desc = []  # type: List[MovementParsed]
    if 'Sin operaciones a extractar' in resp_text:
        return movements_parsed_desc

    # 2 trs per movement
    rows = re.findall(r'(?si)<tr[^>]+data-p-ct__movement_id.*?</tr>\s*<tr[^>]+p-CT__line__details.*?</tr>',
                      resp_text)
    for row in rows:
        # For partic might be:
        # ['AKIWIFI NOSTRAVAN', '13 Ago 2020', 'Recibos varios', '1.861,79 €', '+ 881,93 €']
        # ['PR.FA127873151', '18 Ago 2020', '3,03 €', '+ 1.180,72 €']
        cells = [extract.remove_tags(h) for h in re.findall('(?si)<div.*?>(.*?)</div>', row)]
        try:
            # '24 Ene 2020' -> '24/01/2020'
            operation_date = _convert_spanish_date(cells[1])

            # 10/2021
            # <td class="">
            # <div class="margin--bottom-extrasmall">
            # TRANSF. A SU FAVOR
            #
            # </div>
            # <div class="u-flex">
            # <div class="s-date white_space--nowrap margin--right-normal">14 Oct 2021</div>
            #
            # <div class="p-CT__line__head__note">
            # <div class="p-CT__line__head__note__text">
            # 01824017-APLAZAME S.L.
            # </div>
            # </div>
            #
            # </div>
            # </td>
            descr = cells[0]
            descr_mas_datos = extract.text_wo_scripts_and_tags(extract.re_first_or_blank(
                '(?si)<div class="p-CT__line__head__note__text">(.*?)</div>', row
            ))
            descr_w_mas_datos = '{} ({})'.format(descr, descr_mas_datos) if descr_mas_datos else descr

            amount_str = cells[-4]
            amount = convert.to_float(amount_str)  # always positive
            # use classes to detect amount sign: "s-import--positive", "s-import--negative"
            if 's-import--negative' in row:
                amount = -amount
            # ix 3 for partic, 4 for emp
            temp_balance = convert.to_float(cells[-3])
        except Exception as _e:
            logger.error(
                "{}: can't parse movement: HANDLED EXCEPTION\n{}\n---\nmov html:\n{}\n"
                "Skip the movement".format(
                    fin_ent_account_id,
                    traceback.format_exc(),
                    row
                )
            )
            return movements_parsed_desc

        mov_details_req_params = _get_mov_details_req_params(row, refval_params)
        value_date = datetime.strptime(mov_details_req_params['FECHA_VALOR'], '%d%m%Y').strftime(
            project_settings.SCRAPER_DATE_FMT
        )

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr_w_mas_datos,
            'amount': amount,
            'temp_balance': temp_balance,
            'mov_details_req_params': mov_details_req_params,
            # can be any unique, to process parallel
            'id': '{}--({}/{})--{}'.format(operation_date, amount, temp_balance, uuid.uuid4())
        }
        movements_parsed_desc.append(movement_parsed)

    return movements_parsed_desc
