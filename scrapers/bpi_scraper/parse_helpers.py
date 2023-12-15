import re
from typing import List

from custom_libs import convert
from custom_libs import extract
from project.custom_types import AccountParsed, MovementParsed, ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT
from .custom_types import AccountForMovs


def get_organization_title(resp_text: str) -> str:
    org_title = extract.form_param(resp_text, param_name='lblNome')
    return org_title


def get_org_param_for_movs(resp_text: str) -> str:
    """Parses 4_resp_movs_w_filter_newapi.html"""
    # only 1 company
    org_param = extract.re_first_or_blank(
        '<select[^>]+id="LT_BPINetEmpresas_wt37_block_wtContext_CW_NETEmp_Comum_wtEmpresasContas'
        '_block_LT_BPI_Patterns_wt9_block_wtAccountValue_wtcbListaEmpresas"[^>]*>\s*'
        '<option.*?value="(.*?)">',
        resp_text
    )  # '164903206'
    return org_param


def get_accounts_for_movs(resp_text: str) -> List[AccountForMovs]:
    """Parses 4_resp_movs_w_filter_newapi.html for movement filtering"""
    accs_select_el = extract.re_first_or_blank(
        '(?si)<select[^>]+id="LT_BPINetEmpresas_wt37_block_wtContext_CW_NETEmp_Comum_wtEmpresasContas'
        '_block_LT_BPI_Patterns_wt\d_block_wtAccountValue_wtcbListaContas"'
        '.*?</select>',
        resp_text
    )
    accs_tuples = re.findall(r'(?si)<option[^>]+value="(.*?)"\s*>(.*?)</option>', accs_select_el)
    accounts_for_movs = [
        AccountForMovs(
            # 286972080'
            req_param=a[0],
            # '9-5707988.000.001 - Conta 9-5707988.000.001'
            title=a[1],
        ) for a in accs_tuples
    ]
    return accounts_for_movs


def get_eventtarget_param__filter(resp_text: str) -> str:
    """Parses
    name="LT_BPINetEmpresas_wt37$block$wtMainContent$CW_Contas_Empresas_wtMovimentos$block$WebPatterns_wt154$block$wtContent$LT_BPI_Patterns_wt64$block$wtActionsRight$wtFilterBtn2" value="Filter"
    """
    resp_text_clean = resp_text.replace('\\', '')  # handle js escapes, need for multi-account accesses
    eventtarget_param = extract.re_first_or_blank(
        r'name="([^"]+)"\s+value="Filtrar"',
        resp_text_clean
    ) or extract.re_first_or_blank(
        r'name="([^"]+)"\s+value="Filter"',
        resp_text_clean
    )
    return eventtarget_param


def get_ajax_param__filter(resp_text: str) -> str:
    """Parses
    value="Filter" id="LT_BPINetEmpresas_wt37_block_wtMainContent_CW_Contas_Empresas_wtMovimentos_block_WebPatterns_wt154_block_wtContent_LT_BPI_Patterns_wt64_block_wtActionsRight_wtFilterBtn2"
    """
    resp_text_clean = resp_text.replace('\\', '')  # handle js escapes, need for multi-account accesses
    ajax_param = extract.re_first_or_blank(
        r'value="Filtrar"\s+id="([^"]+)"',
        resp_text_clean
    ) or extract.re_first_or_blank(
        r'value="Filter"\s+id="([^"]+)"',
        resp_text_clean
    )
    return ajax_param


def get_eventtarget_param__seemore(resp_text: str) -> str:
    """Parses
    name="LT_BPINetEmpresas_wt37$block$wtMainContent$CW_Contas_Empresas_wtMovimentos$block$WebPatterns_wt154$block$wtContent$LT_BPI_Patterns_wt64$block$wtActionsRight$wtFilterBtn2" value="Filter"
    """
    resp_text_clean = resp_text.replace('\\', '')
    eventtarget_param = extract.re_first_or_blank(
        r'name="([^"]+)"\s+value="Ver Mais"',
        resp_text_clean
    ) or extract.re_first_or_blank(
        r'name="([^"]+)"\s+value="See More"',
        resp_text_clean
    )
    # eventtarget_param_old = ('LT_BPINetEmpresas_wt37$block$wtMainContent$CW_Contas_Empresas_wtMovimentos$block'
    #                          '$LT_BPI_Patterns_wt49$block$wtActionsRight$wtButtonVerMais')
    return eventtarget_param


def get_ajax_param__seemore(resp_text: str) -> str:
    """Parses
    value="Filter" id="LT_BPINetEmpresas_wt37_block_wtMainContent_CW_Contas_Empresas_wtMovimentos_block_WebPatterns_wt154_block_wtContent_LT_BPI_Patterns_wt64_block_wtActionsRight_wtFilterBtn2"
    """
    resp_text_clean = resp_text.replace('\\', '')
    ajax_param = extract.re_first_or_blank(
        'value="Ver Mais"[^>]id="(.*?)"',
        resp_text_clean
    ) or extract.re_first_or_blank(
        'value="See More"[^>]id="(.*?)"',
        resp_text_clean
    )
    # ajax_param_old = ('LT_BPINetEmpresas_wt37_block_wtMainContent_CW_Contas_Empresas_wtMovimentos'
    #                   '_block_LT_BPI_Patterns_wt119_block_wtActionsRight_wtButtonVerMais')
    return ajax_param


def get_selected_account_req_param(resp_text: str) -> str:
    """For validation
    Parses <option selected="selected" value="298561527">8-3504331.000.001</option>
    """
    account_req_param = extract.re_first_or_blank(
        '(?si)<option[^>]+selected="selected"[^>]+value="([^"]+)">',
        resp_text
    )
    return account_req_param


def get_accounts_parsed(resp_text: str) -> List[AccountParsed]:
    """
    Parses
    ...
    <tr>
    <td class="descricao" onClick="ModalDetalhe({Nuc: &quot;3504331&quot;, NumOp: &quot;3504331000002&quot;,
    Familia: &quot;0&quot;, SubFamilia: &quot;0&quot;, Produto: &quot;1&quot;)">
    DEP. ORDEM - 8-3504331.000.002</td>
    <td class="montante"></td>
    <td class="montante">1.156,33</td></tr>
    ...
    """
    accounts_parsed = []  # type: List[AccountParsed]
    # same for all accs?
    currency = extract.re_first_or_blank('<td class="moeda">([^<]+)<', resp_text)

    acc_htmls = re.findall('(?si)<td class="descricao" onClick="ModalDetalhe.*?</tr>', resp_text)
    for acc_html in acc_htmls:
        tds = re.findall('(?si)<td.*?</td>', acc_html)
        if len(tds) != 3:
            continue
        # '8-3504331.000.002'
        account_no = extract.re_first_or_blank(r'DEP. ORDEM.*?(\d-\d{7}[.]\d{3}[.]\d{3})', tds[0])
        fin_ent_account_id = extract.re_first_or_blank(r'\d{13}', tds[0])  # '3504331000002'
        balance = convert.to_float(extract.remove_tags(tds[2]))
        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
        account_parsed = {
            'account_no': account_no,
            'financial_entity_account_id': fin_ent_account_id,
            'balance': balance,
            'currency': currency,
            'account_type': account_type,
            'country_code': 'PRT'  # Portugal
        }
        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_osvstate_param(resp_text: str) -> str:
    """Parses ('input[name=__OSVSTATE]').val('..')"""
    osvstate_param = extract.re_first_or_blank(r"(?si)input\[name=__OSVSTATE\]'\).val\('(.*?)'", resp_text)
    return osvstate_param


def get_osvstate_param_pagination(resp_text: str) -> str:
    """Parses "__OSVSTATE":"..." """
    osvstate_param = extract.re_first_or_blank(r'"__OSVSTATE":\s*"(.*?)"', resp_text)
    return osvstate_param


def get_osvstate_param_selected_account(resp_text: str) -> str:
    osvstate_param = extract.re_first_or_blank(r'OsJSONUpdate\(\{"hidden":\{"__OSVSTATE":\s*"(.*?)"', resp_text)
    return osvstate_param


def get_viewstategenerator_param(resp_text: str) -> str:
    viewstategenerator_param = extract.form_param(resp_text, '__VIEWSTATEGENERATOR')
    return viewstategenerator_param


def get_movements_parsed(resp_text: str) -> List[MovementParsed]:
    """Parses 5.0_resp_movs_newapi.html"""
    movements_parsed_desc = []  # type: List[MovementParsed]

    trs = re.findall(r'(?si)<tr.*?<\\/tr>', resp_text)
    for tr in trs:
        tr_clean = tr.replace('\\t', '').replace('\\r', '').replace('\\n', '').replace('\\', '')
        tds = [extract.text_wo_scripts_and_tags(td) for td in re.findall(r'(?si)<td.*?</td>', tr_clean)]
        if len(tds) != 6:
            continue  # not a movement

        operation_date = tds[0].replace('-', '/')  # '07-05-2021' -> '07/05/2021'
        value_date = tds[1].replace('-', '/') or operation_date
        description = tds[2]
        amount = convert.to_float(extract.text_wo_scripts_and_tags(tds[4]))
        temp_balance = convert.to_float(tds[5])

        mov_parsed = {
            'value_date': value_date.replace('-', '/'),
            'operation_date': operation_date.replace('-', '/'),
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed_desc.append(mov_parsed)

    return movements_parsed_desc
