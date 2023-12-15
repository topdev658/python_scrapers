from collections import namedtuple
from datetime import date
from typing import NamedTuple

AccountByCompany = namedtuple('AccountByCompany', ['account_scraped', 'company'])

Company = NamedTuple('Company', [
    ('title', str),
    ('idx', int),
    ('idcl_param', str)
])

# from dropdown
AccountForCorrespondence = NamedTuple('AccountForCorrespondence', [
    ('account_no', str),  # "ES6030350238612380020003"
    ('id_cuenta_param', str),  # "20801206315500001480"
    # for debugging
    # 'ES39 2080 1206 3155 0000 1480 - GAMBASTAR SL'
    # 8199-000082-7 - GAMBASTAR SL
    ('account_alias', str),
])

N43FromList = NamedTuple('N43FromList', [
    ('date', date),  # 30-07-2021
    ('descr', str),  # CV210729.CSV
    ('link', str),  # /BEPRJ001/fileServlet?hash=D194BDF1CD39D85FC467D125FFB03403
])

from typing import NamedTuple

ContractGoAbanca = NamedTuple('ContractGoAbanca', [
    ('org_title', str),  # "PIXELWARE S.A."
    ('profile_id_param', str),  # 320245622402
])

