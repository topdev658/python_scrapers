import random
import time
import traceback
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import urljoin

from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    CorrespondenceDocScraped, ScraperParamsCommon, CorrespondenceDocParsed, DBOrganization, PDF_UNKNOWN_ACCOUNT_NO
)
from . import parse_helpers
from . import parse_helpers_receipts
from .custom_types import AccountForCorrespondence
from .kutxa_scraper import KutxaScraper

__version__ = '3.7.0'
__changelog__ = """
3.7.0
download_correspondence: 
    deleted checked_corr_for_account to download all available correspondence
    implemented logic to paginate according to end-of-page markers
3.6.0
upload_account_corrs: manage iceOutTxt as additional case of no account associated to pdf
3.5.0
set empty 'ProductId' as PDF_UNKNOWN_ACCOUNT_NO
3.4.0
upd _open_correspondence_page_params
3.3.0
use basic_should_download_correspondence_for_account
upd log msg
3.2.0
_open_correspondence_page_params (useful for children, esp Cajasur)
3.1.0
_download_correspondence_pdf: retry for resp_pre_pdf
use custom DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS = 4
3.0.0
significant: correspondence: can process 'all accounts' view and paginate correctly (-a 23004) 
2.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
1.2.1
fix logic: use basic_should_download_company_documents
1.2.0
_account_no_for_req
1.1.0
parse_helpers_receipts: get_correspondence_from_list: handle more cases
download_company_documents: check for wrong layout
1.0.0
init
"""

MAX_CORR_OFFSET = 360  # 1yr - padding
DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS = 4


def account_no_to_fin_ent_id(account_no: str) -> str:
    return account_no[-10:]


class KutxaReceiptsScraper(KutxaScraper):
    scraper_name = 'KutxaReceiptsScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self._open_correspondence_page_params = {
            'ice.submit.partial': "false",
            'ice.event.target': "formMenuLateral:j_id2487",
            'ice.event.captured': "formMenuLateral:lateralCorrespondencia",
            'formMenuLateral': "formMenuLateral",
            'javax.faces.RenderKitId': "ICEfacesRenderKit",
            'formMenuLateral:_idcl': 'formMenuLateral:lateralCorrespondencia',
            'ice.focus': 'formMenuLateral:lateralCorrespondencia',
        }
        self.logger.info('INIT KutxaReceiptsScraper')

    def _is_lost_session(self, resp: Response) -> bool:
        return '<session-expired/>' in resp.text

    def _account_no_for_req(self, account_no: str) -> str:
        if ' ' in account_no:
            # -a 22962, '2095 0556 96 1060345872' -> '1060345872'; '1060345872' -> '1060345872'
            return account_no[-10:]
        # -a 9144, '6000059284042'
        return account_no

    def _open_correspondence_page(
            self,
            s: MySession,
            ice_session_id: str) -> Tuple[MySession, Response]:
        self.logger.info('OPEN correspondence page')

        _resp1 = self._send_receive_updates(
            s,
            ice_session_id,
            self._open_correspondence_page_params
        )

        _resp2 = self._dispose_views(s, ice_session_id)

        req_url = self._url('/NASApp/BesaideNet2/pages/buzon/buzon_seleccionDocumentos_consultaServicios.iface')
        resp3 = self._open_page(s, req_url)

        return s, resp3

    def _select_account(
            self,
            s: MySession,
            ice_session_id: str,
            acc_for_corr: AccountForCorrespondence) -> Tuple[MySession, Response]:

        # Handle special case when 'all accounts' option available
        if not acc_for_corr.req_param:
            self.logger.info('{}: no need to SELECT correspondence account (already selected)'.format(
                acc_for_corr.account_no
            ))
            return s, Response()

        self.logger.info('{}: SELECT correspondence account'.format(acc_for_corr.account_no))
        form_id = acc_for_corr.req_param

        optional_data = {
            'ice.submit.partial': 'true',
            'ice.event.target': form_id,
            'ice.event.captured': form_id,
            'formFiltro': "formFiltro",
            'javax.faces.RenderKitId': "ICEfacesRenderKit",
            'formFiltro:seleccionTipoContrato': "C",
            'formFiltro:SelectRadioMenuContratosPropios': self._account_no_for_req(acc_for_corr.account_no),
            'formFiltro:contratoOculto': "",
            'formFiltro:comboTipoDoc': "todos",
            'ice.focus': form_id,
        }
        resp = self._send_receive_updates(s, ice_session_id, optional_data)
        return s, resp

    def _select_corr_filter_by_dates(
            self,
            s: MySession,
            ice_session_id: str,
            acc_for_corr: AccountForCorrespondence) -> Tuple[MySession, Response]:
        """After 'open corr page'"""
        self.logger.info("{}: SELECT correspondence 'enter dates'".format(acc_for_corr.account_no))

        # formFiltro:criteriosFechas:_4
        form_id = 'formFiltro:criteriosFechas:_4'

        optional_data = {
            'ice.submit.partial': 'true',
            'ice.event.target': form_id,
            'ice.event.captured': form_id,
            'formFiltro': 'formFiltro',
            'javax.faces.RenderKitId': '',
            'formFiltro:contratoOculto': "",
            'formFiltro:comboTipoDoc': "todos",
            'formFiltro:criteriosFechas': "desdehasta",
            'ice.focus': form_id,
        }
        if not acc_for_corr.req_param:
            optional_data['formFiltro:seleccionTipoContrato'] = "T"  # todos
        else:
            optional_data['formFiltro:seleccionTipoContrato'] = "C"
            optional_data['formFiltro:SelectRadioMenuContratosPropios'] = \
                self._account_no_for_req(acc_for_corr.account_no)

        resp = self._send_receive_updates(s, ice_session_id, optional_data)
        return s, resp

    def _submit_corr_filter_by_dates(
            self,
            s: MySession,
            ice_session_id: str,
            acc_for_corr: AccountForCorrespondence,
            date_from: datetime) -> Tuple[MySession, Response]:
        """After 'Select 'enter dates'"""
        date_from_str = date_from.strftime('%d/%m/%Y')

        self.logger.info("{}: SUBMIT correspondence 'filter by dates': from {} to {}".format(
            acc_for_corr.account_no,
            date_from_str,
            self.date_to_str
        ))

        # '01/11/2016' -> ['01', '11', '2016']
        from_date_list = date_from_str.split('/')
        to_date_list = self.date_to_str.split('/')

        form_id = 'formFiltro:mostrar'
        optional_data = {
            'ice.submit.partial': 'false',
            'ice.event.target': form_id,
            'ice.event.captured': '',
            'formFiltro': "",
            'formFiltro:contratoOculto': '',
            'formFiltro:comboTipoDoc': 'todos',
            'formFiltro:criteriosFechas': 'desdehasta',
            'formFiltro:calendarioDesde': date_from_str,
            'formFiltro:calendarioDesde_cmb_dias': from_date_list[0],
            'formFiltro:calendarioDesde_cmb_mes': from_date_list[1],
            'formFiltro:calendarioDesde_cmb_anyo': from_date_list[2],
            'formFiltro:calendarioDesde_hdn_locale': 'es_ES_CAS',
            'formFiltro:calendarioHasta': self.date_to_str,
            'formFiltro:calendarioHasta_cmb_dias': to_date_list[0],
            'formFiltro:calendarioHasta_cmb_mes': to_date_list[1],
            'formFiltro:calendarioHasta_cmb_anyo': to_date_list[2],
            'formFiltro:calendarioHasta_hdn_locale': 'es_ES_CAS',
            'formFiltro:_idcl': form_id,
            'formFiltro:j_idformFiltro:calendarioHastasp': '',
            'formFiltro:j_idformFiltro:calendarioDesdesp': '',
            'ice.focus': form_id,
        }

        if not acc_for_corr.req_param:
            optional_data['formFiltro:seleccionTipoContrato'] = "T"  # todos
        else:
            optional_data['formFiltro:seleccionTipoContrato'] = "C"
            optional_data['formFiltro:SelectRadioMenuContratosPropios'] = \
                self._account_no_for_req(acc_for_corr.account_no)

        resp_corr_filtered = self._send_receive_updates(s, ice_session_id, optional_data)
        if self._is_lost_session(resp_corr_filtered):
            self.logger.warning('{}: lost session detected'.format(acc_for_corr.account_no))
            return s, resp_corr_filtered
        return s, resp_corr_filtered

    def _correspondence_by_account_paginate(
            self,
            s: MySession,
            ice_session_id: str,
            acc_for_corr: AccountForCorrespondence,
            page_ix: int,
            corrs_parsed_i: List[CorrespondenceDocParsed]) -> Tuple[MySession, Response]:
        self.logger.info('{}: correspondence PAGINATION: open page #{}'.format(
            acc_for_corr.account_no,
            page_ix
        ))
        form_id = "formCorrespondencia:siguiente"
        optional_data = {
            'ice.submit.partial': "false",
            'ice.event.target': form_id,
            'formCorrespondencia': "formCorrespondencia",
            'javax.faces.RenderKitId': 'ICEfacesRenderKit',
            'formCorrespondencia:checkbox': [str(x) for x in range(20)],
            'formCorrespondencia:_idcl': form_id,
            'ice.focus': form_id,
        }
        if page_ix > 2:
            optional_data['formCorrespondencia'] = ''
            optional_data['javax.faces.RenderKitId'] = ''

        #
        for ix, corr_parsed in enumerate(corrs_parsed_i):
            optional_data['formCorrespondencia:datosCorrespondencia:{}:urlDocs'.format(ix)] = \
                corr_parsed.extra['urldocs']

        resp = self._send_receive_updates(s, ice_session_id, optional_data)

        return s, resp

    def _download_correspondence_pdf(
            self,
            s: MySession,
            ice_session_id: str,
            resp_corr_filtered: Response,
            corr_parsed: CorrespondenceDocParsed) -> Tuple[bool, MySession, bytes]:

        self.logger.info("{}: '{}'@{}: download PDF".format(
            corr_parsed.account_no,
            corr_parsed.descr,
            corr_parsed.operation_date.strftime('%d/%m/%Y')
        ))
        try:
            resp_open_pdf_popup = Response()
            for attempt in range(1, 4):
                resp_open_pdf_popup = self._send_receive_updates(s, ice_session_id,
                                                                 corr_parsed.extra['req_pre_pdf_params'])
                req_pdf_link = parse_helpers_receipts.get_req_pdf_link(resp_open_pdf_popup.text)
                if req_pdf_link:
                    break
                self.logger.warning(
                    "{}: can't download correspondence PDF: wrong resp_pre_pdf. Retry #{}".format(
                        corr_parsed,
                        attempt
                    )
                )
                time.sleep(0.5 + random.random())
            else:
                self.basic_log_wrong_layout(
                    resp_open_pdf_popup,
                    "{}: can't download correspondence PDF: wrong resp_pre_pdf".format(corr_parsed)
                )
                return False, s, b''

            resp_pdf = s.get(
                # urljoin(resp_corr_filtered.url, corr.extra['req_pdf_link']),
                urljoin(resp_corr_filtered.url, req_pdf_link),
                headers=self.req_headers,
                proxies=self.req_proxies,
                stream=True
            )
            resp_pdf_content = resp_pdf.content
            req_close_popup_params = {
                'ice.submit.partial': 'false',
                'ice.event.target': 'formPopUp:j_id389',
                'ice.event.captured': "formPopUp:cerrarVentana",
                'formPopUp': "formPopUp",
                'javax.faces.RenderKitId': "ICEfacesRenderKit",
                'formPopUp:_idcl': "formPopUp:cerrarVentana",
                'ice.focus': "formPopUp:cerrarVentana",
            }
            _resp_close_pdf_popup = self._send_receive_updates(s, ice_session_id, req_close_popup_params)
            if not resp_pdf_content.startswith(b'%PDF'):
                self.basic_log_wrong_layout(resp_pdf, "{}: can't download PDF".format(corr_parsed))
                return False, s, b''

            return True, s, resp_pdf_content
        except Exception as _e:
            self.logger.error("{}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                corr_parsed,
                traceback.format_exc()
            ))
            return False, s, b''

    def _upload_account_corrs(
            self,
            organization: DBOrganization,
            account_no: str,
            corrs_with_contents_desc: List[Tuple[CorrespondenceDocParsed, bytes]]) -> List[CorrespondenceDocScraped]:

        corrs_scraped = []  # type: List[CorrespondenceDocScraped]
        self.logger.info('{}: {}: upload scraped correspondence: total {} docs'.format(
            organization.Name,
            account_no,
            len(corrs_with_contents_desc)
        ))

        corrs_with_contents_asc = list(reversed(corrs_with_contents_desc))
        # Insert all docs in ASC order
        for corr_parsed, doc_pdf_content in corrs_with_contents_asc:
            try:
                document_text = pdf_funcs.get_text(doc_pdf_content)
                # When there is no account associated to the PDF or account_no as 'iceOutTxt',
                # set 'product_id' as PDF_UNKNOWN_ACCOUNT_NO
                if corr_parsed.account_no != '' and corr_parsed.account_no != 'iceOutTxt':
                    product_id = corr_parsed.account_no
                else:
                    product_id = PDF_UNKNOWN_ACCOUNT_NO

                corr_scraped = CorrespondenceDocScraped(
                    CustomerId=self.db_customer_id,
                    OrganizationId=organization.Id,
                    FinancialEntityId=self.db_financial_entity_id,
                    ProductId=product_id,
                    ProductType='',
                    DocumentDate=corr_parsed.operation_date,
                    Description=corr_parsed.descr,
                    DocumentType=corr_parsed.type,
                    DocumentText=document_text,
                    # Need to use Checksum to compare with PDFs from receipts
                    Checksum=pdf_funcs.calc_checksum(bytes(document_text, 'utf-8')),
                    AccountId=None,  # Account DB Id
                    StatementId=None,
                    Amount=corr_parsed.amount,
                    Currency=corr_parsed.currency,
                )

                corr_scraped_upd, should_add = self.basic_check_correspondence_doc_to_add(
                    corr_parsed,
                    corr_scraped,
                    product_to_fin_ent_fn=account_no_to_fin_ent_id
                )

                if should_add:
                    corrs_scraped.append(corr_scraped_upd)
                    self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)
            except Exception as _e:
                self.logger.error(
                    "{}: can't upload correspondence PDF: HANDLED EXCEPTION\n{}\n\nPDF CONTENT\n{}".format(
                        corr_parsed,
                        traceback.format_exc(),
                        str(doc_pdf_content, 'utf-8')
                    )
                )

        return corrs_scraped

    def download_correspondence(
            self,
            s: MySession,
            resp_prev: Response) -> Tuple[bool, List[CorrespondenceDocScraped]]:

        if not self.basic_should_download_correspondence():
            return False, []

        ice_session_id = parse_helpers.get_ice_session_id(resp_prev.text)
        s, resp_corr_filter_page = self._open_correspondence_page(s, ice_session_id)
        organization_title = self.db_customer_name

        organization = self.basic_get_organization(organization_title)  # type: Optional[DBOrganization]

        if not organization:
            self.logger.error("download_correspondence: no organization_saved with title '{}'. "
                              "Can't continue. Abort".format(organization_title))
            return False, []

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=MAX_CORR_OFFSET
        )

        self.logger.info("{}: download correspondence from {} to {}".format(
            organization.Name,
            date_from_str,
            self.date_to_str
        ))

        accs_for_corr = parse_helpers_receipts.get_accounts_for_correspondence(
            resp_corr_filter_page.text
        )  # type: List[AccountForCorrespondence]

        # 'all accounts' available and selected by default - process it this way
        if not accs_for_corr and 'Todos los activos' in resp_corr_filter_page.text:
            accs_for_corr = [AccountForCorrespondence(
                account_no='ALL ACCOUNTS',
                req_param='',
            )]

        for acc_ix, acc_for_corr in enumerate(accs_for_corr):
            account_no = acc_for_corr.account_no

            corrs_with_contents_desc = []  # type: List[Tuple[CorrespondenceDocParsed, bytes]]
            if acc_ix > 0:
                s, _resp_corr_filter_page = self._open_correspondence_page(s, ice_session_id)

            s, _resp_acc_selected = self._select_account(s, ice_session_id, acc_for_corr)
            s, _resp_date_filter_selected = self._select_corr_filter_by_dates(
                s,
                ice_session_id,
                acc_for_corr
            )
            s, resp_corrs = self._submit_corr_filter_by_dates(s, ice_session_id, acc_for_corr, date_from)
            ok, corrs_parsed_desc, end_pagination = parse_helpers_receipts.get_correspondence_from_list(
                self.logger,
                resp_corrs.text,
                account_no
            )
            if not ok:
                self.basic_log_wrong_layout(
                    resp_corrs,
                    "{}: page #1: expected, but didn't get corrs_desc".format(account_no)
                )
                return False, []

            self.logger.info('{}: page #1: got {} correspondence docs for accounts: {}'.format(
                organization_title,
                len(corrs_parsed_desc),
                sorted(list({acc.account_no for acc in corrs_parsed_desc}))
            ))

            for corr_parsed in corrs_parsed_desc:
                ok, s, doc_pdf_content = self._download_correspondence_pdf(
                    s,
                    ice_session_id,
                    resp_corrs,
                    corr_parsed
                )
                if not ok:
                    continue  # next corr, already reported
                corrs_with_contents_desc.append((corr_parsed, doc_pdf_content))

            resp_corrs_i = resp_corrs
            corrs_desc_i = corrs_parsed_desc  # type: List[CorrespondenceDocParsed]
            for page_ix in range(2, 100):
                # not ('SIGUIENTES &raquo;' in resp_corrs_i.text
                #      or 'formCorrespondencia:siguiente' in resp_corrs_i.text // even if no more pages
                #  )
                # Checks the last page marker and next page button to confirm that there are NO more pages to scrape
                # and all PDFs are downloaded
                if end_pagination:
                    self.logger.info('{}: no more pages with correspondence'.format(acc_for_corr.account_no))
                    break

                s, resp_corrs_i = self._correspondence_by_account_paginate(
                    s,
                    ice_session_id,
                    acc_for_corr,
                    page_ix,
                    corrs_desc_i
                )

                ok, corrs_desc_i, end_pagination = parse_helpers_receipts.get_correspondence_from_updated_list(
                    self.logger,
                    resp_corrs_i.text,
                    account_no,
                    corrs_desc_i
                )

                if not ok:
                    self.basic_log_wrong_layout(
                        resp_corrs_i,
                        "{}: page #{}: expected, but didn't get corrs_desc_i".format(account_no, page_ix)
                    )
                    break

                self.logger.info('{}: page #{}: got {} corr(s)'.format(
                    account_no,
                    page_ix,
                    len(corrs_desc_i),
                ))

                for corr_parsed in corrs_desc_i:
                    ok, s, doc_pdf_content = self._download_correspondence_pdf(
                        s,
                        ice_session_id,
                        resp_corrs,
                        corr_parsed
                    )
                    if not ok:
                        continue  # next corr, already reported
                    corrs_with_contents_desc.append((corr_parsed, doc_pdf_content))
            # / end of pagination

            _docs_scraped_and_inserted = self._upload_account_corrs(
                organization,
                acc_for_corr.account_no,
                corrs_with_contents_desc
            )

        # / end of for acc_for_corr in accs_for_corr

        return True, []  # docs not used
