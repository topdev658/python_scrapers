import re
from typing import List

from custom_libs import extract
from project.custom_types import AccountParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT
from .custom_types import CurrencyBalance, AccountForMT940, Contract


def get_csrf_token(resp_text: str) -> str:
    csrf_token = extract.re_first_or_blank(r"var\s+csrfToken\s*[=]\s*'(.*?)'", resp_text)
    return csrf_token


def get_contracts(resp_text: str) -> List[Contract]:
    """
    Parses
        clients.push({
        id: 'EBPCLI427344',
        text: 'Surexport UK Limited',
        email: 'online.desk@ebury.com',
        phone: '+44 (0) 207 197 2421',
        disabled: false
    });
    """
    contracts = []  # type: List[Contract]
    clients_js = re.findall(r"""(?si)clients.push\(.*?\)""", resp_text)
    for client_js in clients_js:
        contract_id = extract.re_first_or_blank(r"id:\s*'(.*?)'", client_js)  # EBPCLI427344
        contract_name = extract.re_first_or_blank(r"text:\s*'(.*?)'", client_js)  # Surexport UK Limited
        contracts.append(Contract(
            contract_id=contract_id,
            contract_name=contract_name,
        ))
    return contracts


def get_contract(resp_text: str) -> Contract:
    client_js = extract.re_first_or_blank(r"""(?si)client:\s*(\{.*?\})""", resp_text)
    contract_id = extract.re_first_or_blank(r'identifier:\s*"(.*?)"', client_js)  # EBPCLI427344
    contract_name = extract.re_first_or_blank(r'name:\s*"(.*?)"', client_js)  # Surexport UK Limited
    contract = Contract(
        contract_id=contract_id,
        contract_name=contract_name,
    )
    return contract


def get_currency_balances(resp_json: dict) -> List[CurrencyBalance]:
    """Parses
    {"total": 2, "count": 2, "items": [
        {"currency": "EUR",
        "outgoing": 0.0,
        "incoming": 0.0,
        "funds_on_account": 0.0,
        "margin_call": 0.0,
        "initial_margin": 0.0,
        "required_funds": 0.0,
        "processing_payments": 0.0},
        {"currency": "USD",
        "outgoing": 0.0,
        "incoming": 0.0,
        "funds_on_account": 88743.19,
        "margin_call": 18256.97,
        "initial_margin": 0.0,
        "required_funds": -88743.19,
        "processing_payments": 0.0}
        ]}
    """
    try:
        cnc_balances = [CurrencyBalance(
            currency=i['currency'],
            balance=i['funds_on_account']
        ) for i in resp_json['items']]
    except Exception as e:
        pass
    return cnc_balances


def get_accounts_for_mt940(resp_json: dict) -> List[AccountForMT940]:
    """
    Parses
    [
      {
        "currency_account_uuid": "8845da84-0c66-b7e5-ba2a-709fad5676f1",
        "currency_account_id": 528032,
        "type": "Clients",
        "currency": "EUR"
      },
      {
        "currency_account_uuid": "6cf9cf07-dd13-6c6d-12d4-1bb59e5b5699",
        "currency_account_id": 528031,
        "type": "Clients",
        "currency": "USD"
      }
    ]
    """
    accs_for_mt940 = [AccountForMT940(
        currency=i['currency'],
        currency_account_id=i['currency_account_id'],
        fin_ent_account_id=i['currency_account_uuid']
    ) for i in resp_json]
    return accs_for_mt940


def get_account_parsed(resp_json: dict, balance: float) -> AccountParsed:
    """Parses  35_resp_account_details_eur.json
    [
      {
        "account_id": "8845da84-0c66-b7e5-ba2a-709fad5676f1",
        "account_detail_id": "d386c27a-2acd-62ee-e808-e72ddcf8bf24",
        "account_details_type": "pooled",
        "alias": null,
        "bank_account_number": "0060000087",
        "bank_identifier": null,
        "bank_identifier_type": null,
        "bic": "BPLCESMM",
        "country": "ES",
        "currency": "EUR",
        "financial_institution_name": "BARCLAYS BANK IRELAND PLC SUCURSAL EN ESPANA",
        "financial_institution_address": "CALLE JOSE ABASCAL 51\n28003\nMADRID",
        "holder_name": "Ebury Partners Belgium NV",
        "holder_address": "Avenue des Arts 52/ Kunstlaan 52,Brussels,1000",
        "iban": "ES9201520348990060000087",
        "primary": null,
        "reference_for_payment": "EBPCLI466830",
        "status": "confirmed"
      }
    ]
    """
    account_dict = resp_json[0]

    currency = account_dict['currency']  # EUR
    country = account_dict['country']  # ES / GB
    # -a 32756, 'Ecommprojects Internet SL', acc CNY has iban=null, use bank_account_number
    account_no = account_dict['iban'] or account_dict['bank_account_number']
    account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

    account_parsed = {
        'account_no': account_no,  # IBAN
        'account_type': account_type,
        'balance': balance,
        'currency': currency,
        'account_detail_id': account_dict['account_detail_id'],
        # TODO must convert to 3-char country_code to save in _TesoraliaAccounts,
        #  but it is not necessary now because the scraper doesn't use these accounts for MT940
        'country': country,
        # '8845da84-0c66-b7e5-ba2a-709fad5676f1'
        'financial_entity_account_id': account_dict['account_id']
    }

    return account_parsed
