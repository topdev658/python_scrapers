import re
from typing import List, Dict
from datetime import datetime

from custom_libs import extract
from project.custom_types import CorrespondenceDocParsed, PDF_UNKNOWN_ACCOUNT_NO


def get_access_gnp2(resp_text: str) -> str:
    """
    Parse

    var clienteCajaEmpresa="0030248450";
    """
    gnp2 = re.findall(
        r'(?s)var clienteCajaEmpresa="([\d]{10})";',
        resp_text
    )

    return gnp2[0]


def get_gcuenta_numbers(resp_text: str) -> List[Dict[str, str]]:
    account_numbers_string = re.findall(
        r'(?s)var cuentasVigentes = "([0-9,]{0,})";',
        resp_text
    )[0]

    account_numbers = account_numbers_string.split(',')
    accounts = []
    for account in account_numbers:
        account_dict = {}
        account_dict['gcuenta'] = account
        account_dict['iban'] = extract.re_first_or_blank(
            '(?si)id="item-' + account + '-ccc">(.*?)</span>',
            resp_text).replace(' ', '')
        accounts.append(account_dict)
    return accounts


def get_correspondence_from_list(
        accounts_for_corr: List[Dict[str, str]],
        resp_text: str) -> List[CorrespondenceDocParsed]:
    corrs = []  # type: List[CorrespondenceDocParsed]
    corr_table = extract.re_first_or_blank('(?si)<table class="tabla">.*?</table>', resp_text)
    trs = re.findall('(?si)<tr.*?</tr>', corr_table)
    for tr in trs:
        rows = re.findall('(?si)<td.*?</td>', tr)
        if not rows:
            continue

        corr_date_str = extract.remove_tags(rows[0])
        corr_date = datetime.strptime(corr_date_str, '%d/%m/%Y')
        corr_type = extract.remove_tags(rows[1])
        corr_descr = extract.remove_tags(rows[2])
        req_link = extract.re_first_or_blank('class="sinSubrayado marginleft5" href="(.*?)"', rows[3])

        gcuenta = extract.re_first_or_blank(
            'GCUENTA=(.*?)&',
            req_link
        )

        account_no = next((item['iban'] for item in accounts_for_corr if gcuenta[-10:] in item['iban']), PDF_UNKNOWN_ACCOUNT_NO )

        corr = CorrespondenceDocParsed(
            type=corr_type,
            account_no=account_no,
            operation_date=corr_date,
            value_date=None,
            amount=None,
            currency=None,
            descr=corr_descr,
            extra={
                'req_link': req_link
            }
        )
        corrs.append(corr)
    return corrs