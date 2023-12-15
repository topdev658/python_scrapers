import re
from typing import List
from datetime import datetime

from custom_libs import extract
from .custom_types import N43FromList


def get_n43s_from_list(resp_text: str) -> List[N43FromList]:
    n43s_from_list = []  # type: List[N43FromList]

    table_html = extract.re_first_or_blank('(?si)<table.*?</table>', resp_text)
    rows = re.findall('(?si)<tr.*?</tr>', table_html)
    for row in rows:
        cells = [c.strip() for c in re.findall('(?si)<td[^>]*>(.*?)</td>', row)]
        # table header
        if len(cells) < 4:
            continue
        link = extract.re_first_or_blank(
            r"(?si)href='(/htmlVersion[^']+accion=descargar[^']+formatoSel=0)'",
            row
        )
        file_date_str = cells[2]
        file_date = datetime.strptime(file_date_str, '%d/%m/%Y %H:%M').date()
        n43_from_list = N43FromList(
            date=file_date,
            link=link
        )
        n43s_from_list.append(n43_from_list)
    return n43s_from_list
