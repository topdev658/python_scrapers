from typing import List

from .custom_types import Contract


def get_contracts_from_nwe_v1(resp_json: dict) -> List[Contract]:
    """
    Parses
    {"logginContractList":[
    {"companyCif":"A17094715","companyName":"COMERCIAL MASOLIVER S.A.U.","contract":{"company":"0049","center":"3488","product":"520","number":"0000001","id":"004934885200000001","bankCode":"0049","branchCode":"3488","productTypeCode":"520","contractCode":"0000001"},"holderData":{"holderName":"33768612001"},"lastAccessDate":"2019-04-19-11.22.19.000000"},
    ]..}
    """
    contract_data_list = resp_json.get('contractList', []).get('logginContractList') or []
    contracts = [
        Contract(
            org_title=c['companyName'],
            details=c
        )
        for c in contract_data_list
    ]
    return contracts


def get_contracts(resp_json: dict) -> List[Contract]:
    """
    Parses
    {"logginContractList":[
    {"companyCif":"A17094715","companyName":"COMERCIAL MASOLIVER S.A.U.","contract":{"company":"0049","center":"3488","product":"520","number":"0000001","id":"004934885200000001","bankCode":"0049","branchCode":"3488","productTypeCode":"520","contractCode":"0000001"},"holderData":{"holderName":"33768612001"},"lastAccessDate":"2019-04-19-11.22.19.000000"},
    ]..}
    """
    contract_data_list = resp_json.get('contractList', {}).get('logginContractList') or []
    contracts = [
        Contract(
            org_title=c['companyName'],
            details=c
        )
        for c in contract_data_list
    ]
    return contracts
