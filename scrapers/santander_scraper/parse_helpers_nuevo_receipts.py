from datetime import datetime
from typing import List, Optional

from custom_libs import convert
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import CorrespondenceDocParsed


def get_correspondence_from_list(
        resp_json: dict,
        org_title: str,
        logger: ScrapeLogger) -> List[CorrespondenceDocParsed]:
    """
    Parses
    {"correspondenceList": [
        {
          "documentId": "00003870",
          "documentCode": "00016076076660211",
          "documentType": "SCC_COMUNICADOS",
          "document": "PI_Ba379010001011737890f87e85000",
          "documentManagement": "SCConDemand",
          "description": "Extracto de cuenta",
          "date": "2020-07-23",
          "readIndicator": "N",
          "contract": {
            "company": "0049",
            "center": "6738",
            "product": "271",
            "number": "6180456",
            "id": "ES3000496738512716180456",
            "iban": "ES30",
            "controlDigit": "51",
            "accountNumber": "2716180456",
            "accountNumberWithControlDigit": "00496738512716180456",
            "ccc": "004967382716180456",
            "productTypeCode": "271",
            "branchCode": "6738",
            "contractCode": "6180456",
            "bankCode": "0049"
          }
        },
        # NO CONTRACT (account)!
        {
          "document": "PI_Ba39401000101176f541532737800",
          "date": "2021-01-13",
          "documentCode": "00016076545471073",
          "documentManagement": "SCConDemand",
          "documentId": "00003870",
          "documentType": "SCC_COMUNICADOS",
          "readIndicator": "N",
          "description": "Extracto integral de fondos"
        },
    ]}
    """
    corrs_from_list = []  # type: List[CorrespondenceDocParsed]
    try:
        for corr_data in resp_json['correspondenceList']:
            corr_date_str = corr_data['date']
            descr = corr_data['description']
            corr_type = corr_data['documentType']
            account_no = corr_data.get('contract', {}).get('id', '')
            corr = CorrespondenceDocParsed(
                account_no=account_no,
                type=corr_type,
                operation_date=datetime.strptime(corr_date_str, '%Y-%m-%d'),  # from "2020-07-23"
                value_date=None,
                descr=descr,
                amount=None,  # no amount available
                currency=None,
                extra=corr_data  # all data for pdf
            )
            corrs_from_list.append(corr)
    except Exception as e:
        # ASC
        logger.error("{}: can't get correspondence: HANDLED EXCEPTION: {}. RESPONSE:\n{}".format(
            org_title,
            e,
            resp_json
        ))
    return corrs_from_list


def get_amount_from_pdf_text(pdf_text: str) -> Optional[float]:
    """
    >>> get_amount_from_pdf_text('>> 228.797,40')
    228797.4
    """
    amount_str = extract.re_first_or_blank(r'>>\s*(-?\s?[0-9.,]+)', pdf_text)  # 228.797,40
    if not amount_str:
        return None
    return convert.to_float(amount_str)
