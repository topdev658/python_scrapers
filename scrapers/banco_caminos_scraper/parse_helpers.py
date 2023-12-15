from typing import List

from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, MovementParsed, AccountParsed


__version__ = '1.2.0'
__changelog__ = """
1.2.0
get_accounts_parsed: get deposits too
1.1.0
extract credit accs
get_movements_parsed: explicit float amount and temp_balance (backend now may return ints)
"""


def get_accounts_parsed(resp_json: dict) -> List[AccountParsed]:
    """
    Parses
       {
      "id": "28b4ff8e-83c8-43fa-b1bd-0e7c4762da76",
      "name": "CUENTA CORRIENTE DIVISA",
      "alias": "CUENTA CORRIENTE",
      "productNumber": {
        "value": "********************0347",
        "format": {
          "id": "IBAN",
          "name": "IBAN"
        }
      },
      "balance": {
        "amount": 28410.12,
        "currency": {
          "id": "USD",
          "code": "840"
        }
      },
      "postedBalance": {
        "amount": 25107.18,
        "currency": {
          "id": "EUR",
          "code": "978"
        }
      },
      "relationType": {
        "id": "07",
        "name": "APODERADO"
      },
      "productType": {
        "id": "01",
        "name": "Cuentas"
      },
      "productSubtype": {
        "id": "03",
        "name": "Cuenta Divisa"
      },
      "signature": {
        "id": "1",
        "name": "SOLIDARIO SIN CONDICIONES",
        "conditions": {
          "limit": {
            "amount": -1,
            "currency": {
              "id": "EUR",
              "code": "978"
            }
          }
        }
      },
      "status": {
        "id": "01",
        "name": "VIGENTE"
      }
    }

    :param resp_json:
    :return:
    """
    accounts_parsed = []  # type: List[AccountParsed]

    # see 110_resp_products_decrypted.json
    for account_dict in resp_json['data']:
        product_name = account_dict['productType']['name']
        if product_name not in ['Cuentas', 'Crédito', 'Depósitos']:
            continue

        # "********************0347"
        account_no = account_dict['productNumber']['value']

        balance = account_dict['balance']['amount']
        currency = account_dict['balance']['currency']['id']  # EUR / USD
        account_type = ACCOUNT_TYPE_CREDIT if (balance < 0 or product_name == 'Crédito') else ACCOUNT_TYPE_DEBIT

        account_id = account_dict['id']

        account_parsed = {
            'account_no': account_no,
            'balance': balance,
            'currency': currency,
            'account_type': account_type,
            'id': account_id
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed(resp_json: dict) -> List[MovementParsed]:
    """
    Parses 130_resp_movs_decrypted.json
    {
      "id": "202112022021120263186303293621",
      "reason": "ABONO OP. TARGET2: RECIBIDA DE: GULERMAK AGIR SANAYI INSAAT VE TA",
      "amount": {
        "amount": 10723.5,
        "currency": {
          "id": "EUR",
          "code": "978"
        }
      },
      "operationDate": "2021-12-02",
      "balance": {
        "amount": 220120.8,
        "currency": {
          "id": "EUR",
          "code": "978"
        }
      },
      "valueDate": "2021-12-02",
      "type": {
        "id": "51006",
        "name": "ABONO OP. TARGET2"
      }
    }
    """
    movements_parsed_desc = []  # type: List[MovementParsed]

    for mov_dict in resp_json['data']:
        operation_date = mov_dict['operationDate']  # '2021-04-16'
        value_date = mov_dict['valueDate']

        amount = float(mov_dict['amount']['amount'])
        temp_balance = float(mov_dict['balance']['amount'])
        description = mov_dict['reason']

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed_desc.append(movement_parsed)

    return movements_parsed_desc
