import datetime
import re
import urllib.parse
from typing import Dict, List

from custom_libs import convert
from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import iban_builder
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed
from scrapers.volkswagenbank_scraper.custom_types import ContractData

BANK_CODE = '1480'
SCRAPER_DATE_FMT = '%d-%m-%y'


def _convert_date_str_to_dt(date_str: str) -> datetime.datetime:
    date_db_format = datetime.datetime.strptime(date_str, SCRAPER_DATE_FMT)
    return date_db_format


def get_digit_href(html_str, digit_position_named):
    href = extract.re_first_or_blank(
        'src="(/servlet/ResolCoordPinServlet[^"]*?coord={})"'.format(digit_position_named),
        html_str
    )
    return href


def get_digit_from_png(saved_images: Dict[int, bytes], digit_png_bytes: bytes) -> int:
    for num, num_bytes in saved_images.items():
        if num_bytes == digit_png_bytes:
            return num
    return -1


def get_contracts_data(basic_url: str, html_str: str) -> List[ContractData]:
    contracts_data = [
        ContractData(urllib.parse.urljoin(basic_url, href), title)
        for href, title in
        re.findall(
            '(?si)<a target="_posicion"[^>]*href="(.*?)".*?<td class=".*?"><span>(.*?)</span>',
            html_str
        )
    ]

    assert contracts_data
    return contracts_data


def get_contract_menu_frame_url(basic_url: str, html_str: str) -> str:
    menu_frame_href = extract.re_first_or_blank(
        'frame src="(.*?)"',
        html_str
    )

    assert menu_frame_href
    return urllib.parse.urljoin(basic_url, menu_frame_href)


def get_position_global_url(basic_url: str, html_str: str) -> str:
    position_global_href = extract.re_first_or_blank(
        '"Posición global","(.*?)"',
        html_str
    )

    assert position_global_href
    return urllib.parse.urljoin(basic_url, position_global_href)


def get_accounts_parsed(html_str) -> List[AccountParsed]:
    accounts_parsed = []

    accounts_htmls = [
        h for h in
        re.findall('(?si)(javascript.*?)(?=javascript)', html_str)
        if h.startswith('javascript:window.showMenu')
    ]

    for account_html in accounts_htmls:
        account_submenu_id = extract.re_first_or_blank(
            'javascript:window.showMenu\(window\.(.*?)\)',
            account_html
        )

        account_movements_href = extract.re_first_or_blank(
            """window.{}.addMenuItem\("Consulta de últimos movimientos","window.location='(.*?)'""".format(
                account_submenu_id
            ),
            html_str
        )
        fin_ent_account_id = extract.re_first_or_blank(
            '(?si)javascript:window.*?<font.*?>(.*?)</font>',
            account_html
        ).strip()
        account_no = iban_builder.build_iban('ES', fin_ent_account_id)

        # first table contains necessary information
        balance_html = extract.re_first_or_blank('(?si)<table>(.*?)</table>', account_html)
        balance_str, currency = [extract.remove_tags(h) for h in re.findall('<td.*?>(.*?)</td>', balance_html)]
        balance = convert.to_float(balance_str)
        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

        account_parsed = {
            'account_no': account_no,
            'financial_entity_account_id': fin_ent_account_id,
            'balance': balance,
            'currency': currency,
            'account_type': account_type,
            'account_movements_href': account_movements_href
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed(html_str: str) -> List[MovementParsed]:
    movements_parsed = []

    mov_trs = re.findall(
        '(?si)(<tr class="(senar|parell)".*?</table>.*?</table>.*?</tr>)',
        html_str
    )

    for mov_tr in mov_trs:
        columns = [extract.remove_tags(c) for c in re.findall('<td.*?</td>', mov_tr[0])]

        operation_date_raw = columns[0]  # 31-12-17
        value_date_raw_wo_year = columns[3]  # 02-01
        value_date_raw_w_year = value_date_raw_wo_year + operation_date_raw[-3:]  # 02-01-17 (!! wrong year)

        operation_date_dt = _convert_date_str_to_dt(operation_date_raw)
        value_date_dt = _convert_date_str_to_dt(value_date_raw_w_year)

        value_date_correct_dt = date_funcs.correct_year_if_new_year(
            operation_date_dt,
            value_date_dt,
            datetime.timedelta(days=15)
        )

        operation_date = date_funcs.convert_dt_to_scraper_date_type1(operation_date_dt)  # 31/12/2017
        value_date = date_funcs.convert_dt_to_scraper_date_type1(value_date_correct_dt)  # 02/01/2018 (! correct year)

        description = columns[2]
        amount = convert.to_float(columns[4])
        temp_balance = convert.to_float(columns[6])

        movement_parsed = {
            'description': description,
            'operation_date': operation_date,
            'value_date': value_date,
            'temp_balance': temp_balance,
            'amount': amount
        }

        movements_parsed.append(movement_parsed)

    return movements_parsed
