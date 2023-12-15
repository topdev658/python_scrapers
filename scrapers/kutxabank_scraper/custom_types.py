from datetime import date
from typing import Dict, Optional, NamedTuple


class ReqAttrs:
    def __init__(self, url: str, req_data: Optional[Dict[str, str]], method: str):
        self.url = url
        self.req_data = req_data
        self.method = method


# filter options
AccountForCorrespondence = NamedTuple('AccountForCorrespondence', [
    ('account_no', str),
    ('req_param', str),
])

CompanyForN43 = NamedTuple('CompanyForN43', [
    ('title', str),  # 'SEGIMON ,DE PEDRAZA ,SANDRA'
    ('selection_value', str),  # 'formBuzonSeleccion:usuarios:_1'
    ('input_value', str)  # '01', '02'
])

N43FromList = NamedTuple('N43FromList', [
    ('date', date),
    ('type', str),  # 'AEB-43'
    ('descr', str),
    ('req_param', str),
])
