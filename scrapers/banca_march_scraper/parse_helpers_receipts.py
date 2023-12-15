import re
from datetime import datetime
from typing import List

from custom_libs import convert
from custom_libs import extract
from project.custom_types import CorrespondenceDocParsed


def get_corespondence_from_list(resp_corr_text: str, pag_param: str) -> List[CorrespondenceDocParsed]:
    """Parses"""
    corrs_parsed = []  # type: List[CorrespondenceDocParsed]
    corr_table = extract.re_first_or_blank(
        '(?si)<table[^>]+id="tablaDocs".*?</table>',
        resp_corr_text
    )
    rows = re.findall('(?si)<tr.*?</tr>', corr_table)
    for row in rows:
        cells = re.findall('(?si)<td.*?</td>', row)
        if len(cells) < 7:
            continue
        # 201140040040977,201140040040977,0,61cfc10746f825c26e9ddd175633ad21
        # map to
        # <lista>
        #  <nodo>
        #   <codigo>201460020024921</codigo>
        #   <pdf>201460020024921</pdf>
        #   <tipo>0</tipo>
        #   <md5>11f3a75cd7b5dcd5008bf30fc7019b8d</md5>
        #   </nodo>
        #  </lista>
        detail_params = extract.re_first_or_blank('value="(.*?)"', cells[0]).split(',')
        amount_str = extract.text_wo_scripts_and_tags(cells[5])  # '-26.288,55 €' or ''
        currency = convert.to_currency_code(re.sub('[0-9.,]', '', amount_str).strip())

        corr = CorrespondenceDocParsed(
            type=extract.text_wo_scripts_and_tags(cells[2]),  # HECHO CORPORATIVO
            # 'ES6800610373110010090113'
            account_no=extract.text_wo_scripts_and_tags(cells[3]).replace(' ', ''),
            # from '26/05/2020'
            operation_date=datetime.strptime(extract.text_wo_scripts_and_tags(cells[4]), '%d/%m/%Y'),
            value_date=None,
            amount=convert.to_float(amount_str) if amount_str else None,
            currency=currency,
            descr=extract.text_wo_scripts_and_tags(cells[6]),  # 'ASISTENCIA A JUNTA' or ''
            # for
            # codigos: <lista>
            # 	<nodo><codigo>201460020024921</codigo><pdf>201460020024921</pdf><tipo>0</tipo><md5>11f3a75cd7b5dcd5008bf30fc7019b8d</md5></nodo>
            # </lista>
            extra={
                'codigo_param': detail_params[0],
                'pdf_param': detail_params[1],
                'tipo_param': detail_params[2],
                'md5_param': detail_params[3],
                'pag_param': pag_param
            }
        )
        corrs_parsed.append(corr)

    return corrs_parsed
