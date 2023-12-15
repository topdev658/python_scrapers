import re
from typing import List


def get_accounts_parsed_wo_balance(resp_text: str) -> List[dict]:
    """Parses
    <label for="accountNumber">Cuenta:*&#160;</label>

    <select id="accountNumber" name="accountNumber">
        <option id="accountNumber-1" value="-1">Seleccione una cuenta, por favor</option>
        <option value="00005440003-0800-EXEA VENTURES B.V.">0800 - 00005440003 : EXEA VENTURES B.V.</option>
        <option value="00005440026-0800-EXEA VENTURES B.V.">0800 - 00005440026 : EXEA VENTURES B.V.</option>
    </select>
    """
    accounts_parsed_wo_balance = []  # type: List[dict]

    # (account_req_param, account_no, organization_title)
    account_datas = re.findall(
        r'(?si)<option\s+value="(.*?)"[^>]*>([- \d]+)\s+:(.*?)</option>',
        resp_text
    )
    for account_data in account_datas:
        account_req_param, account_no, company_title = account_data

        account_parsed_wo_balance = {
            'account_no': account_no.replace(' ', ''),  # '0825 - 00000503382' -> '0825-00000503382'
            'organization_title': company_title.strip(),
            'account_req_param': account_req_param
        }
        accounts_parsed_wo_balance.append(account_parsed_wo_balance)

    return accounts_parsed_wo_balance
