import re
from datetime import datetime
from typing import List, Optional

from custom_libs import convert
from custom_libs import extract
from custom_libs import iban_builder
from project.custom_types import CorrespondenceDocParsed,PDF_UNKNOWN_ACCOUNT_NO


def get_correspondence_from_list(resp_text: str) -> List[CorrespondenceDocParsed]:
    corrs_desc = []  # type: List[CorrespondenceDocParsed]
    # Contains nested correspondence table
    corr_table = extract.re_first_or_blank('(?si)form name=formulario.*?</form>', resp_text)
    trs = re.findall('(?si)<tr.*?</tr>', corr_table)
    for tr in trs:
        cells = re.findall('(?si)<td.*?</td>', tr)
        # Not a correspondence
        if len(cells) != 5:
            continue
        # Title
        if 'Fecha' in cells[2]:
            continue
        pdf_param = extract.re_first_or_blank('value="(.*?)"', cells[0])
        corr_date = datetime.strptime(extract.text_wo_scripts_and_tags(cells[1]), '%d/%m/%Y')  # 21/08/2020
        descr = extract.text_wo_scripts_and_tags(cells[2])  # Abono de Transferencia
        amount = None  # type: Optional[float]
        amount_str = extract.text_wo_scripts_and_tags(cells[3]).strip()  # 72.611,64
        if amount_str:
            amount = convert.to_float(amount_str)

        account_no_raw = extract.text_wo_scripts_and_tags(cells[4]).replace(' ', '')  # 21034749170034711977
        account_iban = account_no_raw
        if account_no_raw:
            try:
                account_iban = iban_builder.build_iban('ES', account_no_raw)
            except:
                pass
        else:
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
