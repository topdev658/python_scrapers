import re
import traceback
from collections import OrderedDict
from datetime import datetime
from typing import List, Tuple

from custom_libs import extract
from custom_libs.date_funcs import month_esp_to_num_str_short
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import (
    ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, AccountScraped, MovementParsed
)

INT_DATE_FMT = '%Y-%m-%d'  # the website date fmt


def _convert_amounts_to_float_with_precision(amount_int, decimals_len) -> float:
    """
    Converts to float with necessary digits after point

    >>> _convert_amounts_to_float_with_precision(-91256, 2)
    -912.56

    >>> _convert_amounts_to_float_with_precision(-5, 2)
    -0.05

    >>> _convert_amounts_to_float_with_precision(-11, 2)
    -0.11

    >>> _convert_amounts_to_float_with_precision(11, 2)
    0.11
    """
    amount_str = str(amount_int)  # '-5'
    sign = extract.re_first_or_blank('[+-]', amount_str) or '+'  # '-'
    amount_abs_str = re.sub('[+-]', '', amount_str)  # '5'
    amount_str_correct = sign + amount_abs_str.rjust(decimals_len + 1).replace(' ', '0')  # '-005'

    amount_float_str = (amount_str_correct[:-decimals_len]
                        + '.'
                        + amount_str_correct[-decimals_len:])  # '-0.05'
    return round(float(amount_float_str), decimals_len)


def filter_mov_parsed_by_dates(movements_parsed, date_from, date_to):
    movements_parsed_filtered = [
        mov
        for mov in movements_parsed
        if date_to >= datetime.strptime(mov['operation_date'], INT_DATE_FMT) >= date_from
    ]
    return movements_parsed_filtered


def get_organization_title(html_str):
    return extract.re_first_or_blank('bk-user-alias="(.*?)"', html_str)


def get_accounts_parsed(data: dict) -> List[AccountParsed]:
    """
    {'alias': '-',
    'codigoProductoCPP': '11355',
    'codigoProductoUrsus': '11355',
    'nombreProductoComercial': 'CUENTA NEGOCIO',
    'numeroDeCuenta': 'ES1920389668516000055938',     <-------------- 2, use 20389668516000055938
    as id
    'saldoDisponible': {'decimales': 2,
                        'importe': 114364094,
                        'nombreMoneda': 'EUR'},
    'saldoInformado': True,
    'saldoReal': {'decimales': 2,
                  'importe': 114364094,               <--------------- amount 1143640,94
                  'nombreMoneda': 'EUR'}}
    """

    cuentas = data['data']['listaCuentas']

    cuentasExtranjero = data['data']['listaCuentasExtranjero']
    cuentasNoRelacionadas = data['data']['listaCuentasNoRelacionadas']

    accounts_raw_datas = cuentas + cuentasExtranjero + cuentasNoRelacionadas

    accounts_parsed = []  # type: List[AccountParsed]
    for account_raw_data in accounts_raw_datas:

        decimals_len = account_raw_data['saldoReal']['decimales']
        balance_float_str = _convert_amounts_to_float_with_precision(account_raw_data['saldoReal']['importe'],
                                                                     decimals_len)
        # handle case like: ES13 2038 9705 1860 0004 8829	No aplica	No aplica (no balance/currency in the UI)
        currency = account_raw_data['saldoReal'].get('nombreMoneda', 'EUR')

        account_parsed = {
            'account_no': account_raw_data['numeroDeCuenta'],
            'financial_entity_account_id': account_raw_data['numeroDeCuenta'][4:],
            'balance': balance_float_str,
            'currency': currency,
            'account_type': ACCOUNT_TYPE_CREDIT if float(
                balance_float_str) < 0 else ACCOUNT_TYPE_DEBIT
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def _get_extended_description(mov_data: OrderedDict) -> str:
    description_extended = ''

    oficina = mov_data.get('oficina', '')
    if oficina:
        description_extended += ' || Oficina : {}'.format(oficina)

    for reference in mov_data.get('referencias', {}):

        ref_title = extract.remove_extra_spaces(reference.get('nombreCorto', ''))
        ref_value = extract.remove_extra_spaces(reference.get('descripcion', ''))
        if not (ref_title and ref_value):
            continue

        msg = '{} {}'.format(ref_title, ref_value)
        description_extended += " || {}".format(msg)

    return description_extended


def get_movements_parsed(resp_data: dict,
                         logger: ScrapeLogger,
                         account_scraped: AccountScraped,
                         date_from_str: str,
                         date_to_str: str) -> Tuple[bool, List[MovementParsed]]:
    """
    Parses mov data
    {'beneficiarioOEmisor': '',
                       'concepto': 'INTERESES',
                       'fechaMovimiento': {'valor': '2016-11-08'},
                       'fechaValor': {'valor': '2016-11-06'},
                       'importe': {'importe': -91256,
                                   'nombreMoneda': 'EUR',
                                   'numeroDecimales': 2},
                       'indicadorDevolucionRecibo': 'false',
                       'indicadorDevolucionReciboManyana': 'false',
                       'indicadorMovimientoCorrespondencia': 'false',
                       'indicadorTransferencia': 'false',
                       'oficina': '0606',
                       'referenciaRecibo': '',
                       'referencias': {
                            'nombreCorto': 'IDENTIF. CHEQUE  :',
                            'codigoCampo': 'MVREF0',
                            'descripcion': '0005128023',
                            'longitudPlantilla': '10',
                            'codigoPlantilla': '0101'
                        },
                       'saldoPosterior': {'importe': -78591895,
                                          'nombreMoneda': 'EUR',
                                          'numeroDecimales': 2}}

    :returns (is_success, List[MovementParsed]])
    """
    try:
        movements_raw_datas = resp_data['data']['movimientos']

        movements_parsed = []  # type: List[MovementParsed]
        for movement_raw_data in movements_raw_datas:
            description_basic = movement_raw_data['concepto']
            description_additional = movement_raw_data['beneficiarioOEmisor']
            if description_additional:
                description_additional = extract.remove_extra_spaces(description_additional)
                description = '{} {}'.format(description_basic, description_additional)
            else:
                description = description_basic

            description_extended = _get_extended_description(movement_raw_data)
            description_full = description + description_extended

            movement_parsed = {
                'amount': _convert_amounts_to_float_with_precision(
                    movement_raw_data['importe']['importe'],
                    movement_raw_data['importe']['numeroDecimales']
                ),
                'temp_balance': _convert_amounts_to_float_with_precision(
                    movement_raw_data['saldoPosterior']['importe'],
                    movement_raw_data['saldoPosterior']['numeroDecimales']
                ),
                'description': description,
                'description_extended': description_full,
                # 2017-01-01 - correct db format, use without conversion
                'operation_date': movement_raw_data['fechaMovimiento']['valor'],
                'value_date': movement_raw_data['fechaValor']['valor'],
                # the movement may have or not a receipt,
                # it will be clear after additional http request
                'may_have_receipt': movement_raw_data['indicadorMovimientoCorrespondencia'] == 'true',
                'receipt_req_args': {
                    'codigoMovimiento': movement_raw_data['codigoMovimiento'],
                    'fechaMovimiento': movement_raw_data['fechaMovimiento'],
                    'fechaValor': movement_raw_data['fechaValor'],
                    'referencias': movement_raw_data['referencias']
                },
            }

            movements_parsed.append(movement_parsed)
    except:
        #  possible error: no necessary fields in var 'data'
        logger.error(
            '{}: get_movements_parsed: dates from {} to {}\n'
            'HANDLED EXCEPTION\n{}\n\n'
            'RESPONSE\n{}\n'
            'Skip.'.format(
                account_scraped.FinancialEntityAccountId,
                date_from_str,
                date_to_str,
                traceback.format_exc(),
                resp_data
            )
        )
        return False, []

    return True, movements_parsed


def _get_date_to_str(text: str) -> str:
    """
    >>> _get_date_to_str('15/ABR/2019')
    '15/04/2019'
    """
    try:
        # '23', 'julio', '2018'
        # 2 steps for type checker
        dmy = re.findall(r'(\d+).(\w+).(\d+)', text)[0]  # type: Tuple[str, str, str]
        d, m, y = dmy
    except:
        return ''
    m_num = month_esp_to_num_str_short(m)
    if m_num == '':
        return ''
    d = d if len(d) > 1 else '0' + d
    return "{}/{}/{}".format(d, m_num, y)
