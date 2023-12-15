import datetime
import re
from typing import List, Optional

from custom_libs import date_funcs
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import (ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed)

__version__ = '1.1.0'
__changelog__ = """
1.1.0
get_accounts_parsed: upd (new resp)
"""


def get_accounts_parsed(resp_json: dict) -> List[AccountParsed]:
    """Parses 005_financial_overview.json
    ...
         {
        "id": "ES0182002000000000000000000477248086XXXXXXXXX",
        "classification": {
          "level": [
            {
              "id": "FIRST_LEVEL",
              "name": "INVERSION",
              "internalCode": "00001"
            },
            {
              "id": "SECOND_LEVEL",
              "name": "CUENTAS EN EUROS Y DIVISAS",
              "internalCode": "00004"
            },
            {
              "id": "THIRD_LEVEL",
              "name": "CUENTAS PERSONALES",
              "internalCode": "00056"
            }
          ]
        },
        "number": "ES5901820121160201685745",
        "numberType": {
          "id": "IBAN"
        },
        "countryId": "ES",
        "bank": {
          "id": "0182"
        },
        "branch": {
          "id": "0121"
        },
        "signedAuthorization": {
          "id": "INDISTINCT"
        },
        "currencies": [
          {
            "currency": "EUR",
            "isMajor": true
          }
        ],
        "participant": {
          "participantType": {
            "id": "HOLDER",
            "order": "2"
          },
          "name": "HOLDER"
        },
        "userAccessControl": [
          {
            "channel": {
              "id": "BBVANet"
            },
            "isVisible": true,
            "canOperate": true
          },
          {
            "channel": {
              "id": "CAJEROS"
            },
            "isVisible": true,
            "canOperate": true
          },
          {
            "channel": {
              "id": "BANCA_TELEFONICA"
            },
            "isVisible": true,
            "canOperate": true
          }
        ],
        "marketerEntity": {
          "id": "0182"
        },
        "product": {
          "id": "0000015109",
          "name": "CUENTAS PERSONALES",
          "description": "CUENTA VA CONTIGO"
        },
        "productType": "ACCOUNT",
        "formats": [
          {
            "number": "01820121002000000000168574",
            "numberType": {
              "id": "BOCF"
            }
          },
          {
            "number": "00000000000000000477248086",
            "numberType": {
              "id": "IUC"
            }
          },
          {
            "number": "01820121160201685745",
            "numberType": {
              "id": "CCC"
            }
          },
          {
            "number": "ES5901820121160201685745",
            "numberType": {
              "id": "IBAN"
            }
          }
        ],
        "isLegacy": false,
        "arrearsSituation": "NO_ARREARS",
        "detail": {
          "specificAmounts": [
            {
              "id": "availableBalance",
              "amounts": [
                {
                  "amount": 40010.46,
                  "currency": "EUR"
                },
                {
                  "amount": 40010.46,
                  "currency": "EUR"
                }
              ]
            },
            {
              "id": "currentBalance",
              "amounts": [
                {
                  "amount": 40010.46,
                  "currency": "EUR"
                },
                {
                  "amount": 40010.46,
                  "currency": "EUR"
                }
              ]
            }
          ],
          "expirationDate": "9999-12-31T00:00:00.000+0100"
        }
      }
      ...

    """
    accounts_dicts = [
        acc_dict for acc_dict in resp_json['data']['contracts']
        if acc_dict['productType'] == 'ACCOUNT'
    ]  # type: List[dict]

    accounts_parsed = []  # type: List[AccountParsed]
    for acc_dict in accounts_dicts:
        # skip inactive account
        # consider
        # 'availableBalance'
        # 'currentBalanceLocalCurrency'

        # From [{
        #     "id": "currentBalance",
        #     "amounts": [
        #         {
        #             "amount": 4112.82,
        #             "currency": "EUR"
        #         },
        #         {
        #             "amount": 4112.82,
        #             "currency": "EUR"
        #         }
        #     ]
        # },...]
        amounts_opt = [
            d['amounts'] for d in acc_dict['detail']['specificAmounts']
            if d['id'] == 'currentBalance'
        ]
        if not amounts_opt:
            continue

        # [
        #     {
        #         "amount": 4112.82,
        #         "currency": "EUR"
        #     },
        #     {
        #         "amount": 4112.82,
        #         "currency": "EUR"
        #     }
        # ]
        amounts = amounts_opt[0]

        # From [{
        #  "number": "ES5901820121160201685745",
        #  "numberType": {
        #    "id": "IBAN"
        #   }
        # }, ...]
        account_iban = [d['number'] for d in acc_dict['formats'] if d['numberType']['id'] == 'IBAN'][0]

        # From "currencies": [
        #     {
        #         "currency": "EUR",
        #         "isMajor": true
        #     }
        # ],
        currency = [d['currency'] for d in acc_dict['currencies'] if d['isMajor']][0]

        # From [{
        #     "amount": 4112.82,
        #     "currency": "EUR"
        # },..]
        balance = [d['amount'] for d in amounts if d['currency'] == currency][0]

        account_type = ACCOUNT_TYPE_DEBIT if balance >= 0 else ACCOUNT_TYPE_CREDIT

        # same as current balance
        available_balance = [
            a['amount'] for a in [
                d['amounts'] for d in acc_dict['detail']['specificAmounts']
                if d['id'] == 'availableBalance'
            ][0]
            if a['currency'] == currency
        ][0]

        account_parsed = {
            'account_no': account_iban,
            'financial_entity_account_id': account_iban,
            'balance': balance,
            'currency': currency,
            'account_type': account_type,
            'available_balance': available_balance,
            'id': acc_dict['id']  # 'ES0182002000000000000000000405303614XXXXXXXXX'
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_organization_title(resp_json: dict) -> str:
    user_info = resp_json.get('customer', {})
    title = '{} {} {}'.format(
        user_info.get('name', ''),
        user_info.get('lastName', ''),
        user_info.get('mothersLastName', ''),
    )
    return title.strip()


def get_movements_parsed(logger: ScrapeLogger, resp_json: dict) -> List[MovementParsed]:
    """The resp_json contains also all info for extended description"""

    movements_dicts = resp_json['accountTransactions']

    movements_parsed_desc = []  # type: List[MovementParsed]
    operation_date_prev = None  # type: Optional[datetime.datetime]
    for mov_dict_raw in movements_dicts:

        operation_date_str = mov_dict_raw['transactionDate'].split('T')[0]  # '2019-09-05T00:00:00.000+0200' -> 20190905
        operation_date = date_funcs.get_date_from_str(operation_date_str, '%Y-%m-%d')

        # Handle tricky case if backend repeats movements in a loop,
        # this case occurred till the API was changed 2019-09-05.
        # But the check still in use
        if operation_date_prev and (operation_date > operation_date_prev):
            break

        value_date = mov_dict_raw['valueDate'].split('T')[0]
        descr = re.sub(
            r'\s+', ' ', '{}; {}'.format(
                mov_dict_raw['humanConceptName'],  # basic descr
                mov_dict_raw['humanExtendedConceptName']).rstrip('; ')  # extra bottom line
        )
        amount = float(mov_dict_raw['amount']['amount'])
        # <class 'dict'>: {'accountingBalance': {'amount': 5120.93, 'currency': {'code': 'EUR', 'id': 'EUR'}}}
        balance_dict = mov_dict_raw['balance']

        temp_balance = float(balance_dict['accountingBalance']['amount'])
        if 'availableBalance' in balance_dict:
            # or from 'accountingBalance'?
            temp_balance_avail = float(mov_dict_raw['balance']['availableBalance']['amount'])
            if temp_balance_avail != temp_balance:
                logger.warning("Dfferent balances: accounting {} != available {}".format(
                    temp_balance,
                    temp_balance_avail
                ))

        movement_parsed = {
            'operation_date': operation_date_str,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance
        }

        operation_date_prev = operation_date
        movements_parsed_desc.append(movement_parsed)

    return movements_parsed_desc


def get_next_page_link(resp_json: dict) -> str:
    return resp_json['pagination'].get('nextPage', '')
