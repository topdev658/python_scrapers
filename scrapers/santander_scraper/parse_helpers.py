import datetime
from typing import Dict, List, Optional

from custom_libs import extract
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed

__version__ = '1.3.0'
__changelog__ = """
1.3.0 2023.04.17
refactored movement_parsed param 'has_final_receipt'
1.2.0
get_accounts_parsed: use saldoCont instead of saldoDisp (example: -a 9603, 0049 1555 10 2110234918)
1.1.1
_get_extended_description: type fixes: strict val of dict to avoid runtime formatting errs  
1.1.0
_get_extended_description: handle 'amount' dict, float fmt
"""

# Unused now, but maybe will be useful later
NO_MOVEMENTS_SIGNS = [
    'NO HAY MOVIMIENTOS',
    'NO DISPONE DE LOS PERMISOS NECESARIOS PARA REALIZAR ESTA OPERACIóN',
    'PRODUCTO NO CONSULTABLE POR ESTA APLICACIÓN.'
]

#  [(title, dict_key), ...]
MOV_EXTENDED_DESCRIPTION_KEYS = [
    ('Concepto', 'concept'),
    ('Fecha de operación', 'operationDate'),
    ('Fecha valor', 'valueDate'),
    ('Tipo de movimiento', 'movementType'),  # H - Haber, D - Debe
    ('Tipo de operación', 'operationType'),
    ('Código de operación', 'operationCode'),
    ('Oficina de origen', 'originOffice'),
    ('Referencia 1', 'referenceOne'),  # None or str
    ('Referencia 2', 'referenceTwo'),  # None or str
    ('Importe', 'amount'),  # float
    ('Nº Documento', 'documentNumber'),  # None or str
    ('Información adicional', 'additionalInformation'),
]


def get_new_universal_cookie(resp_text: str) -> str:
    cookie_val = extract.re_first_or_blank(
        r"""(?si)var\s+cookieData\s*=\s*"(.*?)";\s*var\s+cookieName\s*=\s*"NewUniversalCookie";""",
        resp_text
    )
    return cookie_val


def get_accounts_parsed(resp_json: dict) -> List[AccountParsed]:
    accounts_dicts = resp_json.get('elements', [])

    accounts_parsed = []  # type: List[AccountParsed]
    for account_dict in accounts_dicts:
        """{'iban': {'entity': '0049', 'ccc': 'ES4500491555142810212213', 'office': '1555', 'accountNumber': 
        '2810212213', 'countryIban': 'ES', 'dc': '14', 'dcIban': '45'}, 'saldoCont': {'amount': 0.0, 'currency': {
        'id': 'EUR', 'comment': None, 'caption': None}}, 'typePerson': 'J', 'descAccount': 'CUENTA ESTANDAR 
        EMPRESAS', 'saldoContContr': {'amount': 0.0, 'currency': {'id': 'EUR', 'comment': None, 'caption': None}}, 
        'holder': 'AZORALLOM SLU', 'impVariacion': {'amount': 45424.76, 'currency': {'id': 'EUR', 'comment': None, 
        'caption': None}}, 'saldoDispContr': {'amount': 45424.76, 'currency': {'id': 'EUR', 'comment': None, 
        'caption': None}}, 'codPerson': 1825157, 'impVariacionContr': {'amount': 45424.76, 'currency': {'id': 'EUR', 
        'comment': None, 'caption': None}}, 'alias': 'Asbatu - Operativa', 'saldoDisp': {'amount': 45424.76, 
        'currency': {'id': 'EUR', 'comment': None, 'caption': None}}}
        """

        # 0049 1555 10 2110216740 for backward comp with the previous API-based scraper
        fin_ent_account_id = '{} {} {} {}'.format(
            account_dict['iban']['entity'],
            account_dict['iban']['office'],
            account_dict['iban']['dc'],
            account_dict['iban']['accountNumber'],
        )
        # ES7300491555102110216740
        account_no = account_dict['iban']['ccc']
        # was saldoDisp, but -a 9603: 0049 1555 10 2110234918
        #  shows that saldoCont (== saldo consolidado on new web) is used by movs
        balance = account_dict.get('saldoCont', {}).get('amount', None)

        currency = account_dict.get('saldoCont', {}).get('currency', {}).get('id')  # EUR
        # handle case if currency id == '' (-u 291733 -a 16916)
        if not currency:
            currency = account_dict.get('saldoContContr', {}).get('currency', {}).get('id')  # EUR
        assert currency

        # account-stub, it raises errors in the UI when try to open movements
        if balance is None:
            continue

        account_parsed = {
            'financial_entity_account_id': fin_ent_account_id,
            'account_no': account_no,
            'account_type': ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT,
            'company': account_dict.get('holder'),
            'balance': balance,
            'currency': currency,
            'iban_data': account_dict['iban'],  # to use in process_account
        }
        accounts_parsed.append(account_parsed)

    return accounts_parsed


# Similar to BBVA approach with keys
def _get_extended_description(mov_dict: dict, descr_short: str) -> str:
    """
    Parses

    <class 'dict'>:
    {'valueDate': '2019-05-31',
    'documentNumber': None,
    'referenceOne': None,
    'operationType': 'TRANSFERENCIA DE B',
    'referenceTwo': None,
    'operationDate': '2019-05-31',
    'additionalInformation': '',
    'numMovement': None,
    'concept': 'TRANSFERENCIA DE BALCELLS GANTES LAURA, CONCEPTO 5587.      ',
    'originOffice': '',
    'amount': 1518.03,
    'currencyAmount': {'id': 'EUR', 'comment': None, 'caption': None},
    'operationCode': ' 71',
    'movementType': 'H',
    'pdfStatus': '0',
    'balance': None,
    'currencyBalance': {'id': 'EUR', 'comment': None, 'caption': None}}

    <class 'dict'>:
    {'valueDate': '2019-05-30',
    'documentNumber': '0000000000',
    'referenceOne': None,
    'operationType': 'ABONO TRANSFERENCI',
    'referenceTwo': None,
    'operationDate': '2019-05-30',
    'additionalInformation': '',
    'numMovement': 43,
    'concept': 'TRANSFERENCIA DE CASTILLO ARACENA HILDEMAR, CONCEPTO 56462. ',
    'originOffice': '1916',
    'amount': 412.8,
    'currencyAmount': {'id': 'EUR', 'comment': None, 'caption': None},
    'operationCode': ' 71',
    'movementType': 'H',
    'pdfStatus': '1',
    'balance': 103534.36,
    'currencyBalance': {'id': 'EUR', 'comment': None, 'caption': None}}
    """

    # description_extended = descr_short  # replaced by val with 'Concepto' tag
    description_extended = ''
    for title, field in MOV_EXTENDED_DESCRIPTION_KEYS:
        val = mov_dict.get(field) or ''
        if field == 'movementType':
            # convert to known human-readable vals or leave it as is
            if val == 'H':
                val = 'Haber'
            elif val == 'D':
                val = 'Debe'
        if field == 'amount':
            if isinstance(val, dict):
                # {'amount': 6000.0, 'currency': 'EUR'} -> '6,000.00 EUR'
                val = '{:,.2f} {}'.format(val['amount'], val['currency']).strip()
            if isinstance(val, float):
                val = '{:,.2f}'.format(val)
        msg = '{}: {}'.format(title, extract.remove_extra_spaces(str(val)))
        description_extended += " || {}".format(msg)

    return description_extended.lstrip(' |')  # remove first redundant separator


def get_check_data_from_extended_description(ext_desc: str) -> dict:
    """
    Extract from
    Concepto: ENTREGA DE DOCUMENTOS PARA SU COMPENSACION ||
    Fecha de operación: 2019-07-04 || Fecha valor: 2019-07-08 ||
    Tipo de movimiento: Haber || Tipo de operación: ENTREGA DE DOCUMEN ||
    Código de operación: 35 ||
    Oficina de origen:  || Referencia 1:  || Referencia 2:  || Importe: 1815.0 || Nº Documento: 0001111110 || Información adicional:
    """

    ext_desc_data = {
        'originOffice': None,
        'documentNumber': None,
        'operationCode': None,
        'checkNumber': None
    }  # type: Dict[str, Optional[str]]

    ext_desc_data['originOffice'] = extract.re_first_or_blank(
        r'(?si)Oficina de origen:([^|]*)',
        ext_desc
    ).strip() or None

    ext_desc_data['documentNumber'] = extract.re_first_or_blank(
        r'(?si)Nº Documento:([^|]*)',
        ext_desc
    ).strip() or None

    ext_desc_data['operationCode'] = extract.re_first_or_blank(
        r'(?si)Código de operación:([^|]*)',
        ext_desc
    ).strip() or None

    if ext_desc_data['documentNumber']:
        ext_desc_data['checkNumber'] = "{}-{}-{}".format(
            ext_desc_data['originOffice'],
            ext_desc_data['documentNumber'],
            ext_desc_data['operationCode']
        )
    else:
        ext_desc_data['checkNumber'] = "{}-{}".format(
            ext_desc_data['originOffice'],
            ext_desc_data['operationCode']
        )

    return ext_desc_data


def get_movements_parsed(resp_json: dict) -> List[MovementParsed]:
    movements_dicts = resp_json.get('appointments', [])
    movements_parsed_desc = []  # type: List[MovementParsed]
    for movement_dict in movements_dicts:

        value_date = movement_dict.get('valueDate')  # 2018-01-19
        operation_date = movement_dict.get('operationDate')  # 2018-01-19
        amount = movement_dict.get('amount')
        temp_balance = movement_dict.get('balance')  # can be None, will calc it later
        description = extract.remove_extra_spaces(movement_dict.get('concept', ''))
        description_extended = _get_extended_description(movement_dict, description)

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


# FIXME delete deprecated
def is_desc_ordering(movs_parsed: List[MovementParsed]) -> Optional[bool]:
    """Allows to detect ordering of today and future movements
    (it may be different to prev days)

    >>> mm_asc = [{'temp_balance': 2.0, 'amount': -1.0},\
        {'temp_balance': 3.0, 'amount': 1.0}, \
        {'temp_balance': 4.0, 'amount': 1.0}]
    >>> is_desc_ordering(mm_asc)
    False

    >>> mm_desc = [{'temp_balance': 3.0, 'amount': 1.0},\
        {'temp_balance': 2.0, 'amount': -2.0},\
        {'temp_balance': 4.0, 'amount': 1.0}]
    >>> is_desc_ordering(mm_desc)
    True
    """
    mov_prev = None
    for mov in movs_parsed:
        maybe_asc = False
        maybe_desc = False

        if mov['temp_balance'] is None:
            continue
        if mov_prev is None:
            mov_prev = mov
            continue

        # Desc
        if round(mov_prev['temp_balance'], 2) == round(mov['temp_balance'] + mov_prev['amount'], 2):
            maybe_desc = True
        # Asc
        if round(mov['temp_balance'], 2) == round(mov_prev['temp_balance'] + mov['amount'], 2):
            maybe_asc = True

        if not (maybe_asc or maybe_desc):
            raise Exception('Inconsistent balance')

        if maybe_desc and maybe_asc:  # unclear situation, repeat attempt
            mov_prev = mov
            continue
        else:
            return maybe_desc

    return None  # doesn't matter - only Nones as temp_balances, most probably asc


# FIXME delete deprecated
def reorder_movements_of_current_date(movements_parsed: List[MovementParsed],
                                      account_no: str) -> List[MovementParsed]:
    """
    Santander returns in ascending movements of current date (the first/oldest is first in the list)
    and in descending ordered movements of previous dates (the last/youngest is first in the list)

    Also, in the end of the day there are cases if today's movements already desc, but
    future movs are asc - handle this by is_desc_ordering()

    :returns: movements_parsed_ordered_asc
    """

    # use local time (UTC since 2019-09)
    current_date = datetime.datetime.utcnow().date()

    movs_parsed_future_dates = []
    movs_parsed_current_date = []
    movs_parsed_prev_dates_desc_ordering = []

    # Fill movs_parsed_current_date
    for movement_parsed in movements_parsed:
        mov_date = datetime.datetime.strptime(movement_parsed['operation_date'], '%Y-%m-%d').date()

        if mov_date > current_date or movement_parsed['temp_balance'] is None:
            movs_parsed_future_dates.append(movement_parsed)
        elif mov_date == current_date:  # it depends on time
            movs_parsed_current_date.append(movement_parsed)
        else:
            movs_parsed_prev_dates_desc_ordering.append(movement_parsed)

    movs_parsed_future_date_desc_ordering = (
        movs_parsed_future_dates if is_desc_ordering(movs_parsed_future_dates)
        else movs_parsed_future_dates[::-1]
    )

    movs_parsed_current_date_desc_ordering = (
        movs_parsed_current_date if is_desc_ordering(movs_parsed_current_date)
        else movs_parsed_current_date[::-1]
    )

    movements_parsed_desc_ordering = (movs_parsed_future_date_desc_ordering
                                      + movs_parsed_current_date_desc_ordering
                                      + movs_parsed_prev_dates_desc_ordering)

    return movements_parsed_desc_ordering[::-1]


def reorder_and_calc_temp_balances(movements_parsed: List[MovementParsed]) -> List[MovementParsed]:
    """
    Santander returns in ascending movements of current date (the first/oldest is first in the list)
    and in descending ordered movements of previous dates (the last/youngest is first in the list)

    Also, in the end of the day there are cases if today's movements already desc, but
    future movs are asc - handle this by is_desc_ordering()

    IF THERE ARE NO past movements with known balances, then no movements will be returned
    because we can't calc temp_balances with this approach.
    No way to calc from account.balance because sometimes it counts future movements
    but sometimes not.

    :returns: movements_parsed_ordered_asc

    >>> m = lambda a, b: {'amount': a, 'temp_balance': b}
    >>> newest = reorder_and_calc_temp_balances([m(2, None), m(1, None), m(3, 100), m(4, 97)])[-1]
    >>> newest['temp_balance']
    103
    >>> newest['amount']
    1

    >>> reorder_and_calc_temp_balances([m(2, None), m(1, None)])
    []
    """

    movs_parsed_future_asc = []
    movs_parsed_past_desc = []

    for movement_parsed in movements_parsed:
        if movement_parsed['temp_balance'] is None:  # future and today's movements
            movs_parsed_future_asc.append(movement_parsed)
        else:
            movs_parsed_past_desc.append(movement_parsed)

    movements_parsed_asc = movs_parsed_past_desc[::-1] + movs_parsed_future_asc

    temp_balance = None
    for movement_parsed in movements_parsed_asc:
        mov_temp_balance = movement_parsed['temp_balance']
        if mov_temp_balance is not None:
            temp_balance = mov_temp_balance
            continue
        if mov_temp_balance is None and temp_balance is not None:
            temp_balance = round(temp_balance + movement_parsed['amount'], 2)
            movement_parsed['temp_balance'] = temp_balance
    movements_parsed_asc_w_bal = [m for m in movements_parsed_asc if m['temp_balance'] is not None]

    return movements_parsed_asc_w_bal
