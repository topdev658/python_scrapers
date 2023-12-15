import re
from typing import List


def get_fin_ent_account_ids_for_n43(resp_text: str) -> List[str]:
    # ['01287611100001666001', ..., '01287611510008242001']
    fin_ent_account_ids = re.findall(
        r'(?si)<option value="(\d+)"',
        resp_text
    )
    return fin_ent_account_ids
