import datetime
import re
from typing import List, Tuple

from custom_libs import convert
from custom_libs import extract
from custom_libs import iban_builder
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed
from project.settings import DB_DATE_FMT

SCRAPER_DATE_FMT = '%d/%m/%y'


def get_auth_param(resp_text: str) -> str:
    return extract.re_first_or_blank("&MSCSAuth=(.*?)[&']", resp_text)


def build_req_params_from_form_html(resp_text: str, form_name: str = '',
                                    form_id: str = '') -> Tuple[str, dict]:
    """
    <input type="hidden" name="PRF_CODE" value="[ST]9PNQ0KDOiR4dR3TLwWRopA==">
    """

    if form_name:

        form_html = extract.re_first_or_blank(
            '(?si)<form.*?name="{}".*?</form>'.format(form_name),
            resp_text
        )

    else:
        form_html = extract.re_first_or_blank(
            '(?si)<form.*?id="{}".*?</form>'.format(form_id),
            resp_text
        )

    action_url = extract.re_first_or_blank('action="(.*?)"', form_html)

    # [(name, value), ...]
    fields_tuples_with_values = re.findall(
        """(?si)<input.*?name=["']?([a-zA-Z0-9]*)['"]?.*?value=["'](.*?)['"]""",
        form_html
    )

    fields_tuples_wo_values = re.findall(
        r"""(?si)<input.*?name=["']?([a-zA-Z0-9]*)['"]?\s*()>""",
        form_html
    )

    fields_tuples = []  # type: List[Tuple]
    fields_tuples += fields_tuples_with_values
    fields_tuples += fields_tuples_wo_values

    req_params = {name: value for name, value in fields_tuples}

    return action_url, req_params


def parse_accounts(resp_text: str) -> List[AccountParsed]:
    # [(
    #  'dos',
    #  '2085/9726/54/0300007897-POL.IND. PRADO',
    #  'dos',
    #   '0,00 Eur\n\t\t     \t \t \t'
    #  ), ...]
    accounts_tuples = re.findall(
        r'(?si)<td class="(un|dos)">(.*?)</td>\s*<td align="right" class="(un|dos)">(.*?)</td>',
        resp_text
    )

    accounts_parsed = []
    for acc_tuple in accounts_tuples:
        account_no_wo_iban = extract.re_first_or_blank('[0-9/]*', acc_tuple[1])
        account_no = iban_builder.build_iban('ES', account_no_wo_iban.replace('/', ''))
        description = acc_tuple[1].replace(extract.re_first_or_blank('[0-9/-]*', acc_tuple[1]), '').strip()
        # credit accounts always(?) marked with star in the end of the description
        account_type = ACCOUNT_TYPE_CREDIT if description.endswith('*') else ACCOUNT_TYPE_DEBIT
        # -? to extract possible '-' (rare case for debit accs)
        balance_str = extract.re_first_or_blank('-?[0-9,.]*', acc_tuple[3])
        balance_float = convert.to_float(balance_str)
        # credit acc is displaying with reversed balance (another sign in movements)
        balance = balance_float if account_type == ACCOUNT_TYPE_DEBIT else -balance_float
        currency = acc_tuple[3].replace(balance_str, '').strip().upper()

        accounts_parsed.append(
            {
                'account_no': account_no,
                'account_type': account_type,
                'descr': description,
                'balance': balance,
                'currency': currency
            }
        )

    return accounts_parsed


def parse_movements(resp_text: str) -> List[MovementParsed]:
    mov_table_html = extract.re_first_or_blank('(?si)<div id="tablaMovimientos">(.*?)</div>', resp_text)
    movements_htmls = re.findall(r'(?si)<tr>\s*<td align="left" style.*?</tr>', mov_table_html)

    movements_parsed = []
    for mov_html in movements_htmls:
        movement_datas = re.findall('(?si)<td.*?>(.*?)</td>', mov_html)

        description = re.sub(r'\s+', ' ', extract.remove_tags(movement_datas[0].replace('<br>', ' ')))

        # '01/03/16'
        operation_date = datetime.datetime.strptime(movement_datas[1], SCRAPER_DATE_FMT).strftime(DB_DATE_FMT)
        value_date = datetime.datetime.strptime(movement_datas[2], SCRAPER_DATE_FMT).strftime(DB_DATE_FMT)

        amount_str = movement_datas[4]  # '564,26+', '1,21-'
        amount_raw = convert.to_float(amount_str.strip('+-'))
        amount = amount_raw if '-' not in amount_str else -amount_raw

        temp_balance = convert.to_float(movement_datas[5])  # '1.941,86' -> 1941.86
        currency = movement_datas[6].upper()

        movement = {
            'description': description,
            'operation_date': operation_date,
            'value_date': value_date,
            'temp_balance': temp_balance,
            'currency': currency,
            'amount': amount
        }

        movements_parsed.append(movement)

    return movements_parsed
