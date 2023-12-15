import re
import urllib.parse
from typing import Dict, List, Tuple, Union

import xlrd

from custom_libs import convert
from custom_libs import extract
from custom_libs import iban_builder
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, MovementParsed
from scrapers.kutxabank_scraper import meta
from scrapers.kutxabank_scraper.custom_types import ReqAttrs


def get_ice_session_id(resp_text: str) -> str:
    ice_session_id = extract.rex_first_or_blank(
        meta.Logged.Rex.ice_session_id,
        resp_text
    )
    return ice_session_id


def get_consultas_tab_idcl_and_id(resp_text: str) -> Tuple[str, str]:
    """Parses form[&#39;formMenuPasivo:_idcl&#39;].value=&#39;formMenuPasivo:j_id128:1:j_id130&#39;;return
    iceSubmit(form,this,event);" onfocus="setFocus(this.id);"><span class="iceOutTxt"
    id="formMenuPasivo:j_id128:1:j_id131">Consultas<

    to formMenuPasivo:j_id128:1:j_id130
    and formMenuPasivo:j_id128:1:j_id131
    """
    consultas_tab_idcl, consultas_tab_id = "", ""
    try:
        # 2 steps for type checker
        extracted = re.findall(
            r'form\[&#39;formMenuPasivo:_idcl&#39;].value[=]&#39;(formMenuPasivo[^&]+)&#39;[^>]+>'
            r'<span class="iceOutTxt" id="(formMenuPasivo:[^"]+)">Consultas<',
            resp_text
        )[0]  # type: Tuple[str, str]
        consultas_tab_idcl, consultas_tab_id = extracted
    except:
        pass  # will handle in caller
    return consultas_tab_idcl, consultas_tab_id


def parse_balance_str(bal_str: str) -> Dict[str, Union[str, float]]:
    currencies = {
        '€': 'EUR',
        'EUR': 'EUR',
        '$': 'USD',
        'USD': 'USD'
    }
    currency = None

    for curr_sign, curr_text in currencies.items():
        if curr_sign in bal_str:
            currency = curr_text

    bal_float = convert.to_float(bal_str)

    balance_parsed = {
        'balance': bal_float,
        'currency': currency or 'EUR'
    }  # type: Dict[str, Union[str, float]]

    return balance_parsed


def build_req_data_from_form_params(current_url: str, resp_text: str) -> ReqAttrs:
    """
    parse form params and build params for request
    look at the test below
    :return: {'data': {'activador': 'CAS',
                  'DATA_LOGON_PORTAL': '177C07A48AD22D9AD8A8FAB8CBE40A95|CAC762099F247B3D|0|false',
                  'idioma': 'ES',
                  'tipoacceso': ''},
         'url': 'https://www.kutxabank.es:443/NASApp/BesaideNet2/Gestor?PORTAL_CON_DCT='
                'SI&PRESTACION=login&FUNCION=directoportal&ACCION=control&destino=',
         'method': 'post'}
    """

    action_raw, params_ord = extract.build_req_params_from_form_html_patched(
        resp_text,
        form_name='frmLogin',
        is_ordered=True
    )
    action_url = urllib.parse.urljoin(current_url, action_raw) if action_raw else ''

    # handle hidden error: should send upper even if it is lower case at the page
    # or backend returns err
    # it occurs for -u 189397 -a 4030 - additional step (Selección de empresa)
    if 'idioma' in params_ord:
        params_ord['idioma'] = params_ord['idioma'].upper()

    req_vals = ReqAttrs(
        url=action_url,
        method='post',
        req_data=params_ord,
    )

    return req_vals


def build_req_data_from_refresh_url(current_url: str, resp_text: str) -> ReqAttrs:
    """
    '<html>
    <head>
        <meta http-equiv="refresh" content="0;
        url=/NASApp/BesaideNet2/pages/login/entradaBanca.iface?destino=resumen.home">
    </head>
    </html>'
    :return:
    """
    refresh_url_raw = extract.rex_first_or_blank(meta.Login.Rex.refresh_url, resp_text)
    refresh_url = urllib.parse.urljoin(current_url, refresh_url_raw) if refresh_url_raw else ''

    req_vals = ReqAttrs(
        url=refresh_url,
        method='get',
        req_data=None
    )

    return req_vals


def get_accounts_parsed(html_str):
    accounts_rows = meta.UserAccountPositionTab.Rex.account_row.findall(html_str)

    accounts_parsed = []

    for account_row in accounts_rows:
        account_number = extract.rex_first_or_blank(
            meta.UserAccountPositionTab.Rex.AccountRow.account_number,
            account_row
        )

        financial_entity_account_id = extract.rex_first_or_blank(
            meta.UserAccountPositionTab.Rex.AccountRow.account_id_from_account_number,
            account_number
        )

        account_no = iban_builder.build_iban('ES', account_number)

        balance_str = extract.rex_first_or_blank(
            meta.UserAccountPositionTab.Rex.AccountRow.account_balance,
            account_row
        )

        balance_parsed = parse_balance_str(balance_str)

        account_type = ACCOUNT_TYPE_CREDIT if balance_parsed['balance'] < 0 else ACCOUNT_TYPE_DEBIT

        account_parsed = {
            'account_no': account_no,
            'financial_entity_account_id': financial_entity_account_id,
            'balance': balance_parsed['balance'],
            'currency': balance_parsed['currency'],
            'account_type': account_type
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed_from_excel(resp_excel_bytes: bytes) -> List[MovementParsed]:
    # no movements - no excel, just html
    try:
        book = xlrd.open_workbook(file_contents=resp_excel_bytes)
    except xlrd.XLRDError:
        return []

    sheet = book.sheet_by_index(0)

    movements_parsed = []  # type: List[MovementParsed]
    for row_num in range(8, sheet.nrows):
        movement = {}
        cells = sheet.row_values(row_num)

        movement['operation_date'] = cells[0]  # '24/11/2017'
        movement['value_date'] = cells[2]
        movement['description'] = re.sub('\s+', ' ', cells[1].strip())  # remove redundant spaces
        movement['amount'] = cells[3]
        movement['temp_balance'] = cells[4]

        movements_parsed.append(movement)

    return movements_parsed
