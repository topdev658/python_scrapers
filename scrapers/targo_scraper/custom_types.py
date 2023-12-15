from typing import NamedTuple

AccountForCorrespondence = NamedTuple(
    'AccountForCorrespondence', [
        ('account_title', str),  # "0620000397 CUENTA CORRIENTE DE+USO+PRO+EN+USD+I+GAMBASTAR+SL"
        ('req_param', str),  # '02160585600620000397'
        ('fin_ent_account_id', str),  # from account_scraped '02160585600620000397USD'
    ]
)
