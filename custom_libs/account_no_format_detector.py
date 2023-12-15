import re

from project.custom_types import ACCOUNT_NO_TYPE_IBAN, ACCOUNT_NO_TYPE_BBAN, ACCOUNT_NO_TYPE_UNKNOWN

__version__ = '2.0.0'

__changelog__ = """
2.0.0
account no type project integration 
"""


def detect_account_no_format(account_no: str):
    """
    >>> detect_account_no_format('ES9101825437600101504109')
    'IBAN'
    
    >>> detect_account_no_format('41189 00001 16010160904 28EUR')
    'BBAN'
    
    >>> detect_account_no_format('12345')
    'UNKNOWN'
    """
    patterns = {
        ACCOUNT_NO_TYPE_IBAN: '^\w{2}\d{22}$',             # 'ES9101825437600101504109'
        # https://www.ecbs.org/iban/france-bank-account-number.html
        ACCOUNT_NO_TYPE_BBAN: '^\d{5} \d{5} \d{11} \d{2}'  # '41189 00001 16010160904 28EUR'
    }

    for account_no_format, pattern in patterns.items():
        if re.findall(pattern, account_no):
            return account_no_format

    return ACCOUNT_NO_TYPE_UNKNOWN
