import re
from typing import Tuple, List
from custom_libs import extract


def get_account_nos_for_n43(resp_text: str) -> Tuple[bool, List[str]]:
    """
    Parse
    <select id="cuenta" name="peticionSelected.cuentaCargo" style="width: 250px">
        <option value="ES0420381830136000255776">ES0420381830136000255776</option>
        ...
        <option value="ES6520381046506000576275">ES6520381046506000576275</option>
        ...
    </select>
    """
    select_html = extract.re_first_or_blank('(?si)<select id="cuenta".*?</select>', resp_text)
    if not select_html:
        return False, []

    account_nos = re.findall('<option value="(.*?)">', select_html)
    return True, account_nos
