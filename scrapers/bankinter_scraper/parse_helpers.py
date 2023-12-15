import datetime
import hashlib
import html
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

from custom_libs import convert
from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project import settings as project_settings
from project.custom_types import (
    ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed,
    LeasingContractParsed, LeasingFeeParsed
)
from .custom_types import ReceiptReqParams, Company

__version__ = '1.3.2'
__changelog__ = """
1.3.2
get_movements_parsed_from_html_resp_multicurrency:
  Fixed get movement description from html when description contains link data
1.3.1
get_movements_parsed_from_html_resp:
  Fixed get movement description from html when description contains link data
1.3.0
get_movements_parsed_from_html_resp, get_movements_parsed_from_html_resp_multicurrency: 
   handle not 'receipt_params' case: returns 'unhandled_receipt_params'
1.2.0
get_movements_parsed_from_html_resp_multicurrency: CANCELED_SUB_ACCOUNT_MARKER
used to skip canceled accounts
1.1.0
get_accounts_multicurrency_parsed: account_no without currency suffix
"""

TEXT_TO_CURRENCY = {
    'EUROS': 'EUR',
    'DOLARES USA': 'USD',
    'LIBRAS ESTERLINAS': 'GBP',
    'PESO MEJICANO': 'MXN'
}

CANCELED_SUB_ACCOUNT_MARKER = 'DADO DE BAJA'

def has_cuentas_table(resp_text: str) -> bool:
    cuentas_table_title = extract.re_first_or_blank(
        r'(?si)<h2>\s*<span>Cuentas</span>\s*</h2>',
        resp_text
    )
    return bool(cuentas_table_title)


def get_companies_parsed(resp_text: str, current_url: str) -> List[Company]:
    """
    <a class="link_empresa" href="empresas+cambio_empresa?ext-solapa=cuentas&amp;ext-subsolapa=posicion_global&amp
    ;empresa=50585234">ZEMSANIA S.L.</a>
    """

    # first relative url, second title
    companies_tuples = re.findall('<a class="link_empresa"[^>]+href="(.*?)">(.*?)</a>', resp_text)

    companies = [Company(url=urljoin(current_url, html.unescape(t[0])), title=html.unescape(t[1]))
                 for t in companies_tuples]

    # one contract - another parsing func
    if not companies:
        company_title = extract.re_first_or_blank(r'<div\s*class="empresa_selected">(.*?)</div', resp_text)
        companies = [Company(title=company_title, url=current_url)]

    return companies


def get_accounts_parsed(resp_text: str) -> List[AccountParsed]:
    """
    bank id 0128?

    extract only from position global
    CUENTAS CORRIENTES
    PRÉSTAMOS Y CRÉDITOS
    """
    accounts_parsed = []

    forms_htmls = re.findall(
        r'(?si)<form.*?action="empresas\+cuentas\+credito_movimientos2">(.*?)'
        r'<form method="post".*?action="empresas\+cuentas\+credito_retenciones">',
        resp_text
    )

    """
    <span style="display: none;" id="iban_1_0"><button type="submit" class="for_botonenlace_02"
    id="btnCuentaCVI21" name="btnCuentaCVI21"
    title="No existen datos para esta tabla">ES2301287611830100001666</button>
    """

    for form_html in forms_htmls:

        # Use '<input type="hidden" value="&nbsp;PTA">\s*'
        # to extract currency like it displayed at the web page
        # bcs there are values in euros for all accounts too

        try:
            extracted = re.findall(
                r'<span style="display:\s*none" id="iban.*?"><button type="submit" class="for_botonenlace_02" '
                r'id=".*?" name="btnCuenta(.*?)\d+" title="No existen datos para esta tabla">(.*?)</button>',
                form_html
            )[0]  # type: Tuple[str, str]
            account_type_sign, account_no = extracted
        # Neither debit nor credit account
        # Possible CRÉDITOS MULTIDIVISA
        # Can't extract here
        except (ValueError, IndexError):
            continue

        # balance for debit accs (only if there are no credit accs on the page)
        balance_debit_disponible = extract.re_first_or_blank(
            r'(?si)<td class="numero" headers="cuentacorrienteSaldosDisponibles">.*?'
            r'<input type="hidden" value="&nbsp;PTA">\s*'
            r'<input.*?value="(.*?)"',
            form_html
        )

        balance_disponible = extract.re_first_or_blank(
            r'(?si)<td class="numero" headers="prestamosSaldoDisponible">.*?'
            r'<input type="hidden" value="&nbsp;PTA">\s*'
            r'<input.*?value="(.*?)"',
            form_html
        )

        # balance for credit accs ('- EUR' -- debit acc)
        balance_dispuesto = extract.re_first_or_blank(
            r'(?si)<td class="numero" headers="prestamosSaldoDispuesto">.*?'
            r'<input type="hidden" value="&nbsp;PTA">\s*'
            r'<input.*?value="(.*?)"',
            form_html
        )

        is_credit_acc = balance_dispuesto and ('- ' not in balance_dispuesto)

        account_type = ACCOUNT_TYPE_CREDIT if is_credit_acc else ACCOUNT_TYPE_DEBIT
        balance_to_process = (balance_dispuesto if account_type == ACCOUNT_TYPE_CREDIT else
                              balance_debit_disponible or balance_disponible)

        balance_str_w_currency = balance_to_process.replace('\xa0', ' ')  # '14.162,49 EUR', '0 EUR'
        currency = balance_str_w_currency.split()[-1]
        assert len(currency) == 3
        balance_str_wo_currency = balance_str_w_currency.split(' ')[0].strip()
        if balance_str_wo_currency == '-':
            balance = 0.0
        else:
            balance = convert.to_float(balance_str_wo_currency)

        account_parsed = {
            'account_no': account_no,
            'financial_entity_account_id': account_no[-20:12] + account_no[-9:],
            'account_type': account_type,
            'balance': balance,
            'currency': currency
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_accounts_multicurrency_parsed(resp_text: str) -> List[Dict[str, AccountParsed]]:
    # list of account_parsed_multicurrency where
    # account_parsed_multicurrency is dict with currency as key and subaccount as val
    accounts_parsed_multicurrency = []  # type: List[Dict[str, AccountParsed]]

    table_multicurrency_accounts = extract.re_first_or_blank(
        '(?si)<table[^>]+summary="Se muestran los créditos multidivisa".*?</table>',
        resp_text
    )

    # Some rows contain new account definition, but then several rows contain
    # multicurrency subaccounts details
    rows = re.findall('(?si)<tr.*?>(.*?)</tr>', table_multicurrency_accounts)

    account_type = ACCOUNT_TYPE_CREDIT
    # dict with currency as key and subaccount as val
    account_parsed_multicurrency = {}  # type: Dict[str, AccountParsed]
    account_no_parent = ''
    fin_ent_account_id_parent = ''
    for row in rows:

        # First row should be with account type, let's check the value additionally
        if 'MULTIDIVISA</th>' in row:
            if 'CRÉDITOS MULTIDIVISA' in row:
                account_type = ACCOUNT_TYPE_CREDIT
            else:
                account_type = ACCOUNT_TYPE_DEBIT
            continue

        # Basic account information
        if '<form' in row:
            # Extract basic information for a new account
            account_no_parent = extract.re_first_or_blank(
                r'(?si)>MULTIDIVISA</span><span\s+id="iban[^"]*"[^>]*>(.*?)</span>',
                row
            )
            fin_ent_account_id_parent = account_no_parent[-20:12] + account_no_parent[-9:]

            # Add previous account_parsed_multicurrency if exists
            if account_parsed_multicurrency:
                accounts_parsed_multicurrency.append(account_parsed_multicurrency)
                account_parsed_multicurrency = {}

            continue

        # Extract subaccount information
        balance_str_w_currency = extract.re_first_or_blank(
            # 0,00 USD
            # -141.907,35 EUR
            '<input id="divisas" type="hidden" value="(.*?)">',
            row
        ).replace('\xa0', ' ').strip()

        balance_str, currency = balance_str_w_currency.split(' ')
        assert len(currency) == 3

        balance = convert.to_float(balance_str)

        subaccount_parsed = {
            'account_no': account_no_parent,  # No currency info in account no
            'financial_entity_account_id': fin_ent_account_id_parent + currency,
            'account_type': account_type,
            'balance': balance,
            'currency': currency,
            'fin_ent_account_id_parent': fin_ent_account_id_parent  # to use for movements extraction
        }

        account_parsed_multicurrency[currency] = subaccount_parsed

    # Add last account_parsed_multicurrency
    accounts_parsed_multicurrency.append(account_parsed_multicurrency)

    return accounts_parsed_multicurrency


# UNUSED NOW
def get_movements_parsed_from_excel_resp(resp_text: str) -> List[MovementParsed]:
    movements_parsed = []  # type: List[MovementParsed]
    rows = re.findall('(?si)<tr>.*?</tr>', resp_text)

    for row in rows:
        columns = re.findall('(?si)<td[^>]*>(.*?)</td>', row)

        if len(columns) < 5:
            # Reserved value, not used now
            # if 'Saldo total' in columns[1]:
            #     account_balance_real =  convert.to_float(columns[2])
            #     break
            continue

        operation_date = columns[0]  # 30/01/2017
        value_date = columns[1]
        description = columns[2]

        # not debit/credit acc - another excel, other columns
        if not all('/' in dt for dt in [operation_date, value_date]):
            continue

        if 'SALDO INICIAL' in description:
            continue

        amount = convert.to_float(columns[3])
        temp_balance = convert.to_float(columns[4])

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed.append(movement_parsed)

    return movements_parsed


# UNUSED NOW
def get_movements_parsed_from_excel_resp_multicurrency(
        resp_text: str,
        fin_ent_account_id: str,
        logger: ScrapeLogger) -> Dict[str, List[MovementParsed]]:
    """Need to calculate temp_balance because this source doesn't contain it"""
    # dict where key is currency
    movements_parsed_multicurrency = defaultdict(list)  # type: Dict[str, List[MovementParsed]]

    rows = re.findall('(?si)<tr.*?</tr>', resp_text)
    current_currency = ''
    temp_balance = 0.0
    for row in rows:
        columns = re.findall('(?si)<td[^>]*>(.*?)</td>', row)

        if not columns:
            continue

        # Check final temp_balance
        if len(columns) == 3:
            if 'Saldo total' in columns[1]:
                temp_balance_final = convert.to_float(columns[2])
                if (movements_parsed_multicurrency[current_currency]
                        and temp_balance_final
                        != movements_parsed_multicurrency[current_currency][-1]['temp_balance']):
                    logger.error("{}: Can't calculate correct balance: extracted {} != calculated {}".format(
                        fin_ent_account_id,
                        temp_balance_final,
                        movements_parsed_multicurrency[current_currency][-1]
                    ))
                    return {}
                continue

        if len(columns) < 4:
            # Detect currency (related to subaccount)
            for currency_text, currency in TEXT_TO_CURRENCY.items():
                if currency_text in columns[0]:
                    current_currency = currency
                    break
            continue

        operation_date = columns[0]  # 30/01/2017
        value_date = columns[1]
        description = columns[2]
        amount = convert.to_float(columns[3])

        if 'SALDO INICIAL' in description:
            temp_balance = amount
            continue

        # not debit/credit acc - another excel, other columns
        if not all('/' in dt for dt in [operation_date, value_date]):
            continue

        temp_balance = round(temp_balance + amount, 2)
        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance
        }
        # ascending ordering
        movements_parsed_multicurrency[current_currency].append(movement_parsed)

    return movements_parsed_multicurrency


def _reorder_today_movements(movements_parsed: List[MovementParsed]) -> List[MovementParsed]:
    """Allows to handle different movements' ordering from the website:
    - ordering of movements < today is ASC
    - ordering of movements >= today is DESC

    :returns movements_parsed_asc_all
    """

    # use local time
    today_dt = datetime.datetime.now().date()
    dt_fmt = project_settings.SCRAPER_DATE_FMT

    movements_parsed_asc = []  # type: List[MovementParsed]
    movements_parsed_desc = []  # type: List[MovementParsed]

    for mov in movements_parsed:
        operation_date_dt = datetime.datetime.strptime(mov['operation_date'], dt_fmt).date()
        if operation_date_dt < today_dt:
            movements_parsed_asc.append(mov)
        else:
            movements_parsed_desc.append(mov)

    movements_parsed_asc_all = movements_parsed_asc + list(reversed(movements_parsed_desc))

    # Re-calc balances

    movements_parsed_asc_all_recalc = []  # type: List[MovementParsed]
    temp_bal = None  # type: Optional[float]
    for mov in movements_parsed_asc_all:
        operation_date_dt = datetime.datetime.strptime(mov['operation_date'], dt_fmt).date()
        mov_upd = mov.copy()
        if temp_bal is None:
            # First set of temp_bal is different for
            # - if it's a today movement (use temp_bal of the last mov)
            # - if it's a movement of previous date
            if operation_date_dt < today_dt:
                temp_bal = mov['temp_balance']
            else:
                temp_bal = movements_parsed_asc_all[-1]['temp_balance']
        else:
            temp_bal = round(temp_bal + mov['amount'], 2)
        mov_upd['temp_balance'] = temp_bal
        movements_parsed_asc_all_recalc.append(mov_upd)

    return movements_parsed_asc_all_recalc


def get_movements_parsed_from_html_resp(resp_text: str, include_link_data: bool) -> List[MovementParsed]:
    movements_parsed = []  # type: List[MovementParsed]

    rows = re.findall('(?si)<td class="fecha" headers="fContable">.*?</td>\n', resp_text)

    for row in rows:

        # <td class="fecha" headers="fContable">03/12/18</td><td class="fecha" headers="fValor">03/12/18</td>
        # <td class="texto" headers="descripcion"><A href="#" class="cttxtinforsub"
        # onclick="enviaDatos(&quot;49&quot;,&quot;556416&quot;,&quot;20181203&quot;,&quot;20181203&quot;,
        # &quot;01287712500001871&quot;,&quot;/www/es-es/cgi&quot;);return false;">ORDEN DE COBRO EUR N.0335472</A></td>
        # <td class="numero" headers="importe">150.000,00 H</td><td class="numero" headers="saldo">-158.729,04</td><td
        # class="fecha" headers="detalle">-</td>
        columns = re.findall('(?si)<td[^>]*>(.*?)</td>', row)

        if len(columns) < 5:
            # Reserved value, not used now
            # if 'Saldo total' in columns[1]:
            #     account_balance_real =  convert.to_float(columns[2])
            #     break
            continue

        description = columns[2]
        if 'SALDO INICIAL' in description:
            continue

        # not debit/credit acc
        if not all('/' in dt for dt in [columns[0], columns[1]]):
            continue

        # TODO VB: very similar to ...from_html_resp_multicurrency
        #  try to make generic func

        operation_date = datetime.datetime.strptime(columns[0], '%d/%m/%y').strftime('%d/%m/%Y')  # 30/01/2017
        value_date = datetime.datetime.strptime(columns[1], '%d/%m/%y').strftime('%d/%m/%Y')  # 30/01/2017
        amount = convert.to_float(columns[3])
        if columns[3][-1] == "D":
            amount = -amount

        temp_balance = convert.to_float(columns[4])

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance,
            'may_have_receipt': False,
            'receipt_params': ""
        }
        # Bank returns movement description in two ways depending on if movement has receipt or not:
        # Movement with receipt:
        # <td><A href="#" class="cttxtinforsub" onclick="enviaDatos(&quot;49&quot;,&quot;834264&quot;
        # ,&quot;20181203&quot;,&quot;20181203&quot;,&quot;01280073550025525&quot;,&quot;/www/es-es/cgi&quot;);
        # return false;">
        # TRANSFERENCIA / : 09038</A></td>
        # Movement without receipt:
        # <td id="columna3" class="texto" colspan="2">LIQUIDACION CTA.CREDITO</td>
        receipt_data = re.findall(
            r'(?si)<A href="#" class="cttxtinforsub" onclick="\w+\(&quot;(.*)&quot;\);return false;">(.*)</A>',
            columns[2]
        )

        if receipt_data:
            movement_parsed['description'] = receipt_data[0][1]
            movement_parsed['may_have_receipt'] = True

            # Only parse link_data parameters when PDFs from movements download is activated
            if include_link_data:

                receipt_params_list = [param for param in receipt_data[0][0].split("&quot;") if param != ',']

                if len(receipt_params_list) > 4:
                    movement_parsed['receipt_params'] = ReceiptReqParams(
                        semana=receipt_params_list[0],
                        envio=receipt_params_list[1],
                        cuenta=receipt_params_list[4],
                        fecha=receipt_params_list[2],
                        fecha_valor=receipt_params_list[3]
                    )
                else:
                    movement_parsed['unhandled_receipt_params'] = receipt_data

        movements_parsed.append(movement_parsed)

    return movements_parsed


def get_movements_parsed_from_html_resp_multicurrency(
        resp_text: str,
        fin_ent_account_id: str,
        logger: ScrapeLogger,
        include_link_data_dict: Dict[str, bool]) -> Dict[str, List[MovementParsed]]:
    """Need to calculate temp_balance because this source doesn't contain it"""
    # dict where key is currency
    movements_parsed_multicurrency = defaultdict(list)  # type: Dict[str, List[MovementParsed]]

    re1 = '(<td id="columna1" class="fecha">.*?</td>)\n'
    re2 = '<td id="columna2" class="texto total1">Saldo</td><td [^>]*>([^<]*)'
    re3 = r'>TRAMO EN \s?([^<]*)'  # sub-account
    re4 = r'>(DISPOSICION EN \s?[^<]*)'  # complementary sub-account (should skip)
    rows = re.findall('|'.join('(?si){}'.format(x) for x in (re1, re2, re3, re4)), resp_text)

    current_currency = ''
    temp_balance = 0.0
    must_skip_subaccount = False

    for row in rows:

        # Get the movement data from row[0]
        # <td id="columna1" class="fecha">03/12/18</td><td id="columna2" class="fecha">03/12/18</td><td id="columna3"
        # class="texto" colspan="2">
        # <A href="#" class="cttxtinforsub" onclick="enviaDatos(&quot;49&quot;,&quot;834264&quot;,&quot;20181203&quot;,
        # &quot;20181203&quot;,&quot;01280073550025525&quot;,&quot;/www/es-es/cgi&quot;);return false;">
        # TRANSFERENCIA / : 09038</A></td><td id="columna4" class="numero">17.334,39 D</td>
        cells = re.findall('(?si)<td[^>]*>(.*?)</td>', row[0])

        # New complementary sub-account
        if row[3]:
            must_skip_subaccount = True
            # Internal sub-account for the same currency,
            # see dev/acc_multicurr__samecurr...png
            logger.info(
                "{}: complementary sub-account detected: '{}'. Skip".format(
                    fin_ent_account_id,
                    row[3],
                )
            )
            continue

        # New sub-account, get currency from row[2]
        # <span class="par_mdbold_01">TRAMO EN  DOLARES USA</span>
        if row[2]:
            # Detect currency (related to subaccount)
            must_skip_subaccount = False
            # <span class ="par_mdbold_01">TRAMO EN  EUROS - DADO DE BAJA POR REDENOMINACION</span>
            if CANCELED_SUB_ACCOUNT_MARKER in row[2]:
                must_skip_subaccount = True
                logger.info("{}: canceled sub-account with {} detected".format(
                    fin_ent_account_id, row[2]))
            else:
                for currency_text, currency in TEXT_TO_CURRENCY.items():
                    if currency_text in row[2]:
                        current_currency = currency
                        break
                logger.info("{}: sub-account with {} detected".format(
                    fin_ent_account_id, current_currency))
            continue

        # Skip sub-account, consider it as an internal one
        # with complementing movements to another
        # sub-account with the same currency
        if must_skip_subaccount:
            continue

        # Check final temp_balance
        # Get temp_balance from row[1]
        # <td id="columna1" colspan="2"></td><td id="columna2" class="texto total1">Saldo</td><td id="columna3"
        # class="numero total2">-119.474,79<td id="columna4" class="total2">&nbsp;</td></td>
        if row[1]:
            temp_balance_final = convert.to_float(row[1])
            if (movements_parsed_multicurrency[current_currency]
                    and temp_balance_final
                    != movements_parsed_multicurrency[current_currency][-1]['temp_balance']):
                logger.error("{}: can't calculate correct balance: extracted {} != calculated {}".format(
                    fin_ent_account_id,
                    temp_balance_final,
                    movements_parsed_multicurrency[current_currency][-1]
                ))
                return {}
            continue

        # Not a movement/saldo initial
        if len(cells) < 4:
            continue

        description = cells[2]
        if 'SALDO INICIAL' in description:
            # Get temp_balance
            must_skip_subaccount = False
            temp_balance = convert.to_float(cells[3])
            logger.info("{}: got temp balance for {} from 'saldo inicial' {}".format(
                fin_ent_account_id,
                current_currency,
                temp_balance
            ))
            continue

        # Not a debit/credit acc
        if not all('/' in dt for dt in [cells[0], cells[1]]):
            continue

        operation_date = datetime.datetime.strptime(cells[0], '%d/%m/%y').strftime('%d/%m/%Y')  # 30/01/2017
        value_date = datetime.datetime.strptime(cells[1], '%d/%m/%y').strftime('%d/%m/%Y')  # 30/01/2017

        amount = convert.to_float(cells[3])
        if cells[3][-1] == "D":
            amount = -amount

        temp_balance = round(temp_balance + amount, 2)
        logger.info("{}: {}: {}@{}: calculated temp balance {}".format(
            fin_ent_account_id,
            current_currency,
            amount,
            operation_date,
            temp_balance
        ))

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance,
            'may_have_receipt': False,
            'receipt_params': ""
        }
        # Bank returns movement description in two ways depending on if movement has receipt or not:
        # Movement with receipt:
        # <td><A href="#" class="cttxtinforsub" onclick="enviaDatos(&quot;49&quot;,&quot;834264&quot;
        # ,&quot;20181203&quot;,&quot;20181203&quot;,&quot;01280073550025525&quot;,&quot;/www/es-es/cgi&quot;);
        # return false;">
        # TRANSFERENCIA / : 09038</A></td>
        # Movement without receipt:
        # <td id="columna3" class="texto" colspan="2">LIQUIDACION CTA.CREDITO</td>
        receipt_data = re.findall(
            r'(?si)<a href="#" class="cttxtinforsub" onclick="\w+\(&quot;(.*)&quot;\);return false;">(.*)</A>',
            cells[2]
        )

        if receipt_data:
            movement_parsed['description'] = receipt_data[0][1]
            movement_parsed['may_have_receipt'] = True

            # Only parse link_data parameters when PDFs from movements download is activated
            if include_link_data_dict[current_currency]:
                receipt_params_list = [param for param in receipt_data[0][0].split("&quot;") if param != ',']

                if len(receipt_params_list) > 4:
                    movement_parsed['receipt_params'] = ReceiptReqParams(
                        semana=receipt_params_list[0],
                        envio=receipt_params_list[1],
                        cuenta=receipt_params_list[4],
                        fecha=receipt_params_list[2],
                        fecha_valor=receipt_params_list[3]
                    )
                else:
                    movement_parsed['unhandled_receipt_params'] = receipt_data

        # ascending ordering
        movements_parsed_multicurrency[current_currency].append(movement_parsed)

    return movements_parsed_multicurrency


def get_leasing_companies_from_html_resp(resp_text: str) -> List[dict]:
    results = re.findall(r'(?si)empresa=(\d*?)">(.*?)</a>', resp_text)

    companies_data = []
    for r in results:
        companies_data.append({"name": r[1], "id": r[0]})

    return companies_data


def get_leasing_contracts_from_html_resp(resp_text: str) -> List[LeasingContractParsed]:
    fields = re.findall(
        r'(?si)<a onclick="envia_datos2\(\'(\d*?)\',\'(.*?)\'\);.*?".*?pData\('
        r'"cta".*?"(.*?)".*?".*?pData\("Ldiv".*?"(.*?)", "([^"]*?)"',
        resp_text
    )

    leasing_contracts_parsed = []
    for f in fields:
        pending_repayment = convert.to_float(f[3])
        hashbase = 'BANKINTER{}{}'.format(
            f[0],  # office + company + contract
            f[2]  # contract_reference
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()

        contract_parsed = {
            'office': f[0][4:8],
            'contract_reference': f[2],
            'pending_repayment': pending_repayment,
            'keyvalue': keyvalue,
            'has_details': True,
            'post_data': f[0]
        }
        leasing_contracts_parsed.append(contract_parsed)

    return leasing_contracts_parsed


def get_leasing_contract_details_from_html_resp(
        resp_text: str,
        contract_parsed: LeasingContractParsed) -> Tuple[LeasingContractParsed, List[LeasingFeeParsed]]:
    fc = re.findall('(?si)<b>[^:]*: </b>(.*?)</TD>', resp_text)

    contract_parsed['contract_date'] = fc[1]
    contract_parsed['amount'] = convert.to_float(fc[2].split('\n', 1)[0])
    contract_parsed['taxes'] = convert.to_float(fc[3].split(' ', 1)[0])
    contract_parsed['initial_interest'] = convert.to_float(fc[4].split(' ', 1)[0])
    contract_parsed['fees_quantity'] = int(fc[5].split(' ', 1)[0])
    contract_parsed['current_interest'] = convert.to_float(fc[6].split(' ', 1)[0])
    contract_parsed['expiration_date'] = fc[7]
    contract_parsed['residual_value'] = convert.to_float(fc[8].split('\n', 1)[0])

    fields = re.findall(
        '(?si)<TR.*?>\n<TD class="ctTxBl" align="center">(.*?)</TD><TD class="ctTxBl" align="right">(.*?)'
        '</TD><TD class="ctTxBl" align="center">(.*?)</TD><TD class="ctTxBl" align="right">(.*?)'
        '</TD><TD class="ctTxBl" align="right">(.*?)</TD><TD class="ctTxBl" align="right">(.*?)'
        '</TD><TD class="ctTxBl" align="right">(.*?)</TD><TD class="ctTxBl" align="right">(.*?)'
        '</TD><TD class="ctTxBl" align="right">(.*?)</TD>\n</TR>',
        resp_text
    )

    leasing_fees_parsed = []
    for f in fields:
        amount = convert.to_float(f[3])
        hashbase = 'BANKINTER{}/{}-{}-{}-{}'.format(
            contract_parsed['contract_reference'],
            f[0],  # fee_number
            f[1],  # operational_date
            f[3],  # amount
            f[8]  # pending_repayment
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()

        fee_parsed = {
            'fee_reference': "{}/{}".format(contract_parsed['contract_reference'], f[0]),
            'fee_number': f[0],
            'operational_date': date_funcs.convert_to_ymd_type2(f[1]),
            'currency': f[2],
            'amount': convert.to_float(f[3]),
            'taxes_amount': convert.to_float(f[4]),
            'insurance_amount': 0.00,
            'fee_amount': convert.to_float(f[5]),
            'financial_repayment': convert.to_float(f[6]),
            'financial_performance': convert.to_float(f[7]),
            'pending_repayment': convert.to_float(f[8]),
            'state': '',
            'keyvalue': keyvalue,
            'statement_id': None,
            'contract_id': None,
        }
        leasing_fees_parsed.append(fee_parsed)

    return contract_parsed, leasing_fees_parsed


def get_transfers_companies_parsed(resp_text: str, current_url: str) -> List[Company]:
    """
    <a class="link_empresa" href="empresas+cambio_empresa?ext-solapa=cuentas&amp;ext-subsolapa=posicion_global&amp
    ;empresa=50585234">ZEMSANIA S.L.</a>
    """

    # first relative url, second title
    companies_tuples = re.findall('<a class="link_empresa"[^>]+href="(.*?)">(.*?)</a>', resp_text)

    companies = [Company(url=urljoin(current_url, html.unescape(t[0])), title=html.unescape(t[1]))
                 for t in companies_tuples]

    # one contract - another parsing func
    if not companies:
        company_title = extract.re_first_or_blank(r'<div\s*class="empresa_selected">(.*?)</div', resp_text)
        companies = [Company(title=company_title, url=current_url)]

    return companies


def get_transfers_accounts_parsed(resp_text: str) -> List[AccountParsed]:
    options = re.findall(
        r'(?si)<option value="(.*?)".*?;(.*?)&',
        resp_text
    )

    accounts_parsed = []  # type: List[AccountParsed]

    for option in options:
        account_parsed = {
            'account_no': option[1],
            'financial_entity_account_id': option[0],
            'balance': None
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed
