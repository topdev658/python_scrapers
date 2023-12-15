from datetime import date
from typing import NamedTuple

AccountsDropdownPageData = NamedTuple('AccountsDropdownPageData', [
    ('is_foreign_currency', bool),
    ('contrato_li_class', str),
    ('contrato_link_text', str),
    ('saldo_link_class', str),
    ('saldo_link_text', str)
])

N43FromList = NamedTuple('N43FromList', [
    ('date', date),
    ('link', str)
])
