from datetime import datetime
from typing import List, Optional

from project.custom_types import CorrespondenceDocParsed, PDF_UNKNOWN_ACCOUNT_NO


def get_correspondence_from_list(resp_json: dict) -> List[CorrespondenceDocParsed]:
    """
    Parses dev_corr_202207/10_resp_corr_filtered.json
    "correspondencias": [
    {
      "idCorrespondencia": "3283106685",
      "claveRelacionada": "",
      "tipoCorrespondencia": "U",
      "asunto": "CAMBIO TIPO INTERÉS VARIABLE",
      "fecha": "2022-06-24T00:00:01",
      "leido": "S",
      "papelera": "N",
      "borrado": "N"
    },
    ...
    ]
    """
    corrs_desc = []  # type: List[CorrespondenceDocParsed]
    for corr_dict in resp_json['correspondencias']:
        pdf_param = corr_dict['idCorrespondencia']
        corr_date = datetime.strptime(corr_dict['fecha'].split('T')[0], '%Y-%m-%d')  # from "2022-06-24T00:00:01"
        descr = corr_dict['asunto']  # "CAMBIO TIPO INTERÉS VARIABLE"
        # No amount, no account info in metadata
        amount = None  # type: Optional[float]
        # Unknown account, don't use blank to avoid wrong bindings to saved accs.
        # Also, this val is used as the correspondence doc folder
        account_iban = PDF_UNKNOWN_ACCOUNT_NO

        corr = CorrespondenceDocParsed(
            type='',
            account_no=account_iban,
            operation_date=corr_date,
            value_date=None,
            amount=amount,
            currency=None,
            descr=descr,
            extra={
                'pdf_param': pdf_param
            }
        )
        corrs_desc.append(corr)

    return corrs_desc
