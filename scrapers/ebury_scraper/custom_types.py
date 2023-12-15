from typing import NamedTuple

CurrencyBalance = NamedTuple('CurrencyBalance', [
    ('currency', str),
    ('balance', float)
])

# From currency_accounts
AccountForMT940 = NamedTuple('AccountForMT940', [
    ('currency', str),  # 'EUR'
    ('currency_account_id', int),  # 528032
    ('fin_ent_account_id', str)  # '8845da84-0c66-b7e5-ba2a-709fad5676f1'
])

# From
#     clients.push({
#         id: 'EBPCLI427344',
#         text: 'Surexport UK Limited',
#         email: 'online.desk@ebury.com',
#         phone: '+44 (0) 207 197 2421',
#         disabled: false
#     });
Contract = NamedTuple('Contract', [
    ('contract_id', str),  # 'EBPCLI427344'
    ('contract_name', str)  # 'Surexport UK Limited'
])
