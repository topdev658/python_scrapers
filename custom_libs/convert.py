"""
All 'convert' functions
"""
from typing import Optional

__version__ = '1.6.3'

__changelog__ = """
1.6.3
to_float: use len() instead of __len__()
1.6.2
to_float: cover more cases '$ 101.091.204'
1.6.1
to_float: cover small vals
1.6.0
to_float: cover more cases
1.5.0
float_to_finstr
1.4.1
more CURRENCY_CODES
1.4.0
to_currency_code: all known currency codes as is
1.3.0
to_currency_code: more cases
1.2.0
to_currency_code
1.1.4
remove redundant exc info (use default again)
"""

CURRENCY_CODES = {
    'AED': 'AED',  # United Arab Emirates Dirham
    'AFN': 'AFN',  # Afghanistan Afghani
    'ALL': 'ALL',  # Albania Lek
    'AMD': 'AMD',  # Armenia Dram
    'ANG': 'ANG',  # Netherlands Antilles Guilder
    'AOA': 'AOA',  # Angola Kwanza
    'ARS': 'ARS',  # Argentina Peso
    'AUD': 'AUD',  # Australia Dollar
    'AWG': 'AWG',  # Aruba Guilder
    'AZN': 'AZN',  # Azerbaijan Manat
    'BAM': 'BAM',  # Bosnia and Herzegovina Convertible Mark
    'BBD': 'BBD',  # Barbados Dollar
    'BDT': 'BDT',  # Bangladesh Taka
    'BGN': 'BGN',  # Bulgaria Lev
    'BHD': 'BHD',  # Bahrain Dinar
    'BIF': 'BIF',  # Burundi Franc
    'BMD': 'BMD',  # Bermuda Dollar
    'BND': 'BND',  # Brunei Darussalam Dollar
    'BOB': 'BOB',  # Bolivia Bolíviano
    'BRL': 'BRL',  # Brazil Real
    'BSD': 'BSD',  # Bahamas Dollar
    'BTN': 'BTN',  # Bhutan Ngultrum
    'BWP': 'BWP',  # Botswana Pula
    'BYN': 'BYN',  # Belarus Ruble
    'BZD': 'BZD',  # Belize Dollar
    'CAD': 'CAD',  # Canada Dollar
    'CDF': 'CDF',  # Congo/Kinshasa Franc
    'CHF': 'CHF',  # Switzerland Franc
    'CLP': 'CLP',  # Chile Peso
    'CNY': 'CNY',  # China Yuan Renminbi
    'COP': 'COP',  # Colombia Peso
    'CRC': 'CRC',  # Costa Rica Colon
    'CUC': 'CUC',  # Cuba Convertible Peso
    'CUP': 'CUP',  # Cuba Peso
    'CVE': 'CVE',  # Cape Verde Escudo
    'CZK': 'CZK',  # Czech Republic Koruna
    'DJF': 'DJF',  # Djibouti Franc
    'DKK': 'DKK',  # Denmark Krone
    'DOP': 'DOP',  # Dominican Republic Peso
    'DZD': 'DZD',  # Algeria Dinar
    'EGP': 'EGP',  # Egypt Pound
    'ERN': 'ERN',  # Eritrea Nakfa
    'ETB': 'ETB',  # Ethiopia Birr
    'EUR': 'EUR',  # Euro Member Countries
    'FJD': 'FJD',  # Fiji Dollar
    'FKP': 'FKP',  # Falkland Islands (Malvinas) Pound
    'GBP': 'GBP',  # United Kingdom Pound
    'GEL': 'GEL',  # Georgia Lari
    'GGP': 'GGP',  # Guernsey Pound
    'GHS': 'GHS',  # Ghana Cedi
    'GIP': 'GIP',  # Gibraltar Pound
    'GMD': 'GMD',  # Gambia Dalasi
    'GNF': 'GNF',  # Guinea Franc
    'GTQ': 'GTQ',  # Guatemala Quetzal
    'GYD': 'GYD',  # Guyana Dollar
    'HKD': 'HKD',  # Hong Kong Dollar
    'HNL': 'HNL',  # Honduras Lempira
    'HRK': 'HRK',  # Croatia Kuna
    'HTG': 'HTG',  # Haiti Gourde
    'HUF': 'HUF',  # Hungary Forint
    'IDR': 'IDR',  # Indonesia Rupiah
    'ILS': 'ILS',  # Israel Shekel
    'IMP': 'IMP',  # Isle of Man Pound
    'INR': 'INR',  # India Rupee
    'IQD': 'IQD',  # Iraq Dinar
    'IRR': 'IRR',  # Iran Rial
    'ISK': 'ISK',  # Iceland Krona
    'JEP': 'JEP',  # Jersey Pound
    'JMD': 'JMD',  # Jamaica Dollar
    'JOD': 'JOD',  # Jordan Dinar
    'JPY': 'JPY',  # Japan Yen
    'KES': 'KES',  # Kenya Shilling
    'KGS': 'KGS',  # Kyrgyzstan Som
    'KHR': 'KHR',  # Cambodia Riel
    'KMF': 'KMF',  # Comorian Franc
    'KPW': 'KPW',  # Korea (North) Won
    'KRW': 'KRW',  # Korea (South) Won
    'KWD': 'KWD',  # Kuwait Dinar
    'KYD': 'KYD',  # Cayman Islands Dollar
    'KZT': 'KZT',  # Kazakhstan Tenge
    'LAK': 'LAK',  # Laos Kip
    'LBP': 'LBP',  # Lebanon Pound
    'LKR': 'LKR',  # Sri Lanka Rupee
    'LRD': 'LRD',  # Liberia Dollar
    'LSL': 'LSL',  # Lesotho Loti
    'LYD': 'LYD',  # Libya Dinar
    'MAD': 'MAD',  # Morocco Dirham
    'MDL': 'MDL',  # Moldova Leu
    'MGA': 'MGA',  # Madagascar Ariary
    'MKD': 'MKD',  # Macedonia Denar
    'MMK': 'MMK',  # Myanmar (Burma) Kyat
    'MNT': 'MNT',  # Mongolia Tughrik
    'MOP': 'MOP',  # Macau Pataca
    'MRU': 'MRU',  # Mauritania Ouguiya
    'MUR': 'MUR',  # Mauritius Rupee
    'MVR': 'MVR',  # Maldives (Maldive Islands) Rufiyaa
    'MWK': 'MWK',  # Malawi Kwacha
    'MXN': 'MXN',  # Mexico Peso
    'MYR': 'MYR',  # Malaysia Ringgit
    'MZN': 'MZN',  # Mozambique Metical
    'NAD': 'NAD',  # Namibia Dollar
    'NGN': 'NGN',  # Nigeria Naira
    'NIO': 'NIO',  # Nicaragua Cordoba
    'NOK': 'NOK',  # Norway Krone
    'NPR': 'NPR',  # Nepal Rupee
    'NZD': 'NZD',  # New Zealand Dollar
    'OMR': 'OMR',  # Oman Rial
    'PAB': 'PAB',  # Panama Balboa
    'PEN': 'PEN',  # Peru Sol
    'PGK': 'PGK',  # Papua New Guinea Kina
    'PHP': 'PHP',  # Philippines Peso
    'PKR': 'PKR',  # Pakistan Rupee
    'PLN': 'PLN',  # Poland Zloty
    'PYG': 'PYG',  # Paraguay Guarani
    'QAR': 'QAR',  # Qatar Riyal
    'RON': 'RON',  # Romania Leu
    'RSD': 'RSD',  # Serbia Dinar
    'RUB': 'RUB',  # Russia Ruble
    'RWF': 'RWF',  # Rwanda Franc
    'SAR': 'SAR',  # Saudi Arabia Riyal
    'SBD': 'SBD',  # Solomon Islands Dollar
    'SCR': 'SCR',  # Seychelles Rupee
    'SDG': 'SDG',  # Sudan Pound
    'SEK': 'SEK',  # Sweden Krona
    'SGD': 'SGD',  # Singapore Dollar
    'SHP': 'SHP',  # Saint Helena Pound
    'SLL': 'SLL',  # Sierra Leone Leone
    'SOS': 'SOS',  # Somalia Shilling
    'SPL*': 'SPL*',  # Seborga Luigino
    'SRD': 'SRD',  # Suriname Dollar
    'STN': 'STN',  # São Tomé and Príncipe Dobra
    'SVC': 'SVC',  # El Salvador Colon
    'SYP': 'SYP',  # Syria Pound
    'SZL': 'SZL',  # eSwatini Lilangeni
    'THB': 'THB',  # Thailand Baht
    'TJS': 'TJS',  # Tajikistan Somoni
    'TMT': 'TMT',  # Turkmenistan Manat
    'TND': 'TND',  # Tunisia Dinar
    'TOP': 'TOP',  # Tonga Pa'anga
    'TRY': 'TRY',  # Turkey Lira
    'TTD': 'TTD',  # Trinidad and Tobago Dollar
    'TVD': 'TVD',  # Tuvalu Dollar
    'TWD': 'TWD',  # Taiwan New Dollar
    'TZS': 'TZS',  # Tanzania Shilling
    'UAH': 'UAH',  # Ukraine Hryvnia
    'UGX': 'UGX',  # Uganda Shilling
    'USD': 'USD',  # United States Dollar
    'UYU': 'UYU',  # Uruguay Peso
    'UZS': 'UZS',  # Uzbekistan Som
    'VEF': 'VEF',  # Venezuela Bolívar
    'VND': 'VND',  # Viet Nam Dong
    'VUV': 'VUV',  # Vanuatu Vatu
    'WST': 'WST',  # Samoa Tala
    'XAF': 'XAF',  # Communauté Financière Africaine (BEAC) CFA Franc BEAC
    'XCD': 'XCD',  # East Caribbean Dollar
    'XDR': 'XDR',  # International Monetary Fund (IMF) Special Drawing Rights
    'XOF': 'XOF',  # Communauté Financière Africaine (BCEAO) Franc
    'XPF': 'XPF',  # Comptoirs Français du Pacifique (CFP) Franc
    'YER': 'YER',  # Yemen Rial
    'ZAR': 'ZAR',  # South Africa Rand
    'ZMW': 'ZMW',  # Zambia Kwacha
    'ZWD': 'ZWD',  # Zimbabwe Dollar

    '&dollar;': 'USD',
    'dolares': 'USD',
    'dólar': 'USD',
    'dólar usa': 'USD',
    '$': 'USD',
    '&euro;': 'EUR',
    '€': 'EUR',
    'euros': 'EUR',
    'euro': 'EUR',
    '&pound;': 'GBP',
    '£': 'GBP',
    'libra esterlina': 'GBP',
    'zloty polaco': 'PLN',
    '&#8364;': 'EUR'  # html code
}


def to_float(value_str: str) -> float:
    """
    Convert amounts as str to float

    don't call it to convert '+12001.34', use just float('+12001.34')

    >>> to_float("-249.549,83")
    -249549.83

    >>> to_float("+2.243,20")
    2243.2

    >>> to_float("-6,70 Euros")
    -6.7

    >>> to_float("1327,44+ EUR")
    1327.44

    >>> to_float("200,000.00")
    200000.0

    >>> to_float("100.01")
    100.01

    >>> to_float("100,01")
    100.01

    >>> to_float("$ 101.091.204")
    101091204.0

    >>> to_float("101.091.204,00")
    101091204.0

    """
    value_str_wo_chars = ''.join([l for l in value_str if l in '0123456789+-.,'])
    dot_ix = value_str_wo_chars.find('.')  # -1 if not found
    comma_ix = value_str_wo_chars.find(',')  # -1 if not found
    value_str_cleaned = value_str_wo_chars
    dot_back_ix = value_str_wo_chars.rfind('.')  # -1 if not found
    if comma_ix > -1:
        # '200.000,00' OR '6,70'
        if dot_ix < comma_ix:
            value_str_cleaned = value_str_wo_chars.replace('.', '').replace(',', '.')
        else:
            # '200,000.00'
            value_str_cleaned = value_str_wo_chars.replace(',', '')
    else:
        # 101.091.204 -> 101091204
        if dot_back_ix == len(value_str_wo_chars) - 4:  # three numbers after last dot
            value_str_cleaned = value_str_wo_chars.replace('.', '')

    # 1327,44+ -> +1327,44
    if value_str_cleaned.endswith('+') or value_str_cleaned.endswith('-'):
        value_str_cleaned = value_str_cleaned[-1] + value_str_cleaned[:-1]

    value_float = float(value_str_cleaned)
    return value_float


def float_to_finstr(val: float) -> str:
    """
    >>> float_to_finstr(1234.50)
    '1.234,50'
    """
    return '{:,.2f}'.format(val).replace(',', ';').replace('.', ',').replace(';', '.')


def escape_quote(str_: str) -> str:
    return str_.replace("'", "''")


def to_currency_code(currency_str: str) -> Optional[str]:
    """Returns 3-symbol currency code
    >>> to_currency_code('£')
    'GBP'
    >>> to_currency_code('&euro;')
    'EUR'
    >>> to_currency_code('USD')
    'USD'
    >>> to_currency_code(' Dolares  ')
    'USD'
    >>> to_currency_code('usd')
    >>> to_currency_code('UNKNOWN')
    """
    currency_str = currency_str.strip()
    currency_str_lower = currency_str.lower()
    if currency_str_lower in CURRENCY_CODES.keys():
        return CURRENCY_CODES[currency_str_lower]
    if len(currency_str) == 3 and currency_str.isupper():
        return currency_str
    return None
