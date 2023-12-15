import re
from collections import OrderedDict
from datetime import datetime
from typing import List, Dict

from custom_libs import convert
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import CorrespondenceDocParsed, DOCUMENT_TYPE_CORRESPONDENCE
from .custom_types import AccountForCorrespondence


def get_accounts_for_correspondence(resp_text: str, iban_country_code: str) -> List[AccountForCorrespondence]:
    accs_for_correspondence = []  # type: List[AccountForCorrespondence]
    accs_html = extract.re_first_or_blank(
        r'(?si)<select[^>]+id="formulario:idCuenta".*?</select>',
        resp_text
    )
    # <option selected="selected" value="">
    #     [Seleccione una cuenta]
    # </option>
    # <option value="20801206315500001480">ES39
    #     2080 1206 3155 0000 1480 - GAMBASTAR SL
    # </option>
    #    acc_option_htmls =
    accs_raw = re.findall('(?si)<option value="(.*?)">(.*?)</option>', accs_html)
    for acc_id_param, acc_alias_raw in accs_raw:
        if not acc_id_param or 'selected' in acc_id_param:
            continue
        # from
        # ES39 2080 1206 3155 0000 1480 - GAMBASTAR SL
        # 8199-000082-7 - GAMBASTAR SL
        # ES52 2080 1002 8439 4000 0044
        # or PT50017030000304019502620  -  LVTC SISTEMAS PORTUGAL, UNIPESSOAL LDA
        account_no = (extract.re_first_or_blank(r'^(' + iban_country_code + '[\s\d]+)', acc_alias_raw).strip()  # ES... or PT...
                      or extract.re_first_or_blank(r'^([-\d]+)', acc_alias_raw))  # 8199-000082-7
        acc_for_corr = AccountForCorrespondence(
            account_no=account_no.replace(' ', ''),
            account_alias=acc_alias_raw.strip(),
            id_cuenta_param=acc_id_param,
        )
        accs_for_correspondence.append(acc_for_corr)

    return accs_for_correspondence


def default_corr_filter_req_params() -> Dict[str, str]:
    req_params = OrderedDict([
        ('formulario:panelAyudaOpenedState', ''),
        ('formulario:idCuenta', ''),  # 20801206315500001480
        ('formulario:idCategoria', ''),
        ('formulario:idOpciones', 'RANGO'),
        ('formulario:fechaDesdeInputDate', ''),  # '03-06-2020'
        ('formulario:fechaDesdeInputCurrentDate', ''),  # '06/2020'
        ('formulario:fechaHastaInputDate', ''),  # 02-08-2020
        ('formulario:fechaHastaInputCurrentDate', ''),
        ('formulario:importeDesde', ''),
        ('formulario:importeHasta', ''),
        ('formulario:descripcion', ''),
        ('formulario_SUBMIT', '1'),
        ('formulario:_link_hidden_', ''),
        ('formulario:_idcl', ''),
        ('javax.faces.ViewState', ''),
    ])
    return req_params


def get_correspondence_from_list(resp_text: str,
                                 account_no: str,
                                 logger: ScrapeLogger) -> List[CorrespondenceDocParsed]:
    corrs_from_list_desc = []  # type: List[CorrespondenceDocParsed]
    corr_table = extract.re_first_or_blank(
        '(?si)<table id="formulario:tablaResultados".*?</table>',
        resp_text
    )
    trs = re.findall('(?si)<tr.*?</tr>', corr_table)
    for tr in trs:
        # Parses
        # <tr class="bgLightRow">
        #     <td class="centro td_5"><input type="checkbox"
        #            name="formulario:chk_idsDocumentos"
        #            id="formulario:chk_idsDocumentos"
        #            value="1327126866"
        #            onclick="setMensajeError(this.name,'','','mensaje',false);A4J.AJAX.Submit('_viewRoot','formulario',event,{'actionUrl':'/BEPRJ001/jsp/BEPR_eCorrespondencia_LST.faces?javax.portlet.faces.DirectLink=true','parameters':{'formulario:supportchk_idsDocumentos':'formulario:supportchk_idsDocumentos'} } )"
        #            onfocus="onFocus(this.name,false);"
        #            onblur="onBlur(this.name,false);"/></td>
        #     <td class="centro td_10 padding-05"><span
        #             class="negrita">27-07-2020</span></td>
        #     <td class="izquierda td_30 padding-05"><span class="negrita">RECIBO DE PRESTAMO</span>
        #     </td>
        #     <td class="centro td_10 padding-05"><span class="negrita">20801206383040017505   </span>
        #     </td>
        #     <td class="derecha td_10 padding-05"><span
        #             class="negrita">16.468,01</span></td>
        #     <td class="centro td_5 padding-05"><input type="hidden"
        #                                               id="formulario:tablaResultados:0:hiddenNumSecuencia"
        #                                               name="formulario:tablaResultados:0:hiddenNumSecuencia"
        #                                               value="1327126866"/><a
        #             href="#" id="formulario:tablaResultados:0:lnkMarcarDescargarDoc"
        #             name="formulario:tablaResultados:0:lnkMarcarDescargarDoc"
        #             onclick="A4J.AJAX.Submit('_viewRoot','formulario',event,{'actionUrl':'/BEPRJ001/jsp/BEPR_eCorrespondencia_LST.faces?javax.portlet.faces.DirectLink=true','oncomplete':function(request,event,data){recargarPaginaEcorrespondencia()},'parameters':{'formulario:tablaResultados:0:lnkMarcarDescargarDoc':'formulario:tablaResultados:0:lnkMarcarDescargarDoc'} } );return false;"><img
        #             src="/BEPRJ998/images/ico-pdf.png" alt="Descargar PDF"
        #             title="Descargar PDF"/></a></td>
        # </tr>
        try:
            if 'standardTable_Header' in tr:
                continue
            cells = re.findall('(?si)<td[^>]*>(.*?)</td>', tr)
            if len(cells) == 1:
                continue  # not a correspondence, ['No hay datos para los criterios de búsqueda seleccionados']
            corr_date_str = extract.remove_tags(cells[1])
            corr_date = datetime.strptime(corr_date_str, '%d-%m-%Y')
            descr = extract.remove_tags(cells[2])  # 'NOTIFICACION DE OPERACIONES'
            if len(cells) < 6:  # ABANCA PORTUGAL doesnt have amount field
                amount = None
                num_secuencia_line = cells[4]
            else:
                amount_str = extract.remove_tags(cells[4])
                amount = convert.to_float(amount_str) if amount_str else None
                num_secuencia_line = cells[5]
            # from
            # <input type="hidden" id="formulario:tablaResultados:0:hiddenNumSecuencia"
            # name="formulario:tablaResultados:0:hiddenNumSecuencia" value="1327126860" />
            # <a href="#" id="formulario:tablaResultados:0:lnkMarcarDescargarDoc"
            # name="formulario:tablaResultados:0:lnkMarcarDescargarDoc"
            # onclick="A4J.AJAX.Submit('_viewRoot','formulario',event,
            # {'actionUrl':'/BEPRJ001/jsp/BEPR_eCorrespondencia_LST.faces?javax.portlet.faces.DirectLink=true',
            # 'oncomplete':function(request,event,data){recargarPaginaEcorrespondencia()},
            # 'parameters':{'formulario:tablaResultados:0:lnkMarcarDescargarDoc':
            # 'formulario:tablaResultados:0:lnkMarcarDescargarDoc'} } );return false;">
            # <img src="/BEPRJ998/images/ico-pdf.png" alt="Descargar PDF" title="Descargar PDF" /></a>
            num_secuencia_param = extract.re_first_or_blank(r'value="([-\d+]+)"', num_secuencia_line)
            if not num_secuencia_param:
                logger.error(
                    "{}: get_correspondence_from_list: corresp (type={}, descr='{}'): "
                    "can't get num_secuencia_param. Skip".format(
                        account_no,
                        corr_date_str,
                        descr
                    )
                )
                continue
            ix = extract.re_first_or_blank(
                r'formulario:tablaResultados:(\d+):hiddenNumSecuencia',
                num_secuencia_line
            )
            corr = CorrespondenceDocParsed(
                type=DOCUMENT_TYPE_CORRESPONDENCE,
                account_no=account_no,
                operation_date=corr_date,
                value_date=None,
                amount=amount,
                currency=None,
                descr=descr,
                extra={
                    # it's not repeating from page to page
                    # (starts from ix=0 for page 1, ix=50 for page 2, so on)
                    'ix': ix,
                    'num_secuencia_param': num_secuencia_param,
                }
            )
            corrs_from_list_desc.append(corr)
        except Exception as e:
            logger.error(
                "{}: get_correspondence_from_list: "
                "can't parse corresp. HANDLED EXCEPTION: {}. Skip. Correspondence HTML:\n{}".format(
                    account_no,
                    e,
                    tr
                )
            )
            continue

    return corrs_from_list_desc
