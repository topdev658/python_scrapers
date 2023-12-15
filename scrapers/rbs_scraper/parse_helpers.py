import csv
import html
import io
import re
import urllib.parse
from typing import List, Tuple

from custom_libs import extract
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed
from .custom_types import AccountGroup


def _get_balance_from_balance_raw(balance_raw: str) -> float:
    # '11,017.00', 'Cr'
    balance_str, sign = re.split(r'\s', balance_raw)
    balance = float(balance_str.replace(',', ''))
    if sign == 'Dr':  # Dr - negative, Cr - positive
        balance = -balance
    return balance


def get_random_id(resp_text: str) -> str:
    rand_id = extract.re_first_or_blank(r'(?si)name="RANDOM_ID"\s+value="(.*?)"', resp_text)
    return rand_id


def get_token(resp_text: str) -> str:
    return extract.re_first_or_blank(r'var\s+token\s*=\s*"([^"]+)"', resp_text)


def get_ncn(resp_text: str) -> str:
    return extract.re_first_or_blank(r'ncn=(\d+)"', resp_text)


def map_form_ix_to_letter_ix(resp_text: str, input_name: str) -> List[int]:
    """
    DEPRECATED, used for prev layout.
    Keep it here to compare with the new implementation 'map_ix_to_letter_ix'

    Parses
    <td align="right" width="5%"><b>
    <label for="Pin1"><span style="display:none">Enter </span>2nd
    <span style="display:none"> character from your PIN.
    Note that the cursor will automatically move to the next field after each entry.</span></label></b></td>
    <td width="5%">&nbsp;
    <input type="password" name="pinIndexed[0].value" maxlength="1" size="1" tabindex="1" value="" id="Pin1">
    </td>
    (text: Enter 2nd)

    To get form indexes and corresponding indexes of letters of self.pin/self.pinpass (so called secret_val here)

    :param resp_text: response text
    :param input_name: one of `pinIndexed` (for `pin` secret val) or `passIndexed` (for `pinpass` secret_val)
    :returns List[secret_val_ix] where index of el corresponds to position in form input
    """
    # '1st' -> 0
    res = [int(x) - 1 for x in re.findall(
        r'(?s)>Enter\s*</span>(\d+)[^[]*{}'.format(input_name),
        resp_text
    )]

    return res


def map_ix_to_letter_ix(resp_text: str, input_name: str) -> List[int]:
    """Parses
     parse from var data = {"pin-keys":[3,4,2],"pass-keys":[3,10,13]
    :param resp_text: response text
    :param input_name: one of `pin-keys` (for `pin` secret val) or `pass-keys` (for `pinpass` secret_val)
    :returns List[secret_val_ix] where index of el corresponds to position in form input

    >>> resp_text = 'var data = {"pin-keys":[3,4,2],"pass-keys":[3,10,13], ...'
    >>> map_ix_to_letter_ix(resp_text, "pin-keys")
    [2, 3, 1]
    >>> map_ix_to_letter_ix(resp_text, "pass-keys")
    [2, 9, 12]
    """
    res = []  # type: List[int]

    # '3,4,2'
    indexes_str = extract.re_first_or_blank(
        r'(?s)"{}"\s*:\s*\[([\d,]+)\]'.format(input_name),
        resp_text
    )
    if indexes_str:
        # '1' -> 0
        res = [int(x) - 1 for x in indexes_str.split(',')]
    return res


def get_account_groups(resp_text: str, resp_url: str) -> List[AccountGroup]:
    """
    Parses
    <a href="/bankline/rbs/ai/accsetsummary/linktoaccsum.do?org.apache.struts.taglib.html.TOKEN
    =79c9e4b26c230ed8d51c7c54f8cbe36f&amp;accsetindex=0&ncn=828"
    tabindex="107" title="Account ID" onclick="return clicked();">TESORALIA</a>

    :return: List[Tuple[link_anchor, link_url]]
    """
    account_groups = []  # type: List[AccountGroup]

    # List[Tuple[link, title]
    # expect links like
    # https://www.bankline.rbs.com/bankline/rbs/ai/accsetsummary/linktoaccsum.do?org.apache.struts.taglib.html.TOKEN
    # =4f692af02fe0044cfbafc97e89b5add9&accsetindex=0&ncn=235

    acc_set_tuples = re.findall(r'(?si)<a href="([^"]+)"[^>]+title="Account ID"[^>]+>([^<]+)</a>', resp_text)
    for acc_set_tuple in acc_set_tuples:
        account_set = AccountGroup(
            title=acc_set_tuple[1],
            url=html.unescape(urllib.parse.urljoin(resp_url, acc_set_tuple[0]))
        )
        account_groups.append(account_set)

    return account_groups


def get_account_details_urls(resp_text: str, resp_url: str) -> List[str]:
    """
    Parses
    <a href="/bankline/rbs/ai/accountsummary/linktostatement.do?accountindex=3
    &amp;org.apache.struts.taglib.html.TOKEN=90c457fa7fc1eba02035bf41ac4e7690&ncn=718"
    tabindex="118" title="Statement" onclick="return clicked();">60-00-01 48603139</a>
    """
    acc_urls = [urllib.parse.urljoin(resp_url, html.unescape(link)) for link in
                re.findall(r'(?si)<a href="([^"]+)"[^>]+title="Statement"', resp_text)]  # [^>]+>([^<]+)</a>

    return acc_urls


def get_account_parsed(resp_text: str) -> AccountParsed:
    # GB26NWBK60000148609331
    account_iban = extract.re_first_or_blank(r'(?si)IBAN</td>\s*<td><strong>([^<]+)</strong></td>', resp_text)

    # 60-00-01 48603139
    fin_ent_account_id = "{} {}".format(
        extract.re_first_or_blank(r'(?si)Sort code</td>\s*<td><strong>([^<]+)</strong></td>', resp_text),
        extract.re_first_or_blank(r'(?si)Number</td>\s*<td><strong>(\d+)\s*</strong></td>', resp_text)
    )
    # GBP
    currency = extract.re_first_or_blank(r'(?si)Currency</td>\s*<td><strong>([^<]+)</strong></td>', resp_text)

    # 714.70&nbsp;Cr
    balance_raw = extract.re_first_or_blank(
        # r"(?si)Today's cleared</td>\s*<td>\s*<strong>([^<]+)</strong>\s*</td>",
        # only ledger balance is avail for movs
        r"(?si)Today's cleared</td>\s*<td>\s*<strong>([^<]+)</strong>\s*</td>",
        resp_text
    ).strip()

    balance = _get_balance_from_balance_raw(balance_raw)

    account_parsed = {
        'account_no': account_iban,
        'fin_ent_account_id': fin_ent_account_id,
        'balance': balance,
        'currency': currency,
        'account_type': ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT,
    }

    return account_parsed


def get_date_of_most_recent_movement(resp_text: str) -> str:
    """
    :return: date_str in dd/mm/yyyy fmt
    """
    date_str = extract.re_first_or_blank(
        r'(?si)td headers="y0 x0"[^>]*>\s*([0-9/]+)\s*</td>',
        resp_text
    )
    return date_str


def get_temp_balance_of_most_recent_movement(resp_text: str) -> Tuple[bool, float]:
    """
    :return: (got_movement, val)
    """
    if extract.re_first_or_blank('<td headers="y0 x0"[^>]*>No data</td>', resp_text):
        return False, 0

    # searches for \s*0.00&nbsp;Cr\s*
    temp_balance_raw = extract.re_first_or_blank(
        r'(?si)<td headers="y0 x5" class="rightAlign">([^<]+)</td>',
        resp_text
    ).strip()
    if temp_balance_raw == '':
        return True, 0

    temp_balance = _get_balance_from_balance_raw(temp_balance_raw)

    return True, temp_balance


def get_movements_parsed(resp_text: str, account_balance: float) -> List[MovementParsed]:
    movements_parsed = []  # type: List[MovementParsed]
    temp_balance_next = account_balance
    reader = csv.DictReader(io.StringIO(resp_text))
    # desc ordering (from newest to oldest)
    for mov_dict in reader:
        # Debit - decrease, Credit - increase
        # # Debit with '-' sigh already
        amount = float(mov_dict['Debit'] or '0') + float(mov_dict['Credit'] or '0')
        temp_balance = temp_balance_next
        operation_date = value_date = mov_dict['Date']  # 27/03/2019
        descr = '{} || {} || {} || {} || {} || {}'.format(
            mov_dict['Narrative #1'],
            mov_dict['Narrative #2'],
            mov_dict['Narrative #3'],
            mov_dict['Narrative #4'],
            mov_dict['Narrative #5'],
            mov_dict['Type']
        ).strip()

        movement_parsed = {
            'amount': amount,
            'temp_balance': temp_balance,
            'description': descr,
            'description_extended': descr,
            'operation_date': operation_date,
            'value_date': value_date,
        }

        movements_parsed.append(movement_parsed)

        # for earlier movement
        temp_balance_next = round(temp_balance - amount, 2)

    return movements_parsed
