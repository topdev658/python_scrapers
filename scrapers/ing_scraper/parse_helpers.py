import html
import re
import urllib.parse
from typing import List

import xlrd

from custom_libs import convert
from custom_libs import extract
from custom_libs.myrequests import Response
from project.custom_types import AccountParsed, MovementParsed


def get_f_param(resp_text: str, form_name='formulario') -> str:
    """
    extract from html of url
    """
    action_url, _ = extract.build_req_params_from_form_html(resp_text, form_name)
    return ''.join(extract.re_first_or_blank(r'\?f=(.*)|\?f="(.*)"', action_url))


def get_view_state(resp_text: str) -> str:
    return extract.re_first_or_blank(
        'name="javax.faces.ViewState" value="(.*?)"',
        resp_text
    )


def get_login_enter_uname_url(resp_text: str, base_url: str) -> str:
    for re_body in ['action="(/SME/Transactional/faces/views/login/login-n.xhtml.*?)"',
                    'action="(/SME/Transactional/faces/views/login/login-sca.xhtml.*?)"']:
        req_link = extract.re_first_or_blank(re_body, resp_text)
        if req_link:
            break

    assert req_link
    return urllib.parse.urljoin(base_url, req_link)


def get_login_enter_passw_url(resp_text: str, prev_resp_url: str) -> str:
    # explicitly return equal url
    if 'sme-validate-sca-login' not in resp_text:
        return prev_resp_url

    req_link = extract.re_first_or_blank(
        'action="(/SME/Transactional/faces/templates/sme-validate-sca-login.xhtml.*?)"',
        resp_text
    )

    assert req_link
    return urllib.parse.urljoin(prev_resp_url, req_link)


def build_login_passw_params_from_resp(resp_text: str, passw: str) -> str:
    """
    look at the dev/login_resp2.html

        1. extract pairs {'4': '67AEc0MAhzYvSRpC'}
            from <li><a href="javascript:void(null);"
                    onclick="insertDigitDynamic('security','67AEc0MAhzYvSRpC'); return false;">4</a>
                 </li>
        2. build passw_security based on necessary digits to pass
    """

    # {'4': '67AEc0MAhzYvSRpC', '1': '...', ...}
    num_to_code = {
        pair[1]: pair[0]
        for pair in
        re.findall(r"""(?si)onclick="insertDigitDynamic\('security','(.*?)'\); return false;">(\d+)</a></li>""",
                   resp_text)
    }

    # ['1', '2', '6']
    positions_to_extract = re.findall(
        r'\d',
        # "from '1, 2 y 6'"
        extract.re_first_or_blank('<p id="pinPositions" style="display:none;">(.*?)</p>', resp_text)
    )

    # '730453' -> ['kM1n1UXBbLtoknor', '6NnkbDMZf5m9SN9R', '6NnkbDMZf5m9SN9R'']
    passw_codes_to_build_req = [num_to_code[passw[int(pos) - 1]] for pos in positions_to_extract]

    passw_security = ':'.join(passw_codes_to_build_req)
    assert passw_security != ''
    return passw_security


def get_organization_title(resp_text: str) -> str:
    # expect to process
    #     <div class="admision">
    #         <span style="text-align:right;">JOSE IGNACIO MORENO GARCIA
    #             <br>EKIRAUTO S.L.
    #             <br>&Uacute;ltimo contacto: 24/08/2017 14:59:43
    #        </span>
    title_block = extract.re_first_or_blank(r'(?si)<div\s*class="admision">\s*<span.*?>(.*?)</span>', resp_text)
    # expect ['JOSE IGNACIO MORENO GARCIA', 'EKIRAUTO S.L.', 'Último contacto: 03/09/2017 22:59:27']
    rows = [t.strip() for t in re.split('<br>', title_block)]
    organization_title = ''
    if len(rows) > 1:
        organization_title = rows[1]

    return organization_title


def _get_currency(resp_text: str) -> str:
    text = html.unescape(resp_text)
    currency_map = {
        '€': 'EUR',
        '$': 'USD'
    }

    for k, v in currency_map.items():
        if k in text:
            return v

    return 'EUR'


def get_accounts_parsed(resp_text: str) -> List[AccountParsed]:
    # <span id="j_id395">ES47 1465 0100 9619 0006 6464</span></a>
    #                             </h3>
    #
    #                             <strong class=" class_link_dispatcher">98.439,34
    #                                 &#8364;
    #                             </strong>

    accounts_data = re.findall(
        r"(?s)<h3><a\s*onclick=\"submitForm\("
        r"'formulario',\s*\d+\s*"
        r",{source:'(j_id\d+)',"
        r"'index':'(\d+)',"
        r"'productGroup':'(SAV_TRANSACTIONAL)'"  # SAV_TRANSACTIONAL - debit/credit accounts
        r".*?(ES[^<]*).*?<strong[^>]*>(.*?)</strong>",
        resp_text
    )

    accounts_parsed = []

    for acc_data in accounts_data:
        account_parsed = {
            'id_param': acc_data[0],
            'index_param': acc_data[1],
            'product_group_param': acc_data[2],
            'account_no': acc_data[3].replace(' ', ''),
            'balance': convert.to_float(acc_data[4].split()[0]),
            'currency': _get_currency(acc_data[4])
        }
        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed_from_resp_excel(resp_excel: Response) -> List[MovementParsed]:
    book = xlrd.open_workbook(file_contents=resp_excel.content)
    sheet = book.sheet_by_index(0)

    movements_parsed = []  # type: List[MovementParsed]
    for row_num in range(5, sheet.nrows):
        movement = {}
        cells = sheet.row_values(row_num)

        movement['operation_date'] = cells[0]
        movement['value_date'] = cells[0]  # no value date info - set same
        movement['description'] = re.sub(r'\s+', ' ', cells[2].strip())  # remove redundant spaces

        # handle case if empty cells like ['', '', 'FINANCIERO DE CREDITO S.A.', '', '', '']
        # handle case if first row is head of table (but need to scrape from it to keep all mov in any table format)
        try:
            movement['amount'] = convert.to_float(cells[4])
            movement['temp_balance'] = convert.to_float(cells[5])
        except ValueError:
            continue

        movements_parsed.append(movement)

    return movements_parsed
