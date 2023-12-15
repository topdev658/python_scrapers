from typing import List

from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed


def get_accounts_parsed_nuevo(resp_json: dict) -> List[AccountParsed]:
    accounts_parsed = []  # type: List[AccountParsed]
    account_dicts = resp_json.get('products', [])
    for account_dict in account_dicts:
        account_no = account_dict['code']
        currency = account_dict['currency']
        balance = float(account_dict['balance'])  # also account_dict['availableBalance']
        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
        account_parsed = {
            'account_no': account_no,
            'balance': balance,
            'currency': currency,
            'account_type': account_type,
        }
        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed_nuevo(resp_json: dict) -> List[MovementParsed]:
    movements_parsed = []  # type: List[MovementParsed]
    mov_dicts = resp_json['statements']
    for mov_dict in mov_dicts:
        value_date = mov_dict['value']  # '2020-01-10'
        operation_date = mov_dict['operation']
        amount = mov_dict['amount']
        description = mov_dict['description']
        temp_balance = mov_dict['balance']

        movement_parsed = {
            'value_date': value_date,
            'operation_date': operation_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance,
        }

        movements_parsed.append(movement_parsed)

    return movements_parsed
