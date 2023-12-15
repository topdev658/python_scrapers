from datetime import datetime
from typing import List

from custom_libs import extract
from custom_libs import iban_builder
from project.custom_types import CorrespondenceDocParsed


def _get_account_no(account_no_raw: str) -> str:
    """
    >>> _get_account_no('20859917110330302477')
    'ES5920859917110330302477'
    >>> _get_account_no('')  # -a 24438
    ''
    >>> _get_account_no('09201203150019H000064')  # -a 19508
    '09201203150019H000064'
    """
    account_no = account_no_raw
    if len(extract.re_first_or_blank(r'\d+', account_no_raw)) == 20:
        account_no = iban_builder.build_iban('ES', account_no_raw)
    return account_no


def get_correspondence_from_list(resp_json: dict) -> List[CorrespondenceDocParsed]:
    corrs = []  # type: List[CorrespondenceDocParsed]
    for corr_dict in resp_json['todos']:
        """
        Parses
        {
          "codRefCifrado": "bqbutHuCpihwg912l26y0FMVyhs7cLfy7/F0m1U0aGGqx2UPh0mRJcsEGJ7qjbQA",
          "leido": false,
          "destacados": false,
          "agrupacion": null,
          "importe": 1147.99,
          "fecha": "2021-06-25T00:00:00",
          "contrato": "222657SDD000000001       ",
          "cuentaAsociada": "20859917110330302477",
          "descripcion": "RECIBO VARIOS",
          "accesoDupPapel": {
            "web": true,
            "cajero": true,
            "oficina": true
          },
          "accesoDupFax": {
            "web": true,
            "cajero": true,
            "oficina": true
          },
          "accesoDupMail": {
            "web": true,
            "cajero": true,
            "oficina": true
          },
          "accesoImpLocal": false
        }
        """
        amount = corr_dict['importe']
        account_no_raw = corr_dict['cuentaAsociada']
        account_no = _get_account_no(account_no_raw)
        # "2021-06-25T00:00:00" -> '2021-06-25'
        corr_date = datetime.strptime(corr_dict['fecha'].split('T')[0], '%Y-%m-%d')
        descr = corr_dict['descripcion']  # 'RECIBO VARIOS'
        corr_type = ''  # todo impl, no explicit data: AHORRO/PRESTAMOS
        corr = CorrespondenceDocParsed(
            type=corr_type,
            account_no=account_no,
            operation_date=corr_date,
            value_date=None,
            amount=amount,
            currency='EUR',
            descr=descr,
            extra={
                'cod_ref_param': corr_dict['codRefCifrado']
            }
        )
        corrs.append(corr)
    return corrs
