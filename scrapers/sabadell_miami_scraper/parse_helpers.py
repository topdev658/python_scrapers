import re
from typing import List, Optional

from custom_libs import date_funcs
from custom_libs import extract
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed


def get_accounts_parsed_wo_balance(resp_text: str) -> List[dict]:
    """
    Parses MULTI-account layout
        <div>
        <label for="accountNumber">Cuenta:*&#160;</label>
        <select id="accountNumber" name="accountNumber">
            <option id="accountNumber-1" value="-1">Seleccione una cuenta, por favor</option>
            <option value="00000503382-0825-FERSA-NKE BEARINGS NORTH AMERICA  CCA">0825 - 00000503382 : FERSA-NKE BEARINGS NORTH AMERICA  CCA</option>
            <option value="00000515397-0825-PFI GROUP INC CCA">0825 - 00000515397 : PFI GROUP INC CCA</option>
        </select>

    OR one-account layout

        <div>
        <label for="accountNumber">Cuenta:*&#160;</label>
            0825 - 00000503382 : FERSA-NKE BEARINGS NORTH AMERICA  CCA
            <input id="accountNumber" name="accountNumber" type="hidden"
            value="00000503382-0825-FERSA-NKE BEARINGS NORTH AMERICA  CCA"/>
        </div>

    Tests below covers these layouts:
    >>> t = ' <div> ' \
            '<label for="accountNumber">Cuenta:*&#160;</label> ' \
            '<select id="accountNumber" name="accountNumber"> ' \
            ' <option id="accountNumber-1" value="-1">Seleccione una cuenta, por favor</option>' \
            ' <option value="00000503382-0825-FERSA-NKE BEARINGS NORTH AMERICA  CCA">0825 - 00000503382 : FERSA-NKE BEARINGS NORTH AMERICA  CCA</option>' \
            ' <option value="00000515397-0825-PFI GROUP INC CCA">0825 - 00000515397 : PFI GROUP INC CCA</option>' \
            ' </select>'
    >>> expect = [{'account_no': '0825-00000503382', 'organization_title': 'FERSA-NKE BEARINGS NORTH AMERICA  CCA', 'account_req_param': '00000503382-0825-FERSA-NKE BEARINGS NORTH AMERICA  CCA'}, {'account_no': '0825-00000515397', 'organization_title': 'PFI GROUP INC CCA', 'account_req_param': '00000515397-0825-PFI GROUP INC CCA'}]  # noqa
    >>> actual = get_accounts_parsed_wo_balance(t)
    >>> actual == expect
    True

    >>> t = ' <div> ' \
        ' <label for="accountNumber">Cuenta:*&#160;</label> ' \
        ' 0825 - 00000503382 : FERSA-NKE BEARINGS NORTH AMERICA  CCA '\
        ' <input id="accountNumber" name="accountNumber" type="hidden" ' \
        ' value="00000503382-0825-FERSA-NKE BEARINGS NORTH AMERICA  CCA"/> ' \
        ' </div> '
    >>> expect = [{'account_no': '0825-00000503382', 'organization_title': 'FERSA-NKE BEARINGS NORTH AMERICA  CCA', 'account_req_param': '00000503382-0825-FERSA-NKE BEARINGS NORTH AMERICA  CCA'}]  # noqa
    >>> actual = get_accounts_parsed_wo_balance(t)
    >>> actual == expect
    True
    """
    accounts_parsed_wo_balance = []  # type: List[dict]
    # many accounts layout
    many = [m.groupdict() for m in re.finditer(
        r'(?si)<option\s+value="(?P<req_param>.*?)"[^>]*>(?P<account_no>[- \d]+)\s+:(?P<org_title>.*?)</option>',
        extract.re_first_or_blank('(?si)<select id="accountNumber".*?</select>', resp_text)
    )]
    # one account layout
    one = [m.groupdict() for m in re.finditer(
        r'(?si)</label>\s*(?P<account_no>[- \d]+)\s+:(?P<org_title>.*?)<input id="accountNumber"[^>]+'
        r'value="(?P<req_param>.*?)"',
        resp_text
    )]
    account_data_list = many + one
    for account_data in account_data_list:
        account_no = account_data['account_no']
        org_title = account_data['org_title']
        req_param = account_data['req_param']

        account_parsed_wo_balance = {
            'account_no': account_no.replace(' ', ''),  # '0825 - 00000503382' -> '0825-00000503382'
            'organization_title': org_title.strip(),
            'account_req_param': req_param
        }
        accounts_parsed_wo_balance.append(account_parsed_wo_balance)

    return accounts_parsed_wo_balance


def get_account_parsed(resp_text: str, account_parsed_wo_balance: dict) -> Optional[AccountParsed]:
    # Snd for Sabadell UK
    currency = (
            extract.re_first_or_blank(r'(?si)Divisa:.*?</span>(.*?)<', resp_text).strip()
            or extract.re_first_or_blank(r'(?si)Saldo actual:.*?</span>[.,\d]+&#160;([A-Z]+)<', resp_text)
    )
    if not (currency and len(currency) == 3):
        # Will handle as a wrong layout
        return None
    try:
        # From 'Saldo actual:&#160;</span>448,649.29&#160;USD<a href="javascript:getDetail()"'
        balance = float(extract.re_first_or_blank(r'(?si)Saldo actual:.*?</span>([.,\d]+)', resp_text).
                        replace(',', ''))

        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

        account_parsed = {
            'account_no': account_parsed_wo_balance['account_no'],
            'balance': balance,
            'account_type': account_type,
            'currency': currency,
            'organization_title': account_parsed_wo_balance['organization_title'],
        }
    except Exception as e:
        # Will handle as a wrong layout
        return None

    return account_parsed


def get_movements_parsed(resp_text: str, movement_date_fmt) -> List[MovementParsed]:
    movements_parsed = []  # type: List[MovementParsed]
    mov_htmls = re.findall('(?si)<tr.*?</tr>', resp_text)
    for mov_html in mov_htmls:
        cells = [c.strip() for c in re.findall('(?si)<td.*?>(.*?)</td>', mov_html)]
        if len(cells) != 6:
            continue
        # Necessary convert at this place because movs might have
        # new unknown format like m/d/Y
        # 08/30/2019 -> 20190830
        operation_date = date_funcs.convert_date_to_db_format(cells[0], movement_date_fmt)
        value_date = date_funcs.convert_date_to_db_format(cells[2], movement_date_fmt)
        descr = re.sub(r'\s\s+', '  ', cells[1])  # max 2 spaces
        amount = float(extract.remove_tags(cells[3].replace(',', '')))  # '372,168.37' -> 372168.37
        temp_balance = float(extract.remove_tags(cells[4].replace(',', '')))

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance,
        }

        movements_parsed.append(movement_parsed)

    return movements_parsed
