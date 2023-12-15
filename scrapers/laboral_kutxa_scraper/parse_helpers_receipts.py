from datetime import datetime
from typing import List

from project.custom_types import CorrespondenceDocParsed
from custom_libs import convert
from .custom_types import AccountForCorrespondence


def get_accounts_for_correspondence(resp_json: dict) -> List[AccountForCorrespondence]:
    """
    Parses
    {
      "cuentas": [
        {
          "alias": "SUPER CUENTA EMPRESA",
          "id": "0",
          "numero": "ES6030350238612380020003"
        },
        ...
        ]
    }
    """
    accounts_for_corr = []  # type: List[AccountForCorrespondence]
    for account_dict in resp_json['cuentas']:
        acc = AccountForCorrespondence(
            account_no=account_dict['numero'],  # IBAN
            position_id_param=account_dict['id'],
            alias=account_dict['alias']
        )
        accounts_for_corr.append(acc)
    return accounts_for_corr


def get_correspondence_from_list(resp_json: dict, account_no: str) -> List[CorrespondenceDocParsed]:
    """
    Parses
    {
      "documentos": [
        {
          "cuenta": {
            "alias": "SUPER CUENTA EMPRESA",
            "numero": "2380020003"
          },
          "fecha": "2020-07-15T10:00:00Z",
          "origen": "REMESAS DE IMPORTACION                                                                              ",
          "tipo": "Operaciones extranjeros",
          "total": {
            "cantidad": 92400.00,
            "moneda": "EUR"
          },
          "visto": false,
          "docid": "0"
        },
    ...
    ]
    """
    corrs_from_list = []  # type: List[CorrespondenceDocParsed]
    for corr_dict in resp_json['documentos']:
        amount = corr_dict['total']['cantidad']
        currency = convert.to_currency_code(corr_dict['total']['moneda'])
        descr = corr_dict['origen'].strip()
        corr_type = corr_dict['tipo']
        corr_date = datetime.strptime(corr_dict['fecha'].split('T')[0], '%Y-%m-%d')
        dicid_param = corr_dict['docid']
        corr = CorrespondenceDocParsed(
            type=corr_type,
            account_no=account_no,
            operation_date=corr_date,
            value_date=None,
            amount=amount,
            currency=currency,
            descr=descr,
            extra={
                'docid_param': dicid_param
            }
        )
        corrs_from_list.append(corr)
    return corrs_from_list
