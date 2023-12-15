from .custom_types import AccountForN43
from typing import List, Tuple
import re
from custom_libs import extract


def get_accounts_for_n43(resp_text: str) -> Tuple[bool, List[AccountForN43]]:
    """
    Parses
    <select id="selectAccount" class="dato"  name="SELCTA"   maxlength=20 onChange="javascript:cambiarSeleccion()">
        <option value='30670141613305048823978CUENTAS CORRIENTES' > ES49 3067 0141 6133 0504 8823 | CUENTAS CORRIENTES | Euro </option>
    </select>
    """
    acc_select_html = extract.re_first_or_blank('(?si)<select id="selectAccount".*?<?/select>', resp_text)
    if not acc_select_html:
        return False, []
    accounts_for_n43 = []  # type: List[AccountForN43]
    # ['30670141613305048823978CUENTAS CORRIENTES', ...]
    accs_data = re.findall("<option value='(.*?)'[^>]+>(.*?)</option>", acc_select_html)  # type: List[Tuple[str, str]]
    for acc_data in accs_data:
        selcta_param = acc_data[0]
        acc_title = acc_data[1].strip()  # ES49 3067 0141 6133 0504 8823 | CUENTAS CORRIENTES | Euro
        fin_ent_account_id = acc_title.split('|')[0].replace(' ', '')  # ES4930670141613305048823
        account_for_n43 = AccountForN43(
            title=acc_title,
            fin_ent_account_id=fin_ent_account_id,
            selcta_param=selcta_param,  # '30670141613305048823978CUENTAS CORRIENTES'
            cuenta_param=selcta_param[:20],  # '30670141613305048823'
            divisa_param=selcta_param[20:23],  # '978'
        )
        accounts_for_n43.append(account_for_n43)
    return True, accounts_for_n43
