import uuid
from collections import OrderedDict
from typing import List, Tuple, Optional

import transliterate

from custom_libs import extract
from project.custom_types import (
    ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed
)
from .custom_types import AccProduct, MovsPaginationParams

__version__ = '1.1.0'
__changelog__ = """
1.1.0
use float _sign to cast amount
"""

# from dev/5.0_mov_details_modal.html
EXTENDED_DESCRIPTION_DETAILS = OrderedDict([
    ('Transaction number', 'TransactionReference'),  # always == TransactionTU
    ('Details', 'Reason'),  # always == descr
    ('Sender details', 'SenderDetails'),  # for movs with pos amount (AmountSign=='C')
    ("Beneficiary's details", "SenderDetails"),  # for movs with neg amount (AmountSign=='D')
    ('Conversion details', 'ConversionDetails'),
    ('Additional information', 'AdditionalInformation'),
])


def _translit(text: str) -> str:
    """AlphaBank use greek lang for all movement descriptions,
    but currently, the DB can't save non-latin chars, so,
    let's do transliteration

    Also, it handles unexpected arg and returns it as is if can't transliterate

    >>> _translit('ΕΚΔΟΣΗ ΕΝΤΟΛΗΣ')
    'EKDOSI ENTOLIS'
    """

    # 'el' is greek
    # upper() bcs all descriptions are in upper case
    # but some chars can be recognized and initially converted
    # as lower letters

    try:
        return transliterate.translit(text, 'el', reversed=True).upper()
    except Exception:
        return text


def get_application_id(resp_text: str) -> str:
    return extract.re_first_or_blank('<meta name="ApplicationId" content="(.*?)"', resp_text)


def get_acc_products(resp_json: dict) -> List[AccProduct]:
    """
    Parses

    {'TotalRecords': 1, 'HasMore': False, 'ResultCode': 0, 'Products': [{'HasLoyalty': False,
    'BonusPoints': 0, 'CategoryType': 10001, 'Overdraft': 0, 'AlertsDomesticCashActivated':
    False, 'TotalBloks': 0, 'AlertsCrossBorderSalesActivated': False, 'Result': 0,
    'IsCorporate': True, 'CategoryGroup': -1, 'TypeName': 'ALPHA 290', 'Uses': [],
    'CurrentBalance': 0, 'LoyaltyScheme': 0, 'Color': 0, 'CreditLimit': 0, 'PointsToExpire': 0,
    'ProviderID': 0, 'AlertsCrossBorderCashActivated': False, 'AlertsDomesticSalesActivated':
    False, 'Title': '', 'IsAlphaBankProduct': False, 'LoyaltyPoints': 0,
    'HasEStatementsActivated': False, 'CurrentBalanceSign': None, 'DebitsCurDay': 0,
    'Code': 'GR2101401040104002002026642', 'LoyaltyPointsString': '0', 'CreditLimitSign': None,
    'TypeID': 3, 'ProductID': 7834968, 'Order': 0, 'PointsExpirationDate': None, 'RequestTypes':
    [0, 31, 21], 'CreditsCurDay': 0, 'PointsToExpireStr': '0', 'HasCheques': True,
    'IsPreferred': False}], 'LastRowNumber': 1, 'IsLastPage': True, 'ReplyRecords': 1}

    """
    acc_products = []  # type: List[AccProduct]
    for product_dict in resp_json['Products']:
        acc_product = AccProduct(
            account_no=product_dict['Code'],  # 'GR2101401040104002002026642'
            product_id=product_dict['ProductID'],  # 7834968
            type=product_dict['TypeID']  # 3
        )
        acc_products.append(acc_product)

    return acc_products


def _sign(val: str) -> float:
    # use float to cast amount (avoid int which can lead to wrong checksum (KeyValue)
    return 1.0 if val == 'C' else -1.0


def get_account_parsed(resp_json: dict) -> AccountParsed:
    """
    Parses

    {"ResultCode":0,"Balance":{"Currency":1,"HasCheques":true,
    "IBAN":"GR2101401040104002002026642","Name":"","NetBalance":289633.72,"NetBalanceSign":"C",
    "ProductDescription":"ALPHA 290","ProductTypeId":3,"Surname":"SΜΑLL WΟRLD FΙΝΑΝCΙΑL SΕRVΙCΕS
    SΡΑΙΝ S.Α","WithdrawAmount":289633.72,"WithdrawAmountSign":"C","Owners":[{
    "CompanyName":"SMALL WORLD FINANCIAL SERVICES SPAIN S.A","CompanyTitle":"SMALL WORLD
    FINANCIAL SERVICES SPAIN S.A","Contacts":[{"ContactType":1,"Description":"2109818771",
    "PinVerification":null},{"ContactType":3,"Description":"6976980367","PinVerification":null},
    {"ContactType":4,"Description":"JAVIER.PEREZ@SMALLWORLDFS.COM","PinVerification":null}],
    "CustomerNumber":"00000001837854501","DateOfBirth":"2018-06-22T00:00:00+03:00",
    "FatherName":"","IdentityCode":"82414046","IdentityType":3,"Name":"","Surname":""}]}}

    """

    bal_dict = resp_json['Balance']
    account_no = bal_dict['IBAN']  # type: str
    # No NetBalance key if balance is 0
    balance = _sign(bal_dict['NetBalanceSign']) * bal_dict.get('NetBalance', 0)
    account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
    currency = 'EUR' if bal_dict['Currency'] == 1 else 'UNKNOWN'
    country_code = 'GRC' if account_no.startswith('GR') else 'ESP'
    account_parsed = {
        'account_no': account_no,
        'balance': balance,
        'currency': currency,
        'account_type': account_type,
        'country_code': country_code
    }

    return account_parsed


def get_organization_title(resp_json: dict) -> str:
    """Parses resp for account_parsed"""
    owners = resp_json.get('Balance', {}).get('Owners', [{}])  # type: list
    organization_title = ''
    for owner in owners:
        organization_title = owner.get('CompanyTitle', '')
        if organization_title:
            break
    return organization_title


def get_movements_parsed(
        resp_json: dict,
        temp_balance: float = None) -> Tuple[List[MovementParsed], MovsPaginationParams, Optional[float]]:
    """Parses

    {"ResultCode":0,"CurrentPageIndex":"0001201907130055577","HasMore":false,"ReplyRecords":10,
    "TotalRecords":10,"NewGrossBalance":484633.72,"NewGrossBalanceSign":"C",
    "PreviousGrossBalance":1190749.72,"PreviousGrossBalanceSign":"C",
    "Statements":[{
    "Amount":195000,"AmountSign":"C","BalanceSign":"C","EntryDate":"12/7/2019",
    "HasCumulative":false,"Reason":"LCC ΤRΑΝS SΕΝDΙΝG LΤ","TransactionUN":"20190712949044Ξ112",
    "Valeur":"12/7/2019","Branch":"949"},

    {"Amount":11326.5,"AmountSign":"C","BalanceSign":"C",
    "BranchInfo":{"Address":"2, Achilleos St","City":"2, Achilleos St","Code":"327","Fax":"210
    523 0292","Name":"Karaiskaki Square","Phone":"210 520 5745","ZipCode":"10437"},
    "EntryDate":"12/7/2019","HasCumulative":false,"Reason":"Τ SΕRVΙCΕS 61001    ",
    "TransactionUN":"201907123279610092","Valeur":"12/7/2019","Branch":"327"},

    {"Amount":28538.5,
    "AmountSign":"C","BalanceSign":"C","BranchInfo":{"Address":"2, Achilleos St","City":"2,
    Achilleos St","Code":"327","Fax":"210 523 0292","Name":"Karaiskaki Square","Phone":"210 520
    5745","ZipCode":"10437"},"EntryDate":"12/7/2019","HasCumulative":false,"Reason":"ΒURRΑQ ΑΕ
    61004     ","TransactionUN":"201907123279610088","Valeur":"12/7/2019","Branch":"327"}
    """

    pagination_params = MovsPaginationParams(
        has_more_pages=resp_json.get('HasMore', False),
        LastPageIndex_param=resp_json.get('CurrentPageIndex'),
        LastExtraitKey_param=resp_json.get('LastExtraitKey'),
    )

    movements_parsed_desc = []  # type: List[MovementParsed]
    # Handle 'no movs':
    # {'TotalRecords': 0, 'NewGrossBalanceSign': None, 'HasMore': False, 'ResultCode': 0,
    # 'ReplyRecords': 0, 'LastExtraitKey': None, 'PreviousGrossBalanceSign': None}
    if resp_json['ReplyRecords'] == 0:
        return movements_parsed_desc, pagination_params, temp_balance

    if temp_balance is None:
        # NewGrossBalance is the same for all pages,
        # That's why we need to use temp_bal of the last mov from the previous page.
        # Get it 1s time if None provided
        temp_balance = _sign(resp_json['NewGrossBalanceSign']) * resp_json['NewGrossBalance']
    mov_dicts = resp_json['Statements']
    for mov_dict in mov_dicts:
        amount = _sign(mov_dict['AmountSign']) * mov_dict['Amount']
        operation_date = mov_dict['EntryDate']
        value_date = mov_dict['Valeur']
        description = _translit(mov_dict['Reason'])
        branch = mov_dict.get('BranchInfo', {}).get('Code', '') or mov_dict.get('Branch', '')
        movement_parsed = {
            'operation_date': operation_date,   # '7/1/2021'
            'value_date': value_date,
            'description': description.strip(),
            'amount': amount,
            'temp_balance': temp_balance,
            'branch': branch,
            # several related movements may have the same TransactionUN
            # (main mov and comission mov..
            # EXAMPLE
            # -u 340332 -a 20002
            #  11/7/2019
            #  250D
            #  10...0D)
            'un': mov_dict['TransactionUN'],
            'id': '{}--{}'.format(mov_dict['TransactionUN'], uuid.uuid4())
        }

        movements_parsed_desc.append(movement_parsed)
        temp_balance = round(temp_balance - amount, 2)

    return movements_parsed_desc, pagination_params, temp_balance


def get_description_extended(resp_json: dict, mov_parsed: MovementParsed) -> str:
    """
    Parses

    {"ResultCode":0,"CurrentPageIndex":"","HasMore":false,"ReplyRecords":1,
    "TotalRecords":1,"LastExtraitKey":null,"NewGrossBalanceSign":null,
    "PreviousGrossBalanceSign":null,"Statements":[{"Amount":195000.0,"AmountSign":"C",
    "EntryDate":"12/7/2019 12:00:00 πμ","HasCumulative":false,"Reason":"LCC ΤRΑΝS SΕΝDΙΝG
    LΤ","StatementDetails":[{"AdditionalInformation":"","Amount":195000.0,"AmountSign":"C",
    "ConversionDetails":"","IBAN":"GR2101401040104002002026642","Reason":"LCC ΤRΑΝS SΕΝDΙΝG
    LΤ","SenderDetails":"LCC ΤRΑΝS SΕΝDΙΝG LΙΜΙΤΕD",
    "TransactionDate":"2019-07-12T00:00:00+03:00",
    "TransactionReference":"20190712949044Ξ112","ValueDate":"2019-07-12T00:00:00+03:00"}],
    "TransactionUN":"20190712949044Ξ112","Valeur":"12/7/2019 12:00:00 πμ"}]}

    Also, it handles responses w/o details or for several movements with
    the same TransactionUn (check the dev folder)
    """

    # Default details, will be used if resp doesn't provide it
    details = {
        'TransactionReference': mov_parsed['un'],
        'Reason': mov_parsed['description']
    }

    # Handle case:
    # several related movements may have the same TransactionUN
    # (main mov and comission mov..
    # EXAMPLE
    # -u 340332 -a 20002
    #  11/7/2019
    #  250D
    #  10...0D)
    # Detect exact movement by amount
    # Check response examples in dev/5.1_mov_details...json
    for mov in resp_json.get('Statements', []):
        for det in mov.get('StatementDetails', {}):
            amt_wo_sign = det.get('Amount')
            sign_str = det.get('AmountSign')
            # handle nones
            if (amt_wo_sign is not None and sign_str
                and _sign(sign_str) * amt_wo_sign) == mov_parsed['amount']:
                # found the movement
                details = det
                break

    description_extended = mov_parsed['description']
    description_extended += ' || Branch: {}'.format(mov_parsed.get('branch', '')).rstrip()

    for det_title, det_key in EXTENDED_DESCRIPTION_DETAILS.items():
        detail = details.get(det_key) or ''
        # overwrite one of shared details, depends of movement's sign
        if det_title == 'Sender details' and mov_parsed['amount'] < 0:
            detail = ''
        if det_title == "Beneficiary's details" and mov_parsed['amount'] >= 0:
            detail = ''
        msg = '{}: {}'.format(det_title, _translit(detail)).strip()

        description_extended += ' || {}'.format(msg)

    return description_extended.strip()
