from typing import List

from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import AccountParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT, MovementParsed
from . import parse_helpers
from .custom_types import Contract, OrganizationParsed

__version__ = '1.5.0'
__changelog__ = """
1.5.0 2023.07.10
get_accounts_parsed_from_tesoreria: skip 'FINANCIACION IMPORTACION' account processing
1.4.0 2023.07.07
get_accounts_parsed_from_tesoreria: added detection 'FINANCIACION IMPORTACION' account
1.3.0 2023.04.17
refactored movement_parsed param 'has_final_receipt'
1.2.0
get_movements_parsed_api_v2
1.1.0
get_accounts_parsed_from_tesoreria: use contract-level currency for zero-balance accounts
"""


def _fin_ent_account_id_from_iban(account_no: str) -> str:
    """For backward comp
    >>> _fin_ent_account_id_from_iban('ES2500491800112010632768')
    '0049 1800 11 2010632768'
    """
    fin_ent_account_id = '{} {} {} {}'.format(
        account_no[4:8],
        account_no[8:12],
        account_no[12:14],
        account_no[14:]
    )
    return fin_ent_account_id


def get_contracts(resp_json: dict) -> List[Contract]:
    """
    Parses
    {"logginContractList":[
    {"companyCif":"A17094715","companyName":"COMERCIAL MASOLIVER S.A.U.","contract":{"company":"0049","center":"3488","product":"520","number":"0000001","id":"004934885200000001","bankCode":"0049","branchCode":"3488","productTypeCode":"520","contractCode":"0000001"},"holderData":{"holderName":"33768612001"},"lastAccessDate":"2019-04-19-11.22.19.000000"},
    ]..}
    """
    contract_data_list = resp_json.get('logginContractList') or []
    contracts = [
        Contract(
            org_title=c['companyName'],
            details=c
        )
        for c in contract_data_list
    ]
    return contracts


def get_accounts_parsed_from_productos(resp_json: dict) -> List[AccountParsed]:
    """Parses resp_accs_productos.json
    {
    "accountList": [{
      "iban": "ES2500491800112010632768",
      "amount": "2739.0",
      "availableAmount": "2739.0",
      "productName": "CREDITO NEGOCIO A TIPO VARIABLE",
      "contractDate": "2019-11-20",
      "currencyCode": "EUR",
      "variation": 0.0,
      "contractHolder": "FIVEMASA SA",
      "typePerson": "J",
      "codePerson": "000584102",
      "contract": "004918001000002408",
      "branch": "1800",
      "oldContract": "004918002010632768"
    }
    ...
    }
    """
    accounts_parsed = []  # type: List[AccountParsed]
    for acc_dict in resp_json['accountList']:
        balance_str = acc_dict.get('amount')

        # account-stub, it raises errors in the UI when try to open movements
        if not balance_str:
            continue

        account_no = acc_dict['iban']
        fin_ent_account_id = _fin_ent_account_id_from_iban(account_no)
        balance = float(balance_str)
        currency = acc_dict['currencyCode']
        org_title = acc_dict['contractHolder']
        account_parsed = {
            'financial_entity_account_id': fin_ent_account_id,
            'account_no': account_no,
            'account_type': ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT,
            'org_title': org_title,
            'balance': balance,
            'currency': currency,
        }
        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_accounts_parsed_from_tesoreria(resp_json: dict) -> List[AccountParsed]:
    """Parses resp_accs_tesoreria.json
    {
     "elements": [
        {
          "iban": {
            "countryIban": "ES",
            "dcIban": "02",
            "entity": "0049",
            "office": "1837",
            "dc": "50",
            "accountNumber": "2610467236",
            "ccc": "ES0200491837502610467236"
          },
          "holder": "VIA CELERE DESARROLLOS INMOBILIARIOS S A",
          "alias": "DUNA BEACH II CEC",
          "descAccount": "CUENTA ENTREGA A CUENTA PROMOTOR",
          "saldoDisp": {
            "amount": 1542124.91,
            "currency": {
              "id": "EUR",
              "caption": null,
              "comment": null
            }
          },
          "saldoDispContr": {
            "amount": 1542124.91,
            "currency": {
              "id": "EUR",
              "caption": null,
              "comment": null
            }
          },
          "saldoContContr": {
            "amount": 1542124.91,
            "currency": {
              "id": "EUR",
              "caption": null,
              "comment": null
            }
          },
          "saldoCont": {
            "amount": 1542124.91,
            "currency": {
              "id": "EUR",
              "caption": null,
              "comment": null
            }
          },
          "impVariacion": {
            "amount": 0.0,
            "currency": {
              "id": "EUR",
              "caption": null,
              "comment": null
            }
          },
          "impVariacionContr": {
            "amount": 0.0,
            "currency": {
              "id": "EUR",
              "caption": null,
              "comment": null
            }
          },
          "typePerson": "J",
          "codPerson": 940573
        },
    ...
    ]
    """
    accounts_parsed = []  # type: List[AccountParsed]
    has_accounts_from_financiacion = False
    for acc_dict in resp_json['elements']:
        # SaldoCont displays balance of past movements
        # SaldoDist calcs balance with future movements
        # (-a 23404, ES06 0049 1837 5521 1046 5772)
        balance = acc_dict.get('saldoCont', {}).get('amount')
        # Avoid downloading 'FINANCIACION IMPORTACION' accounts since they are not current or debit accounts
        if 'FINANCIACION IMPORTACION' in acc_dict.get('descAccount', ''):
            has_accounts_from_financiacion = True
            continue

        # account-stub, it raises errors in the UI when try to open movements (?)
        if balance is None:
            continue

        account_no = acc_dict['iban']['ccc']
        fin_ent_account_id = _fin_ent_account_id_from_iban(account_no)
        # No currency shown from zero-balance accounts w/o movs, use contract-level currency (?)
        #   see dev_newweb/no_currency_account.png
        # 'saldoDisp' = {'amount': 0.0, 'currency': {'id': '', 'caption': None, 'comment': None}}
        # 'saldoDispContr' = {'amount': 0.0, 'currency': {'id': 'EUR', 'caption': None, 'comment': None}}
        currency = acc_dict['saldoDisp']['currency']['id'] or acc_dict['saldoDispContr']['currency']['id']
        org_title = acc_dict['holder']
        account_parsed = {
            'financial_entity_account_id': fin_ent_account_id,
            'account_no': account_no,
            'account_type': ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT,
            'org_title': org_title,
            'balance': balance,
            'currency': currency,
        }
        accounts_parsed.append(account_parsed)

    return accounts_parsed, has_accounts_from_financiacion


def get_organizations_parsed(logger: ScrapeLogger, resp_json: dict) -> List[OrganizationParsed]:
    """
    Parses
    {
      "subsidiaries": [
        {
          "personType": "Z2tHWHYvZ1pjWE5IWWlsSjVPNU9GWCtpNVdCYjlIWmY=",
          "personCode": "bDNkcU9YTEQzUTJSc0ZyMmtheE5OQWJCQ1VLekRXK1ErRnBjMC9xM3lWZz0=", // to use in filters
          "tipDoc": null,
          "cif": "B09417932", // id
          "companyName": "GAMBASTAR S.L." // title
        }
      ],
      ...
    }
    """
    orgs = []  # type: List[OrganizationParsed]
    try:
        for org_dict in resp_json['subsidiaries']:
            org = OrganizationParsed(
                title=org_dict['companyName'].strip(),
                personCode=org_dict['personCode'],
                personType=org_dict['personType'],
            )
            orgs.append(org)
    except Exception as e:
        logger.error("Can't get organizations_parsed: HANDLED EXCEPTION: {}: resp_json:\n{}".format(
            e,
            resp_json
        ))
        return []
    return orgs


def get_movements_parsed(resp_json: dict) -> List[MovementParsed]:
    movements_dicts = resp_json.get('appointments', [])
    movements_parsed_desc = []  # type: List[MovementParsed]
    for movement_dict in movements_dicts:

        value_date = movement_dict.get('valueDate')  # 2018-01-19
        operation_date = movement_dict.get('operationDate')  # 2018-01-19
        # from {'amount': 250000.0, 'currency': 'EUR'}
        amount = movement_dict.get('amount', {}).get('amount')
        # Can be None, will calc it later
        # from {'currency': 'EUR', 'amount': 2739.0}
        temp_balance = movement_dict.get('balance', {}).get('amount')
        description = extract.remove_extra_spaces(movement_dict.get('concept', ''))
        description_extended = parse_helpers._get_extended_description(movement_dict, description)

        # handle empty response (can occur if 20 movs at the last page and no more movs)
        if not (value_date and operation_date and amount):
            return []

        movement_parsed = {
            'value_date': value_date,
            'operation_date': operation_date,
            'description': description,
            'description_extended': description_extended,
            'amount': amount,
            'temp_balance': temp_balance,
            'has_final_receipt': movement_dict.get('pdfStatus', '0') == '2',
            'num_movement': movement_dict.get('numMovement')  # for receipts
        }

        movements_parsed_desc.append(movement_parsed)
    return movements_parsed_desc


def get_movements_parsed_api_v2(resp_json: dict) -> List[MovementParsed]:
    """
    Parses
    [...{
		"idMovimiento": "2022-07-2907100000",
		"fechaOperacion": "2022-07-29",
		"fechaValor": "2022-07-29",
		"importe": 200,
		"saldo": 169027.31,
		"tipoOperacion": "ABONO-TRANSFERENCI",
		"tipoMovimiento": "H",
		"codigoOperacion": "71",
		"concepto": "TRANSFERENCIA DE SAS MARTINEZ VICTOR MANUEL, CONCEPTO MATRICULA ACONDICIONAMIENTO FISICO IBON SAS PEDRUEZA.",
		"pdfIndicator": 0,
		"monedaImporte": "EUR",
		"monedaSaldo": "EUR",
		"infoAdicional": ""
	}, ...]
    """
    movements_dicts = resp_json.get('_embedded', {}).get('movimientoList', [])
    movements_parsed_desc = []  # type: List[MovementParsed]
    for movement_dict in movements_dicts:
        value_date = movement_dict.get('fechaValor')  # 2018-01-19
        operation_date = movement_dict.get('fechaOperacion')  # 2018-01-19
        amount = movement_dict.get('importe')

        # handle empty response (can occur if 20 movs at the last page and no more movs)
        if not (value_date or operation_date or amount):
            return []

        temp_balance = movement_dict['saldo']
        description = extract.remove_extra_spaces(movement_dict.get('concepto', ''))
        description_extended = description  # no extended description

        movement_parsed = {
            'value_date': value_date,
            'operation_date': operation_date,
            'description': description,
            'description_extended': description_extended,
            'amount': amount,
            'temp_balance': temp_balance,
            'has_final_receipt': movement_dict['pdfIndicator'] == 1,
            'num_movement': movement_dict['idMovimiento']  # for receipts, NOT implemented?
        }

        movements_parsed_desc.append(movement_parsed)
    return movements_parsed_desc
