import json
from custom_libs import extract
from .custom_types import Contract
from project.custom_types import AccountParsed, MovementParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT
from typing import List, Dict


def get_auth_id(resp_text: str) -> str:
    """Parses
    window['authorizationData']={
        "id":"8507x9QOwxHbtn1hMDRdlPjRUML1bfQAM8HRK",
        "interactionId":"a52adb1a3da00143",
        "type":"ACCESS",
        "status":"WAITING_HANDSHAKE",
        "validUntil":"2022-03-02T22:50:57",
        "visualizationData":{"theme":"companiesbanking"},
        "identificationData":{"clientData":{"clientId":"empresas-web","displayName":"empresas-web"},
                                "secondClientData":{}},
        "integrationData":{"system":"CA","caSessionId":"a722b306-7071-471a-aae6-10d2e462062a"},
        "challenges":[],"consents":[],"messages":[],"existsAdditionalConsents":false,
        "backAllowed":false,"allowedFlowPreferences":[]
    };
    """
    auth_data_str = extract.re_first_or_blank(r"""(?si)window\['authorizationData']=(\{.*?});""", resp_text)
    auth_data_dict = json.loads(auth_data_str)
    auth_id = auth_data_dict['id']
    return auth_id


def get_contracts(resp_json: dict) -> List[Contract]:
    """Parses
    {
      "page": 0,
      "items": [
        {
          "id": "c5cdxcDHDDfs",
          "company": "ESOFITEC GLOBAL SOLUTIONS SL",
          "byDefault": true,
          "cif": "B25832965"
        }
      ],
      "totalElements": 1
    }
    """
    contracts = []  # type: List[Contract]
    for item in resp_json['items']:
        contract = Contract(
            id=item['id'],
            org_title=item['company'],
            cif=item['cif']
        )
        contracts.append(contract)
    return contracts


def get_accounts_single_currency_parsed(resp_json: dict) -> List[AccountParsed]:
    """Parses
    {
      "overview": {
        "totalBalance": {
          "amount": 1004874.85,
          "currency": "EUR"
        },
        "productsNumber": 1
      },
      "accounts": [  <----
        {
          "id": "56c2229fB9DsBxw9Je9cccOwxO2cDOODfHDxoxo2",
          "display": "ES8601280560380100048767",
          "type": "CURRENT",  <---
          "currency": "EUR",
          "nickname": "Cuenta Corriente",
          "balance": {
            "amount": 1004874.85,
            "currency": "EUR",
            "euroEquivalent": 1004874.85
          }
        }
      ]
    }
    """
    accounts_parsed = []  # type: List[AccountParsed]
    for acc_dict in (resp_json.get('accounts') or resp_json.get('credits', [])):
        if acc_dict.get('balanceBrackets'):
            continue  # skip multi-currency
        balance = acc_dict['balance']['amount']
        account_type = ACCOUNT_TYPE_CREDIT if (balance < 0 or resp_json.get('credits')) else ACCOUNT_TYPE_DEBIT
        currency = acc_dict['balance']['currency']
        account_no = acc_dict['display']  # 'ES8601280560380100048767'

        account_parsed = {
            'account_no': account_no,
            # for DB
            'financial_entity_account_id': account_no[-20:12] + account_no[-9:],  # BACK COMP: '01280560100048767'
            'account_type': account_type,
            'balance': balance,
            'currency': currency,
            'req_params': {
                'id': acc_dict['id']  # "56c2229fB9DsBxw9Je9cccOwxO2cDOODfHDxoxo2"
            }
        }
        accounts_parsed.append(account_parsed)
    return accounts_parsed


def get_accounts_multi_currency_parsed(resp_json: dict) -> List[Dict[str, AccountParsed]]:
    """Parses
    {
      "overview": {
        "totalBalance": {
          "amount": 600000.0,
          "currency": "EUR"
        },
        "productsNumber": 1
      },
      "credits": [  <---
        {
          "id": "659cDBecSB2Dcs2wB9OSccOofBJHcJJDBBBDOxc2",
          "display": "ES1901287681980550055387",
          "type": "multicurrency",  <----
          "nickname": "Cr\u00e9dito Multidivisa",
          "balance": {
            "amount": 600000.0,
            "currency": "EUR",
            "euroEquivalent": 600000.0
          },
          "drawnDownBalance": {
            "amount": 382316.93,
            "currency": "EUR"
          },
          "limit": {
            "amount": 600000.0,
            "currency": "EUR",
            "euroEquivalent": 600000.0
          },
          "balanceBrackets": [
            {
              "dueDate": "2022-06-25",
              "interestRate": 1.58,
              "balance": {
                "amount": 382316.93,
                "currency": "EUR",
                "euroEquivalent": 382316.93
              }
            },
            {
              "dueDate": "2022-06-25",
              "interestRate": 1.85,
              "balance": {
                "amount": 0.0,
                "currency": "GBP",
                "euroEquivalent": 0.0
              }
            }
          ]
        }
      ]
    }
    :returns list of account_parsed_multicurrency where
             account_parsed_multicurrency is dict with currency as key and subaccount as val
    """
    accounts_parsed = []  # type: List[AccountParsed]

    for acc_dict in (resp_json.get('accounts') or resp_json.get('credits', [])):
        if not acc_dict.get('balanceBrackets'):
            continue  # skip one-currency

        acc_multi = {}  # type: Dict[str, AccountParsed]
        for subaccount in acc_dict['balanceBrackets']:
            account_no_parent = acc_dict['display']  # 'ES8601280560380100048767'
            fin_ent_account_id_parent = account_no_parent[-20:12] + account_no_parent[-9:]

            sign = 1  # TODO check
            balance = sign * subaccount['balance']['amount']
            account_type = ACCOUNT_TYPE_CREDIT if (balance < 0 or resp_json.get('credits')) else ACCOUNT_TYPE_DEBIT
            currency = subaccount['balance']['currency']

            subaccount_parsed = {
                'account_no': account_no_parent,  # No currency info in account no
                'financial_entity_account_id': fin_ent_account_id_parent + currency,
                'account_type': account_type,
                'balance': balance,
                'currency': currency,
                'fin_ent_account_id_parent': fin_ent_account_id_parent,  # to use for movements extraction
                'req_params': {
                    'id': acc_dict['id']
                }
            }
            acc_multi[currency] = subaccount_parsed
        accounts_parsed.append(acc_multi)

    return accounts_parsed


def get_movements_parsed(resp_json: dict) -> List[MovementParsed]:
    """Parses
    {"items":
      {
      "id": "9dd1r4gOnXjb",
      "type": "EXPENSE",
      "description": "TRANS /ESOFITEC GLOBAL SOLUTIO",
      "categoryName": "Transferencias",
      "iconKey": "icon--arrow-right-2-toggle-16",
      "transactionAmount": {
        "amount": 500000.00,
        "currency": "EUR"
      },
      "transactionBalance": {
        "amount": 522543.41,
        "currency": "EUR"
      },
      "date": "2022-03-25",
      "accountInfo": {
        "concept_key": "100",
        "accountingDate": "2022-03-25",
        "debit": {
          "amount": -500000.00,
          "currency": "EUR"
        },
        "credit": {
          "amount": 0,
          "currency": "EUR"
        }
      },
      "attachment": {
        "idWebmail": "8123hkR7xGuHgNfhpUSqwcbzjQ3htAKqL8vDtfPYQYqpULHokvm2bjTWGYTRefrMhYm",
        "attachmentIndicator": "1"
      },
      "reference": "535",
      "referenceReceiver": "000000000000",
      "referencePayer": "0000000000000000"
      },
    ...
    }
    """
    movements_parsed = []  # type: List[MovementParsed]
    for mov_dict in resp_json['items']:
        value_date = mov_dict['date']  # '2022-03-25'
        operation_date = mov_dict['accountInfo']['accountingDate']

        sign = 1 if mov_dict['type'] == 'INCOME' else -1
        amount = sign * mov_dict['transactionAmount']['amount']
        temp_balance = mov_dict['transactionBalance']['amount']
        description = mov_dict['description']
        mov_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance,
            'may_have_receipt': False,  # TODO impl
            'receipt_params': ""
        }
        movements_parsed.append(mov_parsed)

    return movements_parsed

