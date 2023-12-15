import re
from typing import List
from collections import OrderedDict

from custom_libs import convert
from custom_libs import extract
from project.custom_types import ACCOUNT_TYPE_CREDIT, AccountParsed, MovementParsed


def get_accounts_params(resp_text: str) -> List[str]:
    """
    Parses
        <div class="link-arrow-bottom collapsed">
            <a href="" title='Mov. últimos 90 días' data-account-number='000358065780020' data-client-number='7402570334'
            data-account-type='DO'>
            Mov. últimos 90 días
            </a>
            <div class="icon">
            </div>
        </div>
        ...
    """
    accounts_resp_text = re.findall(r"(?si)<a href=\"\" title='.*?'(.*?)</a>", resp_text)
    accounts_params_parsed = []
    for account_resp_text in accounts_resp_text:
        account_params_parsed = OrderedDict([
            ('clientNumber', extract.re_first_or_blank("data-client-number='(.*?)'", account_resp_text)),
            ('accountNumber', extract.re_first_or_blank("data-account-number='(.*?)'", account_resp_text))
        ])
        accounts_params_parsed.append(account_params_parsed)
    return accounts_params_parsed


def get_organization_title(resp_text: str) -> str:
    org_title = extract.re_first_or_blank(
        r'(?si)<div class="company">\s*<span class="name">(.*?)</span>',
        resp_text
    ).strip()
    return org_title


def get_account_parsed(resp_text: str, account_number_param: str) -> AccountParsed:
    account_no = re.sub(r'\s', '', extract.re_first_or_blank(r'IBAN: (PT[\d\s]+)</span>', resp_text))

    # Movements temp balance displays saldo contable (not disponible)
    # '3 865,25'
    # handle Contable (ES) and Contabilístico (PT)
    balance_str = extract.re_first_or_blank(r'(?si)Contab\w+:.*?<span class="val">(.*?)</span>', resp_text)
    if not (balance_str and account_no):
        return {}

    balance = convert.to_float(balance_str)
    currency = extract.re_first_or_blank('>{}</span>(.*?)</div>'.format(balance_str), resp_text).strip()

    account_parsed = {
        'account_no': account_no,
        'financial_entity_account_id': account_number_param,
        'account_type': ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_CREDIT,
        'currency': currency,
        'balance': balance,
    }

    return account_parsed


def get_movements_parsed(resp_json: dict) -> List[MovementParsed]:
    """
    Parses
    [{'a': 672.0,
      'avisoDisponivel': True,
      'avisoLido': True,
      'b': '4630.62',
      'd': 'TRF DE REEMBOLSOS-90274900',
      'i': 2553778866,
      'o': 20180816,
      'referenciaAviso': '331446400',
      'u': {'movId': '2553778866', 'ref': '6615NR90274900', 'type': 'sepa'},
      'v': 20180815}, ...]
    """
    movements_parsed_asc = []  # type: List[MovementParsed]

    for mov_dict in resp_json:
        movement_parsed = {
            'operation_date': str(mov_dict['o']),  # 20180816
            'value_date': str(mov_dict['v']),  # 20180815
            'description': mov_dict['d'],
            'amount': mov_dict['a'],
            'temp_balance': round(float(mov_dict['b']), 2)
        }

        movements_parsed_asc.append(movement_parsed)

    return movements_parsed_asc
