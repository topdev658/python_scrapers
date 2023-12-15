from typing import NamedTuple


AccountFromDropdown = NamedTuple('AccountFromDropdown', [
    ('fin_ent_account_id', str),
    ('currency', str),
    ('product_code', str),  # "0232-0105-00-0029493443" to build IBAN
    ('codigo_insitucion_param', str),
    ('divisa_institucion_param', str),  # EUR
    ('institucion_collectiva_param', str),  # '5358217'
    ('tipo_cuenta_param', str),  # 'AG'
])
