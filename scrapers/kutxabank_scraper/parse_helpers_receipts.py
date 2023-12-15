import re
from datetime import datetime
from typing import List, Tuple, Optional
from urllib.parse import unquote

from custom_libs import convert
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import CorrespondenceDocParsed
from .custom_types import AccountForCorrespondence


def get_accounts_for_correspondence(resp_text: str) -> List[AccountForCorrespondence]:
    """
    Parses
    for="formFiltro:SelectRadioMenuContratosPropios:_3">1410269441</label></span>
    see dev_corr/resp_corr_page.html
    """
    accs_for_corr_tuples = re.findall(
        '(?si)"(formFiltro:SelectRadioMenuContratosPropios[^"]+)">([^<]+)</label',
        resp_text
    )
    accs_for_corr = []  # type: List[AccountForCorrespondence]
    for tpl in accs_for_corr_tuples:
        # AccountForCorrespondence(
        #     account_no='2095 0556 90 3910413736',
        #     req_param='formFiltro:SelectRadioMenuContratosPropios:_0'
        # )
        acc = AccountForCorrespondence(
            account_no=tpl[1],
            req_param=tpl[0]
        )
        accs_for_corr.append(acc)
    return accs_for_corr


def get_req_pdf_link(resp_text: str) -> str:
    # /NASApp/BesaideNet2/Gestor/1151446408_25_09_2020_391041373.pdf
    # ?PRESTACION=buzon&FUNCION=buzon
    # &ACCION=pdf&envio=1151446408&codigoEntidad=01&fechaDocumento=2020-09-25
    # &tipoProducto=KT&codigoContrato=391041373&tipoDocumento=I
    # &tipoProdMatriz=KT&contratoMatriz=391041373
    req_link = extract.re_first_or_blank(
        '<iframe[^>]+id="mainFrame"[^>]+src="(.*?)"',
        resp_text
    )
    return req_link


def parse_corr_tag_tr(
        ix: int,
        row: str,
        logger: ScrapeLogger) -> Optional[CorrespondenceDocParsed]:
    """
    Parses dev_corr/corr_row_tag_tr.html
    """
    corr_date_str = extract.re_first_or_blank(
        r'id="formCorrespondencia:datosCorrespondencia:\d+:fecha">(.*?)</span>',
        row
    )

    if not corr_date_str:
        return None

    # For the 1st row we always expect corr_date_str, so corr_date never be None
    corr_date = datetime.strptime(corr_date_str, '%d/%m/%Y')

    # 3910413736 - last 10 digits of account
    account_no = extract.re_first_or_blank(
        r'id="formCorrespondencia:datosCorrespondencia:\d+:concepto">(.*?)</span>',
        row
    )
    reg_exp_descr = 'id="formCorrespondencia:datosCorrespondencia:\d+:j_id249">(.*?)</span>'
    descr = extract.remove_tags(extract.re_first_or_blank(
        r'{}'.format(reg_exp_descr),
        row
    ))
    amount_currency_str = extract.re_first_or_blank(
        r'id="formCorrespondencia:datosCorrespondencia:\d+:importe">(.*?)</span>',
        row
    )

    amount = convert.to_float(amount_currency_str) if amount_currency_str else None
    currency = convert.to_currency_code(amount_currency_str.split()[-1]) if amount_currency_str else None

    # LINK: /NASApp/BesaideNet2/Gestor?PRESTACION=buzon&amp;FUNCION=buzon&amp;
    # ACCION=marco&amp;envio=1145158728&amp;codigoEntidad=01&amp;fechaDocumento=2020-09-02&amp;
    # tipoProducto=KT&amp;codigoContrato=391041373&amp;codigoControl=6&amp;tipoDocumento=I&amp;
    # tipoProdMatriz=KT&amp;contratoMatriz=391041373&amp;duplicado=true
    req_pdf_link_raw = unquote(extract.re_first_or_blank(
        r'(?si)id="formCorrespondencia:datosCorrespondencia:\d+:urlDocs[^>]+value="(.*?)"',
        row
    ))

    if not (descr and req_pdf_link_raw):
        logger.error("{}: corr ix={}: can't parse description using reg_exp: {}".format(
                account_no,
                ix,
                reg_exp_descr
            ))
        return None

    link_doc_param = 'formCorrespondencia:datosCorrespondencia:{}:link_doc'.format(ix)
    req_params = {
        'ice.submit.partial': 'false',
        'ice.event.target': 'formCorrespondencia:datosCorrespondencia:{}:j_id245'.format(ix),
        'ice.event.captured': link_doc_param,
        'formCorrespondencia': 'formCorrespondencia',
        'formCorrespondencia:datosCorrespondencia:{}:urlDocs'.format(ix): req_pdf_link_raw,
        'formCorrespondencia:_idcl': link_doc_param,
        'ice.focus': link_doc_param,
        'javax.faces.RenderKitId': 'ICEfacesRenderKit',
    }

    corr = CorrespondenceDocParsed(
        type='',
        account_no=account_no,
        operation_date=corr_date,
        value_date=None,
        amount=amount,
        currency=currency,
        descr=descr,
        extra={
            'urldocs': req_pdf_link_raw,
            'req_pre_pdf_params': req_params,
        },
    )
    return corr


def parse_corr_tag_span(
        ix: int,
        row: str,
        corr_prev_page: CorrespondenceDocParsed,
        logger: ScrapeLogger) -> Optional[CorrespondenceDocParsed]:
    """
    From the update list only,
    parses dev_corr/corr_row_tag_span.html

    :param ix: index of the row
    :param row: update data
    :param corr_prev_page: the correspondence doc with the same
                index from the previous page
                (Kutxa sends only diffs, so we need it to fill absent data)
    """

    # Get explicitly from url path: fechaDocumento=2020-11-23&
    corr_date_str = extract.re_first_or_blank('fechaDocumento=(.*?)&', row)
    if not corr_date_str:
        return None
    corr_date = datetime.strptime(corr_date_str, '%Y-%m-%d')

    # 3910413736 - last 10 digits of account, from url to details
    account_no = extract.re_first_or_blank(
        r'<!\[CDATA\[formCorrespondencia:datosCorrespondencia:\d+:concepto]].*?<!\[CDATA\[(.*?)]]',
        row
    )
    if not account_no:
        if ':concepto' not in row:
            account_no = corr_prev_page.account_no  # fill absent
        else:
            return None  # parse err, maybe tag_tr would be suitable

    reg_exp_descr = '<!\[CDATA\[formCorrespondencia:datosCorrespondencia:\d+:j_id\d.*?]].*?<!\[CDATA\[(.*?)]]'
    descr = extract.remove_tags(extract.re_first_or_blank(
        r'{}'.format(reg_exp_descr),
        row
    ))
    if not descr:
        logger.error("{}: corr ix={}: can't parse description using reg_exp: {}".format(
                account_no,
                ix,
                reg_exp_descr
            ))
        return None

    amount_currency_str = extract.re_first_or_blank(
        r'<!\[CDATA\[formCorrespondencia:datosCorrespondencia:\d+:importe]].*?<!\[CDATA\[(.*?)]]',
        row
    )
    if not amount_currency_str:
        if ':importe' not in row:
            amount_currency_str = '{} {}'.format(corr_prev_page.amount, corr_prev_page.currency)  # fill
        else:
            return None  # parse err

    amount = convert.to_float(amount_currency_str) if amount_currency_str else None
    currency = convert.to_currency_code(amount_currency_str.split()[-1]) if amount_currency_str else None

    # LINK: /NASApp/BesaideNet2/Gestor?PRESTACION=buzon&amp;FUNCION=buzon&amp;ACCION=marco&amp;envio=1145158728&amp;codigoEntidad=01&amp;fechaDocumento=2020-09-02&amp;tipoProducto=KT&amp;codigoContrato=391041373&amp;codigoControl=6&amp;tipoDocumento=I&amp;tipoProdMatriz=KT&amp;contratoMatriz=391041373&amp;duplicado=true
    req_pdf_link_raw = unquote(extract.re_first_or_blank(
        r'<!\[CDATA\[formCorrespondencia:datosCorrespondencia:\d+:urlDocs]].*?'
        r'<attribute name="value"><!\[CDATA\[(.*?)]]',
        row
    ))

    link_doc_param = 'formCorrespondencia:datosCorrespondencia:{}:link_doc'.format(ix)
    req_params = {
        'ice.submit.partial': 'false',
        'ice.event.target': 'formCorrespondencia:datosCorrespondencia:{}:j_id245'.format(ix),
        'ice.event.captured': link_doc_param,
        'formCorrespondencia': 'formCorrespondencia',
        'formCorrespondencia:datosCorrespondencia:{}:urlDocs'.format(ix): req_pdf_link_raw,
        'formCorrespondencia:_idcl': link_doc_param,
        'ice.focus': link_doc_param,
        'javax.faces.RenderKitId': 'ICEfacesRenderKit',
    }

    if not req_pdf_link_raw:
        return None

    corr = CorrespondenceDocParsed(
        type='',
        account_no=account_no,
        operation_date=corr_date,
        value_date=None,
        amount=amount,
        currency=currency,
        descr=descr,
        extra={
            'urldocs': req_pdf_link_raw,
            'req_pre_pdf_params': req_params,
        },
    )
    return corr


def get_correspondence_from_list(
        logger: ScrapeLogger,
        resp_text: str,
        account_no) -> Tuple[bool, List[CorrespondenceDocParsed]]:
    """:returns (is_success, corrs)"""
    corrs_parsed = []  # type: List[CorrespondenceDocParsed]

    # Checks if the next page button is available to confirm that there are more pages to scrape
    next_page_marker = re.findall(
        '<a class="iceCmdLnk boton_redondeado".*?id="formCorrespondencia:siguiente"',
        resp_text
    )
    end_pagination = False if next_page_marker else True

    rows = re.findall(
        r'(?si)<tr[^>]+id="formCorrespondencia:datosCorrespondencia:\d+">.*?'
        r'id="formCorrespondencia:datosCorrespondencia:\d+:urlDocs.*?</td></tr>',
        resp_text
    )
    for ix, row in enumerate(rows):
        corr_opt = parse_corr_tag_tr(ix, row, logger)
        if corr_opt is None:
            logger.error("{}: corr ix={}: can't parse corr from row: {}".format(
                account_no,
                ix,
                row
            ))
            continue

        corrs_parsed.append(corr_opt)

    if not corrs_parsed:
        if ('No hay documentos que cumplan los criterios de busqueda especificados' in resp_text
                or 'No disponemos datos para su consulta. Modifique los criterios de busqueda' in resp_text):
            return True, [], True
        else:
            return False, [], True

    return True, corrs_parsed, end_pagination


def get_correspondence_from_updated_list(
        logger: ScrapeLogger,
        resp_text: str,
        account_no: str,
        corrs_prev_page: List[CorrespondenceDocParsed]) -> Tuple[bool, List[CorrespondenceDocParsed]]:
    """
    Sends only diffs to corr from the previous page (!), use it for pages > 1
    :param logger: the logger
    :param resp_text: response text
    :param account_no: there is no explicit account_no at the page
    :param corrs_prev_page: corrs from previous page to fill absent data of the update
    """
    corrs_parsed = []  # type: List[CorrespondenceDocParsed]

    # Checks if the last page marker is available to confirm that there are NO more pages to scrape
    # see dev_corr/resp_corr_last_page.html
    last_page_marker = '<![CDATA[icePnlGrdCol panelBotonesCol buzonConsulta_columna_siguientes]]>'
    end_pagination = last_page_marker in resp_text

    # Some correspondence have no dates
    rows = re.findall(
        r'(?si)<tr[^>]+id="formCorrespondencia:datosCorrespondencia:\d+">.*?'
        r'id="formCorrespondencia:datosCorrespondencia:\d+:urlDocs.*?</td></tr>',
        resp_text
    )

    if not rows:
        rows = re.findall(
            r'(?si)<update address="formCorrespondencia:datosCorrespondencia.*?'
            r'formCorrespondencia:datosCorrespondencia:\d+:urlDocs.*?</update>',
            resp_text
        )

    for ix, row in enumerate(rows):
        # Both tags are possible (-a 23004, see dev_corr/resp_corr_filtered_span_tr_tags.html)
        corr_opt = parse_corr_tag_span(ix, row, corrs_prev_page[-1], logger) or parse_corr_tag_tr(ix, row, logger)
        if corr_opt is None:
            logger.error("{}: corr ix={}: can't parse corr from row: {}".format(
                account_no,
                ix,
                row
            ))
            continue
        corrs_parsed.append(corr_opt)
    if not corrs_parsed:
        return False, []

    return True, corrs_parsed, end_pagination
