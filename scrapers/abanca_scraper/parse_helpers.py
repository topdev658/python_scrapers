import re
from typing import List, Tuple

import xlrd

from custom_libs import convert
from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import Response
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed
from scrapers.abanca_scraper.custom_types import Company


def get_view_state_param(resp_text: str) -> str:
    return extract.re_first_or_blank(
        r'(?si)id="javax.faces.ViewState"\s*value="(.*?)"',
        resp_text
    ).strip()


def check_no_accounts(resp_text: str) -> Tuple[bool, bool]:
    """Checks for explicit 'No accounts' sign
    Parses dev/20_resp_no_accs.html
    <tr class="standardTable_Row1"><td class="invisibleTable-column"><table id="formulario:dataOrdenacion:0:tablaCuentas" cellpadding="0" cellspacing="0" width="100%" class="resultPanel"><tbody><tr><td class="pgc-column-0"><div class="dr-pnl rich-panel dr-pnl boton-ocultar-ext-cock-tabla" id="formulario:dataOrdenacion:0:_idJsp439"><div class="dr-pnl-b rich-panel-body " id="formulario:dataOrdenacion:0:_idJsp439_body"><a id="formulario:dataOrdenacion:0:btnCAT_CTAS_PT" name="formulario:dataOrdenacion:0:btnCAT_CTAS_PT" href="#" onclick="CGCoreJs.ocultarFilas('formulario:dataOrdenacion:0:CAT_CTAS_PT','formulario:dataOrdenacion:0:btnCAT_CTAS_PT');" class="boton-ocultar-cock-a">-</a></div></div></td><td class="pgc-columntabla">
        <table id="formulario:dataOrdenacion:0:CAT_CTAS_PT" class="resultTable">
            <thead>
            <tr><th class="standardTable_Header izquierda">CUENTAS</th><th class="standardTable_Header">SALDO</th><th class="standardTable_Header">BLOQUEADO</th><th class="standardTable_Header">DISPONIBLE</th><th class="standardTable_Header">DIVISA</th><th class="standardTable_Header"></th></tr></thead>
            <tbody id="formulario:dataOrdenacion:0:CAT_CTAS_PT:tbody_element"></tbody>
            <tr><td colspan="6" class="standardTable_Footer">Usted no dispone de cuentas</td></tr></table>
    </td></tr>
    :returns (is_success, has_no_accounts)"""
    cuentas_table = extract.re_first_or_blank('(?si)CUENTAS</th>.*?</table>', resp_text)
    if not cuentas_table:
        return False, False
    has_no_accs = 'Usted no dispone de cuentas' in cuentas_table
    return True, has_no_accs


def check_no_accounts_pt(resp_text: str) -> Tuple[bool, bool]:
    """Checks for explicit 'No accounts' sign for ABANCA PORTUGAL
    <tr class="standardTable_Row1"><td class="invisibleTable-column"><table id="formulario:dataOrdenacion:0:tablaCuentas" cellpadding="0" cellspacing="0" width="100%" class="resultPanel"><tbody><tr><td class="pgc-column-0"><div class="dr-pnl rich-panel dr-pnl boton-ocultar-ext-cock-tabla" id="formulario:dataOrdenacion:0:_idJsp439"><div class="dr-pnl-b rich-panel-body " id="formulario:dataOrdenacion:0:_idJsp439_body"><a id="formulario:dataOrdenacion:0:btnCAT_CTAS_PT" name="formulario:dataOrdenacion:0:btnCAT_CTAS_PT" href="#" onclick="CGCoreJs.ocultarFilas('formulario:dataOrdenacion:0:CAT_CTAS_PT','formulario:dataOrdenacion:0:btnCAT_CTAS_PT');" class="boton-ocultar-cock-a">-</a></div></div></td><td class="pgc-columntabla">
        <table id="formulario:dataOrdenacion:0:CAT_CTAS_PT" class="resultTable">
            <thead>
            <tr><th class="standardTable_Header izquierda">CONTAS &#192; ORDEM</th><th class="standardTable_Header">SALDO</th><th class="standardTable_Header">BLOQUEADO</th><th class="standardTable_Header">DISPON&#205;VEL</th><th class="standardTable_Header">MOEDA</th><th class="standardTable_Header"></th></tr></thead>
            <tbody id="formulario:dataOrdenacion:0:CAT_CTAS_PT:tbody_element"></tbody>
            <tr><td colspan="6" class="standardTable_Footer">Você não tem contas</td></tr></table>
    </td></tr>
    :returns (is_success, has_no_accounts)"""
    cuentas_table = extract.re_first_or_blank('(?si)CONTAS &#192; ORDEM</th>.*?</table>', resp_text)
    if not cuentas_table:
        return False, False
    has_no_accs = 'n&#227;o tem contas' in cuentas_table
    return True, has_no_accs


def get_companies(resp_text: str) -> List[Company]:
    companies_html = extract.re_first_or_blank('(?si)formSeleccion.*?</form>', resp_text)
    companies = [
        Company(idcl_param=res[0], title=res[1].strip(), idx=ix)
        for ix, res in
        enumerate(re.findall(
            r'(?si)<td class="padding-10 td_50 izquierda">\s*'
            r'<a.*?id="(formSeleccion:data_lstContratosCliEsp:.*?)">(.*?)</a>', companies_html))
    ]
    return companies


def get_idcc_param(resp_text: str) -> str:
    return extract.re_first_or_blank(
        '(?si)name="formulario:idcc" value="(.*?)"',
        resp_text
    ).strip()


def get_flow_execution_key(resp_url: str) -> str:
    return extract.re_first_or_blank(
        'flowExecutionKey=(.*)',
        resp_url
    ).strip()


def get_excel_param(resp_text: str) -> str:
    """Parses
    <td><a href="#" id="formAux:_idJsp610" name="formAux:_idJsp610" onclick="A4J.AJAX.Submit('_viewRoot','formAux',
    event,
    {'actionUrl':'/BEPRJ001/jsp/BEPR_movimientos_LST.faces?javax.portlet.faces.DirectLink=true',
    'parameters':{'formAux:_idJsp610':'formAux:_idJsp610'} } );return false;">
    <img src="/BEPRJ998/images/ico-excel.png" alt="Exportar a xls" title="Exportar a xls"></a></td> -> ABANCA ES
    or <img src="/BEPRJ998/images/ico-excel.png" alt="Exportar para xls" title="Exportar para xls" /></a> -> ABANCA PT
    """
    # Top button 'Export to XLS'
    # It sends requests different comparing to bottom button
    excel_param = extract.re_first_or_blank(
        """'parameters':{'([^']+)':[^>]+><img src="[^"]+" alt="Exportar .*a xls""",
        resp_text
    )
    return excel_param


def get_date_separator(resp_text: str) -> str:
    """Different accesses have different (!) separators for dates: '-' or '/'"""
    return extract.re_first_or_blank(
        r"validateDate[^;]+dd([/-])mm",
        resp_text
    )


def _get_accounts_parsed_from_table(
        table_html: str,
        account_type,
        iban_country_code: str) -> List[AccountParsed]:
    accounts_htmls = []  # type: List[str]
    accounts_htmls_raw = re.findall('(?si)<tr.*?</tr>', table_html)
    if accounts_htmls_raw:
        # drop first - it's thead,  drop last - it's Total
        accounts_htmls = accounts_htmls_raw[1:-1]

    accounts_parsed = []  # type: List[AccountParsed]
    for account_html in accounts_htmls:
        account_no = extract.re_first_or_blank(
            iban_country_code + r'\d+',
            extract.remove_tags(
                extract.re_first_or_blank(
                    '(?si)<td class="pglobal-column-1">(.*?)</td>',
                    account_html
                )
            ).replace('/', '').replace(' ', '').strip()
        )  # 'ES3620801208263040000102' or 'PT50017030190304001606514'

        if not account_no:
            continue  # not an account, skip 'Total' subsum

        balance = convert.to_float(extract.remove_tags(extract.re_first_or_blank(
            '(?si)<td class="pglobal-column-2">(.*?)</td>',
            account_html
        )))

        currency = extract.remove_tags(extract.re_first_or_blank(
            '(?si)<td class="pglobal-column-8">(.*?)</td>',
            account_html
        ))

        account_parsed = {
            'account_no': account_no,
            'balance': balance,
            'currency': currency,
            'account_type': account_type
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_account_idcl_param(resp_text: str, account_no: str) -> Tuple[bool, str]:
    """
    :param resp_text: response text
    :param account_no: without spaces
    """

    # (idcl_param, iban)
    all_accounts_tuples = [
        (idcl_param, extract.remove_tags(text_raw).replace(' ', ''))
        for _, idcl_param, text_raw in
        re.findall(r'(?si)<td class="pglobal-column-1">\s*(<script.*?</script>\s*)?<a.*?id="(.*?)".*?>(.*?)</td>',
                   resp_text)
    ]

    for acc_tuple in all_accounts_tuples:
        if account_no in acc_tuple[1]:
            return True, acc_tuple[0]
    return False, ''


def get_accounts_parsed(resp_text: str, iban_country_code: str) -> Tuple[bool, List[AccountParsed]]:
    """
    extract cuentas
    + extract creditos
    + extract depositios
    also, validate by prestamos if there are no current accounts
    """

    accounts_parsed = []  # type: List[AccountParsed]

    # DEBIT
    cuentas_table_html = extract.re_first_or_blank(
        '(?si)<table id="formulario:tablaCuentas".*?<table id="formulario:CAT_CTAS_PT".*?>(.*?)</table>',
        resp_text
    )

    accounts_parsed += _get_accounts_parsed_from_table(cuentas_table_html, ACCOUNT_TYPE_DEBIT, iban_country_code)

    # CREDIT
    creditos_table_html = extract.re_first_or_blank(
        '(?si)<table id="formulario:tablaCreditos".*?<table id="formulario:CAT_CREDITO_PT".*?>(.*?)</table>',
        resp_text
    )

    accounts_parsed += _get_accounts_parsed_from_table(creditos_table_html, ACCOUNT_TYPE_CREDIT, iban_country_code)

    # PRESTAMOS - only for layout validation purposes
    prestamos_table_html = extract.re_first_or_blank(
        '(?si)<table id="formulario:tablaPrestamos".*?<table id="formulario:CAT_PRESTAMO_PT".*?>(.*?)</table>',
        resp_text
    )
    # We're expecting accounts or at least 'prestamos' section
    # (accounts can't be parsed using _get_accounts_parsed_from_table)
    ok = bool(accounts_parsed) or bool(prestamos_table_html)
    return ok, accounts_parsed


def get_movements_parsed(resp_text: str) -> List[MovementParsed]:
    # will be '' if there are no movements
    mov_table_html_raw = extract.re_first_or_blank(
        r'(?si)<tbody id="formulario:dataMovimientos:tbody_element">(.*?)</table>\s*<div class="dr-dscr',
        resp_text
    )

    mov_table_html = re.sub('(?si)<table.*?</table>', '', mov_table_html_raw)

    movements_parsed = []  # type: List[MovementParsed]
    # no movements
    if 'No tiene movimientos en la cuenta para' in mov_table_html:
        return movements_parsed

    mov_htmls = re.findall('(?si)<tr.*?</tr>', mov_table_html)
    for mov_html in mov_htmls:
        # remove included tables - not used, but break parsing if not removed
        mov_datas = [extract.remove_tags(h).strip() for h in re.findall('(?si)<td.*?</td>', mov_html)]
        value_date = mov_datas[0].replace('-', '/')  # 31-12-2016 -> 31/12/2016
        operation_date = mov_datas[1].replace('-', '/')  # 31-12-2016 -> 31/12/2016
        description = mov_datas[3].split('\n')[0].strip()
        amount = convert.to_float(mov_datas[4])
        temp_balance = convert.to_float(mov_datas[5])

        mov_parsed = {
            'value_date': value_date,
            'operation_date': operation_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed.append(mov_parsed)

    return movements_parsed


def get_movements_parsed_from_excel(
        excel_resp: Response,
        account_iban: str) -> Tuple[List[MovementParsed], str]:
    """:returns (movs_parsed, err_reason)"""

    book = xlrd.open_workbook(file_contents=excel_resp.content)
    sheet = book.sheet_by_index(0)

    excel_account_no = sheet.row_values(1)[1]
    if excel_account_no not in account_iban:
        return [], 'Incorrect account IBAN in response with movements. Contains {} instead of {}'.format(
            excel_account_no,
            account_iban
        )

    movements_parsed = []  # type: List[MovementParsed]
    for row_num in range(4, sheet.nrows):
        cells = sheet.row_values(row_num)
        try:
            # Must use F.Contable (cells[1]) instead of F.Oper (cells[2])
            operation_date = date_funcs.get_date_using_td_days_since_epoch(int(cells[1]))
            value_date = date_funcs.get_date_using_td_days_since_epoch(int(cells[0]))
        # not a movement - additional rows in the end of the file
        except Exception as exc:
            continue

        # Handle different data formats
        description = re.sub(r'\s+', ' ', cells[4].strip())  # removes redundant spaces
        try:
            amount = float(re.sub('[^-0-9.]', '', cells[6]))  # fixes cases like "'-13.05"
        except TypeError:
            amount = float(cells[6])
        try:
            temp_balance = float(re.sub('[^-0-9.]', '', cells[7]))
        except TypeError:
            temp_balance = float(cells[7])

        movement = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance,
        }

        movements_parsed.append(movement)

    return movements_parsed, ''
