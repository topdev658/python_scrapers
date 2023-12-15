from typing import List

from custom_libs import extract
from project.custom_types import AccountParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT, MovementParsed
from .custom_types import Contract


def get_contracts(resp_json: dict) -> List[Contract]:
    """Parses 70_resp_contracts.json"""
    contracts = []  # type: List[Contract]
    for contract_dict in resp_json['contratos']['results']:
        contract = Contract(
            id=contract_dict['numero'],  # Z43414
            title=contract_dict['identidadTitular'],  # 1B83233346 00
            org_title=contract_dict['nombreTitular'],  # "ACTURUS CAPITAL SL"
            orden_param=str(contract_dict['orden']),  # 3
            negocio_param='true' if contract_dict['negocio'] is True else 'false',  # true
        )
        contracts.append(contract)
    return contracts


def get_accounts_parsed(resp_json: dict) -> List[AccountParsed]:
    """Parses 80_resp_accounts.json"""
    accounts_parsed = []  # type: List[AccountParsed]
    for account_dict in resp_json['results']:
        # We don't use actual fin_ent_account_id for backward comp
        # will calc it on the fly
        # fin_ent_account_id = account_dict['numero']  # 208597271194...
        account_no = account_dict['iban']  # ES81208597271194...
        balance = account_dict['saldo']
        account_type = ACCOUNT_TYPE_CREDIT if account_dict['tipoCuenta'] == 'Credito' else ACCOUNT_TYPE_DEBIT
        currency = account_dict['monedaISO']  # 'EUR'
        account_parsed = {
            'account_no': account_no,
            'balance': balance,
            'account_type': account_type,
            'currency': currency
        }
        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed(resp_json: dict) -> List[MovementParsed]:
    """Parses 90_resp_movements.json"""
    movs_parsed_desc = []  # type: List[MovementParsed]
    for mov_dict in resp_json['movimientos']:
        descr = '{}  {}'.format(mov_dict['textoLinea1'].strip(), mov_dict['textoLinea2'].strip()).strip()
        operation_date = mov_dict['fechaMovimiento'].split('T')[0]  # "2021-05-18T00:00:00"
        value_date = mov_dict['fechaValor'].split('T')[0]
        amount = float(mov_dict['importe'])  # already float, but convert to be sure
        temp_balance = float(mov_dict['saldoPosterior'])
        currency = mov_dict['moneda']
        sign = -1 if mov_dict['tipoMovimiento'] == 3 else 1
        movement = {
            'description': descr,
            'operation_date': operation_date,
            'value_date': value_date,
            'temp_balance': temp_balance,
            'currency': currency,
            'amount': sign * amount
        }
        movs_parsed_desc.append(movement)

    return movs_parsed_desc


def get_login_type(resp_text: str) -> str:
    return extract.re_first_or_blank(r'"login_type.*?\:.*?".*?"', resp_text) # "login_type"="nego" or "part"
