from collections import namedtuple
from typing import NamedTuple

ReceiptOption = namedtuple('ReceiptOption', [
    'descr_part',  # as str
    'req_params'  # as ReceiptReqParams
])

ReceiptReqParams = namedtuple('ReceiptReqParams', [
    'semana',  # '50'  (or 'A04' for various opts)
    'envio',  # '1548091' (or 'F008' for for various opts)
    'cuenta',  # '01287712500001871'
    'fecha',  # '20181213'
    'fecha_valor'  # '20181213'
])

Company = namedtuple('Company', [
    'url',
    'title'
])

AccountForCorrespondence = NamedTuple('AccountForCorrespondence', [
    ('account_displayed', str),  # 9426/14.000021.4 -- it's neither an IBAN, nor a fin_ent_account_id
    ('fin_ent_account_id', str)  # 01289426140000214 -- fin_ent_account_id
])
