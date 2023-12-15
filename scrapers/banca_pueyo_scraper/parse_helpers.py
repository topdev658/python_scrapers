from typing import List

from project.custom_types import AccountParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT, MovementParsed


def get_accounts_parsed(resp_json: dict, resp_script: str) -> List[AccountParsed]:
    """Parses 30_resp_accounts.json"""
    accounts_parsed = []  # type: List[AccountParsed]
    for account_dict in resp_json['accounts']:
        account_no = account_dict['displayContractNumber'].replace(' ', '')  # ES81208597271194...
        balance = account_dict['capitalBalance']
        account_type = ACCOUNT_TYPE_DEBIT if 'CORRIENTE' in account_dict['subtype'] else ACCOUNT_TYPE_CREDIT
        if 'Saldo \\u20ac / Saldo disponible \\u20ac' in resp_script:
            currency = 'EUR'
        elif 'Saldo \\u00a3 / Saldo disponible \\u00a3' in resp_script:
            currency = 'GBP'
        else:
            currency = 'USD'
        org_title = account_dict['owner']
        contract_number = account_dict['contractNumber']
        account_parsed = {
            'account_no': account_no,
            'balance': balance,
            'account_type': account_type,
            'currency': currency,
            'org_title': org_title,
            'contract_number': contract_number  # internal contract number, it's needed to get link for parsing movements
        }
        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed(resp_json: dict) -> List[MovementParsed]:
    """Parses 40_resp_movements.json"""
    movs_parsed = []  # type: List[MovementParsed]
    mov_pages = resp_json['pages']
    for mov_page in mov_pages:
        for mov_dict in reversed(mov_page['data']):
            operation_date = mov_dict['operationDate'].split('T')[0]  # "2021-05-18T00:00:00"
            value_date = mov_dict['valorDate'].split('T')[0]
            amount = mov_dict['amount']
            balance = mov_dict['balance']
            description = '{}  {}'.format(mov_dict['concept'].strip(),
                                          mov_dict['conceptDetail'].strip()).strip()
            movement = {
                'operation_date': operation_date,
                'value_date': value_date,
                'amount': amount,
                'temp_balance': balance,
                'description': description
            }
            movs_parsed.append(movement)

    return movs_parsed