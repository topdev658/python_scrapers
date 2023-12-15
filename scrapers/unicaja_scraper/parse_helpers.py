import re
from typing import List, Optional, Tuple

import xlrd

from custom_libs import convert
from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import Response
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed


def get_organization_title(resp_text: str) -> str:
    return extract.remove_tags(
        extract.re_first_or_blank('(?si)<strong>Titular contrato:</strong>(.*?)</div>', resp_text)
    ).strip()


def get_contracts(resp_text: str) -> List[str]:
    if 'LISTADO DE CONTRATOS' not in resp_text:
        return []
    contracts_nums = list(set(
        re.findall(r'numContrato=(\d+)', resp_text)
    ))
    return contracts_nums


def get_accounts_parsed(resp_text: str) -> List[AccountParsed]:
    accounts_htmls = re.findall(
        r'(?si)<tr class="filagris\d*">.*?</tr>|<tr class="filablanca\d*">.*?</tr>',
        resp_text
    )

    accounts_parsed = []  # type: List[AccountParsed]
    for account_html in accounts_htmls:

        tds = [
            extract.remove_tags(td)
            for td in re.findall('(?si)<td[^>]*>(.*?)</td>', account_html)
        ]

        # '<tr class="filablanca"><td colspan="6">&nbsp;</td></tr>' in the end -> [""]
        if tds == [""]:
            continue

        account_no_raw = tds[1]  # 'ES42 2108 4832 0500 3350 7175'
        # 'ES42 2108 4832 0500 3350 7175' -> 'ES4221084832050033507175'
        account_no = re.sub(' ', '', account_no_raw)
        balance_str = tds[3].strip()  # -84.219,04 EUR
        currency = balance_str[-3:]  # EUR
        balance = convert.to_float(balance_str)  # -84219.04
        # balance_disponible = convert.to_float(tds[4])   # 15780.96   # not used for parsing now

        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

        account_parsed = {
            'account_no': account_no,
            'account_type': account_type,
            'currency': currency,
            'balance': balance,
            'financial_entity_account_id': account_no_raw
            # 'balance_str': balance_str,     # '20.582,46', for mob req
            # 'codmoneda': codmoneda,         # for mov req
            # 'numcta': numcta,               # for mov req
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_ppp_param_for_account_processing(resp_text: str, fin_ent_acc_id: str) -> str:
    """
    Find matching ppp param for given fin_ent_acc_id (iban with spaces)
    :param resp_text: resp text
    :param fin_ent_acc_id:  ie ES42 2108 4832 0500 3350 7175

    >>> t = '<SELECT class="form" name="ppp" id="id-ppp" >'\
            '<OPTION value="001"> ES42 7175</OPTION><OPTION value="002"> ES02 9690</OPTION></SELECT>'
    >>> get_ppp_param_for_account_processing(t, 'ES42 7175')
    '001'
    """

    ppp_form_hrml = extract.re_first_or_blank('(?si)<select[^>]*id="id-ppp"[^>]*>(.*?)</select>', resp_text)
    # [('001', ' ES42 2108 4832 0500 3350 7175'), ('002', ' ES02 2108 4832 0505 5315 9690')]
    ppp_options = re.findall(r'(?si)<option\s*value="(.*?)"\s*>(.*?)</option>', ppp_form_hrml)

    ppp_param = extract.by_index_or_blank([
        option[0] for option in ppp_options
        if fin_ent_acc_id in option[1].strip()
    ], 0)

    return ppp_param


def get_movements_parsed_from_excel_resp(resp_excel: Response) -> Tuple[List[MovementParsed], Optional[str]]:
    file_content = resp_excel.raw.read()  # type: bytes
    # no movements
    if not file_content.strip():
        return [], None

    if b'No existen movimientos para listar' in file_content:
        return [], None

    try:
        book = xlrd.open_workbook(file_contents=file_content)
    except Exception as exc:
        # Don't decode file_content to str to handle all possible cases (when it contains non-utf8 bytes)
        return [], "Can't extract movements. Invalid excel: {}:\n{!r}".format(exc, file_content)
    sheet = book.sheet_by_index(0)

    movements_parsed = []  # type: List[MovementParsed]
    for row_num in range(5, sheet.nrows):
        movement = {}
        cells = sheet.row_values(row_num)
        # 42430.0 - days from year 1900
        movement['operation_date'] = date_funcs.get_date_using_td_days_since_epoch(cells[0])
        movement['value_date'] = date_funcs.get_date_using_td_days_since_epoch(cells[0])
        movement['description'] = re.sub(r'\s+', ' ', cells[2].strip())  # remove redundant spaces
        movement['amount'] = cells[3]
        movement['temp_balance'] = cells[5]

        movements_parsed.append(movement)

    return movements_parsed, None
