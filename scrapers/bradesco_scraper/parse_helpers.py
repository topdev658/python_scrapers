import re
from typing import List, Optional, Tuple

from custom_libs import convert
from custom_libs import extract
from project.custom_types import (MovementParsed, MovementScraped,
                                  AccountParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT)
from scrapers.bradesco_scraper.custom_types import AccountToFilter


def get_ctrl_param_from_url(url: str) -> str:
    return extract.re_first_or_blank(r'CTRL=(\d+)', url)


def get_organization_title(resp_text: str) -> str:
    org_title = extract.re_first_or_blank(
        r'(?si)id="_id112"[^>]+>(.*?)<',
        resp_text
    )
    return org_title


def get_accounts_to_filter(resp_text: str) -> List[AccountToFilter]:
    accounts_to_filter = []  # type: List[AccountToFilter]
    accounts_to_filter_raw = re.findall(
        r'<input type="checkbox" name="contas" value="(\d+)"[^>]*>(.*?)<',
        resp_text
    )
    for acc_to_filter in accounts_to_filter_raw:
        accounts_to_filter.append(
            AccountToFilter(
                select_option_ix=acc_to_filter[0],
                # '0054 | 0001486-9'
                fin_ent_account_id=acc_to_filter[1].rstrip()
            )
        )
    return accounts_to_filter


def get_accounts_from_dropdown(resp_text: str) -> List[AccountToFilter]:
    accounts_from_dropdown = []  # type: List[AccountToFilter]
    select_html = extract.re_first_or_blank('(?si)<select id="contaDebito".*</select>',
                                            resp_text)

    # <option value="0">0054 | 0001486-9 | Conta-Corrente</option>
    # <option value="1">0054 | 0001486-9 | Conta-Poupança</option>
    # <option value="2">0054 | 0001486-9 | Conta-Investimento</option>
    # -> [('0', '0054 | 0001486-9 | Conta-Corrente'), ...]
    accounts_from_dropdown_raw = re.findall(
        r'(?si)<option value="(\d+)"[^>]*>(.*?)</option>',
        select_html
    )
    for acc_drop in accounts_from_dropdown_raw:
        accounts_from_dropdown.append(
            AccountToFilter(
                select_option_ix=acc_drop[0],
                # title=acc_drop[1],
                # '0054 | 0001486-9'
                fin_ent_account_id=extract.re_first_or_blank('[-0-9 |]+', acc_drop[1]).strip(' | ')
            )
        )
    return accounts_from_dropdown


def get_account_parsed(resp_text: str,
                       account_to_filter: AccountToFilter,
                       movement_scraped_last: Optional[MovementScraped]) -> Tuple[bool, AccountParsed]:
    currency_raw = extract.re_first_or_blank(r'Total\s*[(](.*?)[)]', resp_text)
    currency = 'BRL' if currency_raw == 'R$' else currency_raw

    balance = 0.0
    if movement_scraped_last:
        balance = movement_scraped_last.TempBalance
    else:
        # No movement_scraped_last.
        # Well, let's get today's balance from "Total (R$)" (may be != real if date_to < today)
        balance_str = extract.re_last_or_blank(
            'td class="valor">(.*?)<',
            resp_text
        )
        if not balance_str:
            return False, {}
        balance = convert.to_float(balance_str)

    account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
    account_parsed = {
        'account_no': account_to_filter.fin_ent_account_id,
        'financial_entity_account_id': account_to_filter.fin_ent_account_id,
        'balance': balance,
        'currency': currency,
        'account_type': account_type
    }
    return True, account_parsed


def get_movements_parsed(resp_text: str) -> List[MovementParsed]:
    movements_parsed_asc = []  # type: List[MovementParsed]
    # From both tables:
    # Extrato de: Ag: ...| CC: ... | Entre 20/08/2019 e 04/09/2019
    # and Últimos Lançamentos
    mov_rows = re.findall(r'(?si)<tr\s+class="tabelaSaldosTr.*?</tr>', resp_text)
    operation_date_actual = ''
    for mov_row in mov_rows:
        cells = re.findall('(?si)<td[^>]*>(.*?)</td>', mov_row)
        if len(cells) != 7:
            continue
        operation_date = cells[0] or operation_date_actual
        if operation_date == 'Data' or not operation_date:
            continue

        operation_date_actual = operation_date
        value_date = operation_date  # no real val
        description = extract.remove_tags(cells[1])
        if description == 'SALDO ANTERIOR' and not (cells[4] + cells[5]):
            continue
        dctno = cells[3]  # destination?
        # Only 1 extra field, always dctno
        decsr_extended = '{} || Dcto: {}'.format(description, dctno).rstrip()
        amount = convert.to_float(cells[4] + cells[5])  # positive + negative str (one of two is filled)
        temp_balance = convert.to_float(cells[6])
        mov_parsed = {
            'value_date': value_date,
            'operation_date': operation_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance,
            'description_extended': decsr_extended
        }

        movements_parsed_asc.append(mov_parsed)

    return movements_parsed_asc


def get_movements_parsed_except_recent(resp_text: str) -> List[MovementParsed]:
    """Paginated movements,
    never contain recent movs even if date_to == today.
    The site implicitly splits filtered movements and
    put the movements of last 2 days to another table 'Últimos Lançamentos'
    """
    movs_html = extract.re_first_or_blank('(?si)tabelaListagemImpressao.*?ltimos Lan',
                                          resp_text)
    return get_movements_parsed(movs_html)


def get_movements_parsed_recent(resp_text: str) -> List[MovementParsed]:
    """Available on each paginated result"""
    movs_html = extract.re_first_or_blank('(?si)ltimos Lan.*',  # Últimos Lançamentos
                                          resp_text)
    return get_movements_parsed(movs_html)
