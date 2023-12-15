from typing import List, Tuple
from .custom_types import ContractGoAbanca
from project.custom_types import AccountParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT, MovementParsed


__version__ = '1.0.0'
__changelog__ = """
1.0.0
init
"""

def get_contracts(resp_json: dict) -> Tuple[bool, List[ContractGoAbanca]]:
    """Parses 20_resp_me.json"""
    contracts = []  # type: List[ContractGoAbanca]
    contracts_data = resp_json.get('data', {}).get('profiles', [])
    if not contracts_data:
        return False, []
    for contract_data in contracts_data:
        # {
        #     "id": "320245622402",
        #     "holderLegalId": "A81142358",
        #     "contractNumber": "3202456224",
        #     "contractName": "PIXELWARE S.A.",
        #     "relationShip": {
        #         "id": "02",
        #         "name": "OPERATIVO"
        #     },
        #     "group": {}
        # }
        contact = ContractGoAbanca(
            profile_id_param=str(contract_data['id']),
            org_title=contract_data['contractName']
        )
        contracts.append(contact)

    return True, contracts


def get_accounts_parsed(resp_json: dict) -> Tuple[bool, List[AccountParsed]]:
    accounts_parsed = []  # type: List[AccountParsed]
    accounts_data = resp_json.get('data')
    if accounts_data is None:
        return False, []
    for account_data in accounts_data:
        # {
        #     "id": "01318813502718000367",
        #     "balance": {
        #         "amount": 17283.67,
        #         "currency": {
        #             "id": "EUR",
        #             "code": "978"
        #         }
        #     },
        #     "postedBalance": {
        #         "amount": 17283.67,
        #         "currency": {
        #             "id": "EUR",
        #             "code": "978"
        #         }
        #     },
        #     "operationalStatus": "1",
        #     "currency": {
        #         "id": "EUR",
        #         "code": "978"
        #     },
        #     "status": {
        #         "id": "01",
        #         "name": "vigente"
        #     },
        #     "formats": [
        #         {
        #             "format": {
        #                 "id": "IBAN",
        #                 "name": "IBAN"
        #             },
        #             "value": "ES7601318813502718000367"
        #         }
        #     ],
        #     "hasLocks": false
        # }
        fin_ent_account_id = account_data['id']  # 01318813502718000367
        account_no = account_data['formats'][0]['value']  # ES7601318813502718000367
        currency = account_data['balance']['currency']['id']  # EUR
        balance = account_data['balance']['amount']  # 17283.67
        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

        account_parsed = {
            'financial_entity_account_id': fin_ent_account_id,
            'account_no': account_no,
            'balance': balance,
            'currency': currency,
            'account_type': account_type
        }
        accounts_parsed.append(account_parsed)

    return True, accounts_parsed


def get_movements_parsed(resp_json: dict) -> Tuple[bool, List[MovementParsed]]:
    movs_parsed_desc = []  # type: List[MovementParsed]
    movs_data = resp_json.get('data')
    if movs_data is None:
        return False, []

    for mov_data in movs_data:
        # {
        #     "id": "000145",
        #     "reference": "000145",
        #     "amount": {
        #         "amount": 9755.63,
        #         "currency": {
        #             "id": "EUR",
        #             "code": "978"
        #         }
        #     },
        #     "type": {
        #         "id": "188",
        #         "name": "TRANSFERENCIA"
        #     },
        #     "reason": "TRANSFERENCIA - SEPAR20208862129978 RADIO TELEVISION MAD",
        #     "operationNumber": "",
        #     "operationDate": "2020-12-23T00:00:00.000+0000",
        #     "valueDate": "2020-12-23T00:00:00.000+0000",
        #     "balance": {
        #         "amount": 17283.67,
        #         "currency": {
        #             "id": "EUR",
        #             "code": "978"
        #         }
        #     },
        #     "hasDetail": true,
        #     "aditionalInfo": {
        #         "SEPAR20208862129978 RADIO TELEVISION MAD": null
        #     }
        # }
        descr = mov_data['reason']
        oper_date = mov_data['operationDate'].split('T')[0]  # '2020-12-23'
        value_date = mov_data['valueDate'].split('T')[0]
        amount = float(mov_data['amount']['amount'])  # int to float
        temp_balance = float(mov_data['balance']['amount'])  # int to float
        mov_parsed = {
            'operation_date': oper_date,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance
        }
        movs_parsed_desc.append(mov_parsed)

    return True, movs_parsed_desc


def get_next_page_key(resp_json: dict) -> Tuple[bool, bool, str]:
    """
    :returns (ok, has_next_page, next_page_key)
    """
    #   "paging": {
    #     "size": 0,
    #     "totalElements": 0,
    #     "totalPages": 0,
    #     "number": 0,
    #     "nextPaginationKey": "MjAyMDA3MTMwMDAxMTIwMDAwMDA1OTU5ODY4",
    #     "hasMorePages": true
    #   },
    pagination_data = resp_json.get('paging')
    if pagination_data is None:
        return False, False, ''
    has_next_page = pagination_data['hasMorePages']
    next_page_key = pagination_data.get('nextPaginationKey', '')  # absent if no next page
    return True, has_next_page, next_page_key
