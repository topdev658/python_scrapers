import re
from typing import List, Optional, Tuple
from xml.dom import minidom

from custom_libs import convert
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import (ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT,
                                  AccountParsed, MovementParsed)


def get_contracts_datas(resp_text: str) -> List[Tuple[str, str]]:
    # [('115', '9860595'), ...]
    contracts_datas = re.findall(
        r"bNet\.casca\.mudaEmpresa\('(.*?)','(.*?)',this\)",
        resp_text
    )  # type: List[Tuple[str, str]]
    return contracts_datas


def get_contract_home_url_raw(resp_text: str) -> str:
    url_raw = extract.re_first_or_blank(
        '<p id="HostHomePage">(.*?)</p>',
        resp_text
    )
    return url_raw


def get_organization_title(resp_text: str) -> str:
    title = extract.re_first_or_blank(
        '<span class="icon firm">.*?<a href="#" onclick="return false;">(.*?)<',
        resp_text
    ).strip()
    return title


def get_accounts_ibans(resp_text: str) -> List[str]:
    accounts_ibans = re.findall('iban="(.*?)"', resp_text)
    return accounts_ibans


def get_account_select_param(resp_text: str, account_iban: str) -> str:
    req_param = extract.re_first_or_blank(r'option[^>]+value="([^"]+)"\s+iban="{}"'.format(account_iban),
                                          resp_text)
    return req_param


def get_account_parsed(resp_text: str, account_iban: str) -> AccountParsed:
    # 1st - for Spain, 2nd - for Portugal
    balance_w_currency = (
            extract.re_first_or_blank(r'(?si)Contable.*?<span[^>]+>(.*?)</span>',
                                      resp_text).strip()
            or extract.re_first_or_blank(r'(?si)Contabilistico.*?<span[^>]+>(.*?)</span>',
                                         resp_text).strip()
    )
    currency = 'EUR' if '€' in balance_w_currency else 'USD'
    balance = convert.to_float(balance_w_currency)
    account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

    account_parsed = {
        'account_no': account_iban,
        'balance': balance,
        'account_type': account_type,
        'currency': currency
    }

    return account_parsed


def _convert_mov_excel_date(date_mov: str) -> str:
    """Convert 2017-09-22 to 22/09/2017"""

    y, m, d = date_mov.split('-')
    return '{}/{}/{}'.format(d, m, y)


def _get_movements_parsed_from_xml(resp_xml_text: str,
                                   fin_ent_account_id: str,
                                   logger: ScrapeLogger) -> List[MovementParsed]:
    movements_parsed_desc = []  # type: List[MovementParsed]

    if '?xml version' not in resp_xml_text:
        return movements_parsed_desc

    dom = minidom.parseString(resp_xml_text)
    rows = dom.getElementsByTagName('Row')

    # -u 340332 -a 20004 has broken temp balances
    # 20190625	ENT	DEPOSITO DE NUMERARIO REF. CLAUDIO DIAS	-	216	24052,31
    # 20190625	ENT	DEPOSITO DE NUMERARIO REF. CLAUDIO DIAS	-	100	24052,31 // same!
    # SOLUTION: Calculate temp_balances on the fly with warning messages if it
    # different to scraped, but prefer calculated
    # NOTE: first temp_balance always from web
    temp_balance_calc = None  # type: Optional[float]
    n_temp_bal_warnings = 0
    for ix, row in enumerate(rows):
        cells = row.getElementsByTagName('Cell')
        # not movements row
        if len(cells) != 10:
            continue

        # xml example: novobanco_scraper/dev/mov.xml
        # Last cell may have child like "Canais Directos"
        # OR may have not for future movements.
        # To avoid index error exceptions, don't use list comprehensions
        # to handle absent XML nodes
        cells_vals = []  # type: List[str]

        for c in cells:
            val = ''
            node1 = extract.by_index_or_none(c.childNodes, 0)
            if node1:
                node2 = extract.by_index_or_none(node1.childNodes, 0)
                if node2:
                    val = node2.data
            cells_vals.append(val)

        # table header in Spanish/Portugal, handle 'Não existem movimentos'
        if cells_vals[0] in ['Fecha Operación', 'Data Operação']:
            continue

        # dates: from 2018-04-05T00:00:00 to 05/04/2018

        operation_date = _convert_mov_excel_date(cells_vals[0].split('T')[0])
        value_date = _convert_mov_excel_date(cells_vals[1].split('T')[0])

        description = re.sub(r'\s+', ' ', cells_vals[3].strip())
        amount_minus = float(cells_vals[4] if cells_vals[4] != '-' else '0')
        amount_plus = float(cells_vals[5] if cells_vals[5] != '-' else '0')
        amount = amount_plus - amount_minus

        # there are info rows w/o movements - skip them
        if amount == 0:
            continue

        temp_balance_scraped = float(cells_vals[6])

        temp_balance = (temp_balance_calc
                        if temp_balance_calc is not None
                        else temp_balance_scraped)

        mov_parsed = {
            'value_date': value_date,
            'operation_date': operation_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed_desc.append(mov_parsed)
        if temp_balance != temp_balance_scraped:
            n_temp_bal_warnings += 1
            logger.warning("{}: mov {} has wrong temp_balance_scraped={}. Use calculated".format(
                fin_ent_account_id,
                mov_parsed,
                temp_balance_scraped
            ))

        # will be used for the next movement
        temp_balance_calc = round(temp_balance - amount, 2)

    if n_temp_bal_warnings > 3:
        logger.error(
            "{}: too many n_temp_bal_warnings={}. Probably, parsing error. "
            "Check the log and the website. movements_parsed_desc={}".format(
                fin_ent_account_id,
                n_temp_bal_warnings,
                movements_parsed_desc,
            )
        )

    return movements_parsed_desc


def get_movements_parsed_from_html_excel(resp_text: str,
                                         fin_ent_account_id: str,
                                         logger: ScrapeLogger) -> List[MovementParsed]:
    if '?xml version' in resp_text:
        movements_parsed = _get_movements_parsed_from_xml(resp_text, fin_ent_account_id, logger)
        return movements_parsed

    movements_parsed = []
    mov_table_html = extract.re_first_or_blank('(?si)<table.*?</table>', resp_text)
    rows = re.findall('(?si)<tr.*?</tr>', mov_table_html)
    # todo check date: skip earlier dates
    for row in rows[9:]:
        columns = [extract.remove_tags(h).strip() for h in re.findall('(?si)<td.*?</td>', row)]
        # not movement? continue
        if len(columns) != 6:
            continue

        operation_date = _convert_mov_excel_date(columns[0])
        value_date = _convert_mov_excel_date(columns[1])

        description = columns[2].strip()
        amount_minus = convert.to_float(columns[3] if columns[3] != '-' else '0')
        amount_plus = convert.to_float(columns[4] if columns[4] != '-' else '0')
        amount = amount_plus - amount_minus
        temp_balance = convert.to_float(columns[5])

        # there are info rows w/o movements - skip them
        if amount == 0:
            continue

        mov_parsed = {
            'value_date': value_date,
            'operation_date': operation_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed.append(mov_parsed)

    return movements_parsed
