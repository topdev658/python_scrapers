from datetime import date
from typing import NamedTuple

# from dropdown
CorrespondenceAccountOption = NamedTuple('CorrespondenceAccountOption', [
    ('account_no', str),
    ('gcuenta_param', str),
    ('cuentaenvia_param', str),
    ('ibanorigen_param', str),
])

#     {
#       "FICHERO":"F0811192.Q43",
#       "EXTENSION":"Q43",
#       "LONGITUD":"0000410",
#       "FECHA":"12/08/2021"
#     }
N43FromList = NamedTuple('N43FromList', [
    ('fichero', str),  # "F0811192.Q43"
    ('longitud', str),  # "0000410"
    ('date', date),  # 30-07-2021
])
