import re
from typing import List, Tuple, Optional

from custom_libs import convert
from custom_libs import extract
from project.custom_types import (
    ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT,
    AccountParsed, MovementParsed,
)


def get_account_parsed(resp_text: str, fin_ent_acc_id: str) -> AccountParsed:
    account_balance = convert.to_float(extract.re_first_or_blank(
        r'(?si)A - Saldo de Conta Corrente</td>\s*<td.*?>(.*?)</td>',
        resp_text
    ))

    account_parsed = {
        'account_no': fin_ent_acc_id,
        'account_type': ACCOUNT_TYPE_DEBIT if account_balance >= 0 else ACCOUNT_TYPE_CREDIT,
        'currency': 'BRL',  # Brasilian real
        'balance': account_balance,
    }
    return account_parsed


def get_movements_parsed(resp_text: str) -> Tuple[bool, List[MovementParsed]]:
    """:returns (ok, movements_parsed)"""
    movements_parsed_asc = []  # type: List[MovementParsed]
    movs_htmls = re.findall('(?si)<tr.*?</tr>', resp_text)
    temp_balance_prev = None  # type: Optional[float]
    for mov_html in movs_htmls:
        cells = [extract.remove_tags(cell) for cell in re.findall('(?si)<td.*?</td>', mov_html)]
        if len(cells) != 6:
            continue

        operation_date = cells[0]  # 11/10/2018
        # skip title
        if operation_date == 'Data':
            continue

        descr = re.sub(r'\s+', ' ', cells[2]).strip()
        # saldo initial
        if descr == 'SALDO ANTERIOR':
            temp_balance_prev = convert.to_float(cells[5])
            continue

        amount = convert.to_float(cells[4])

        # check for parsing error (couldn't set temp_balance_prev)
        if temp_balance_prev is None:
            return False, []

        temp_balance = round(temp_balance_prev + amount, 2)

        movement_parsed = {
            'operation_date': operation_date,
            # there is no information about value date in the web/excel
            'value_date': operation_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed_asc.append(movement_parsed)
        temp_balance_prev = temp_balance

    return True, movements_parsed_asc
