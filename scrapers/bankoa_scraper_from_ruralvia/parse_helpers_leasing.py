import datetime
import hashlib
import re
from collections import OrderedDict
from typing import Dict, List, Tuple, Optional

from custom_libs import convert
from custom_libs import date_funcs
from custom_libs import extract
from project.custom_types import (
    LeasingContractParsed, LeasingFeeParsed
)
from .custom_types import (
    SettlementReqParams,
    SettlementParsed,
    PDFReqParams,
    PDFParsed
)

__version__ = '1.0.2'

__changelog__ = """
1.0.2
VB
get_leasing_contract_details_from_html_resp: fee_number = 0 to keep var type
removed dead code
1.0.1
JFM: fixed fee number: BANKOA does not shows this data and we don't calculate it
1.0.0
DAF: init
new functions in parse_helpers:
get_isum_ciph_param
get_form_data_for_settlements_form_init
get_form_data_for_settlements_filter_formget_settlements_list
get_form_data_for_settlement_details
get_form_data_for_situation_form
get_leasing_contracts_from_html_resp
get_leasing_contract_details_from_html_resp
get_settlement_from_html_resp
get_leasing_fee_details_from_text_pdf_receipt
get_pdf_req_params
get_form_data_for_pdf
get_contract_number_and_description
get_receipt_description_from_contract_id
"""


def get_form_data_for_settlements_filter_form(
        contract_id: str,
        date_from_str: str,
        date_to_str: str) -> Dict[str, str]:
    contract_number, contract_description = get_contract_number_and_description(contract_id)

    req_params = OrderedDict([
        ('ISUM_OLD_METHOD', 'POST'),
        ('ISUM_ISFORM', 'true'),
        ('primeraVez', '1'),
        ('paginaActual', '0'),
        ('tamanioPagina', '25'),
        ('campoPaginacion', 'lista'),
        ('pagXpag', ''),
        ('clavePagina', 'BDP_FINAN_LEASING_LIQUID_LISTA'),
        ('cuenta', contract_number),
        ('indicador', 'L'),
        ('CUENTA_SELEC', '{}   {}'.format(contract_number, contract_description)),
        ('FECHADESDE', date_from_str.replace('/', '-')),
        ('FECHAHASTA', date_to_str.replace('/', '-')),
        ('IDIOMA', 'es_ES')
    ])
    return req_params


def get_settlements_list(resp_text: str) -> List[List[str]]:
    settlements_div = extract.re_first_or_blank(
        r'(?si)BODY_LISTA.*?<Table.*?table>.*?',
        resp_text)

    # Parses <tr id="TrColor" class="PAR" >
    # <td CLASS="listaC" >29-08-2019</TD>
    # <td CLASS="listaI" >
    # <A HREF="...l" onClick="validar(
    #     '1,00',
    #     '29-08-2019',
    #     'FACTURACION',
    #     'IMPUTADO',
    #     '1.450,19',
    #     '29-07-2019',
    #     '29-08-2019')
    settlements = re.findall(
        r'(?si)<tr id="TrColor.*?'
        r"'(.*?)',\s+"
        r"'(.*?)',\s+"
        r"'(.*?)',\s+"
        r"'(.*?)',\s+"
        r"'(.*?)',\s+"
        r"'(.*?)',\s+"
        r"'(.*?)'\).*?</tr>",
        settlements_div
    )
    return settlements


def get_form_data_for_settlement_details(
        contract_id: str,
        settlement_req_params: SettlementReqParams,
        date_from_str: str,
        date_to_str: str) -> Dict[str, str]:
    contract_number, contract_description = get_contract_number_and_description(contract_id)
    date_from = date_from_str.replace('/', '-')
    date_to = date_to_str.replace('/', '-')

    # Expecting
    # req_params = OrderedDict([
    #     ('ISUM_OLD_METHOD', 'POST'),
    #     ('ISUM_ISFORM', 'true'),
    #     ('primeraVez', '1'),
    #     ('paginaActual', '0'),
    #     ('tamanioPagina', '25'),
    #     ('campoPaginacion', 'lista'),
    #     ('pagXpag', ''),
    #     ('clavePagina', 'BDP_FINAN_LEASING_LIQUID_DETALLE'),
    #     ('indicador', 'L'),
    #     ('cuenta', '01380001110195424957'),
    #     ('CUENTA_SELEC', '01380001110195424957   LEASING MOBILIARIO'),
    #     ('FECHADESDE', '01-06-2019'),
    #     ('FECHAHASTA', '21-02-2020'),
    #     ('SECUENCIA', '1'),
    #     ('FECHA_LIQ', '29-06-2019'),
    #     ('TIPO_LIQ', 'FACTURACION'),
    #     ('SITUACION', 'IMPUTADO'),
    #     ('IMPORT', '1.450,19'),
    #     ('PERIODO_LIQ_INI', '29-05-2019'),
    #     ('PERIODO_LIQ_FIN', '29-06-2019'),
    #     ('IDIOMA', 'es_ES')
    # ])

    req_params = OrderedDict([
        ('ISUM_OLD_METHOD', 'POST'),
        ('ISUM_ISFORM', 'true'),
        ('primeraVez', '1'),
        ('paginaActual', '0'),
        ('tamanioPagina', '25'),
        ('campoPaginacion', 'lista'),
        ('pagXpag', ''),
        ('clavePagina', 'BDP_FINAN_LEASING_LIQUID_DETALLE'),
        ('indicador', 'L'),
        ('cuenta', contract_number),
        ('CUENTA_SELEC', contract_number + '   ' + contract_description),
        ('FECHADESDE', date_from),
        ('FECHAHASTA', date_to),
        ('SECUENCIA', '1'),
        ('FECHA_LIQ', settlement_req_params.FECHA_LIQ),
        ('TIPO_LIQ', settlement_req_params.TIPO_LIQ),
        ('SITUACION', settlement_req_params.SITUACION),
        ('IMPORT', settlement_req_params.IMPORT),
        ('PERIODO_LIQ_INI', settlement_req_params.PERIODO_LIQ_INI),
        ('PERIODO_LIQ_FIN', settlement_req_params.PERIODO_LIQ_FIN),
        ('IDIOMA', 'es_ES'),
    ])
    return req_params


def get_form_data_for_situation_form(
        contract_id: str,
        date_from_str: str) -> Dict[str, str]:
    contract_number, contract_description = get_contract_number_and_description(contract_id)
    date_limit = (date_funcs.get_date_from_str(date_from_str) + datetime.timedelta(days=365)).strftime(
        '%d-%m-%Y')
    date_now = date_funcs.today().strftime('%d-%m-%Y')
    req_params = OrderedDict([
        ('ISUM_OLD_METHOD', 'get'),
        ('ISUM_ISFORM', 'true'),
        # ('SELCTA', '01380001110195424957   LEASING MOBILIARIO'),
        ('SELCTA', contract_number + '   ' + contract_description),
        # ('cuenta', '01380001110195424957'),
        ('cuenta', contract_number),
        # ('descripcionCuenta', '   LEASING MOBILIARIO'),
        ('descripcionCuenta', '   ' + contract_description),
        ('clavePagina', 'BDP_LEASING_SALDO'),
        ('indicador', 'L'),
        # ('CUENTA_SELEC', '01380001110195424957   LEASING MOBILIARIO'),
        ('CUENTA_SELEC', contract_number + '   ' + contract_description),
        # ('fechaLimite', '15-03-2020'),
        ('fechaLimite', date_limit),
        # ('FECACTUAL', '12-02-2020'),
        ('FECACTUAL', date_now),
        ('clavePaginaVolver', 'MENUP_LEAS_SALDO_LEASING'),
        ('primeraVez', ''),
        ('paginaActual', ''),
        ('campoPaginacion', ''),
        ('tamanioPagina', ''),
    ])
    return req_params


def get_leasing_contracts_from_html_resp(resp_text: str) -> List[LeasingContractParsed]:
    """Parses from position_global
    <!--xxxxxxxxxxxxx   TABLA LEASING xxxxxxxxxxxxxxxxxxxxx -->
    ...
    <form method="post" name="form_lea_0"...
        ...
        <input type="hidden" name="cuenta" value="01380008310108672650">
        <input type="hidden" name="clavePagina" value="">
        <input type="hidden" name="opcion" value="1">
        <input type="hidden" name="fechaDesde" value="">
        <input type="hidden" name="fechaHasta" value="">

        <input type="hidden" name="descripcionCuenta" value="Cuenta de Leasing">
        <input type="hidden" name="CUENTA" value="01380008310108672650">
     </form>
     ...
     <!--xxxxxxxxxxxxx FIN TABLA LEASING  xxxxxxxxxxxxxxxxxxxxx -->

    VB: NOTE: can use extract.build_req_params_from_form_html_patched to get all params
    """

    table_html = extract.re_first_or_blank(
        r'(?si)[x]+\s+TABLA LEASING\s+[x]+.*?[x+]\s+FIN TABLA LEASING\s+[x]+',
        resp_text
    )
    # Expecting # [('60.502,14', '01380001110195424957', 'LEASING MOBILIARIO')]
    leasings_raw = re.findall(
        '(?si)<td class="totImplista".*?\-(\d+(?:\.\d+),\d\d).*?'
        r'(?si)<input type="hidden" name="cuenta" value="(\d+)">.*?'
        r'<input type="hidden" name="descripcionCuenta" value="(.*?)">',
        table_html)

    leasing_contracts_parsed = []  # type: List[LeasingContractParsed]
    # leasing_accounts = []  # type: List[LeasingAccount]
    for leasing_raw in leasings_raw:
        office_company_contract = leasing_raw[1][4:20]
        office = leasing_raw[1][4:8]
        contract_reference = leasing_raw[1]
        pending_repayment = leasing_raw[0]  # convert.to_float(f[3])
        contract_description = leasing_raw[2]

        hashbase = 'BANKOA{}{}'.format(
            office_company_contract,  # office + company + contract
            contract_reference  # contract_reference
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()

        contract_parsed = {
            'office': office,
            'contract_reference': contract_reference,
            'pending_repayment': pending_repayment,
            'keyvalue': keyvalue,
            'has_details': True,
            'post_data': contract_reference + ' | ' + contract_description
        }
        leasing_contracts_parsed.append(contract_parsed)

    return leasing_contracts_parsed


def get_leasing_contract_details_from_html_resp(
        resp_text: str,
        contract_parsed: LeasingContractParsed,
        settlements: List[SettlementParsed]) -> Tuple[bool, LeasingContractParsed, List[LeasingFeeParsed]]:

    # Parsing 041_resp_leasing_situacion_account.html
    fc = dict(re.findall(r'(?si)<tr.*?<td.*?>(.*?)<.*?<td.*?>(.*?)<.*?</tr', resp_text))  # type: Dict[str, str]

    try:
        contract_parsed['contract_date'] = fc["Fecha Formalización"]
        contract_parsed['amount'] = convert.to_float(fc["Precio Total"])
        contract_parsed['taxes'] = convert.to_float(fc["Tipo Impuesto (%)"])
        contract_parsed['initial_interest'] = convert.to_float(fc["Interés (%)"])
        contract_parsed['fees_quantity'] = ''  # Can be calculated but bank does not give us this value.
        # Initial and current interest are the same, review this. Bank only give us one interest value.
        contract_parsed['current_interest'] = convert.to_float(fc["Tipo Impuesto (%)"])
        contract_parsed['expiration_date'] = fc["Fecha Vencimiento"]
        contract_parsed['residual_value'] = convert.to_float(fc["Valor Residual"])
    except Exception as exc:
        return False, contract_parsed, []

    leasing_fees_parsed = []
    for settlement in settlements:
        fee_amount = convert.to_float(settlement.importe_str)
        # Bankoa doesn't give us this value, calculated
        amount = convert.to_float(settlement.capital_facturado) + convert.to_float(settlement.interes_deudor)
        fee_reference = settlement.numero_factura
        hashbase = 'BANKOA{}/{}-{}-{}-{}'.format(
            contract_parsed['contract_reference'],
            fee_reference,  # Bankoa leasing fee number is only available after pdf file is available.
            settlement.fecha_liq,  # operational_date
            amount,  # amount.
            settlement.precio_pendiente  # pending_repayment
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()

        fee_parsed = {
            'fee_reference': "{}/{}".format(contract_parsed['contract_reference'], fee_reference),
            'fee_number': 0,  # Bankoa does not show fee number
            'operational_date': date_funcs.convert_to_ymd(settlement.fecha_liq, from_fmt='%d-%m-%Y'),
            'currency': 'EUR',  # Bankoa does not show currency
            'amount': amount,
            'taxes_amount': convert.to_float(settlement.impuestos),
            'insurance_amount': 0.00,
            'fee_amount': fee_amount,
            'financial_repayment': convert.to_float(settlement.capital_facturado),
            'financial_performance': convert.to_float(settlement.interes_deudor),
            'pending_repayment': convert.to_float(settlement.precio_pendiente),
            'state': '',
            'keyvalue': keyvalue,
            'statement_id': None,
            'contract_id': None,
        }
        leasing_fees_parsed.append(fee_parsed)

    return True, contract_parsed, leasing_fees_parsed


def get_settlement_from_html_resp(
        settlement_req_params: SettlementReqParams,
        pdf_file_parsed: PDFParsed,
        resp_text: str) -> SettlementParsed:

    capital_facturado = extract.re_first_or_blank(
        r'(?si)<td.*?CAPITAL FACTURADO</TD>.*?CLASS="implista" >(.*?)</TD',
        resp_text)

    interes_deudor = extract.re_first_or_blank(
        r'(?si)<td.*?INTERÉS DEUDOR</TD>.*?CLASS="implista" >(.*?)</TD',
        resp_text)

    impuestos = extract.re_first_or_blank(
        r'(?si)<td.*?IMPUESTOS</TD>.*?CLASS="implista" >(.*?)</TD',
        resp_text)

    comision_apertura = extract.re_first_or_blank(
        r'(?si)<td.*?COMISIÓN APERTURA</TD>.*?CLASS="implista" >(.*?)</TD',
        resp_text)

    settlement_parsed = SettlementParsed(
        fecha_liq=settlement_req_params.FECHA_LIQ,  # '29-11-2019'
        tipo_liq=settlement_req_params.TIPO_LIQ,  # 'FACTURACION' # 'CONSTITUCION'
        situacion=settlement_req_params.SITUACION,  # 'IMPUTADO'
        importe_str=settlement_req_params.IMPORT,  # '1.450,19'
        periodo_liq_ini=settlement_req_params.PERIODO_LIQ_INI,  # '29-10-2019'
        periodo_liq_fin=settlement_req_params.PERIODO_LIQ_INI,

        capital_facturado=capital_facturado,  # '1.126,63' FACTURACION
        interes_deudor=interes_deudor,  # '71,87' Only on FACTURACION
        impuestos=impuestos,  # '251,69' CONSTITUCION and FACTURACION
        comision_apertura=comision_apertura,  # '250,00' Only on CONSTITUCION
        numero_factura=pdf_file_parsed.fee_number,  # L2000012
        precio_pendiente=pdf_file_parsed.pending_repayment,
    )
    return settlement_parsed


# Parses pdf fee receipt file.
# Bankoa has two different pdf file models, see dev folder for examples
def get_leasing_fee_details_from_text_pdf_receipt(pdf_text: str) -> Optional[PDFParsed]:
    # Look for fee number and other pdf data in leasing_receipt_model_2 pdf text
    fee_number = extract.re_first_or_blank(r'(?i)Núm. Factura: (.*?)\n', pdf_text)

    if fee_number:
        pending_repayment = extract.re_first_or_blank(r'(?i)PRECIO PENDIENTE: (.*?)\n', pdf_text)

    else:
        # Look for fee number and other pdf data in leasing_receipt_modell_1 pdf text
        fee_number = extract.re_first_or_blank(r'(?i)Factura.*?\n.+?\n.+?\n.+?\n(.+?)\n', pdf_text)
        pending_repayment = extract.re_first_or_blank(r'(?i)Precio pendiente de pago\s+(.*?)\s+.*?\n', pdf_text)

    if not fee_number:
        return None

    pdf_parsed = PDFParsed(
        fee_number=fee_number,
        pending_repayment=pending_repayment
    )
    return pdf_parsed


def get_pdf_req_params(
        contract_id: str,
        liquidation_date: str,
        amount_str_param,
        resp_text: str) -> Optional[PDFReqParams]:
    movements_text = extract.re_first_or_blank(r'(?si)>(Fecha Operación.*?Fecha Valor.*?)</div>', resp_text)
    # re.findall(r'abrirDoc\((.*?\'-479.91\'.*?)\)', resp_text)
    # onClick = "javascript:abrirDoc('01380001120195420021', '0138', '03-02-2020 00:00:00.000', '02-02-2020 00:00:00.000',  '-479,91', 'HL','195420021','0000056','','0');return false;" >

    receipt_description = get_receipt_description_from_contract_id(contract_id)
    trs = re.findall('(?si)<tr[^>]+>(.*?)</tr>', movements_text)
    for tr in trs:
        # Find and parse the exact movement == settlement_parsed
        tds = re.findall('(?si)<td[^>]+>(.*?)</td>', tr)
        # PDF file uses to be available a few days after movement exists.
        # That will make tds[5] '{IndexError}raise list index out of range'
        if len(tds) < 6:
            continue

        operation_date = tds[1]  # 03-02-2020
        if operation_date != liquidation_date:
            continue
        amount_str = tds[3].strip('-')  # "-479,91"
        if convert.to_float(amount_str) != convert.to_float(amount_str_param):
            continue

        # value_date = tds[1]  # 02-02-2020
        # amount = convert.to_float(amount_str)
        descr = tds[2].strip()  # RECIBO LEASING0200990356
        if descr != receipt_description:
            continue
        # temp_balance = convert.to_float(tds[4])  # "27.601, 44" -> 27601.44
        js_data = re.findall("'(.*?)'", extract.re_first_or_blank(r'javascript:abrirDoc\(.*?\)', tds[5]))
        if len(js_data) != 10:
            continue

        pdf_req_params = PDFReqParams(
            acuerdo=js_data[0][-10:],  # '0195420021',
            Entidad=js_data[1],  # '1038'
            fechaValor=js_data[2][:10],  # '2020-02-02'
            fechaOperacion=js_data[3][:10],  # '2020-02-03'
            importe=js_data[4].strip('-'),  # '-479.91'
            origenApunte=js_data[5],  # 'HL'
            # 'BDP_PAS_GENERA_DOC'
            clavePagina=extract.re_first_or_blank(r'document.FORM_RVIA_1.clavePagina.value\s*=\s*"(.*?)"',
                                                  resp_text),
            acuerdoDocumento=js_data[6],  # '195420021'
            numeroSecuencialApunteDoc=js_data[7],  # '0000056'
            codigoDocumento=js_data[8],  # ''
            numSecPDF=js_data[9],  # '0'
        )
        return pdf_req_params

    # Didn't find the movement
    return None


def get_form_data_for_pdf(pdf_req_params: PDFReqParams) -> OrderedDict:
    req_params = OrderedDict([
        ('ISUM_OLD_METHOD', 'post'),
        ('ISUM_ISFORM', 'true'),
        ('acuerdo', pdf_req_params.acuerdo),
        ('Entidad', pdf_req_params.Entidad),  # '0138'
        ('fechaValor', pdf_req_params.fechaValor),  # '2020-02-02',
        ('fechaOperacion', pdf_req_params.fechaOperacion),  # '2020-02-03',
        ('importe', pdf_req_params.importe),  # '479.91',
        ('origenApunte', pdf_req_params.origenApunte),
        ('clavePagina', pdf_req_params.clavePagina),  # 'BDP_PAS_GENERA_DOC'
        ('acuerdoDocumento', pdf_req_params.acuerdoDocumento),  # '195420021',
        ('numeroSecuencialApunteDoc', pdf_req_params.numeroSecuencialApunteDoc),  # '0000056',
        ('codigoDocumento', pdf_req_params.codigoDocumento),
        ('numSecPDF', pdf_req_params.numSecPDF),
    ])
    return req_params


def get_contract_number_and_description(contract_id: str) -> Tuple[str, str]:
    contract_number = contract_id.split(' | ')[0]
    contract_description = contract_id.split(' | ')[1]
    return contract_number, contract_description


def get_receipt_description_from_contract_id(contract_id: str) -> str:
    return 'RECIBO LEASING' + contract_id[10:20]
