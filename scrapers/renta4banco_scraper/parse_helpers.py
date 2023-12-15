import html
import re
from typing import List, Tuple

from custom_libs import convert
from custom_libs import date_funcs
from custom_libs import extract
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed


def get_token(resp_text: str) -> str:
    return extract.re_first_or_blank(r'(?s)name="TOKEN"\s+value="(.*?)">', resp_text)


def get_organization_title(resp_text: str) -> str:
    """
    Parses
        function getNombreUsuario() {
        return 'AMPER SA  ';
    }
    """
    org_title = extract.re_first_or_blank(r"(?si)function getNombreUsuario.*?return\s*'(.*?)'", resp_text).strip()
    return org_title


def get_date_to_str_from_page(resp_text: str) -> str:
    """
    >>> page = '[11528] Le informamos que la fecha hasta no debe ser superior 23 de julio de 2018'
    >>> get_date_to_str_from_page(page)
    '23/07/2018'
    """
    try:
        # '23', 'julio', '2018'
        # 2 steps for type checker
        dmy = re.findall(r'no debe ser superior (\d+) de (\w+) de (\d+)', resp_text)[0]  # type: Tuple[str, str, str]
        d, m, y = dmy
    except:
        return ''
    m_num = date_funcs.month_esp_to_num_str(m)
    if m_num == '':
        return ''
    d = d if len(d) > 1 else '0' + d
    return "{}/{}/{}".format(d, m_num, y)


def get_accounts_parsed(resp_text: str) -> List[AccountParsed]:
    accounts_parsed = []  # type: List[AccountParsed]
    accounts_raw = re.findall(r'(?si)id="outLimOperHome">(.*?)</strong>(.*?)</p>.*?IBAN:\s+(ES\d+)', resp_text)
    # [('400.698,44', ' €.', 'ES9700830001110053637032')]
    for acc_raw in accounts_raw:
        balance = convert.to_float(acc_raw[0])
        account_no = acc_raw[2]
        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
        currency = 'EUR' if '€' in html.unescape(acc_raw[1]) else 'USD'

        account_parsed = {
            'account_no': account_no,
            'balance': balance,
            'account_type': account_type,
            'currency': currency
        }
        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed_mi_patrimonio(resp_text: str, currency: str) -> List[MovementParsed]:
    movements_parsed_asc = []  # type: List[MovementParsed]
    table = extract.re_first_or_blank(
        r'(?si)<h2[^<>]*><span>Saldo en\s*{}\s*Liquidado</span></h2>.*?<table[^<>]*>(.*?)</table>'.format(
            currency
        ),
        resp_text
    )
    rows = re.findall(r'(?si)<tr.*?>(.*?)</\s*tr>', table)
    for row in rows:
        cells = re.findall(r'(?si)<td.*?>(.*?)</\s*td>', row)
        if len(cells) < 6 or cells[0] == '':
            continue

        amount_d_str = cells[2].strip()
        amount_h_str = cells[3].strip()

        # initial month balance like
        # SALDO ANTERIOR ...
        if not (amount_h_str or amount_d_str):
            continue

        if amount_h_str and amount_d_str:
            raise Exception('unexpected amount_h_str and amount_d_str. Check the layout: {}'.format(
                table
            ))

        if amount_h_str:
            amount = convert.to_float(amount_h_str)
        else:
            amount = -(convert.to_float(amount_d_str))

        operation_date = cells[0]  # '02/07/2018'
        value_date = operation_date  # no info on the page
        description = extract.remove_tags(cells[1])
        temp_balance = convert.to_float(cells[4])
        temp_balance_signchar = cells[5].strip()  # H+ /D-
        if temp_balance_signchar.lower() == 'd':
            temp_balance = -temp_balance

        mov_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance,
        }
        movements_parsed_asc.append(mov_parsed)

    return movements_parsed_asc


def get_movements_parsed(resp_text: str) -> List[MovementParsed]:
    movements_parsed = []  # List[MovementParsed]
    table = extract.re_first_or_blank(
        '(?si)<h6>MOVIMIENTOS DEL PERIODO EN EURO</h6>.*?<table.*?>(.*?)</table>',
        resp_text
    )
    rows = re.findall(r'(?si)<tr.*?>(.*?)</\s*tr>', table)
    for row in rows:
        cells = re.findall(r'(?si)<td.*?>(.*?)</\s*td>', row)
        if len(cells) < 4 or cells[0] == '':
            continue

        operation_date = cells[0]  # '02/07/2018'
        value_date = operation_date  # no info on the page
        description = extract.remove_tags(cells[1])
        amount = convert.to_float(cells[2])
        temp_balance = convert.to_float(cells[3])

        mov_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance,
        }
        movements_parsed.append(mov_parsed)

    return movements_parsed
