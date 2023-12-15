from typing import NamedTuple

# Generic form of account info appropriate for this scraper
AccountExtracted = NamedTuple('AccountExtracted', [
    ('account_no', str),  # 0014347800
    ('reference', str),  # '0'
    ('account_alias', str)  # 'SIT GIRONA'
])
