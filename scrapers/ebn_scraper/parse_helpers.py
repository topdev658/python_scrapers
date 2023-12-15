from typing import List, Tuple

from project.custom_types import AccountParsed, MovementParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT


def get_accounts_parsed(resp_json: dict) -> List[AccountParsed]:
    accounts_parsed = []  # type: List[AccountParsed]
    accounts_dicts = resp_json['accounts']
    for account_dict in accounts_dicts:
        # see 20_resp_accounts.json
        if account_dict['type'] == 'CCC':
            account_no = account_dict['iban']  # "ES3902110001710040173397"
            balance = account_dict['balance']
            currency = account_dict['ccy']  # EUR
            account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

            account_parsed = {
                'account_no': account_no,
                'account_type': account_type,
                'currency': currency,
                'balance': balance
            }

            accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed(resp_json: dict) -> Tuple[bool, List[MovementParsed]]:
    movs_parsed_desc = []  # type: List[MovementParsed]
    # 30_resp_movs.json, 30_resp_movs_nomovs.json
    movs_dicts = resp_json['account'].get('movements', [])
    if resp_json['error'] != '0000' and not movs_dicts:
        return False, []
    for mov_dict in movs_dicts:
        # {
        #     "movementUuid": "1705050",
        #     "operationDate": "2021-07-13",
        #     "valueDate": "2021-07-13",
        #     "type": "Comisión préstamo",
        #     "concept": "COMISION TRIMESTRAL ANTICIPADA AVAL BILATERAL 2101596 TIPO: 0,25% S/ 2.550,00",
        #     "amount": -10.00,
        #     "balance": 234140.27,
        #     "amountEur": -10.00,
        #     "balanceEur": 234140.27
        # }
        operation_date = mov_dict['operationDate'].replace('-', '')  # '20210713'
        value_date = mov_dict['valueDate'].replace('-', '')
        # Get concept or blank to avoid scraping exception
        descr = mov_dict.get('concept', '')
        amount = mov_dict['amount']
        temp_balance = mov_dict['balance']

        mov = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movs_parsed_desc.append(mov)

    return True, movs_parsed_desc
