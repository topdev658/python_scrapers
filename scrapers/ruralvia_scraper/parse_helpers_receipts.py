import re
from datetime import datetime
from typing import List, Tuple, Dict

from custom_libs import convert
from custom_libs import extract
from project.custom_types import CorrespondenceDocParsed


def get_correspondence_menu_url(resp_text: str, resp_url: str) -> str:
    """Parses
    010_resp_company.html
    <script>
    pintarTablaMenu('<a href="/isum/Main?ISUM_ID=menu&ISUM_SCR=groupScr&ISUM_CIPH=%2Fv6xbzpuIWg...">Buzón</a>');
    </script>
    """
    req_link = extract.get_link_by_text(resp_text, resp_url, 'Buzón')
    return req_link


def get_corr_all_accounts_param(resp_text: str) -> str:
    """Parses
    020_resp_corr_filter_form.html
    document.FORM_RVIA_0.listaCuentas.value = "30603001212070456427|30603001242317022925|30603001222279261925|";
    """
    # 30603001212070456427|30603001242317022925|30603001222279261925|
    all_accs_param = extract.re_first_or_blank(
        'document.FORM_RVIA_0.listaCuentas.value = "(.*?)";',
        resp_text
    )
    return all_accs_param


def check_corr_pagination_next_page(resp_text: str, next_page_ix: int) -> bool:
    """
    Parses
    <a class="pag" href="/isum/Main?ISUM_ID=portlets_area&ISUM_SCR=linkServiceScr&ISUM_CIPH=..."
    onClick="javascript:paginar('1');return false;" >2 - </a>
    The link is incorrect, use page_form_link instead
    Returns True if has next page
    """
    has_next = bool(extract.re_first_or_blank(
        r"""(?si)<a class="pag" href="([^"]+)" onClick="javascript:paginar\('{}'\)""".format(next_page_ix),
        resp_text
    ))
    return has_next


def get_corr_page_form_link_and_req_params(
        resp_text: str,
        corrs_per_page: int) -> Tuple[str, Dict[str, str]]:
    """:returns (corr_page_form_link, corr_page_form_req_params)"""
    # FROM
    # <INPUT type='hidden' name='codigoFormularioTotal' value="EXW0GPA1A01#PVO0ATA1B01#ACV0AFB1A01#ACV0HMA3A01#ACV0ADB1A01#ACV0AFB1A01#ACV0ANA1A01#PVO0ATA1B01#ACV0AFB1A01#ACV0AFB1A01#PVO0ATA1B01#ACV0AFB1A01#ACV0CJA1A01#LIQ0BDB4A01#ACV0AFB1A01#TRA0AMB4A01#PVO0ATA1B01#ACV0AFB1A01#KAR0EJA1A01#KAL0HOA1A01#EXW0GPA1A01#ACV0HMA3A01#ACV0ADB1A01#ACV0AFB1A01#KAR0EJA1A01#KAR0EJA1A01#EXW0GPA1A01#EXW0GPA1A01#KAL0HOA1A01#EXT0EXA1A01#PVO0ATA1B01#ACV0AFB1A01#EXT0GQA1A01#ACV0AFB1A01#PVO0ATA1B01#ACV0CJA1A01#LIQ0BDB4A01#ACV0AFB1A01#PVO0ATA1B01#KAR0EJA1A01#EXW0GPA1A01#ACV0HMA3A01#ACV0ADB1A01#ACV0AFB1A01#EXV0GOA1A01#PVO0ATA1B01#LIQ0BDB2A01#EXT0GQA1A01#KAL0HOA1A01#EXU0EYA1A01#EXT0EXA1A01#ACV0AFB1A01#EXT0GQA1A01#KAL0HOA1A01#EXT0EXA1A01#KAR0EJA1A01#KAL0HOA1A01#EXU0EYA1A01#EXU0EYA1A01#EXW0GPA1A01#PVO0ATA1B01#PVO0FGD1B01#ACV0CJA1A01#LIQ0BDB4A01#ACV0AFB1A01#TRA0AMB4A01#PVO0ATA1B01#TRA0AMB4A01#KAR0EJA1A01#KAR0EJA1A01#EXW0GPA1A01#ACV0HMA3A01#ACV0ADB1A01#ACV0AFB1A01#EXT0GQA1A01#EXT0GQA1A01#KAL0HOA1A01#EXT0EXA1A01#PVO0ATA1B01#EXU0EYA1A01#TRA0AMB4A01#KAR0GFA3A01#ACV0AFB1A01#KAR0EJA1A01#EXW0GPA1A01#PVO0ATA1B01#KAR0EJA1A01#TRA0AMB4A01#ACV0CJA1A01#ACV0CIA1A01#LIQ0BDB4A01#ACV0AFB1A01#"/>
    # <INPUT type='hidden' name='fechaDocumentoTotal' value="2020-10-08#2020-10-01#2020-09-30#2020-09-16#2020-09-16#2020-09-16#2020-09-07#2020-09-01#2020-08-29#2020-08-15#2020-08-06#2020-07-30#2020-07-21#2020-07-20#2020-07-15#2020-07-09#2020-07-02#2020-06-30#2020-06-25#2020-06-25#2020-06-24#2020-06-16#2020-06-16#2020-06-16#2020-06-10#2020-06-10#2020-06-09#2020-06-09#2020-06-08#2020-06-08#2020-06-01#2020-05-30#2020-05-28#2020-05-15#2020-05-04#2020-04-21#2020-04-20#2020-04-16#2020-04-02#2020-03-25#2020-03-20#2020-03-16#2020-03-16#2020-03-14#2020-03-09#2020-03-03#2020-02-29#2020-02-25#2020-02-25#2020-02-25#2020-02-25#2020-02-15#2020-02-12#2020-02-12#2020-02-12#2020-02-10#2020-02-10#2020-02-10#2020-02-10#2020-02-07#2020-02-03#2020-01-27#2020-01-21#2020-01-20#2020-01-16#2020-01-09#2020-01-02#2019-12-31#2019-12-24#2019-12-24#2019-12-24#2019-12-16#2019-12-16#2019-12-14#2019-12-03#2019-12-03#2019-12-03#2019-12-03#2019-12-02#2019-12-02#2019-11-28#2019-11-19#2019-11-16#2019-11-11#2019-11-07#2019-11-04#2019-10-28#2019-10-23#2019-10-22#2019-10-22#2019-10-20#2019-10-16#"/>
    # <INPUT type='hidden' name='idDocumentoTotal' value="ORACLE-08/10/2020-3060-2020-10-10-14-50-01-38-000018308-B09417932           -A4SPDF#ORACLE-01/10/2020-3060-2020-10-02-05-24-15-04-000315496-B09417932           -TERCIOSPDF#ORACLE-30/09/2020-3060-2020-10-02-05-24-15-04-000315497-B09417932           -TERCIOSPDF#ORACLE-16/09/2020-3060-2020-09-17-04-29-43-69-000043002-B09417932           -TERCIOSPDF#ORACLE-16/09/2020-3060-2020-09-17-04-29-43-69-000043001-B09417932           -TERCIOSPDF#ORACLE-16/09/2020-3060-2020-09-18-04-27-29-99-000029863-B09417932           -TERCIOSPDF#ORACLE-07/09/2020-3060-2020-09-08-04-53-17-12-000095079-B09417932           -TERCIOSPDF#ORACLE-01/09/2020-3060-2020-09-02-08-06-21-75-001081559-B09417932           -TERCIOSPDF#ORACLE-29/08/2020-3060-2020-09-02-08-06-21-75-001081560-B09417932           -TERCIOSPDF#ORACLE-15/08/2020-3060-2020-08-19-04-14-42-83-000099818-B09417932           -TERCIOSPDF#ORACLE-06/08/2020-3060-2020-08-07-06-41-30-57-000245644-B09417932           -TERCIOSPDF#ORACLE-30/07/2020-3060-2020-08-01-04-45-52-89-000105684-B09417932           -TERCIOSPDF#ORACLE-21/07/2020-3060-2020-07-22-04-20-56-72-000074123-B09417932           -TERCIOSPDF#ORACLE-20/07/2020-3060-2020-07-23-04-15-04-54-000068326-B09417932           -TERCIOSPDF#ORACLE-15/07/2020-3060-2020-07-18-04-18-50-27-000001421-B09417932           -TERCIOSPDF#ORACLE-09/07/2020-3060-2020-07-11-04-27-55-52-000086241-B09417932           -TERCIOSPDF#ORACLE-02/07/2020-3060-2020-07-03-06-18-11-18-000526185-B09417932           -TERCIOSPDF#ORACLE-30/06/2020-3060-2020-07-03-06-18-11-18-000526186-B09417932           -TERCIOSPDF#ORACLE-25/06/2020-3060-2020-06-27-04-20-21-41-000017018-B09417932           -TERCIOSPDF#ORACLE-25/06/2020-3060-2020-06-27-04-58-33-40-000008862-B09417932           -A4SPDF#ORACLE-24/06/2020-3060-2020-06-25-04-56-53-96-000004254-B09417932           -A4SPDF#ORACLE-16/06/2020-3060-2020-06-17-04-19-04-85-000096199-B09417932           -TERCIOSPDF#ORACLE-16/06/2020-3060-2020-06-17-04-19-04-85-000096198-B09417932           -TERCIOSPDF#ORACLE-16/06/2020-3060-2020-06-18-04-23-24-84-000069246-B09417932           -TERCIOSPDF#ORACLE-10/06/2020-3060-2020-06-12-04-19-49-91-000092571-B09417932           -TERCIOSPDF#ORACLE-10/06/2020-3060-2020-06-12-04-19-49-91-000092570-B09417932           -TERCIOSPDF#ORACLE-09/06/2020-3060-2020-06-10-09-45-49-39-000022049-B09417932           -A4SPDF#ORACLE-09/06/2020-3060-2020-06-10-09-45-49-39-000022048-B09417932           -A4SPDF#ORACLE-08/06/2020-3060-2020-06-10-09-45-49-39-000022051-B09417932           -A4SPDF#ORACLE-08/06/2020-3060-2020-06-10-09-45-49-39-000022050-B09417932           -A4SPDF#ORACLE-01/06/2020-3060-2020-06-02-05-37-19-69-000001233-B09417932           -TERCIOSPDF#ORACLE-30/05/2020-3060-2020-06-03-04-28-41-53-000089922-B09417932           -TERCIOSPDF#ORACLE-28/05/2020-3060-2020-05-30-04-28-30-17-000113090-B09417932           -TERCIOSPDF#ORACLE-15/05/2020-3060-2020-05-20-04-20-25-19-000077525-B09417932           -TERCIOSPDF#ORACLE-04/05/2020-3060-2020-05-05-07-03-09-34-000082918-B09417932           -TERCIOSPDF#ORACLE-21/04/2020-3060-2020-04-22-04-21-54-76-000061895-B09417932           -TERCIOSPDF#ORACLE-20/04/2020-3060-2020-04-23-04-17-16-58-000047604-B09417932           -TERCIOSPDF#ORACLE-16/04/2020-3060-2020-04-18-04-23-31-81-000033680-B09417932           -TERCIOSPDF#ORACLE-02/04/2020-3060-2020-04-03-11-29-50-01-000650421-B09417932           -TERCIOSPDF#ORACLE-25/03/2020-3060-2020-03-27-04-19-58-96-000061051-B09417932           -TERCIOSPDF#ORACLE-20/03/2020-3060-2020-03-24-04-41-38-41-000007967-B09417932           -A4SPDF#ORACLE-16/03/2020-3060-2020-03-22-20-10-14-20-000093577-B09417932           -TERCIOSPDF#ORACLE-16/03/2020-3060-2020-03-22-20-10-14-20-000093576-B09417932           -TERCIOSPDF#ORACLE-14/03/2020-3060-2020-03-18-04-19-43-20-000097398-B09417932           -TERCIOSPDF#ORACLE-09/03/2020-3060-2020-03-22-10-51-11-07-000017108-B09417932           -A4SPDF#ORACLE-03/03/2020-3060-2020-03-20-22-53-56-20-000482203-B09417932           -TERCIOSPDF#ORACLE-29/02/2020-3060-2020-03-20-22-53-56-20-000482204-B09417932           -TERCIOSPDF#ORACLE-25/02/2020-3060-2020-02-27-04-22-26-47-000010738-B09417932           -TERCIOSPDF#ORACLE-25/02/2020-3060-2020-02-27-04-55-43-07-000005205-B09417932           -A4SPDF#ORACLE-25/02/2020-3060-2020-02-27-04-55-43-07-000005204-B09417932           -A4SPDF#ORACLE-25/02/2020-3060-2020-02-27-04-55-43-07-000005203-B09417932           -A4SPDF#ORACLE-15/02/2020-3060-2020-02-19-04-22-47-93-000091869-B09417932           -TERCIOSPDF#ORACLE-12/02/2020-3060-2020-02-14-04-16-12-27-000084332-B09417932           -TERCIOSPDF#ORACLE-12/02/2020-3060-2020-02-14-04-39-07-27-000008654-B09417932           -A4SPDF#ORACLE-12/02/2020-3060-2020-02-14-04-39-07-27-000008653-B09417932           -A4SPDF#ORACLE-10/02/2020-3060-2020-02-12-04-45-39-88-000102682-B09417932           -TERCIOSPDF#ORACLE-10/02/2020-3060-2020-02-12-06-06-23-90-000010563-B09417932           -A4SPDF#ORACLE-10/02/2020-3060-2020-02-12-06-06-23-90-000010562-B09417932           -A4SPDF#ORACLE-10/02/2020-3060-2020-02-12-06-06-23-90-000010561-B09417932           -A4SPDF#ORACLE-07/02/2020-3060-2020-02-10-17-30-55-55-000032402-B09417932           -A4SPDF#ORACLE-03/02/2020-3060-2020-02-04-05-38-34-08-000198157-B09417932           -TERCIOSPDF#ORACLE-27/01/2020-3060-2020-01-28-05-04-04-25-000263243-B09417932           -TERCIOSPDF#ORACLE-21/01/2020-3060-2020-01-22-04-08-46-66-000011991-B09417932           -TERCIOSPDF#ORACLE-20/01/2020-3060-2020-01-23-05-28-45-54-000145796-B09417932           -TERCIOSPDF#ORACLE-16/01/2020-3060-2020-01-23-05-28-45-54-000145795-B09417932           -TERCIOSPDF#ORACLE-09/01/2020-3060-2020-01-13-18-50-35-12-000048452-B09417932           -TERCIOSPDF#ORACLE-02/01/2020-3060-2020-01-03-06-15-34-05-000281644-B09417932           -TERCIOSPDF#ORACLE-31/12/2019-3060-2020-01-03-06-15-34-05-000281645-B09417932           -TERCIOSPDF#ORACLE-24/12/2019-3060-2019-12-27-04-15-38-40-000024323-B09417932           -TERCIOSPDF#ORACLE-24/12/2019-3060-2019-12-27-04-15-38-40-000024322-B09417932           -TERCIOSPDF#ORACLE-24/12/2019-3060-2019-12-27-04-38-02-34-000006831-B09417932           -A4SPDF#ORACLE-16/12/2019-3060-2019-12-17-04-35-53-73-000060595-B09417932           -TERCIOSPDF#ORACLE-16/12/2019-3060-2019-12-17-04-35-53-73-000060594-B09417932           -TERCIOSPDF#ORACLE-14/12/2019-3060-2019-12-18-04-30-40-43-000104396-B09417932           -TERCIOSPDF#ORACLE-03/12/2019-3060-2019-12-05-04-43-43-16-000042032-B09417932           -TERCIOSPDF#ORACLE-03/12/2019-3060-2019-12-05-04-43-43-16-000042031-B09417932           -TERCIOSPDF#ORACLE-03/12/2019-3060-2019-12-05-05-54-35-98-000005709-B09417932           -A4SPDF#ORACLE-03/12/2019-3060-2019-12-05-05-54-35-98-000005708-B09417932           -A4SPDF#ORACLE-02/12/2019-3060-2019-12-03-07-52-27-30-000379548-B09417932           -TERCIOSPDF#ORACLE-02/12/2019-3060-2019-12-04-19-02-17-17-000108397-B09417932           -A4SPDF#ORACLE-28/11/2019-3060-2019-12-03-04-54-35-91-000029050-B09417932           -TERCIOSPDF#ORACLE-19/11/2019-3060-2019-11-21-04-22-08-19-000106426-B09417932           -TERCIOSPDF#ORACLE-16/11/2019-3060-2019-11-20-04-19-34-90-000085102-B09417932           -TERCIOSPDF#ORACLE-11/11/2019-3060-2019-11-13-14-35-38-15-000060278-B09417932           -TERCIOSPDF#ORACLE-07/11/2019-3060-2019-11-08-05-25-40-56-000007336-B09417932           -A4SPDF#ORACLE-04/11/2019-3060-2019-11-05-07-02-30-97-000106733-B09417932           -TERCIOSPDF#ORACLE-28/10/2019-3060-2019-10-30-04-34-22-37-000199698-B09417932           -TERCIOSPDF#ORACLE-23/10/2019-3060-2019-10-25-04-13-45-89-000026844-B09417932           -TERCIOSPDF#ORACLE-22/10/2019-3060-2019-10-23-04-20-37-84-000138807-B09417932           -TERCIOSPDF#ORACLE-22/10/2019-3060-2019-10-23-04-20-37-84-000138806-B09417932           -TERCIOSPDF#ORACLE-20/10/2019-3060-2019-10-23-04-20-37-84-000138808-B09417932           -TERCIOSPDF#ORACLE-16/10/2019-3060-2019-10-18-04-15-37-60-000090468-B09417932           -TERCIOSPDF#"/>
    # <INPUT type='hidden' name='visualizadoTotal' value="1#0#0#0#1#1#0#0#0#0#0#0#1#0#1#1#0#0#1#1#0#0#0#0#1#1#0#0#1#1#1#0#0#0#1#0#1#0#0#0#0#0#0#1#0#0#1#1#1#1#1#1#1#1#1#1#1#1#1#0#0#0#0#1#0#0#0#0#1#1#0#0#0#1#1#1#1#1#1#1#0#0#0#1#0#0#0#0#0#0#1#0#"/>
    codigo_total_param = extract.form_param(resp_text, 'codigoFormularioTotal')
    fecha_total_param = extract.form_param(resp_text, 'fechaDocumentoTotal')
    id_doc_total_param = extract.form_param(resp_text, 'idDocumentoTotal')
    visual_total_param = extract.form_param(resp_text, 'visualizadoTotal')
    # id_doc_param = extract.re_first_or_blank('document.FORM_RVIA_0.idDocumento.value = "(.*?)"', resp_corr_filtered.text)
    lista_chequeo_param = extract.re_first_or_blank('var StrListaChequeos = "(.*?)"', resp_text)
    lista_leido_param = extract.re_first_or_blank('var StrListaleido = "(.*?)"', resp_text)

    link, req_params = extract.build_req_params_from_form_html_patched(
        resp_text,
        'FORM_RVIA_0',
        is_ordered=True
    )
    # See req-resp 'OPEN CORR PAG2'
    # params from paginar() func
    req_params['ISUM_OLD_METHOD'] = 'POST'
    req_params['ISUM_ISFORM'] = 'true'
    req_params['campoPaginacionAux'] = 'ListaCorrespondencia'
    req_params['clavePagina'] = 'BDP_BZVIRTUAL_LISTA'
    # req_params['clavePaginaVolver'] = 'BDP_BZVIRTUAL_LISTA'
    req_params['campoPaginacion'] = 'ListaCorrespondencia'
    req_params['listaChequeo'] = lista_chequeo_param
    req_params['listaLeido'] = lista_leido_param
    req_params['codigoFormularioTotal'] = codigo_total_param
    req_params['fechaDocumentoTotal'] = fecha_total_param
    req_params['idDocumentoTotal'] = id_doc_total_param
    req_params['visualizadoTotal'] = visual_total_param
    req_params['primeraVez'] = '0'
    req_params['tamanioPagina'] = str(corrs_per_page)
    req_params['validationToken'] = extract.re_first_or_blank('<div data-token="(.*?)" id="tokenValid">', resp_text)

    return link, req_params


def get_correspondence_from_list(resp_text: str) -> List[CorrespondenceDocParsed]:
    corrs_desc = []  # type: List[CorrespondenceDocParsed]
    corrs_table = extract.re_first_or_blank('(?si)<div id="BODY_LISTA">.*?</table>', resp_text)
    trs = re.findall('(?si)<tr.*?</tr>', corrs_table)

    for tr in trs:
        cells = re.findall('(?si)<td[^>]*>(.*?)</td>', tr)

        if len(cells) != 7:
            continue

        # Header
        if cells[3] == 'Fecha':
            continue

        descr = extract.text_wo_scripts_and_tags(cells[6])
        corr_date = datetime.strptime(cells[3], '%d-%m-%Y')

        account_no = cells[4].replace(' ', '')
        amount_str = cells[5]
        amount = convert.to_float(amount_str) if amount_str else None

        # FROM
        # <a href="#" title="LIQUIDACIÓN DE ANTICIPOS IMPORT-EXPORT"
        # class="dato"
        # onclick="detalleDocumento('30603001212070456427',
        # 'ORACLE-14/10/2020-3060-2020-10-16-04-59-50-60-000009002-B09417932           -A4SPDF',
        # 'KAL0HOA1A01',
        # '2020-10-14',
        # '1',
        # 'LIQUIDACIÓN DE ANTICIPOS IMPORT-EXPORT',
        # '000009002', '0'  );return false;" >

        # VIA
        # ['30603001212070456427',
        # 'ORACLE-14/10/2020-3060-2020-10-16-04-59-50-60-000009002-B09417932           -A4SPDF',
        # 'KAL0HOA1A01',
        # '2020-10-14',
        # '1',
        # 'LIQUIDACIÓN DE ANTICIPOS IMPORT-EXPORT',
        # '000009002']

        # PRODUCES
        # idDocumento=ORACLE-14/10/2020-3060-2020-10-16-04-59-50-60-000009002-B09417932           -A4SPDF  <--
        # codigoFormulario=KAL0HOA1A01   <--
        # nomDocumento=LIQUIDACI%D3N DE ANTICIPOS IMPORT-EXPORT  <--
        # nDocum=000009002  <--
        # cuenta=30603001212070456427  <--

        pdf_params_list = re.findall("'(.*?)',", extract.re_first_or_blank(
            r"detalleDocumento\((.*?)\);return false;",
            tr
        ))
        pdf_params_dict = {
            'cuenta': pdf_params_list[0],
            'idDocumento': pdf_params_list[1],
            'codigoFormulario': pdf_params_list[2],
            'fecha': pdf_params_list[3],
            'nomDocumento': pdf_params_list[5],
            'nDocum': pdf_params_list[6]
        }

        corr = CorrespondenceDocParsed(
            type='',
            account_no=account_no,
            operation_date=corr_date,
            value_date=None,
            amount=amount,
            currency=None,
            descr=descr,
            extra={
                'pdf_params': pdf_params_dict,
            }
        )
        corrs_desc.append(corr)

    return corrs_desc
