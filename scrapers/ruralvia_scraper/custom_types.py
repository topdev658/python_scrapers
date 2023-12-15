from typing import NamedTuple, List

Contract = NamedTuple('Contract', [
    ('req_params_list', List[str]),  # ['[ST]58A3nnkn53PGrvRVshM2IRNspPwwXgU4LUxg6NDrSAw=', ...]
    ('org_title', str),
])


AccountForN43 = NamedTuple(
    'AccountForN43', [
        ('title', str),  # ES49 3067 0141 6133 0504 8823 | CUENTAS CORRIENTES | Euro
        ('fin_ent_account_id', str),  # ES4930670141613305048823 -- will calc from title
        ('selcta_param', str),  # '30670141613305048823978CUENTAS CORRIENTES'
        ('cuenta_param', str),  # '30670141613305048823'
        ('divisa_param', str),  # '978'
    ]
)

