import re
from typing import List

from custom_libs import convert
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed
from .custom_types import AccountsDropdownPageData


def get_accounts_details_urls_params(resp_text: str) -> List[str]:
    ccs_params = re.findall(r"option class='contrato' value='(\d+)'", resp_text)
    return ccs_params


def get_accounts_list_url(logger: ScrapeLogger,
                          resp_text: str,
                          basic_url: str,
                          acc_dropdown_page_data: AccountsDropdownPageData) -> str:
    """Extracts url of the page with a dropdown list with acounts.
    Provides basic url from 'Información de contrato' page
    or if fallback_saldo_link_class is provided and 'Información de contrato'
    is not available, then from fallback 'Consulta saldo disponible' page (-u 226491 -a 11121)

    :returns url or '' if not such kind of accounts
    """

    contrato_link_html = extract.re_first_or_blank(
        '(?si)<li class="{}">.*?</li>'.format(acc_dropdown_page_data.contrato_li_class),
        resp_text
    )
    url_contrato = extract.get_link_by_text(
        contrato_link_html,
        basic_url,
        acc_dropdown_page_data.contrato_link_text
    )

    url_saldo = extract.get_link_by_text(
        extract.re_first_or_blank(
            '(?si)<li class="{}">.*?</li>'.format(acc_dropdown_page_data.saldo_link_class),
            resp_text
        ),
        basic_url,
        acc_dropdown_page_data.saldo_link_text
    )

    # got only url_saldo for foreign_currency account
    if url_saldo and (not url_contrato) and acc_dropdown_page_data.is_foreign_currency:
        logger.error(
            "'Información de contrato' is not available for foreign currency account. "
            "'Consulta saldo disponible' as a fallback info is used. "
            "In this case, it is possible to get correct balance in foreign currency only from movements. "
            "Be sure, that you scraped movements of the account and scrape it manually if necessary. "
            "Also, set the account currency manually."
        )

    return url_contrato or url_saldo


def get_account_parsed_from_details(resp_text: str, ccs_param: str) -> AccountParsed:
    """Useful for _get_accounts_parsed_from_acc_details only. Rare case"""

    # from basic ES98 0061 0383 7100 0211 0114 - ROSA GRES, S.L.U
    account_no = re.sub(
        r'\s+',
        '',
        # general from Información de contrato
        extract.re_first_or_blank(
            r'(?si)Contrato:\s*(ES[0-9 ]*)[^<]*</span>',
            resp_text
        ) or
        # as a fallback from Consulta de saldo
        extract.re_first_or_blank(
            r'(?si)<p class="subtitulo">\s*(ES[0-9 ]*)[^<]*</p>',
            resp_text
        )
    )

    # expect 189.952,55 € or 189.952,55  USD (balance with currency sign for Información de contrato)
    balance_str = (
        # general from Información de contrato
        extract.re_first_or_blank(
            r'(?si)<td class="tdLabel">Saldo actual</td>\s*<td[^>]*>(.*?)</td>',
            resp_text
        ).strip()
        or
        # as a fallback from  Consulta de saldo
        # NOTE: balance only in EUR even for foreign currency accounts
        # -u 226491 -a 11121 (no Información de contrato available)
        # Already reported by get_accounts_list_url()
        extract.re_first_or_blank(
            r'(?si)<td class="tdLabel">Saldo posición</td>\s*<td[^>]*>(.*?)</td>',
            resp_text
        ).strip()
    )

    balance = convert.to_float(balance_str)
    currency_str = balance_str.split()[-1]
    currency = 'EUR' if currency_str == '€' else currency_str
    account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

    account_parsed = {
        'account_no': account_no,
        'balance': balance,
        'currency': currency,
        'account_type': account_type,
        'ccs_param': ccs_param
    }

    return account_parsed


def get_movements_parsed(resp_plain_text: str) -> List[MovementParsed]:
    movements_parsed = []  # type: List[MovementParsed]
    if 'No hay movimientos' in resp_plain_text:
        return movements_parsed

    rows = resp_plain_text.split('\n')

    should_parse = False
    for row in rows:
        # skip upper title row
        if ('F.Operación' not in row) and not should_parse:
            continue

        if not row.strip():
            continue

        if 'F.Operación' in row:
            should_parse = True
            continue

        columns = row.split('\t')
        if columns[1] == 'null':
            continue  # not a valid movement ['18/09/2019', 'null', '', 'Saldo', '', '453,25\r']

        operation_date = columns[0]
        operation_year = operation_date[-4:]
        value_date = '{}/{}'.format(columns[1], operation_year)
        description = columns[3]
        amount = convert.to_float(columns[4])
        temp_balance = convert.to_float(columns[5])

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed.append(movement_parsed)

    return movements_parsed
