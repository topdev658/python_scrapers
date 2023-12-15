from datetime import datetime
from typing import NamedTuple

Contract = NamedTuple('Contract', [
    # "COMERCIAL MASOLIVER S.A.U.
    ('org_title', str),
    # {"companyCif":"A17094715","companyName":"COMERCIAL MASOLIVER S.A.U.",
    # "contract":{"company":"0049","center":"3488","product":"520","number":"0000001",
    # "id":"004934885200000001","bankCode":"0049","branchCode":"3488",
    # "productTypeCode":"520","contractCode":"0000001"},
    # "holderData":{"holderName":"33768612001"},"lastAccessDate":"2019-04-19-11.22.19.000000"},
    ('details', dict)
])

OrganizationParsed = NamedTuple('OrganizationParsed', [
    ('title', str),
    ('personType', str),
    ('personCode', str),
])

# Contains necessary parts to build request,
# examples for ES2500491800112010632768
IbanData = NamedTuple('IbanData', [
    ('countryIban', str),  # ES
    ('dcIban', str),  # 25
    ('entity', str),  # 0049
    ('office', str),  # 1800
    ('dc', str),  # 11
    ('accountNumber', str)  # 2010632768
])

N43Parsed = NamedTuple('N43Parsed', [
    ('file_id_pre', str),  # for req_n43_pre
    ('operation_date', datetime),
    ('account_iban', str)
])


LeasingCompany = NamedTuple('LeasingCompany', [
    # from {"subsidiaries":[{"personType":"J","personCode":789925,"tipDoc":"S","cif":"A08072415","companyName":"FERROCARRILES Y TRANSPORTES SA"},{"personType":"J","personCode":2966947,"tipDoc":"S","cif":"A43000348","companyName":"COMPAÑIA REUSENSE DE AUTOMOVILES HISPANI"},{"personType":"J","personCode":802275,"tipDoc":"S","cif":"A08552770","companyName":"17 BAGES BUS S.A.U."},{"personType":"J","personCode":257216,"tipDoc":"S","cif":"A07284375","companyName":"32 EIVISSA BUS S.A."},{"personType":"J","personCode":4981649,"tipDoc":"S","cif":"B17834839","companyName":"MAYPE TAXIS Y MICROBUSES SL"}],"_links":{"self":{"href":"https://empresas3.gruposantander.es/paas/api/nwe-subsidiary-api/v1/subsidiary?otherSubsidiary=true&pagination.codperss=2951219&pagination.tipdoc=S&pagination.apellnom=25%20OSONA%20BUS%20S.A.U.&pagination.tipopel=J&pagination.coddocud=A08290538"}}}
    ('personCode', str),  # "789925"
    ('cif', str),  # "A08072415"
    ('companyName', str),  # "FERROCARRILES Y TRANSPORTES SA"
])
