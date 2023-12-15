from collections import OrderedDict
from typing import List, Tuple

from project.custom_types import AccountParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT, MovementParsed

__version__ = '1.1.0'
__changelog__ = """
1.1.0
get_access_token: handle err resp
"""

# {"sequence":"306960",
# + "operation_date":"2019-07-15T00:00:00",
# + "operation_value_date":"2019-07-15T00:00:00",
# + "statement_description":"TRF MB -   ANTONIO M L ALBANO       ",
# + "operation_amount":200.0,
# + "debit_credit_indicator":"1",
# + "balance":12296.25,
# + "beneficiary_name":"",
# + "detailed_description":"R 25 de Abril 8          S. ",
# + "payer_name":"  ANTONIO M L ALBANO       ",
# + "payer_nib":"004563304011228660583",
# + "reference":"",
# "statement_description_1":"",
# "statement_description_2":""},
# OR
# {"sequence":"307050",
# "operation_date":"2019-07-16T00:00:00",
# "operation_value_date":"2019-07-16T00:00:00",
# "statement_description":"TRANSF SEPA -TRANS ENVIO AGENC",
# "operation_amount":3000.0,
# "debit_credit_indicator":"1",
# "balance":12607.86,
# "beneficiary_name":"PG ORDENS",
# "detailed_description":"",
# "payer_name":"TRANS ENVIO AGENCIA DE CAMBIOS LDA",
# "payer_nib":"PT50001000003504331000170",
# "reference":"PG ORDENS",
# "statement_description_1":"",
# "statement_description_2":""},
EXTENDED_DESCRIPTION_DETAILS = OrderedDict([
    ('Nome Ordenante', 'payer_name'),
    ('NIB/IBAN/Conta Ordenante', 'payer_nib'),
    ('Nome do Beneficiário', 'beneficiary_name'),
    ('Referência', 'reference'),
    ('Descritivo', 'detailed_description'),
])


def get_access_token(resp_json: dict) -> str:
    """Parses
    {"access_token":"eyJ0....uTwAcPKelSw",
    "token_type":"Bearer",
    "expires_in":"3600","error":null,"status_code":"200",
    "Json":"{\"access_token\":\"eyJ0...cPKelSw\",\"expires_in\":3600,\"token_type\":\"Bearer\"}",
    "GeneratedDate":"2019-08-04T20:54:01",
    "ExpireDate":"2019-08-04T21:54:01",
    "CaprotAuthCtx":null,"CaprotOpCtx":null,
    "isAuthorization":false}

    OR if credentials error:

    {"access_token":null,
    "token_type":null,
    "expires_in":null,"error":"Grant validation error",
    "status_code":"400",
    "Json":"{\"error\":\"Grant validation error\"}",
    "GeneratedDate":"0001-01-01T00:00:00",
    "ExpireDate":"0001-01-01T00:00:00",
    "CaprotAuthCtx":null,"CaprotOpCtx":null,"isAuthorization":false}

    OR if wrong req params (captcha error)

    {'ErrorCode': 'ERROR',
    'FriendlyErrorMessage': 'Lamentamos não poder satisfazer o seu pedido por ter ocorrido uma situação anómala.',
    'TechnicalErrorMessage': None,
    'ErrorMessages': None,
    'CorrelationId': None,
    'Type': None,
    'LogEntryId': None,
    'ClientMessageId': None,
    'status_code': 405}

    :returns access_token or '' if not authorized
    """

    access_token = resp_json.get('access_token', '')
    return access_token


def get_organization_title(resp_json: dict) -> Tuple[bool, str]:
    """Parses
    {"company_name":"TRANS ENVIO -AGENCIA DE CAMBIOS LDA",
    "company_abbreviated_name":"TRANS ENVIO LDA",
    "customer_title":null,"branch_description":"DR-B.Castilho",
    "representative_name":"RICARDO JOSE PAULA SANTOS",
    "representative_abbreviated_name":"RICARDO JOSE SANTOS",
    "company_client_number":"2773456",
    "company_tax_id_number":"505915804",
    "representative_client_number":"3124223"}
    """
    if 'company_abbreviated_name' not in resp_json:
        return False, ''
    return True, resp_json['company_abbreviated_name']


def get_accounts_wo_iban_parsed(resp_json: dict) -> List[dict]:
    """Parses
    {"AccountCollection":[
    {"ProductGroup":null,"AccountId":"40191910010","ProductId":"1102",
    "Balance":15248.69,"Branch":null,"BranchDescription":null,
    "AccountingBalance":15248.69,"AuthorizedBalance":15248.69,
    "AvailableBalance":15248.69,"AccountDetail":null,

    "AccountOnline":{"account_id":"40191910010","nib":"004590604019191001015",
    "branch":"9060","branch_description":"DR-B.Castilho","account_selected":"0",
    "account_alias":null,"account_product_description":"DEPÓSITOS À ORDEM EMPRESAS",
    "digital_documentation_status":"3","blocked":"1","account_state":"0",
    "activation_condition":"0","treasury_contract":"0","ccca":"1",
    "preferred_account_indicator":"0","account_color":"none"},
    "AccountAddress":null,"AccountColor":"none","Quantity":0.0,
    "CustomerInformation":null,"Position":null}]}
    """
    accounts_wo_iban_parsed = []  # type: List[dict]

    account_dicts = resp_json['AccountCollection']
    for acc_dict in account_dicts:
        balance = acc_dict['Balance']
        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
        acc_wo_iban_parsed = {
            'financial_entity_account_id': acc_dict['AccountId'],
            'balance': balance,
            'currency': 'EUR',
            'account_type': account_type,
        }
        accounts_wo_iban_parsed.append(acc_wo_iban_parsed)

    return accounts_wo_iban_parsed


def get_account_parsed(resp_json: dict, acc_parsed_wo_iban: dict) -> AccountParsed:
    """Parses
    {"account_detail_dda":
    {"nib":"004590604019191001015","iban":"PT50004590604019191001015","bank_bic":"CCCMPTPL",
    "first_holder_name":"TRANS ENVIO -AGENCIA DE CAMBIOS LDA"}}
    """
    acc_parsed = acc_parsed_wo_iban.copy()
    acc_parsed['account_no'] = resp_json['account_detail_dda']['iban']
    return acc_parsed


def _get_description_extended(mov_dict: dict) -> str:
    description_extended = mov_dict['statement_description'].strip()

    for det_title, det_key in EXTENDED_DESCRIPTION_DETAILS.items():
        detail = mov_dict.get(det_key, '').strip()
        msg = '{}: {}'.format(det_title, detail).strip()
        description_extended += ' || {}'.format(msg)

    return description_extended.strip()


def get_movements_parsed(resp_json: dict) -> List[MovementParsed]:
    """Parses
    {"operation_log_collection":[
    {"sequence":"306960",
    "operation_date":"2019-07-15T00:00:00",
    "operation_value_date":"2019-07-15T00:00:00",
    "statement_description":"TRF MB -   ANTONIO M L ALBANO       ",
    "operation_amount":200.0,
    "debit_credit_indicator":"1", // 1 => +, 0 => -
    "balance":12296.25,
    "beneficiary_name":"",
    "detailed_description":"R 25 de Abril 8          S. ",
    "payer_name":"  ANTONIO M L ALBANO       ",
    "payer_nib":"004563304011228660583",
    "reference":"",
    "statement_description_1":"",
    "statement_description_2":""},
    {"sequence":"306970",
    "operation_date":"2019-07-15T00:00:00",
    "operation_value_date":"2019-07-15T00:00:00",
    "statement_description":"SIMONE SANTOS",
    "operation_amount":75.0,
    "debit_credit_indicator":"1",
    "balance":12371.25,
    "beneficiary_name":"",
    "detailed_description":"",
    "payer_name":"",
    "payer_nib":"",
    "reference":"",
    "statement_description_1":"",
    "statement_description_2":""},
    ]}
    """
    movements_parsed_asc = []  # type: List[MovementParsed]

    mov_dicts = resp_json['operation_log_collection']
    for mov_dict in mov_dicts:
        operation_date = mov_dict['operation_date'].split('T')[0]  # 2019-07-15
        value_date = mov_dict['operation_value_date'].split('T')[0]  # 2019-07-15
        descr = mov_dict['statement_description'].strip()
        descr_extended = _get_description_extended(mov_dict)
        amount_abs = mov_dict['operation_amount']
        amount_sign = 1 if mov_dict['debit_credit_indicator'] == '1' else -1
        amount = amount_sign * amount_abs

        temp_balance = mov_dict['balance']
        movement = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance,
            'description_extended': descr_extended
        }

        movements_parsed_asc.append(movement)

    return movements_parsed_asc
