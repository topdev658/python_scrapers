import re
from datetime import datetime
from typing import List

from custom_libs import extract
from .custom_types import ISMFileFromList, FilterOperation


def get_ism_files_from_list(resp_text: str, filter_operation: FilterOperation) -> List[ISMFileFromList]:
    """
    Parses
    <tr>
        <td align="middle" class="bgfila"><p class="txtdato">&nbsp;24/02/2021</p></td>
        <td align="middle" class="bgfila"><p class="txtdato">&nbsp;12243001.ISM</a></p></td>
        <td align="middle" class="bgfila"><p class="txtdato">&nbsp;Movimientos de Cuentas Personales&nbsp;</a></p>
        </td>

        <td align="middle" class="bgfila"><input type="Checkbox" name="lficheros"
                                                 id="@@07ACC92C42D22BDD2E181E6C1C3953035FA417A7"
                                                 value="0"></font></td>

    </tr>

    """
    ism_files_desc = []  # type: List[ISMFileFromList]

    # Historical ['21/05/2021', '15213001.ISM', 'Movimientos de Cuentas Personales', '']
    # Pending ['', '21/05/2021', '15213001.ISM', 'Movimientos de Cuentas Personales']
    date_cell_ix = 0 if filter_operation == FilterOperation.historical else 1
    title_cell_ix = 1 if filter_operation == FilterOperation.historical else 2
    trs = re.findall('(?si)<tr[^>]*>.*?</tr>', resp_text)
    for tr in trs:
        cells = [extract.text_wo_scripts_and_tags(td) for td in re.findall('(?si)<td[^>]*>.*?</td>', tr)]
        # <input type="Checkbox" name="lficheros" id="@@B29A05772EBF57ADD8F17ECAC9D4DFBB5D4BB622" value="0" class="sp1">
        ism_file_id = extract.re_first_or_blank(r'name="lficheros"\s+id\s*=\s*"(.*?)"', tr)
        ism_file_ix = extract.re_first_or_blank(r'name="lficheros"[^>]*value\s*=\s*"(.*?)"', tr)
        if not ism_file_id:
            continue
        ism_file_date = datetime.strptime(cells[date_cell_ix], '%d/%m/%Y').date()
        ism_file_title = cells[title_cell_ix]
        ism_file = ISMFileFromList(
            date=ism_file_date,
            title=ism_file_title,
            id=ism_file_id,
            ix=ism_file_ix,
        )
        ism_files_desc.append(ism_file)
    return ism_files_desc
