from typing import List

from custom_libs import currency as currency_lib, extract
from project.custom_types import AccountParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT, MovementParsed
from .custom_types import Contract


def get_contracts(resp_json: dict) -> List[Contract]:
    """Parses 20_resp_logged_in_decoded.json"""
    contracts = []  # type: List[Contract]
    for contract_dict in resp_json['datos']['Contratos']:
        contract = Contract(
            org_title=contract_dict['nombre'],
            id=contract_dict['id'],
            nif=contract_dict['nif']
        )
        contracts.append(contract)
    return contracts


def get_accounts_parsed(resp_json: dict) -> List[AccountParsed]:
    """Parses 30_resp_home_decoded.json"""
    accounts_parsed = []  # type: List[AccountParsed]
    for acc_group in resp_json['cuentasCliente']['grupos']:
        if acc_group['grupoCuenta'] != '001':  # current accounts
            continue
        currency_code = int(acc_group['monedaTotal'])  # 978
        currency = currency_lib.get_by_code(currency_code)
        for acc_dict in acc_group['cuentas']:
            account_no = acc_dict['ctaFormat'].replace(' ', '')  # 'ES3630810234111105194920'
            fin_ent_account_id = acc_dict['gcuenta']  # '30810102340000111105194920'
            sign = 1 if acc_dict['signoSaldo'] == '+' else -1
            balance = sign * float(acc_dict['saldo'])
            account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
            account_parsed = {
                'account_no': account_no,
                'financial_entity_account_id': fin_ent_account_id,
                'balance': balance,
                'account_type': account_type,
                'currency': currency
            }
            accounts_parsed.append(account_parsed)
    return accounts_parsed


def get_movements_parsed(resp_json: dict) -> List[MovementParsed]:
    """Parses 40_resp_movs.json"""
    movs_parsed_desc = []  # type: List[MovementParsed]
    for mov_dict in resp_json['BLQUNO']:
        # {
        #   "REFERENCIA" : "000000000003188",
        #   "HASDETAIL" : "true",
        #   "SALDOMON" : "EUR",
        #   "TIPOID" : "0000007476",
        #   "SPECIFICCODE" : "9002",
        #   "PROCESSCODE" : "9401166250",
        #   "TIPO" : "ADSR",
        #   "FECHAOPER" : "20220815",
        #   "ERRORTIPO" : "",
        #   "IMPORTE" : "-000000000194.9800",
        #   "ID" : "000000000003188",
        #   "FECHAVALOR" : "20220815",
        #   "DOCUMENTID" : "",
        #   "CONCEPTO" : "RECIBO PLUS ULTRA SEGUROS",
        #   "CONDETALLE" : "true",
        #   "NUMEROOPER" : "",
        #   "TIPOSEG" : "",
        #   "CODIGOERROR" : "",
        #   "IMPORTEMON" : "EUR",
        #   "REF" : "ENT: A30014831-SDD REF:9401166250   0234",
        #   "FECHAOPERFRMT" : "15-08-2022",
        #   "DATA" : "",
        #   "CONDOCUMENTO" : "false",
        #   "FECHAVALORFRMT" : "15-08-2022",
        #   "SALDO" : "000000032798.6900",
        #   "ERRORDESC" : "",
        #   "IDTRANS" : "",
        #   "LONGITUD" : "",
        #   "TMP2" : "",
        #   "TMP1" : ""
        # }
        descr = mov_dict['CONCEPTO'].strip()
        operation_date = mov_dict['FECHAOPER']  # "20220815"
        value_date = mov_dict['FECHAVALOR']
        amount = float(mov_dict['IMPORTE'])
        temp_balance = float(mov_dict['SALDO'])
        currency = mov_dict['IMPORTEMON']
        movement = {
            'description': descr,
            'operation_date': operation_date,
            'value_date': value_date,
            'temp_balance': temp_balance,
            'currency': currency,
            'amount': amount
        }
        movs_parsed_desc.append(movement)

    return movs_parsed_desc


def get_url_login_js(resp_text: str) -> List[str]:

    url = extract.re_first_or_blank('type="text/javascript" src="(.*?)"', resp_text)
    return url


def get_encrypted_cookie_params(resp_login_text: str, resp_login_js_text: str) -> List[str]:
    """Extract necessary params to get encrypted cookie "TSc7f0f12a075" related to F5 Network anti-bot techniques"""
    bobcmn = extract.re_first_or_blank('bobcmn\".*?\"(.*?)\"', resp_login_text)
    con = extract.re_first_or_blank('\"(0.*?)\"', resp_login_text)
    secret = extract.re_last_or_blank(r'(?s)delete Number.*?\"(.*?)\"', resp_login_js_text)
    return bobcmn, con, secret
