import re
from typing import List

from custom_libs import extract


def get_account_names(resp_text: str) -> List[str]:
    select_html = extract.re_first_or_blank('(?si)<select name="accountdiv".*?</select>', resp_text)
    # ['2085/8428/18/0330033048 - C.CTE', ... ]
    account_names = re.findall('(?si)<option value="([^"]+)">', select_html)

    return account_names


def get_file_ids(resp_text: str) -> List[str]:
    file_ids = re.findall(
        r'(?si)name="checkdescargar" value="(\d+)"',  # 4907332
        resp_text
    )
    return file_ids


def get_file_name(resp_text: str) -> str:
    # 0;;394815_04301_20210216_18.sop
    file_name = extract.re_first_or_blank(
        r"manageResponse\('[^']+;;(.*?)'\);",
        resp_text
    )
    return file_name
