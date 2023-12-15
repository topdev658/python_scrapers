import html
import re
from typing import List, Optional, Tuple

from custom_libs import convert
from custom_libs import extract
from custom_libs import iban_builder
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed

__version__ = '2.3.0'
__changelog__ = """
2.3.0 2023.04.17
refactored movement_parsed param 'has_final_receipt'
2.2.0
get_filial_account_parsed: use _build_req_iban_data to for PDFs for Empresas (Nuevo) access type
2.1.0
get_filial_movements_parsed: 'has_receipt' stub field added to align with common movs
"""

#  [(title, dict_key), ...]
MOV_EXTENDED_DESCRIPTION_KEYS = [
    # \d+ corresponds to the page index of the movement
    ('Concepto', r'con\d+'),
    ('Fecha de operación', r'f_op\d+'),
    ('Fecha valor', r'fechaValorMT\d+'),
    ('Código de operación', r'ope\d+'),
    ('Oficina de origen', r'oficinaOrigen\d+'),
    ('Referencia 1', r'ref1\d+'),  # None or str
    ('Referencia 2', r'ref2\d+'),  # None or str
    # ('Importe', 'amount'),  # float
    ('Nº Documento', r'doc\d+'),  # None or str
    # ('Información adicional', 'additionalInformation'),
]


def _build_req_iban_data(account_iban: str):
    """
    To align with non-filial accounts. Need for movement processing
    >>> res = _build_req_iban_data('ES 80 0049 4711 51 2516745213')
    >>> res == {'countryIban': 'ES', 'dcIban': '80', 'entity': '0049', 'office': '4711', 'dc': '51', \
                'accountNumber': '2516745213'}
    True
    """
    account_iban = account_iban.replace(' ', '')
    return {
        "countryIban": account_iban[:2],  # ES
        "dcIban": account_iban[2:4],  # 80
        "entity": account_iban[4:8],  # 0049
        "office": account_iban[8:12],  # 4711
        "dc": account_iban[12:14],  # 51
        "accountNumber": account_iban[14:],  # 2516745213
    }


def get_filial_account_parsed(resp_text: str, balance_str: str,
                              logger: ScrapeLogger) -> Optional[AccountParsed]:
    """
    :param resp_text: resp_text doesn't contain balance because we had to pass it from
                      filial accounts list page explicitly
                      Instead this we just pass it here as param
    :param balance_str: like '2.306.243,65 EUR'
    :param logger: scraper's logger
    """
    fin_ent_account_id = extract.re_first_or_blank(
        r"cta_ccc\='([^']*?)'",  # '0049 1837 59 2810463257'
        resp_text
    ).strip()

    # iban
    try:
        account_no = iban_builder.build_iban('ES', fin_ent_account_id)
    except Exception as e:
        logger.error("Can't build correct IBAN, got exception: {} from resp\n{}. Abort".format(
            e,
            resp_text
        ))
        return None

    if balance_str:
        currency = balance_str.split()[1][:3]
        balance = convert.to_float(balance_str)
    else:
        currency = 'EUR'
        balance = 0

    company = extract.re_first_or_blank(
        '(?si)Titulares cuenta:</td>.*?<td[^>]*>(.*?)</td>',
        resp_text
    ).strip()

    account_parsed = {
        'financial_entity_account_id': fin_ent_account_id,
        'account_no': account_no,
        'account_type': ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT,
        'company': company,
        'balance': balance,
        'currency': currency,
        'iban_data': _build_req_iban_data(account_no)  # for PDF receipt requests
    }

    return account_parsed


def _get_extended_description(mov_html: str, descr_short: str) -> str:
    """
    Parses mov from get_filial_movements_parsed
    and produces extended description
    similar to parse_helpers for non-branch movs
    """

    # description_extended = descr_short  # replaced by val with 'Concepto' tag
    description_extended = ''
    for title, field in MOV_EXTENDED_DESCRIPTION_KEYS:
        # handle Nones
        val = (extract.re_first_or_blank('(?i)var {}[=]"(.*?)"'.format(field), mov_html) or '').strip()

        # NOT USED NOW
        if field == 'movementType':
            # convert to known human-readable vals or leave it as is
            if val == 'H':
                val = 'Haber'
            elif val == 'D':
                val = 'Debe'

        msg = '{}: {}'.format(title, extract.remove_extra_spaces(str(val)))
        description_extended += " || {}".format(msg)

    return description_extended.lstrip(' |')  # remove first redundant separator


# ONLY FOR Empresas e Instituciones
# Empresas (Nuevo) with filiales uses general process_account
# TODO switch to Empresas (Nuevo)
def get_filial_movements_parsed(
        resp_text: str,
        last_known_temp_balance: Optional[float]) -> Tuple[List[MovementParsed], Optional[float]]:
    movements_parsed_asc = []  # type: List[MovementParsed]

    """
    FROM
    
    num_mov++
    var f_op3="23-12-2019"
    var f_va3="23-12"
    var ope3=" 71"
    var ref13="            "
    var ref23="                "
    var doc3="0000000000"
    var conc1_3="TRANSFERENCIA DE ESTACION SERVICIO BARDENAS SA, CONCEPTO A-7"
    var conc2_3="1008163.                                                    "
    var conc3_3="                                                            "
    var descAbrev3="ABONO TRANSFERENCI"
    var con3="TRANSFERENCIA DE ESTACION SERVICIO BARDENAS SA, CONCEPTO A-7 1008163.                                                                                                                 "
    var imp3="+      206.051,93 "
    var importeBKS3="206051.93"
    var signoImporteBKS3="H"
    var fechaOperacionBKS3="20191223"
    var fechaValorBKS3="20191223"
    var fechaValorMT3="23-12-2019"
    var posMovimiento3=4
    var oficinaOrigen3="6668"
    var numMovimiento3="00.004"
    var numMovimientoMT3="00004"
    document.writeln('<tr>')
    document.writeln('<td align=left valign=top><input type=radio name=botonmov  
        Onclick="{actualiza1(f_op3,f_va3,ope3,ref13,ref23,doc3,imp3);actualiza2(con3);
        actualizaNuevoDetalle(fechaOperacionBKS3,fechaValorBKS3,ope3,ref13,ref23,doc3,
        importeBKS3,signoImporteBKS3,conc1_3,conc2_3,conc3_3, descAbrev3, posMovimiento3, 
        numMovimiento3, oficinaOrigen3);
        actualizaDetalleMvtosModeloTextos(fechaOperacionBKS3,fechaValorMT3,ope3,ref13,ref23,
        doc3,importeBKS3,signoImporteBKS3,conc1_3,conc2_3,conc3_3, descAbrev3, 
        posMovimiento3, numMovimientoMT3, oficinaOrigen3)}"></td>')
    document.writeln('<td class=tdrescent valign=top>23-12-2019</td>')
    document.writeln('<td class=tdrescent valign=top>23-12</td>')
    document.writeln('<td class=tdresizq valign=top>TRANSFERENCIA DE ESTACION SERVICIO BARDENAS SA, CONCEPTO A-7 1008163.                                                                                                                 </td>')
    document.writeln('<td class=tdresdcha valign=top>+      206.051,93 </td>')
    document.writeln('<td class=tdresdcha valign=top>+     1.921.672,56 </td>')
    document.writeln('</tr>')
    
    WAS FROM (prev version)
    
    document.writeln('<td align=left valign=top><input type=radio name=botonmov  Onclick="{actualiza1(f_op0,f_va0,
    ope0,ref10,ref20,doc0,imp0);actualiza2(con0);actualizaNuevoDetalle(fechaOperacionBKS0,fechaValorBKS0,ope0,ref10,
    ref20,doc0,importeBKS0,signoImporteBKS0,conc1_0,conc2_0,conc3_0, descAbrev0, posMovimiento0, numMovimiento0, 
    oficinaOrigen0);actualizaDetalleMvtosModeloTextos(fechaOperacionBKS0,fechaValorMT0,ope0,ref10,ref20,doc0,
    importeBKS0,signoImporteBKS0,conc1_0,conc2_0,conc3_0, descAbrev0, posMovimiento0, numMovimientoMT0, 
    oficinaOrigen0)}"></td>')
    document.writeln('<td class=tdrescent valign=top>02-03-2018</td>')
    document.writeln('<td class=tdrescent valign=top>02-03</td>')
    document.writeln('<td class=tdresizq valign=top>TRANSFERENCIA A FAVOR DE CONSPACE CONCEPTO PTMO EMPRESAS GRU PO
    </td>')
    document.writeln('<td class=tdresdcha valign=top>-       92.000,00 </td>')
    document.writeln('<td class=tdresdcha valign=top>+     1.926.209,65 </td>')
    document.writeln('</tr>')
    """
    movements_htmls = re.findall(
        r"(?si)num_mov\+\+.*?document.writeln\('</tr>'\)",
        resp_text
    )

    for mov_html in movements_htmls:
        tds = re.findall('<td.*?>(.*?)</td>', mov_html)
        operation_date = tds[1].replace('-', '/')  # 02/03/2018
        value_date_raw = tds[2]  # 02-03
        if not (operation_date and value_date_raw):
            continue

        value_date = (value_date_raw + '-' + operation_date.split('/')[-1]).replace('-', '/')
        description = re.sub(r'\s+', ' ', tds[3]).strip()
        amount = convert.to_float(re.sub(r'\s', '', html.unescape(tds[4])))
        temp_balance_raw = re.sub(r'\s', '', html.unescape(tds[5]))  # handle &nbsp

        # Stop the parsing on the first future movement if previous temp_balance is unknown!
        # REASON: the displayed account balance is equal
        # to the temp_balance of the most recent 'past' movement
        # Thus, if there are no 'past' movements, then displayed account_balance is 0 (it's unknown really)
        # and it breaks the calculations and then brings the balance integrity error
        # without the possibility to fix it automatically.
        # Earlier, the temp_balances of the future movements were
        # calculated from the temp_balance of last_known_temp_balance
        # which was extracted from account_balance,
        # but, as described above, it causes balance errors if there are no
        # previous movements with explicit temp_balances.
        # Now the last_known_temp_balance is optional (None or float) and
        # become float only if there movements with an explicit temp_balance.
        # Conclusion: if there are no previous movements with explicit temp_balances,
        # the scraper WILL NOT scrape the movements w/o temp_balances.
        if temp_balance_raw:
            temp_balance = convert.to_float(temp_balance_raw)
        else:
            if last_known_temp_balance is not None:
                # calc temp balance
                temp_balance = round(last_known_temp_balance + amount, 2)
            else:
                # stop if no previous movements at all with known temp_balance
                return movements_parsed_asc, None

        movement_parsed = {
            'value_date': value_date,
            'operation_date': operation_date,
            'description': description,
            'description_extended': _get_extended_description(mov_html, description),
            'amount': amount,
            'has_final_receipt': False,  # stub, not implemented TODO switch to Empresas (Nuevo)
            'temp_balance': temp_balance,  # optional, will be calculated later
        }
        last_known_temp_balance = temp_balance

        movements_parsed_asc.append(movement_parsed)

    return movements_parsed_asc, last_known_temp_balance
