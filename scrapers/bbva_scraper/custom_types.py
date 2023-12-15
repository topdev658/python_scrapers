from datetime import date
from enum import Enum
from typing import NamedTuple

# from dropdown
AccountForCorrespondence = NamedTuple('AccountForCorrespondence', [
    # from <option value="0@EUR0182 2351 41 0201507277">0182 2351 41 0201507277 EUR   &nbsp;</option>
    ('account_no', str),  # 'ES2001822351410201507277', use iban_builder
    ('req_param', str),  # 0@EUR0182 2351 41 0201507277
    ('title', str),  # '0182 2351 41 0201507277 EUR'
    ('ix', str),  # '0'
    ('currency', str),  # EUR
])

ISMFileFromList = NamedTuple('ISMFileFromList', [
    ('date', date),
    ('title', str),
    ('id', str),
    ('ix', str)
])


class FilterOperation(Enum):
    pending = 'BHOpRecSeleccionarFicheroPendiente'
    historical = 'BHOpRecSeleccionarFicheroHistorico'


LeasingCompany = NamedTuple('LeasingCompany', [
    # from {"businesses":[{"id":"201ES0182001236615","businessDocuments":[{"businessDocumentType":{"id":"NIF"},"documentNumber":"B08405268","country":{"id":"ES"},"isPreferential":false,"name":"BARCELONA BUS S.L."
    ('id', str),  # "201ES0182001236615"
    ('cif', str),  # "B08405268"
    ('name', str),  # "BARCELONA BUS S.L."
])