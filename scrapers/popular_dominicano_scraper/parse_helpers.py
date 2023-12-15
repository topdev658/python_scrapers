import html
import re
from typing import List, Tuple
from urllib.parse import urljoin

from custom_libs import convert
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import (
    ACCOUNT_NO_TYPE_UNKNOWN, ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT,
    AccountParsed, MovementParsed
)

CURRENCIES = {
    'US$': 'USD',
    'RD$': 'DOP',  # Dominican peso
    'EUR': 'EUR'
}


def _to_float(text: str) -> float:
    # $24,684.68- -> -24684.68
    return convert.to_float(text.replace(',', '').replace('.', ','))


def get_organization_title(resp_text: str) -> str:
    res = extract.re_first_or_blank(r'(?si)(Buenos Dias|Buenas Tardes)(.*?)</b>', resp_text)
    if len(res) == 0:
        return ''  # silent failure
    return res[1].strip()


def get_page_link(resp_text: str, page_num: int) -> str:
    """Parses from
    | <A
                  HREF="banco.popular.aspx?nfm=2&_SOURCESCREEN=&pID
                  =480214197223186206168281255192209210261278156223259255208207249300237219156279205214252214257303210282184301243512&isGet=184&_SmallAmt=&_BigAmt=&_RefNum=&SerialNum=&_Type=3&_View=&_STARTDATE=10%2F01%2F2018&_ENDDATE=09%2F02%2F2019&trnob=268294265315242326292353315&trnp=196&trnod=376478393431422406396461391&f=312346353359314342160353395456473354441394416475367423452447429464433">4</A>
                |"""
    return extract.re_first_or_blank(r'(?si)[|]\s*<a href="([^"]*)"\s*>{}</a>\s*[|]'.format(page_num),
                                     resp_text)


def get_account_details_urls(resp_text: str, resp_url: str) -> List[str]:
    table_html = extract.re_first_or_blank(
        r'(?si)(<table[^>]+md-maketable.*?)<table[^>]+md-maketable',
        resp_text
    )
    account_details_urls = [
        urljoin(resp_url, link)
        for link in
        set(re.findall(r'(?si)<a\s+href="(banco.popular.aspx[?]nfm=2&e=.*?.*?)"',
                       table_html))
    ]
    return account_details_urls


def get_account_parsed(resp_text: str, logger: ScrapeLogger) -> Tuple[bool, AccountParsed]:
    account_parsed = {}   # type: AccountParsed

    # DO57BPDO00000000000808393177
    account_no = extract.re_first_or_blank(r'Cuenta Regional:</td>\s+<td.*?>(.*?)</td>', resp_text)
    # $24,684.68
    balance_str = extract.re_first_or_blank(r'Balance Actual:</td>\s+<td.*?>(.*?)</td>', resp_text)
    # can't use convert.to_float due to collision of ,. separators

    # There is a floating case when can't parse account due to wrong response
    # Should be handled in the future (need to define additional err text markers)
    if not (account_no and balance_str):
        logger.error("Can't parse account (most probably during concurrent processing. Skip.\n"
                     "RESPONSE:\n{}".format(resp_text))
        return False, {}

    balance = _to_float(balance_str)

    # <br>Transacciones <BR>Cuenta Corriente / RD$ 81008738
    # <br>Transacciones <BR>Cuenta de Ahorro / RD$ 81008738
    currency_raw = extract.re_first_or_blank(
        r'(?si)<br>Transacciones\s*<br>Cuenta[^/]*/ ([^\s]+) {}'.format(account_no[-9:]),
        resp_text
    )
    currency = CURRENCIES.get(currency_raw, 'EUR')
    account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
    account_parsed = {
        'account_no': account_no,
        'balance': balance,
        'currency': currency,
        'account_type': account_type,
        'country_code': 'DOM',  # Dominican Republic
        'account_no_format': ACCOUNT_NO_TYPE_UNKNOWN
    }

    return True, account_parsed


def get_movements_parsed(resp_text: str, logger: ScrapeLogger) -> List[MovementParsed]:
    movements_parsed_asc = []  # type: List[MovementParsed]

    movs_table_html_tpl = extract.re_first_or_blank(
        r'(?si)(<table[^>]+md-maketable.*?)</table>\s*(<br>|<script.*?>)',
        resp_text
    )

    if not movs_table_html_tpl:
        logger.error("Expected, but didn't find the table with movements at the page. Skip.\n"
                     "RESPONSE:\n{}".format(resp_text))
        return []

    mov_htmls = re.findall('(?si)<tr.*?</tr>', movs_table_html_tpl[0])

    for mov_html in mov_htmls:
        cells = [html.unescape(v).strip() for v in re.findall('(?si)<td.*?>(.*?)</td>', mov_html)]
        if len(cells) < 9:
            continue
        operation_date = cells[0]  # 04/10/2018
        value_date = cells[1]  # 04/10/2018
        description = '{} || {}'.format(cells[2], cells[4])
        amount = _to_float(extract.remove_tags(cells[5]))  # $5.00- -> -5.00
        temp_balance = _to_float(cells[6])

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed_asc.append(movement_parsed)

    return movements_parsed_asc
