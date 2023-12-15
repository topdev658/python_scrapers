import json
import re
from datetime import datetime
from typing import List

from custom_libs import extract
from project.custom_types import (
    AccountParsed, ACCOUNT_NO_TYPE_UNKNOWN, ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT,
    MovementParsed
)

__version__ = '1.3.0'
__changelog__ = """
1.3.0
parse_mov: mov_dict['balanceAmount']: handle blank str when provided instead of dict
1.2.0
recalc_mov_temp_balances_from_account_bal
1.1.0
handle unpaid status
1.0.0
init
"""


def get_noscript_img_urls(resp_text: str) -> List[str]:
    noscripts = re.findall('(?si)<noscript>(.*?)</noscript>', resp_text)
    img_urls = []  # type: List[str]
    for noscript in noscripts:
        img_url = extract.re_first_or_blank(r'(?si)<img\s+src="([^"]+)"', noscript)
        if img_url:
            img_urls.append(img_url)
    return img_urls


def get_accounts_parsed(resp_text: str, username: str) -> List[AccountParsed]:
    """
    Parses dict from dev_nojs/30_resp_dashboard.html
    """
    accounts_parsed = []  # type: List[AccountParsed]
    # 'Currencies as accounts' approach
    accounts_json_str = extract.re_first_or_blank(r'(?si)__initialProps__\s*=\s*({.*?});\s*</script>', resp_text)
    accounts_json = json.loads(accounts_json_str)
    # "balance": {
    #     "totalAvailable": {
    #       "raw": 35603.34,
    #       "formattedSymbolicISOCurrency": "35.603,34 USD"
    #     },
    #     "totalReserved": {
    #       "raw": 0,
    #       "formattedSymbolicISOCurrency": "0,00 USD"
    #     },
    #     "balances": [
    #       {
    #         "currency": "USD",
    #         "available": {
    #           "total": {
    #             "raw": 34591.83,
    #             "formattedCurrency": "34.591,83 USD"
    #           }
    #         }
    #       },
    #       {
    #         "currency": "EUR",
    #         "available": {
    #           "total": {
    #             "raw": 897.43,
    #             "formattedCurrency": "897,43 EUR"
    #           }
    #         }
    #       }
    #     ]
    account_dicts = accounts_json['readyFragments'][0]['initialState']['graphql']['data']['wallet']['balance'][
        'balances']
    for account_dict in account_dicts:
        # {"currency":"USD","available":{"total":{"raw":34591.83,"formattedCurrency":"34.591,83 USD"}}}
        currency = account_dict['currency']
        balance = float(account_dict['available']['total']['raw'])
        account_no = '{}_{}'.format(username, currency)

        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
        account_parsed = {
            'account_no': account_no,
            'balance': balance,
            'currency': currency,
            'account_type': account_type,
            'account_no_format': ACCOUNT_NO_TYPE_UNKNOWN,
        }
        accounts_parsed.append(account_parsed)

    return accounts_parsed


def _parse_mov(mov_dict: dict) -> MovementParsed:
    # {
    #   "description": "Pago a",
    #   "name": "STILL TRYING S.L."
    # }
    descr_dict = mov_dict['transactionDescription']
    descr = '{} {}'.format(descr_dict['description'], descr_dict['name'])
    # net (not gross!) see dev/Download.CSV (-a 31902, USD):
    # 04/10/2021 (gross: -174,2	fee: -174,2	net: 26402,27 tmp bal: 26402,27)
    # 04/10/2021 (gross: 262,65 fee: -9,23 net: 253,42  tmp bal (by net!): 26655,69)
    amount = float(mov_dict['netAmount']['amountUnformatted'])
    # from "2021-10-20T15:50:45.000Z"
    operation_date = datetime.strptime(mov_dict['transactionTimeUnformatted'].split('T')[0],
                                       '%Y-%m-%d').strftime('%d/%m/%Y')
    value_date = operation_date
    # "956.45" -> 956.45
    #  mov_dict['balanceAmount'] can be '', not dict
    temp_balance_str = mov_dict['balanceAmount']['amountUnformatted'] if mov_dict['balanceAmount'] else '0'
    temp_balance = float(temp_balance_str)
    currency = mov_dict['netAmount']['currency']  # 'EUR' or 'USD'

    mov = {
        'operation_date': operation_date,
        'value_date': value_date,
        'description': descr,
        'amount': amount,
        'temp_balance': temp_balance,
        'currency': currency  # do detect account by currency
    }
    return mov


def get_movements_parsed(resp_json: dict) -> List[MovementParsed]:
    """Parses 50_movs_filtered_by_currency.jsotruetruen"""
    movs_parsed_desc = []  # type: List[MovementParsed]

    mov_dicts = resp_json['data']['transactions']
    if not mov_dicts:
        # no movs -> mov_dicts is None
        return movs_parsed_desc
    for mov_dict in mov_dicts:
        if mov_dict['transactionStatus'] in ['Cancelado', 'Impagado']:
            continue

        mov = _parse_mov(mov_dict)
        movs_parsed_desc.append(mov)

        # Process secondary transactions before!
        # finance@gasmobi.com_USD, Amount=-29.98, TempBalance=36629.2, OperationalDate='20211029'
        for mov_sub_dict in mov_dict['secondaryTransactions']:
            mov = _parse_mov(mov_sub_dict)
            movs_parsed_desc.append(mov)

    return movs_parsed_desc


def recalc_mov_temp_balances_from_account_bal(
        account_balance: float,
        movs_parsed_desc: List[MovementParsed]) -> List[MovementParsed]:
    """
    Some movements can be extracted in different order comparing to
    the order how the website calculates temp balances.
    Solution: recalc all balances
    """
    temp_balance = account_balance
    movs_parsed_desc_calculated = []  # type: List[MovementParsed]
    for mov in movs_parsed_desc:
        mov_new = mov.copy()
        mov_new['temp_balance'] = temp_balance
        temp_balance = round(temp_balance - mov['amount'], 2)
        movs_parsed_desc_calculated.append(mov_new)
    return movs_parsed_desc_calculated

