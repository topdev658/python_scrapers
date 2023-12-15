from typing import List, Tuple, Optional, Dict

from deprecated.classic import deprecated

from project.custom_types import AccountParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT, MovementParsed
from .custom_types import Contract
import re

@deprecated(reason='Bank returns ES6721032975980550100055, back compatibility with '
                   'ES67 2103 2975 9805 5010 0055 is no longer needed')
def calc_fin_ent_account_id(account_no: str) -> str:
    """Back comp
    ES6721032975980550100055 -> ES67 2103 2975 9805 5010 0055
    """
    account_no_clean = account_no.replace(' ', '')  # be sure no spaces
    assert len(account_no_clean) == 24
    fin_ent_acc_id = ' '.join([account_no_clean[i:i + 4] for i in range(0, len(account_no_clean), 4)])
    return fin_ent_acc_id


def get_req_login_params() -> List[Dict]:
    """Returns req_login_params (temporary solution with values manually extracted from the browser)
    """
    req_login_params = {
        'error': None,
        'old_token': None,
        'performance': {'interrogation': 442},
        'solution': {
            'interrogation': {
                'cr': 394634885,
                'og': 1,
                'p': "KStDEYFG8AlzgKVXPyxhxt/ucAHuTnMri5Rz6qzhOKEHq438UV3xN3oRi74R/rAJ/vnDwsxF/co0RyHZ+qCnipz/9hKuC"
                     "zazzsbwcHEk7z3cPNVoDJH6PDoEhCKcvOiApuEHXMMPvo29Uu4MN/7nVdOpJAXyF6Oi1xBi5uA2dPqHNsIkV19iMWQPC"
                     "KAQMGMLoznDzU3LeUb+Bq1fPaYuwZzxPhNkCS1tHdwta2S+/DdLNdlvDBH4divRHz1NJfsUtSVXWJjf6ZLq2XGNoCMrCZ"
                     "lgPcyq2SBj2BltIa/ytfiT/d5gC5t9fP9DCq1fNezYpiFHlEpK+A19gyBdPyP3zoH46N29xuK7HtWga6/j+fvCqw322FQ"
                     "jtisFHqqH6P0VtahVXVra5VAqEyACeCzoAVgx8p3mgPk9AYN6dDmqbm/UJ919DwA3u7wFCiocPn4EL3mAS4aSNdO63iyH"
                     "NXzqXI+0Y1txSux2nMh6PDlpraHLcEn+xtn2uztFh2YeN6w…KyQYF8uHVl5+EeMAk9BY42LbaMQj9dPaKP57YcilTcbVl"
                     "h2jOQ9br9jEd45B92CL772ATtuzPgICGf7NIhTdi4u74FCHUab2VY4ySKnwcaspejEf9CO7WwUQbibE3xXizvHl7k6rs"
                     "ydbqPN9ujDN5xvfoPAefX+CzM5TLYzlDJaZnu3vwPZH72WI4rOZviRq2i3d3l5aivd7UFuhbuxxmgI2AUUz2DbfUXPCHG"
                     "lJVJr4CoWTuHYPjwWMtkfI42F2hk2Zci/Xkknf8OY735yQu8IYrpFeUgEU+nZKY68nUNO0Ho3NRkdqAQ0n1VZ3eKYHZMg"
                     "M7AeVTqkWQJefhr2t0teY5umaQo29qp5OS2KHoX+8TgmBLtvinOWKJDY7WTc+4X2tCLrU4sxTHd9ST+10qpa8u3Wb+tSZ"
                     "fsYTM2r/MavZEqCNExd74HTScX5ybXZKXImE6fvBc9lSbDejVwGIonLkL21umh3Z6noHhypzdWsBzqgpEh62vbm7caLm0"
                     "U",
                'sr': 1367610210,
                'st': 1694676615
            },
            'version': 'beta'
        }
    }
    return req_login_params


def get_contracts(resp_json: dict) -> Tuple[bool, List[Contract]]:
    contracts = []  # type: List[Contract]
    # multi- or single-contract access returns different resp
    ok = ('contratos' in resp_json) or ('titularcontrato' in resp_json)
    for c in resp_json.get('contratos', []):
        contracts.append(Contract(
            numcontrato_param=c['numcontrato'],
            org_title=c['descontrato']
        ))
    return ok, contracts


def get_org_title(resp_contract_json: dict) -> str:
    return resp_contract_json['titularcontrato']


def get_csrf_token(resp_json: dict) -> str:
    return resp_json['tokenCSRF']


def get_next_page_num_mov_param(resp_json: dict) -> Optional[str]:
    # "masmovimientos": {
    #     "ultnummov": "361",
    #     "saldo": "138095.16",
    #     "indMovimientosOTP": "N"
    #   }
    # OR "masmovimientos": {} if not movs
    # OR {'noDatos': 'No existen datos a listar'}
    if 'noDatos' in resp_json:
        return None
    return resp_json['masmovimientos'].get('ultnummov', None)


def get_accounts_parsed(resp_json: dict) -> List[AccountParsed]:
    """Parses 30_resp_accounts.json"""
    accounts_parsed = []  # type: List[AccountParsed]
    cuentas_key = 'cuentas'
    if cuentas_key in resp_json:
        for acc_dict in resp_json[cuentas_key]:
            # skip inactive accounts (-a 9403, 'MAS MOTOR SA', 'ES4221037407810030001448')  # todo check
            if acc_dict['estadocuenta'] == 'CANCELADO':
                continue
            account_no = acc_dict['iban']
            currency = acc_dict['saldo']['moneda']
            balance = acc_dict['saldo']['cantidad']

            account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

            account_parsed = {
                'account_no': account_no,
                'account_type': account_type,
                'currency': currency,
                'balance': balance,
                'financial_entity_account_id': account_no,
                'ppp_param': acc_dict['ppp']  # '001'
            }

            accounts_parsed.append(account_parsed)
    return accounts_parsed


def get_movements_parsed(resp_json, account_parsed) -> Tuple[bool, List[MovementParsed]]:
    """Parses 40_resp_movs.json, 40_resp_movs__no_movs.json
    mov:
        {
          "fechaoper": "2022-03-25",
          "fechavalor": "2022-03-24",
          "concepto": "INTERESES 25122021-24032022",
          "importe": {
            "cantidad": -467.14,
            "moneda": "EUR"
          },
          "importemonedaorigen": {},
          "nummov": "754",
          "oficina": "0006",
          "saldo": {
            "cantidad": -59818.40,
            "moneda": "EUR"
          },
          "recibo": "N",
          "categoria": "ID22"
        },
    """
    movements_parsed = []  # type: List[MovementParsed]
    # check for 'no movs', see 40_resp_movs__no_movs.json
    ok = resp_json.get('noDatos') or resp_json.get('movimientos')

    for mov_dict in resp_json.get('movimientos', []):
        operation_date = mov_dict['fechaoper']  # "2022-03-25"
        # Real fecha_valor is only available at new web, nor old web.
        # Use operation date instead mov_dict['fechavalor'] to keep backwards integrity with old web movements.
        # TODO fix to use mov_dict['fechavalor'] keeping in mind that backwards integrity should be granted.
        value_date = operation_date
        descr = re.sub(r'\s+', ' ', mov_dict['concepto'].strip())  # remove redundant spaces
        amount = mov_dict['importe']['cantidad']
        temp_balance = mov_dict['saldo']['cantidad']

        extra_params = {}
        extra_params['nummov'] = mov_dict['nummov']
        extra_params['ppp_param'] = account_parsed['ppp_param']
        extra_params['recibo'] = mov_dict['recibo']

        mov = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr,
            'amount': float(amount),  # assert float
            'temp_balance': float(temp_balance),
            'receipt_params': extra_params
        }
        movements_parsed.append(mov)

    return ok, movements_parsed
