from datetime import datetime
from typing import List, Tuple
from urllib import parse as urlparse
from urllib.parse import SplitResult

from .custom_types import N43Parsed


def get_n43s_parsed_from_recepcion(resp_json: dict) -> List[N43Parsed]:
    """Parses 110_resp_recepcion_list.json"""
    n43s_parsed = []  # type: List[N43Parsed]
    for n43_dict in resp_json.get('files', []):
        # {
        #   "fileId": "3004000002015834",
        #   "statusCode": "01",
        #   "periodicity": "01",
        #   "lastPostDate": "2021-01-08",
        #   "startDate": "2021-01-08",
        #   "endDate": "2021-01-08",   #  '2022-04-21T00:00:00.000+02:00'
        #   "userPetition": "SCHEZIBANEZ",
        #   "account": {
        #     "id": "ES1800491864347070008790",
        #     "bankCode": "0049",
        #     "branchCode": "1864",
        #     "productTypeCode": "707",
        #     "contractCode": "0008790",
        #     "iban": "ES18",
        #     "controlDigit": "34",
        #     "accountNumber": "7070008790",
        #     "ccc": "004918647070008790",
        #     "accountNumberWithControlDigit": "00491864347070008790"
        #   }
        # },
        end_date = n43_dict['endDate'].split('T')[0]
        n43_parsed = N43Parsed(
            file_id_pre=n43_dict['fileId'],  # for req_n43_pre
            account_iban=n43_dict['account']['id'],
            operation_date=datetime.strptime(end_date, '%Y-%m-%d')
        )
        n43s_parsed.append(n43_parsed)
    return n43s_parsed


def get_accounts_for_n43_from_peticion(resp_json: dict) -> List[str]:
    """Parses dev_nv43/010_resp_accs.json
    :returns [account_iban]
    """
    #     {
    #       "company": "0075",
    #       "center": "3179",
    #       "product": "050",
    #       "number": "0074074",
    #       "id": "ES3000753179440500074074",
    #       "iban": "ES30",
    #       "controlDigit": "44",
    #       "description": "CREDITO NEGOCIO A TIPO FIJO",
    #       "balance": "0.00",
    #       "currency": "EUR",
    #       "ccc": "007531790500074074",
    #       "accountNumber": "0500074074",
    #       "accountNumberWithControlDigit": "00753179440500074074",
    #       "contractCode": "0074074",
    #       "productTypeCode": "050",
    #       "branchCode": "3179",
    #       "bankCode": "0075"
    #     }
    return [a['id'] for a in resp_json['accountList']]


def url_without_empty_get_params(url: str) -> str:
    """
    Drops params without vals like:
        &pagination.installationCode
        &pagination.recordNumber
        &pagination.account
    because they lead to server error.
    Web drops them too.
    """
    # SplitResult(
    # scheme='https',
    # hostname='empresas3.gruposantander.es',
    # netloc='empresas3.gruposantander.es:8080',
    # path='/paas/api/nwe-norm43-api/v1/file',
    # query='pagination.intervalNumber=1&pagination.recordNumber&...&pagination.statusCode=01',
    # fragment='')
    split = urlparse.urlsplit(url)  # type: SplitResult
    req_params = urlparse.parse_qsl(split.query)  # type: List[Tuple[str, str]]
    # Drop empty vals which lead to server err
    req_params_upd = {k: v for k, v in req_params if v}
    query_upd = urlparse.urlencode(req_params_upd)
    # Low-level SplitResult build to provide correct 'unsplit'
    split_upd = SplitResult(
        scheme=split.scheme,
        netloc=split.hostname,
        path=split.path,
        query=query_upd,
        fragment=split.fragment
    )  # noqa
    # url_upd_old = urlparse.urljoin(url, query_upd)
    url_upd = urlparse.urlunsplit(split_upd)
    return url_upd
