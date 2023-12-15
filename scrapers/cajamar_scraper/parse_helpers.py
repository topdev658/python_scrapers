import re
from typing import List
from typing import Tuple

from custom_libs import convert
from custom_libs import extract
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed

__version__ = '1.3.0'
__changelog__ = """
1.3.0 2023.09.19
get_accounts_parsed: modified regexp to get balances_str
1.2.0 2023.07.20
get_salt: modified regexp to get encrypted_salt
1.1.0
get_dt_param: use extract.unescape_html_from_json
"""


def get_salt(resp_text: str) -> str:
    # expect '111' or similar
    salt = extract.re_first_or_blank(
        r'(?si)cod_pass=[^"]+;\s*c=(\d+);',
        resp_text
    )
    return salt


def get_cap_param(resp_text: str) -> str:
    cap_param = extract.re_first_or_blank('"CAP","(.*)"', resp_text)
    return cap_param


def get_org_title(resp_text: str) -> str:
    org_title = extract.re_first_or_blank(
        r'<p class="infoUsuario"\s*>(.*?)</p>',
        resp_text
    ).strip()
    return org_title


def get_dt_param(resp_text: str) -> str:
    """
    Parses  30_resp_mov_filter.html
        [0, 'sNEQ_', {
        dt: 'z_seo',
        cu: '\x2FBE',
        uu: '\x2FBE\x2Fzkau',
        ru: '\x2Fplantillas\x2Fout_zk\x2FW_S_MOV_NCTA_v1.zul'
    },

    >>> get_dt_param(r"dt: 'z_gjY2d0wPC_02IiI\\x2DEHXA9A'")
    'z_gjY2d0wPC_02IiI-EHXA9A'
    """
    dt_param = extract.unescape_html_from_json(extract.re_first_or_blank(r"dt:\s*'(.*?)'", resp_text))
    return dt_param


def get_zkau_form_param(resp_text: str, param_name: str) -> str:
    # 'O_A_PETIC_EXTRACTO1614967762260-S_A_PETICANUL_EXTRACTO_v1\\xAC1614967762293'
    val_escaped = extract.re_first_or_blank(r'(?si)value=\\"([^"]+)\\" name=\\"{}\\"'.format(param_name), resp_text)
    # 'O_A_PETIC_EXTRACTO1614967762260-S_A_PETICANUL_EXTRACTO_v1¬1614967762293'
    val = val_escaped.encode('utf8').decode('unicode_escape')
    return val


def get_op_code(resp_text: str) -> str:
    return get_zkau_form_param(resp_text, 'OP_CODE')


def get_accounts_parsed(resp_text: str) -> Tuple[List[AccountParsed], str]:
    accounts_parsed = []  # type: List[AccountParsed]
    accs_data = extract.re_first_or_blank(
        r'(?si)zul[.]grid[.]Rows(.*?);\s*var pch=',  # skip header
        resp_text
    )

    # ['zul.wgt.Label','eL9Pu',{id:'MM_BD_SEL_CUENTASVISTA_RR[0].NCTA',
    # $onClick:true,value:'ES53 3105 2644 1827 2000 9763'},{},[]],
    # temp bal: 146.622,68 eur
    accounts_nos = re.findall(
        r"MM_BD_SEL_CUENTASVISTA_RR\[\d+][.]NCTA.*?value:'(.*?)'",  # ['ES53 3105 2644 1827 2000 9763']
        accs_data
    )

    # ['zul.wgt.Cell','eL9P40',{$onClick:true,domExtraAttrs:{'data-title':'Saldo disponible'
    #  },align:null,valign:null},{},[
    # ['zul.wgt.Label','eL9P50',{value:'146.622,68 eur'},{},[]]]],
    balances_str = re.findall(
        r"(?si)'data-title':'Saldo contable.*?value:'(.*?)'",  # ['146.622,68 eur']
        accs_data
    )
    if len(accounts_nos) != len(balances_str):
        err = "can't get accounts_parsed:  len(account_nos) != len(balances_str)"
        return [], err

    for (account_no, balance_str) in zip(accounts_nos, balances_str):
        account_no = account_no.replace(' ', '')
        balance = convert.to_float(balance_str)
        currency_raw = balance_str.split()[-1].upper()
        currency = convert.to_currency_code(currency_raw)

        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

        # No valid currency available here
        # get later from acc details
        account_parsed = {
            'account_no': account_no,
            'account_type': account_type,
            'balance': balance,
            'currency': currency
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed, ''


def get_movements_parsed(resp_text: str) -> List[MovementParsed]:
    """Parses 40_resp_movs.text"""

    movements_parsed_asc = []
    # ['nA3Qp5', ...]
    mov_ids = re.findall(r"',(.*?)',{id:'LISTA_MOV_row_\d+", resp_text)

    for mov_id in mov_ids:
        # one row
        # ['zul.grid.Row', 'nA3Qv', {id: 'LISTA_MOV_row_0', _index: 0}, {}, [
        #     ['zul.wgt.Cell', 'nA3Qw', {
        #         domExtraAttrs: {
        #             'data-title': 'Fecha'
        #         }, align: null, valign: null
        #     }, {}, [
        #         ['zul.wgt.Label', 'nA3Qx', {value: '30/09/2020'}, {}, []]]],
        #     ['zul.wgt.Cell', 'nA3Qy', {
        #         domExtraAttrs: {
        #             'data-title': 'F. valor'
        #         }, align: null, valign: null
        #     }, {}, [
        #         ['zul.wgt.Label', 'nA3Qz', {value: '30-09'}, {}, []]]],
        #     ['zul.wgt.Cell', 'nA3Q_0', {
        #         id: 'LISTA_MOV[0].CELDA', domExtraAttrs: {
        #             'data-title': 'Concepto'
        #         }, align: null, valign: null
        #     }, {}, [
        #         ['zul.wgt.Label', 'nA3Q00', {
        #             id: 'LISTA_MOV[0].TEXTO',
        #             value: 'COMISION MTO. ACTIVIDAD\n20200831202009300100000000000001000-    REF: J202058368'
        #         }, {}, []],
        #         ['zul.wgt.Toolbarbutton', 'nA3Q10', {
        #             id: 'LISTA_MOV[0].ENLACE',
        #             visible: false,
        #             $onClick: true,
        #             left: '0px',
        #             top: '0px',
        #             tabindex: 0,
        #             mode: 'default'
        #         }, {}, []]]],
        #     ['zul.wgt.Cell', 'nA3Q20', {
        #         domExtraAttrs: {
        #             'data-title': ''
        #         }, align: null, valign: null
        #     }, {}, [
        #         ['zul.wgt.Label', 'nA3Q30', {value: 'COMISION MTO. ACTIVIDAD\n20200831202009300100000000000001000-    REF: J202058368'}, {}, []]]],
        #     ['zul.wgt.Cell', 'nA3Q40', {
        #         domExtraAttrs: {
        #             'data-title': 'Importe'
        #         }, align: null, valign: null
        #     }, {}, [
        #         ['zul.wgt.Label', 'nA3Q50', {
        #             style: 'color:red',
        #             value: '-10,00'
        #         }, {}, []]]],
        #     ['zul.wgt.Cell', 'nA3Q60', {
        #         domExtraAttrs: {
        #             'data-title': 'Saldo'
        #         }, align: null, valign: null
        #     }, {}, [
        #         ['zul.wgt.Label', 'nA3Q70', {value: '42.723,25'}, {}, []]]],
        #     ['zul.wgt.Cell', 'nA3Q80', {
        #         domExtraAttrs: {
        #             'data-title': ''
        #         }, align: null, valign: null
        #     }, {}, [
        #         ['zul.wgt.Label', 'nA3Q90', {value: '30092020'}, {}, []]]],
        #     ['zul.wgt.Cell', 'nA3Qa0', {
        #         domExtraAttrs: {
        #             'data-title': ''
        #         }, align: null, valign: null
        #     }, {}, [
        #         ['zul.wgt.Label', 'nA3Qb0', {value: '03102020'}, {}, []]]],
        #     ['zul.wgt.Cell', 'nA3Qc0', {
        #         domExtraAttrs: {
        #             'data-title': ''
        #         }, align: null, valign: null
        #     }, {}, [
        #         ['zul.wgt.Label', 'nA3Qd0', {}, {}, []]]],
        #     ['zul.wgt.Cell', 'nA3Qe0', {
        #         domExtraAttrs: {
        #             'data-title': ''
        #         }, align: null, valign: null
        #     }, {}, [
        #         ['zul.wgt.Label', 'nA3Qf0', {}, {}, []]]],
        #     ['zul.wgt.Cell', 'nA3Qg0', {
        #         domExtraAttrs: {
        #             'data-title': ''
        #         }, align: null, valign: null
        #     }, {}, [
        #         ['zul.wgt.Label', 'nA3Qh0', {}, {}, []]]]]],
        mov_str = extract.re_first_or_blank(r'(?si){}.*?\[]]]]]],'.format(mov_id), resp_text)
        oper_date = extract.re_first_or_blank(r"(?si)'Fecha'.*?value:\s*'(.*?)'", mov_str)  # 30/09/2020
        year = oper_date.split('/')[-1]
        value_date = extract.re_first_or_blank(r"(?si)'F. valor'.*?value:\s*'(.*?)'", mov_str)  # 10-02
        descr = extract.re_first_or_blank(r"(?si)'Concepto'.*?value:\s*'(.*?)'", mov_str).replace(
            '\\n',
            '\n'
        )
        # '-10,00'
        amount = convert.to_float(extract.re_first_or_blank(r"(?si)'Importe'.*?value:\s*'(.*?)'", mov_str))
        temp_balance = convert.to_float(extract.re_first_or_blank(r"(?si)'Saldo'.*?value:\s*'(.*?)'", mov_str))

        mov_parsed = {
            'operation_date': oper_date,  # 10/02/2017
            'value_date': '{}/{}'.format(value_date.replace('-', '/'), year),  # 10-02 -> 10/02/2017
            'description': extract.text_wo_scripts_and_tags(descr).replace('\n', '  '),
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed_asc.append(mov_parsed)

    return movements_parsed_asc
