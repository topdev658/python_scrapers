import re
from datetime import datetime
from typing import Tuple, List

from custom_libs import extract
from .custom_types import N43FromList


def get_id_empresa_con_param(resp_text: str) -> Tuple[bool, str]:
    """Parses
    <select id="formBusqueda:idEmpresaCon" name="formBusqueda:idEmpresaCon"
    size="1"
    onfocus="onFocus(this.id,true);"
    onblur="onBlur(this.id,true);"
    onchange="setMensajeE...dEmpresaCon'} } )">
    <option value="6695841">UTE REBOREDO</option></select>
    """
    select_html = extract.re_first_or_blank(
        '(?si)<select id="formBusqueda:idEmpresaCon".*?</select>',
        resp_text
    )
    # Expecting only 1 option with company parameter (selected company/contract)
    options = re.findall(r'<option\s*value="(.*?)"', select_html)
    if len(options) != 1:
        return False, ''
    return True, options[0]


def get_n43s_from_list(resp_text: str) -> List[N43FromList]:
    """Parses dev_n43/40_resp_n43_filtered.html"""
    n43s_from_list = []  # type: List[N43FromList]
    table = extract.re_first_or_blank(
        r'(?si)<table[^>]+formBusqueda:dataTableFicheros.*?</table>\s*<div[^>]+id="formBusqueda:sDataFicheros"',
        resp_text
    )
    trs = [r[0] for r in re.findall(
        r'(?si)(<tr class="bg[^"]*".*?</tr>\s*)'
        r'((?=<tr class="bg)|(?=</tbody></table>\s*<div[^>]+id="formBusqueda:sDataFicheros"))',
        table
    )]
    for tr in trs:
        cells = [
            extract.text_wo_scripts_and_tags(row)
            for row in re.findall('(?si)<td.*?</td>', tr)
        ]
        n43_date = datetime.strptime(cells[0], '%d-%m-%Y').date()

        # ix=6 due to parsed 'service' rows with column names
        descr = cells[6].strip()  # CV210803.CSV / GE210803.Q43
        if not descr.endswith('.Q43'):
            # not a N43 file
            continue

        # <td><a id="formBusqueda:dataTableFicheros:0:idDescargarSow"
        # name="formBusqueda:dataTableFicheros:0:idDescargarSow"
        # href="/BEPRJ001/fileServlet?hash=0D665CB41C88FA857A958674BCF9DAAB" class="oculto">Descargar</a>
        link = extract.re_first_or_blank(
            r'<a[^>]+id="formBusqueda:dataTableFicheros:\d+:idDescargarSow"[^>]+href="(.*?)"',
            tr
        )
        n43_from_list = N43FromList(
            date=n43_date,
            descr=descr,
            link=link
        )
        n43s_from_list.append(n43_from_list)

    return n43s_from_list
