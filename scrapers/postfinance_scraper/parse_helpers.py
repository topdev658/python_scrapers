from typing import List

from custom_libs import extract
from project.custom_types import AccountParsed, MovementParsed


def get_token_question(resp_text: str) -> str:
    # 'id="challenge">92 781 184 </p>'
    return extract.re_first_or_blank('id="challenge">(.*?)</p>', resp_text)


def get_organization_title(resp_text: str) -> str:
    return ''


def get_accounts_parsed(resp_text: str) -> List[AccountParsed]:
    accounts_parsed = []  # type: List[AccountParsed]
    return accounts_parsed


def get_movements_parsed(resp_text: str) -> List[MovementParsed]:
    movements_parsed = []  # type: List[MovementParsed]
    return movements_parsed
