import re
from typing import List, Tuple
from .custom_types import AccountExtracted

from custom_libs import extract


def get_verification_token(resp_text: str) -> str:
    return extract.re_first_or_blank(
        r'(?si)name=__RequestVerificationToken type=hidden value=(.*?)>',
        resp_text
    ).strip()


def get_verification_token_account(resp_text: str) -> str:
    return extract.re_first_or_blank(
        r'name="__RequestVerificationToken" type="hidden" value="(.*?)"',
        resp_text
    ).strip()


def get_accounts_extracted(resp_text: str) -> List[AccountExtracted]:
    accounts = []  # type: List[AccountExtracted]
    find = r"""(?si)'accountNumber':'(.*?)','referencia':'(.*?)'}\)"><td>(.*?)<td>(.*?)<"""
    account_and_references = re.findall(find, resp_text)
    for account_no, reference, text, company in account_and_references:
        account = AccountExtracted(
            account_no=account_no,  # '0014347800'
            reference=reference,  # '0'
            account_alias=company  # 'SIG GIRONA'
        )
        accounts.append(account)
    return accounts
