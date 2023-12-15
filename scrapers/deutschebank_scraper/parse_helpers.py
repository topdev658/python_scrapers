import re
from typing import Dict, List, Union

import xlrd

from custom_libs import convert
from custom_libs import extract
from custom_libs import iban_builder
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed


COLUMNS_LEN_TO_PROCESS = 8  # to skip parsing if less than necessary columns


def _get_rows(resp_text: str) -> List[str]:
    rows = re.findall('(?si)<tr.*?</tr>', resp_text)
    return rows


def _get_columns(row_html_text: str) -> List[str]:
    columns = re.findall('(?si)<td.*?</td>', row_html_text)
    return columns


def parse_accounts_overview(resp_text: str) -> List[AccountParsed]:
    """
    get data from table
    """

    accounts_parsed = []  # type: List[AccountParsed]
    rows = _get_rows(resp_text)
    currency = ''
    for row in rows:
        account = {}  # type: AccountParsed
        columns = _get_columns(row)

        if len(columns) < COLUMNS_LEN_TO_PROCESS:
            # not accounts' table
            continue

        columns_texts = [extract.remove_tags(column).strip() for column in columns]

        if columns_texts[0]:
            # currency from first column, and continue
            currency = columns_texts[0]
            continue

        if not columns_texts[1]:
            # subtotal row
            continue

        account['financial_entity_account_id'] = columns_texts[2]
        # convert only if correct iban
        if len(account['financial_entity_account_id']) == 20:
            account['account_no'] = iban_builder.build_iban('ES', account['financial_entity_account_id'])
        else:
            account['account_no'] = account['financial_entity_account_id']
        account['company_title'] = re.sub(r'\s+', ' ', columns_texts[1])
        account['currency'] = currency
        account['balance'] = convert.to_float(columns_texts[5])

        account['account_type'] = ACCOUNT_TYPE_CREDIT if account['balance'] < 0 else ACCOUNT_TYPE_DEBIT

        accounts_parsed.append(account)

    return accounts_parsed


def parse_movements_from_resp_excel(resp_content: bytes) -> List[MovementParsed]:
    book = xlrd.open_workbook(file_contents=resp_content)
    sheet = book.sheet_by_index(0)

    movements_parsed = []  # type: List[MovementParsed]
    for row_num in range(6, sheet.nrows):
        movement = {}
        cells = sheet.row_values(row_num)

        movement['operation_date'] = cells[0].replace('.', '/')
        movement['value_date'] = cells[1].replace('.', '/')
        movement['description'] = re.sub(r'\s+', ' ', cells[2].strip())  # remove redundant spaces
        movement['amount'] = convert.to_float(cells[3])
        movement['temp_balance'] = convert.to_float(cells[4])

        movements_parsed.append(movement)

    return movements_parsed


def get_new_date_from_if_restrictions(resp_text: str) -> str:
    """To replace current date_from due to getting errors if it's too early"""
    new_date_from_str = ''
    # in EN: 'Transaction not exists from the selected date', 'You can query from date'
    if ('No existen movimientos para la fecha inicial seleccionada' in resp_text
            and 'Puede consultar movimientos desde' in resp_text):
        new_date_from_str = extract.re_first_or_blank(
            r'Puede consultar movimientos desde.*?(\d+[.]\d+[.]\d+)',
            resp_text
        )
    return new_date_from_str
