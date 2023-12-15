from datetime import datetime
import re
from typing import Dict, List, Tuple, Optional

import xlrd

from custom_libs import convert
from custom_libs import extract
from custom_libs import date_funcs
from custom_libs.myrequests import Response
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT, AccountParsed, MovementParsed
from scrapers._basic_scraper import movement_helpers


def get_several_companies_parsed(resp_text: str) -> List[dict]:
    """
    <td class="listaC" ><A class=lista href="javascript:enviar('[
    ST]KsXgZWU9Mcr9O+YsjtQXYk9qBb8eL+6vnAwnDn97b7s=',
    '[ST]ifxacNs4JvhwSnV7W0j6/R+XbTyjebHSBeDN2QxgMi+/deRn9KaWZ1kTqFaiwnjHPyny8tN0Y55LPVqL6Vwx1w
    ==', '[ST]dIan85YEYl24dtDD5kqkuQ==', '[ST]c1IQvHj+9RQSQgFjrJ2tLQ==' ,
    '[ST]rAM/VwVQvDidCLbVhCvASQ==' , '[ST]fDef6UMcVKRyp+SRf9WzQA==',
    '[LO]qXKBRBkiTcEeWFR4NrWuUA==',
    '[ST]XkyoMX...o5SfbhgQ=' ,'[ST]PsvzVIN1GmWMEO5Kr84FPw==', '[LO]iPMBOiqMposTLRUDkNeEXw==',
    '[LO]nGu8rAfEip0LT8XOmBceew==', '[ST]UQWQx/qnZuS8fGU7eXlvvg==','00000000002144851892' )"
    >00000000002144851892</A></td>
    <td class="listaI" >&nbsp;ALTUNA Y URIA, S.A.                               </td>
    <td class="listaC" >&nbsp;***0291**</td>
    """

    companies_htmls = re.findall('(?si)<tr id="TrColor".*?</tr>', resp_text)
    companies_parsed = []
    for company_html in companies_htmls:
        req_params_str = extract.re_first_or_blank(r'enviar\(.*?\)', company_html)
        req_params_separated = re.findall("'(.*?)'", req_params_str)
        company_title = extract.remove_tags(extract.re_first_or_blank(
            '<td class="listaI" >(.*?)</td>',
            company_html
        ))

        company_dict = {
            'req_params_list': req_params_separated,
            'title': company_title
        }

        companies_parsed.append(company_dict)

    return companies_parsed


def get_company_title_from_inicio_page(db_customer_name: str, resp_text: str) -> str:
    company_title = extract.re_first_or_blank(
        '(?si)<p class=titular><span>Titular:  </span>(.*?)</p>',
        resp_text
    )

    # sometimes get 'null' name
    if not company_title or company_title == 'null':
        company_title = db_customer_name

    return company_title


def parse_accounts_overview(resp_text: str) -> List[AccountParsed]:
    """
    <input type="hidden" name="clavePaginaVolver" value="BEL_FR_POS_GLOBAL_OPT_PORTAL">

    <input type="hidden" name="cuenta" value="30080152611751331420">
    <input type="hidden" name="descripcionCuenta" value="Altuna y Uria cc">
    <input type="hidden" name="clavePagina" value="">
    <INPUT type="hidden" name="primeraVez" value="1">
    <input type="hidden" name="campoPaginacion" value="lista">
    <input type="hidden" name="opcion" value="1">
    <input type="hidden" name="fechaDesde" value="0">
    <input type="hidden" name="fechaHasta" value="0">
    <input type="hidden" name="FechaDesde" value="0">
    <input type="hidden" name="FechaHasta" value="0">

    <input type="hidden" name="Nmovs" value="0">
    <input type="hidden" name="TRANCODE" value="32">
    <input type="hidden" name="paginaActual" value="0">
    <input type="hidden" name="tamanioPagina" value="0">
    <input type="hidden" name="campoPaginacion" value="0">
    <input type="hidden" name="CUENTA" value="30080152611751331420">
    <input type="hidden" name="descEstado" value="">
    <input type="hidden" name="ENTIDAD_I" value="3008">
    <input type="hidden" name="ACUERDO_I" value="1751331420">
    <INPUT type='hidden' name='clavePaginaEjecutar' value='TRANSF_DETALLE_SIMULACION'>
    <input type="hidden" name="DIVISA_COD" value="978">
    <input type="hidden" name="CUENTASEL" value="30080152611751331420978Altuna y Uria cc">
    """
    cuentas_html = extract.re_first_or_blank(
        '(?si)<div id="BODY_LISTA".*?<!--xxxxx TABLA POLIZA GLOBAL  xxxxxxxxxx -->',
        resp_text
    )

    accounts_parsed = []
    accounts_htmls = re.findall(
        r'(?si)<tr\s*>\s*<td class="totlistaC".*?<input type="hidden" name="CUENTASEL" value=".*?">',
        cuentas_html
    )

    for account_html in accounts_htmls:
        # replace internal and external spaces of iban data
        account_no = re.sub('[\t\n ]', '', extract.re_first_or_blank(
            r'(?si)<td class="totlistaC"\s*>(.*?)</td>',
            account_html
        ))

        account_title_raw = extract.re_first_or_blank(
            r'(?si)<td class="totlistaI"\s*>(.*?)</td>',
            account_html
        ).strip()

        account_title_raw_divided = account_title_raw.split('|')
        account_title = account_title_raw_divided[0].strip()
        account_currency_raw = account_title_raw_divided[1].strip()

        if 'USA' in account_currency_raw:
            account_currency = 'USD'
        else:
            account_currency = account_currency_raw.replace(' ', '').upper()[:3]

        account_balance_raw = extract.re_first_or_blank(
            r'(?si)<td class="totimplista"\s*>(.*?)</td>',
            account_html
        ).strip()

        if account_balance_raw == '-':
            account_balance_raw = '0'

        account_balance = convert.to_float(account_balance_raw)

        # [(name, value), ...]
        fields_tuples = re.findall(
            """(?si)<input.*?name=["'](.*?)['"].*?value=["'](.*?)['"]""",
            account_html
        )

        """
        {'primeraVez': '1', 'DIVISA_COD': '978', 'fechaDesde': '0', 'paginaActual': '0', 
        'cuenta': '30080065351156542225', 'TRANCODE': '32', 'CUENTASEL': 
        '30080065351156542225978Ptamo Murueta', 'ENTIDAD_I': '3008', 'campoPaginacion': '0', 
        'FechaDesde': '0', 'clavePaginaEjecutar': 'TRANSF_DETALLE_SIMULACION', 
        'descripcionCuenta': 'Ptamo Murueta', 'CUENTA': '30080065351156542225', 'descEstado': 
        'TODOS', 'ACUERDO_I': '1156542225', 'Nmovs': '50', 'tamanioPagina': '50', 'clavePagina': 
        'PAS_MOV_CUENTAS_POSGLOB', 'FechaHasta': '0', 'fechaHasta': '0', 'opcion': '1', 
        'clavePaginaVolver': 'BEL_FR_POS_GLOBAL_OPT_PORTAL'}
        """
        req_params_raw = {name: value for name, value in fields_tuples}

        # set necessary then req_params_raw in 01-01-2017 format
        # <input type="hidden" name="fechaDesde" value="0">  == 26-11-2016 -- ?
        # <input type="hidden" name="fechaHasta" value="0">  == 26-02-2017
        # <input type="hidden" name="FechaDesde" value="0">  == 26-01-2017
        # <input type="hidden" name="FechaHasta" value="0">  == 26-02-2017
        # reset to defaults
        req_params_raw['Nmovs'] = '50'
        req_params_raw['tamanioPagina'] = '50'
        req_params_raw['descEstado'] = 'TODOS'
        req_params_raw['clavePagina'] = 'PAS_MOV_CUENTAS_POSGLOB'

        action_url = extract.re_first_or_blank(  # relative url
            '(?si)href="(.*?)".*?Movimientos',
            account_html
        )

        account_parsed = {
            'account_no': account_no,
            'account_type': ACCOUNT_TYPE_DEBIT if account_balance >= 0 else ACCOUNT_TYPE_CREDIT,
            'title': account_title,
            'currency': account_currency,  # EUR
            'currency_raw': account_currency_raw,  # Euro
            'balance': account_balance,
            'action_url': action_url,
            'req_params_raw': req_params_raw  # set necessary dates then
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_acc_balance_from_movfiter_page(logger: ScrapeLogger,
                                       fin_ent_account_id: str,
                                       resp_text: str) -> Tuple[bool, float]:
    """
    Parses
    <INPUT type='hidden' name='clavePaginaSiguiente' value='PAS_MOV_CUENTAS'>
    <INPUT type='hidden' name='clavePaginaVolver' value='PAS_MOV_CUENTAS'>
    <INPUT type='hidden' name='cuenta' value= '31903118434972304226' >
    <INPUT type='hidden' name='DIVISA_COD' value= '978'>
    <INPUT type='hidden' name='DIVISA_NAME' value= 'Euro' >
    <INPUT type="hidden" name="DIVISA_DESC" value='EUR' >
    <INPUT type='hidden' name='descripcionCuenta' value= 'C/C EMPRESAS' >
    <INPUT type='hidden' name='SALDO_CONTABLE' value= '0.0' >
    <INPUT type='hidden' name='cuentaSel' value= '' >
    """
    balance = 0.0
    balance_str = extract.re_first_or_blank(
        r"(?si)<INPUT type='hidden' name='cuenta' value=\s*'{}' >.*?"
        r"<INPUT type='hidden' name='SALDO_CONTABLE'\s*value=\s*'(.*?)'".format(
            fin_ent_account_id[-20:]
        ),
        resp_text
    )
    if not balance_str:
        return False, balance

    try:
        balance = float(balance_str)
    except Exception as exc:
        logger.error(
            "{}: can't get balance from mov filter page. Parsing error for '{}': {}".format(
                fin_ent_account_id,
                balance_str,
                exc
            )
        )
        return False, balance
    return True, balance


# todo deprecated
def build_req_params_from_form_html(resp_text: str, form_name: str = '',
                                    form_id: str = '') -> Tuple[str, Dict[str, str]]:
    """
    <input type="hidden" name="PRF_CODE" value="[ST]9PNQ0KDOiR4dR3TLwWRopA==">
    """

    if form_name:
        form_html = extract.re_first_or_blank(
            '(?si)<form.*?name="{}".*?</form>'.format(form_name),
            resp_text
        )
    else:
        form_html = extract.re_first_or_blank(
            '(?si)<form.*?id="{}".*?</form>'.format(form_id),
            resp_text
        )

    action_url = extract.re_first_or_blank('action="(.*?)"', form_html)

    # [(name, value), ...]
    fields_tuples = re.findall(
        """(?si)<input.*?name=["'](.*?)['"].*?value=["'](.*?)['"]""",
        form_html
    )

    req_params = {name: value for name, value in fields_tuples}

    return action_url, req_params


def get_selcta_option_from_mov_filter_form(resp: Response, account_parsed: AccountParsed) -> Optional[str]:
    # <option value='3008015263248114612097803_11UTE Biofisica'>ES40 3008 0152 6324 8114 6120  |
    # UTE Biofisica | Euro </option>
    # [(selcta_option, selcta_text),...]

    fin_ent_acc_id = account_parsed['req_params_raw']['CUENTA']

    selcta_options = re.findall(
        "option value='(.*?)'",
        resp.text
    )

    for option_val in selcta_options:
        if fin_ent_acc_id in option_val:
            return option_val
    return None


def parse_movements_from_html(resp_text: str) -> List[MovementParsed]:
    """

    <tr >\n\t\t\t\t\t\t<td class="listaC" >07-02-2017</td>\n\t\t\t\t\t\t<td class="listaC"
    >07-02-2017</td>\n\t\t\t\t\t\t\n\t\t\t\t\t\t\t<td class="listaI" >RCBO.
    PRÃ‰STAMO1180881151</td>\n\t\t\t\t\t\t\n\t\t\t\t\t\t\t<td class="implistaN" >-555,
    32</td>\n\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t<td class="implista" >475,
    26</td>\n\t\t\t\t\t\t\t\n\t\t\t\t\t\t\n\t\t\t\t\t</tr>
    """
    mov_htmls = re.findall(r'(?si)<tr >\s*<td class="listaC".*?</tr>', resp_text)
    mov_form_action = extract.re_first_or_blank(r'(?si)<form name="FORM_RVIA_1" action="(.*?)"', resp_text)

    movements_parsed = []
    for mov_html in mov_htmls:
        fields = re.findall('(?si)<td.*?>(.*?)</td>', mov_html)
        movement_parsed = {
            'operation_date': fields[0].replace('-', '/'),
            'value_date': fields[1].replace('-', '/'),
            'description': extract.remove_tags(fields[2]),
            'amount': convert.to_float(fields[3]),
            'temp_balance': convert.to_float(fields[4])
        }

        if len(fields) > 5:
            movement_parsed['receipt_params'] = {}
            movement_parsed['receipt_params']['action_url'] = mov_form_action # extract.get_link_contains_text(fields[5], '', '')
            receipt_params = [f.replace("'", "") for f in re.findall("(?si)\'.*?\'", fields[5])]
            receipt_params_dict = {
                'ISUM_OLD_METHOD': 'post',
                'ISUM_ISFORM': 'true',
                'acuerdo': receipt_params[0][10:20],
                'Entidad': receipt_params[1],
                'fechaValor': datetime.strptime(receipt_params[2][:10], '%d-%m-%Y').strftime('%Y-%m-%d'),
                'fechaOperacion': datetime.strptime(receipt_params[3][:10], '%d-%m-%Y').strftime('%Y-%m-%d'),
                'importe': abs(convert.to_float(receipt_params[4])),
                'origenApunte': receipt_params[5],
                'clavePagina': 'BDP_PAS_GENERA_DOC',
                'acuerdoDocumento': receipt_params[6],
                'numeroSecuencialApunteDoc': receipt_params[7],
                'codigoDocumento': receipt_params[8],
                'numSecPDF': receipt_params[9],
                'validationToken': extract.form_param(resp_text, 'validationToken')
            }

            movement_parsed['receipt_params']['req_params'] = receipt_params_dict

        movements_parsed.append(movement_parsed)

    return movements_parsed


def parse_movements_from_resp_excel(resp_excel):
    book = xlrd.open_workbook(file_contents=resp_excel.raw.read())
    sheet = book.sheet_by_index(0)

    movements_parsed = []
    for row_num in range(6, sheet.nrows):
        movement = {}
        cells = sheet.row_values(row_num)

        movement['operation_date'] = cells[0].replace('.', '/')
        movement['value_date'] = cells[1].replace('.', '/')
        movement['description'] = re.sub(r'\s+', ' ', cells[2].strip())  # remove redundant spaces
        movement['amount'] = convert.to_float(cells[3])
        movement['temp_balance'] = convert.to_float(cells[4])

        movements_parsed.append(movement)

    return movements_parsed


def _is_asc_ordering_by_dates(movements_parsed: List[MovementParsed]) -> Optional[bool]:
    """True/False - ASC or DESC detected, None - Unknown (one date)"""
    if not movements_parsed:
        return True
    fst = date_funcs.get_date_from_str(movements_parsed[0]['operation_date'])
    lst = date_funcs.get_date_from_str(movements_parsed[-1]['operation_date'])
    if fst == lst:
        return None
    return fst < lst


def is_asc_ordering(movements_parsed: List[MovementParsed]) -> bool:
    is_asc_by_dates_opt = _is_asc_ordering_by_dates(movements_parsed)
    if is_asc_by_dates_opt is not None:
        return is_asc_by_dates_opt

    is_desc_opt = movement_helpers.is_desc_ordering_by_temp_balance(movements_parsed)
    if is_desc_opt is None:
        return True  # can't detect, consider as ASC == no re-order later
    return not is_desc_opt


def movements_parsed_order_asc(movements_parsed: List[MovementParsed]) -> List[MovementParsed]:
    """Sometimes website returns movements_parsed in DECS even if req arg = ASC
    This functions tries to detect the correct order and reorder in ASC if necessary
    """
    if is_asc_ordering(movements_parsed):
        return movements_parsed
    return movements_parsed[::-1]  # DESC -> ASC

