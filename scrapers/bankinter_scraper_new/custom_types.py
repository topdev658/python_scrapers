from typing import NamedTuple

#     {
#       "id": "c5cdxcDHDDfs",
#       "company": "ESOFITEC GLOBAL SOLUTIONS SL",
#       "byDefault": true,
#       "cif": "B25832965"
#     }
Contract = NamedTuple('Contract', [
    ('id', str),  # 'c5cdxcDHDDfs'
    ('org_title', str),  # 'ESOFITEC GLOBAL SOLUTIONS SL'
    ('cif', str)  # 'B25832965'
])
