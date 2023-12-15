from datetime import datetime
from typing import NamedTuple, Optional

Contract = NamedTuple('Contract', [
    ('org_title', str),  # "ECHEVARRI TURISMOS, S.A."
    ('id', str),  # "AU00011909"
    ('cif', str)  # "B95120259"
])

# from dropdown
AccountForCorrespondence = NamedTuple('AccountForCorrespondence', [
    ('account_no', str),  # "ES6030350238612380020003"
    ('position_id_param', str),  # "0", "10"
    ('alias', str),
])

CorrespondenceFromList = NamedTuple('CorrespondenceFromList', [
    ('type', str),  # 'EXTRACTOS DE CUENTA'
    ('account_no', str),  # from args
    ('date', datetime),
    ('amount', Optional[float]),  # from '-39,40'
    ('descr', str),  # 'ASISTENCIA A JUNTA', ''
    ('docid_param', str),  # "0", "1", ..
])
