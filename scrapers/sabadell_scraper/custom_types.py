from typing import NamedTuple

AccountFromDropdown = NamedTuple(
    'AccountFromDropdown', [
        ('idx', int),
        # IBAN: 'ES3500810085690002533764'
        ('account_no', str),
        ('org_title', str),
        # 'CUENTA RELACIÓN'
        # 'CUENTA EXPANSIÓN NEGOCIOS'
        # 'CUENTA EXPANSION NEGOCIOS PLUS'
        # 'CUENTA EN DIVISA GESTIONADA'
        # 'CUENTA CORRIENTE'
        ('account_type_raw', str),
        ('currency', str),
        ('balance', float)
    ]
)

AccountForCorrespondence = NamedTuple(
    'AccountForCorrespondence', [
        ('account_title', str),
        ('req_param', str)
    ]
)
