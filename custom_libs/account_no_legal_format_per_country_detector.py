from project.custom_types import ACCOUNT_NO_TYPE_IBAN, ACCOUNT_NO_TYPE_UNKNOWN

country_to_format_map = {
    'ESP': [ACCOUNT_NO_TYPE_IBAN, ACCOUNT_NO_TYPE_UNKNOWN],
    'FRA': [ACCOUNT_NO_TYPE_IBAN],
    'PER': [ACCOUNT_NO_TYPE_UNKNOWN],
    'BRA': [ACCOUNT_NO_TYPE_UNKNOWN],
    'CHL': [ACCOUNT_NO_TYPE_UNKNOWN],
    'DOM': [ACCOUNT_NO_TYPE_UNKNOWN],
    'PRT': [ACCOUNT_NO_TYPE_IBAN],
    # Allow non-IBAN format for Sabadell UK
    'GBR': [ACCOUNT_NO_TYPE_IBAN, ACCOUNT_NO_TYPE_UNKNOWN],
    'GRC': [ACCOUNT_NO_TYPE_IBAN],
    'USA': [ACCOUNT_NO_TYPE_UNKNOWN],
    'CHE': [ACCOUNT_NO_TYPE_IBAN],  # Switzerland
    'ARG': [ACCOUNT_NO_TYPE_IBAN],
}

__version__ = '2.12.0'

__changelog__ = """
2.12.0
ESP allow ACCOUNT_NO_TYPE_UNKNOWN
2.11.0
ARG
2.10.0
dict of lists of allowed formats
CBR: allow IBAN and UNKNOWN (for Sabadell UK)
2.9.0
CHE
2.8.0
USA
2.7.0
GRC
2.6.0
GBR
2.5.0
Portugal: allow IBAN
2.4.0
Dominican Republic: allow UNKNOWN account type format 
2.3.0
Chile: allow UNKNOWN account type format
2.2.0
Brasil: allow UNKNOWN account type format 
2.1.0
Peru: allow UNKNOWN account type format 
2.0.0
custom_types integrated
"""


def is_legal_format_for_country(country_code: str, account_no_format: str):
    """
    >>> is_legal_format_for_country('ESP', ACCOUNT_NO_TYPE_IBAN)
    True

    >>> is_legal_format_for_country('ESP', ACCOUNT_NO_TYPE_UNKNOWN)
    False

    >>> is_legal_format_for_country('FRA', ACCOUNT_NO_TYPE_IBAN)
    True

    >>> is_legal_format_for_country('GBR', ACCOUNT_NO_TYPE_IBAN)
    True

    >>> is_legal_format_for_country('GBR', ACCOUNT_NO_TYPE_UNKNOWN)
    True

    >>> is_legal_format_for_country('UNKNOWN_COUNTRY', ACCOUNT_NO_TYPE_UNKNOWN)
    False

    """
    is_legal = account_no_format in country_to_format_map.get(country_code, [])
    return is_legal
