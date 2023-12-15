import re
from datetime import datetime
from typing import List, Tuple, Dict

from custom_libs import extract
from .custom_types import CompanyForN43, N43FromList

__version__ = '1.4.0'
__changelog__ = """
1.4.0
added get_table_from_html_resp: get html or xml with the list of files parsing multiple responses
1.3.0
added get_single_company_title: get company title without users on 'Recepción'
get_n43s_from_list__table_tag: calculates index of columns in the table to parse rows
1.2.0
get_n43s_from_list__table_tag
get_n43s_from_list__tr_tags
get_n43s_from_list__incremental_updates
1.1.0
get_n43s_from_list_updates
"""


def get_companies_for_n43_from_recepcion_tab(resp_text: str) -> List[CompanyForN43]:
    """
    <div class="icePnlGrp normal" id="formBuzonSeleccion:usuariosdivMenuRadio1">
    <span><input id="formBuzonSeleccion:usuarios:_1"
                 name="formBuzonSeleccion:usuarios"
                 onblur="setFocus(&#39;&#39;);"
                 onclick="setFocus(this.id);submitComboCuentas(form, this, event);"
                 onfocus="setFocus(this.id);"
                 onkeypress="setFocus(this.id);submitComboCuentas(form, this, event);Ice.util.radioCheckboxEnter(form,this,event);"
                 onmousedown="setFocus(this.id);activarClick(form, this, event);"
                 type="radio" value="02"/><label class="iceSelOneRb menuRadio"
                                                 for="formBuzonSeleccion:usuarios:_1">SEGIMON ,DE PEDRAZA ,SANDRA</label></span>
    </div>
    """
    # can be <input checked="checked" id=...
    found = re.findall(
        r'<input[^>]+id="(formBuzonSeleccion:usuarios:_\d+)"[^>]+value="(.*?)"[^>]+>'
        r'<label[^>]+for="formBuzonSeleccion:usuarios:_\d+">(.*?)<',
        resp_text
    )  # type: List[Tuple[str, str, str]]
    companies_for_n43 = [
        CompanyForN43(
            title=title,
            selection_value=selection_value,  # 'formBuzonSeleccion:usuarios:_1'
            input_value=input_value  # '01', '02', ...
        ) for (selection_value, input_value, title) in found
    ]
    return companies_for_n43


def get_selected_company_for_n43_selection_value(resp_text: str) -> str:
    """Used for validation"""
    sel_value = extract.re_first_or_blank(
        r'<input checked="checked" id="(formBuzonSeleccion:usuarios:_\d+)"',
        resp_text
    )
    return sel_value


def get_single_company_title(resp_text: str) -> str:
    """Get the company title to process n43 files when there is no user in 'Recepcion'"""
    company_title = extract.re_first_or_blank(
        r'<label class="iceOutLbl" id="formMenuLateral:j_id\d{3}">(.*?)</label>',
        resp_text
    )
    return company_title


def get_table_from_html_resp(resp_text: str) -> str:
    """Get html or xml with the list of files parsing multiple responses

    Cases:
        20_resp_recepcion__32255_lorena.html (ficheros_buzon_detalle.iface),
        30_resp_comp_n43_selected__32255_estefania.xml (send-receive-updates),
        20_resp_recepcion_without_users.html (no 'Usuario' column)"""
    table_html = extract.re_first_or_blank(
        '(?si)<table[^>]+buzon_detalle_tabla_ficheros.*?</table>',
        resp_text
    )
    if not table_html:
        # Case 30_resp_comp_n43_selected__19602_gaminde_iñigo.xml
        table_html = extract.re_first_or_blank(
            '(?si)<update address="formFicherosBuzon:datosBuzon" tag="table">.*?</update>',
            resp_text
        )
    return table_html


def get_n43s_from_list__table_tag(resp_text: str) -> List[N43FromList]:
    """Parses
    20_resp_recepcion__32255_lorena.html (ficheros_buzon_detalle.iface),
    30_resp_comp_n43_selected__32255_estefania.xml (send-receive-updates)
    AND 20_resp_recepcion_without_users.html (no 'Usuario' column)
    'table' tag
    Calculates index of columns to parse the rows
    """
    n43s_from_list = []  # type: List[N43FromList]
    table_html = get_table_from_html_resp(resp_text)
    if not table_html:
        return n43s_from_list
    trs = re.findall('(?si)<tr.*?</tr>', table_html)
    ix = 0
    for tr in trs:
        ths = [extract.text_wo_scripts_and_tags(th) for th in re.findall('(?si)<th[^>]*>(.*?)</th>', trs[0])]
        tds = [extract.text_wo_scripts_and_tags(td) for td in re.findall('(?si)<td[^>]*>(.*?)</td>', tr)]
        if len(tds) < 7:
            if ths[0] == 'Usuario':
                ix = 1
            continue  # not a file N43 line info
        file_type = tds[ix+2]  # 'AEB-43'
        descr = tds[ix+3]
        created_date_str = tds[ix+1]  # 24/06/2021
        created_date = datetime.strptime(created_date_str, '%d/%m/%Y').date()
        req_param = extract.re_first_or_blank(r'formFicherosBuzon:datosBuzon:\d+:link_descargar', tr)

        n43_from_list = N43FromList(
            date=created_date,
            type=file_type,  # 'AEB-43' or other
            descr=descr,
            req_param=req_param  # formFicherosBuzon:datosBuzon:0:link_descargar
        )
        n43s_from_list.append(n43_from_list)
    return n43s_from_list


def get_n43s_from_list__tr_tags(resp_text: str) -> List[N43FromList]:
    """Parses 20_resp_recepcion_updates.xml
    (no 'table', only 'tr' tags)
    """
    n43s_from_list = []  # type: List[N43FromList]
    updates = re.findall(r'(?si)<update address="formFicherosBuzon:datosBuzon:\d+" tag="tr">.*?</update>', resp_text)
    for row in updates:
        tds = [extract.text_wo_scripts_and_tags(td) for td in re.findall('(?si)<td[^>]*>(.*?)</td>', row)]
        if len(tds) < 8:
            continue  # not a file info
        file_type = tds[3]  # 'AEB-43'
        descr = tds[4]
        created_date_str = tds[2]  # 24/06/2021
        created_date = datetime.strptime(created_date_str, '%d/%m/%Y').date()
        req_param = extract.re_first_or_blank(r'formFicherosBuzon:datosBuzon:\d+:link_descargar', row)

        n43_from_list = N43FromList(
            date=created_date,
            type=file_type,  # 'AEB-43' or other
            descr=descr,
            req_param=req_param  # formFicherosBuzon:datosBuzon:0:link_descargar
        )
        n43s_from_list.append(n43_from_list)
    return n43s_from_list


def get_n43s_from_list__incremental_updates(resp_text: str, n43s_from_list_prev: List[N43FromList]) -> List[
    N43FromList]:
    """Parses incremental update
    (see 30_resp_comp_n43_selected__32255_del_castillo_part_after_lorena.xml)
    In case if there is no html data in the received xml update,
    then we'll be using incremental update for the previously extracted n43s
    neither 'table' nor 'tr' tags
    """
    # FOR the previous HTML
    # <tr class="iceDatTblRow buzon_detalle_tabla_ficherosRow buzon_detalle_texto_tabla2n" id="formFicherosBuzon:datosBuzon:1">
    #     <td class="iceDatTblCol buzon_detalle_tabla_ficherosCol buzon_detalle_columna_usuario"><span class="iceOutTxt" id="formFicherosBuzon:datosBuzon:1:usuarioval">08</span></td>
    #     <td class="iceDatTblCol buzon_detalle_tabla_ficherosCol buzon_detalle_columna_referencia"><span class="iceOutTxt" id="formFicherosBuzon:datosBuzon:1:referenciaval">210200</span></td>
    #     <td class="iceDatTblCol buzon_detalle_tabla_ficherosCol buzon_detalle_columna_fechaEnvio"><span class="iceOutTxt" id="formFicherosBuzon:datosBuzon:1:fechaenvioval">01/07/2022</span></td>
    #     <td class="iceDatTblCol buzon_detalle_tabla_ficherosCol buzon_detalle_columna_tipoAEB"><span class="iceOutTxt" id="formFicherosBuzon:datosBuzon:1:tipoaebval">AEB-43</span></td>
    #     <td class="iceDatTblCol buzon_detalle_tabla_ficherosCol buzon_detalle_columna_descripcion"><div class="icePnlGrp" id="formFicherosBuzon:datosBuzon:1:j_id119"><span class="iceOutTxt" id="formFicherosBuzon:datosBuzon:1:descripcionval">diario. 30/06/2022 - 30/06/2022. 9116704518</span></div></td>
    #     <td class="iceDatTblCol buzon_detalle_tabla_ficherosCol buzon_detalle_columna_tamano"><span class="iceOutTxt" id="formFicherosBuzon:datosBuzon:1:tamanoval">1.230</span></td>
    # UPDATES ARE
    #     <update address="formFicherosBuzon:datosBuzon:1:usuarioval" tag="span">
    #         <attribute name="class"><![CDATA[iceOutTxt]]></attribute>
    #         <attribute name="id"><![CDATA[formFicherosBuzon:datosBuzon:1:usuarioval]]></attribute>
    #         <content><![CDATA[01]]></content>
    #     </update>
    #     <update address="formFicherosBuzon:datosBuzon:1:referenciaval" tag="span">
    #         <attribute name="class"><![CDATA[iceOutTxt]]></attribute>
    #         <attribute name="id"><![CDATA[formFicherosBuzon:datosBuzon:1:referenciaval]]></attribute>
    #         <content><![CDATA[210199]]></content>
    #     </update>
    #     <update addr

    # Only for incremental update.
    # If there are html tags here, then it's not incremental update and it must be parsed before
    if '<tr' in resp_text:
        return []

    n43s_from_list = []  # type: List[N43FromList]
    for row_ix, n43_from_list_prev in enumerate(n43s_from_list_prev):
        # ['usuarioval', 'referenciaval', 'fechaenvioval', 'tipoaebval', 'descripcionval', 'tamanoval']
        row_updates = {}  # type: Dict[str, str]  # extracted updates
        for attr in ['fechaenvioval', 'tipoaebval', 'descripcionval']:
            q = 'formFicherosBuzon:datosBuzon:{}:{}'.format(row_ix, attr)
            val = extract.re_first_or_blank(
                r'(?si)<update address="{}" tag="span".*?<content><!\[CDATA\[(.*?)]]></content>'.format(q),
                resp_text
            )
            row_updates[attr] = val
        n43_from_list = N43FromList(
            date=row_updates['fechaenvioval'] or n43_from_list_prev.date,
            type=row_updates['tipoaebval'] or n43_from_list_prev.type,
            descr=row_updates['descripcionval'] or n43_from_list_prev.descr,
            req_param='formFicherosBuzon:datosBuzon:{}:link_descargar'.format(row_ix)
        )
        n43s_from_list.append(n43_from_list)
    return n43s_from_list


def get_n43_file_link(resp_text: str) -> str:
    file_link = extract.re_first_or_blank(
        "'(/NASApp/BesaideNet2/Gestor[?]PRESTACION=ficheros.*?)'",
        resp_text
    )
    return file_link
