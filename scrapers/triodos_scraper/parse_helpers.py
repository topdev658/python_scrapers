import re
from typing import Tuple, List
from urllib.parse import urljoin

from deprecated import deprecated

from custom_libs import convert
from custom_libs import extract
from project.custom_types import (
    ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT,
    AccountParsed, MovementParsed
)


@deprecated(reason='generate the URL directly using page_ix')
def get_next_movs_url(resp_text: str, resp_prev_url: str) -> Tuple[bool, str]:
    """:returns (has_next_page, next_page_url)"""

    # 'getmovementsaccount.do?page=1&methodController=getAccountMovementsByPeriod'
    # 'getmovementsaccount.do?page=2&methodController=getAccountMovementsByPeriod'
    next_movs_link = extract.re_first_or_blank(
        '<a href="(.*?)">Siguiente</a>',
        resp_text
    )
    if not next_movs_link:
        return False, ''
    return True, urljoin(resp_prev_url, next_movs_link)


def get_token(resp_text: str) -> str:
    return extract.re_first_or_blank('request_token: "(.*?)"', resp_text)


def get_organization_title(resp_text: str) -> str:
    title_one_contract = extract.re_first_or_blank(
        r'<span class="labeltext">\s*Contrato.*?<strong>(.*?)</strong>',
        resp_text
    ).strip()

    title_multicontract = extract.re_first_or_blank(
        r'(?si)<span class="labeltext">\s*Contrato.*?selected="selected">(.*?)</option>',
        resp_text
    ).strip()

    title = title_one_contract or title_multicontract
    return title


def _parse_accounts_html_str(accounts_html_str, account_type) -> List[AccountParsed]:
    accounts_htmls = re.findall(
        '(?si)<div class="product">.*?class="product-link plus"',
        accounts_html_str
    )

    accounts_parsed = []  # type: List[AccountParsed]
    for account_html in accounts_htmls:
        account_no = re.sub(
            r'\s', '',
            extract.re_first_or_blank('<span class="product-numero">(.*?)</span>', account_html)
        )
        balance_w_currency = extract.re_first_or_blank(
            '(?si)<span class="product-valor">(.*?)</span>',
            account_html
        ).strip()

        balance = convert.to_float(balance_w_currency)
        currency = 'EUR' if '€' in balance_w_currency else 'USD'

        account_parsed = {
            'account_no': account_no,
            'balance': balance,
            'currency': currency,
            'account_type': account_type
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_debit_accounts_parsed(resp_text: str) -> List[AccountParsed]:
    accounts_debit_html_str = extract.re_first_or_blank(
        '(?si)<div class="product-wrapper products-cuentas">(.*?)<a class="product-link" href="getpartial',
        resp_text
    )

    accounts_parsed = _parse_accounts_html_str(accounts_debit_html_str, ACCOUNT_TYPE_DEBIT)

    return accounts_parsed


def get_credit_accounts_parsed(resp_text: str) -> List[AccountParsed]:
    accounts_parsed = []  # type: List[AccountParsed]
    accs_table = extract.re_first_or_blank('(?si)<table.*?</table>', resp_text)
    accs_htmls = [
        row for row in
        re.findall('(?si)<tr.*?</tr>', accs_table)
        if ('<th' not in row)
    ]

    for acc_html in accs_htmls:
        columns = [extract.remove_tags(c) for c in re.findall('(?si)<td.*?</td>', acc_html)]
        balance_w_currency = columns[3]
        balance = convert.to_float(balance_w_currency)
        currency = 'EUR' if '€' in balance_w_currency else 'USD'
        account_parsed = {
            'account_no': re.sub(r'\s', '', columns[1]),
            'balance': balance,
            'currency': currency,
            'account_type': ACCOUNT_TYPE_CREDIT
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed(resp_text: str) -> Tuple[bool, List[MovementParsed]]:
    """
    Parses movements, returns (False, []) if expected, but didn't get movements
    :returns (is_success, movs_parsed)"""
    # no movements
    if 'No hay resultados para su búsqueda' in resp_text:
        return True, []

    movements_parsed_desc = []  # type: List[MovementParsed]

    movements_table = extract.re_first_or_blank('(?si)<table.*?</table>', resp_text)
    # exclude title and links details tr-s
    movements_htmls = [
        row for row in
        re.findall('(?si)<tr.*?</tr>', movements_table)
        if ('tr class="detalles"' not in row) and ('<th' not in row)
    ]

    for movement_html in movements_htmls:
        columns = [extract.remove_tags(c) for c in re.findall('(?si)<td.*?</td>', movement_html)]
        movement_parsed = {
            'operation_date': columns[1],
            'value_date': columns[2],
            'description': columns[3],
            'amount': convert.to_float(columns[4]),
            'temp_balance': convert.to_float(columns[5])
        }

        movements_parsed_desc.append(movement_parsed)

    return bool(movements_parsed_desc), movements_parsed_desc


def get_contracts_ids(resp_text: str) -> List[str]:
    contracts_ids = re.findall(
        r"javascript:changeCurrentContractUser\('(.*?)'\)",
        resp_text
    )
    return contracts_ids
