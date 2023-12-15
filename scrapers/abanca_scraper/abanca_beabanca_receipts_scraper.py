import traceback
import urllib
from collections import OrderedDict
from datetime import datetime
from typing import List, Tuple, Optional

from custom_libs import date_funcs
from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession, Response
from project.custom_types import CorrespondenceDocScraped, DBOrganization, CorrespondenceDocParsed
from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
from . import parse_helpers
from . import parse_helpers_receipts
from .abanca_beabanca_scraper import AbancaBeAbancaScraper
from .custom_types import AccountForCorrespondence, Company

__version__ = '4.1.0'

__changelog__ = """
4.1.0 2023.10.20
refactored request urls and 'iban_country_code' references to run ABANCA PORTUGAL with same methods
parse_helpers_receipts: fixed PDF correspondence void Description and wrong DocumentType
4.0.0
renamed from abanca_receipts_scraper to abanca_beabanca_receipts_scraper
3.2.0
use basic_should_download_correspondence_for_account
3.1.0
_load_position_global_page_details: call with company title
3.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
2.2.0
correspondence: currency field support
2.1.0
use project-level offset for corr
2.0.0
use basic funcs for correspondence
1.2.0
DocumentScraped: upd field (DocumentDate: datetime)
1.1.0
with pagination
1.0.0
init
no pagination: max 50 docs per account
"""


class AbancaBeAbancaReceiptsScraper(AbancaBeAbancaScraper):
    """
    No pagination for now:
        scrape only 1 page with correspondence per account (max 50 docs)
    """
    scraper_name = 'AbancaBeAbancaReceiptsScraper'
    iban_country_code = 'ES'
    base_url = 'https://be.abanca.com/'

    def download_correspondence(self) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Implements the documents downloading from corr mailbox.
        It gets the pdf files, saves them to the "receipts folder"
        and inserts the documents data in _TesoraliaDocuments table.

        Redefines download_documents method to provide real results
        """

        if not self.basic_should_download_correspondence():
            return False, []

        self.logger.info('Download correspondence')

        # Need to log in to the new backend
        s, resp_logged_in, is_logged, _is_credentials_error, reason = self.login()
        if not is_logged and reason:
            self.logger.error("Can't log in for download_correspondence. Abort. Reason: {}".format(
                reason
            ))
            return False, []

        if not is_logged:
            self.logger.error("Can't log in for download_correspondence. Abort")
            return False, []

        self.process_companies_for_correspondence(s, resp_logged_in)
        return True, []  # not used

    def process_companies_for_correspondence(
            self,
            s: MySession,
            resp_logged_in: Response) -> bool:
        companies, req_params, req_url = self._get_companies(resp_logged_in)
        is_multicontract = bool(companies)
        self.logger.info('Is multicontract: {}'.format(is_multicontract))

        # several contracts
        if is_multicontract:
            # iterate over len of companies, each company param could be redefined
            # when logged in again
            for company in companies:
                self.process_company_for_correspondence(s, resp_logged_in, company, is_multicontract=True)
        # one contract
        else:
            company = self._default_company()
            s, resp_company_selected_loaded = self._load_position_global_page_details(
                s,
                company.title,
                resp_logged_in.text
            )
            self.process_company_for_correspondence(
                s,
                resp_company_selected_loaded,
                company,
                is_multicontract=False
            )

        return True

    def _click_select_date_filter(
            self,
            s: MySession,
            resp_prev: Response) -> Tuple[MySession, Response]:

        view_state_param = parse_helpers.get_view_state_param(resp_prev.text)

        req_url = urllib.parse.urljoin(self.base_url, 'BEPRJ001/jsp/BEPR_eCorrespondencia_LST.faces?javax.portlet.faces.DirectLink=true')
        cur_date_param = date_funcs.now_str('%m/%Y')
        req_params = parse_helpers_receipts.default_corr_filter_req_params()
        req_params.update(OrderedDict([
            ('AJAXREQUEST', '_viewRoot'),
            ('formulario:fechaDesdeInputCurrentDate', cur_date_param),  # '08/2020'
            ('formulario:fechaHastaInputCurrentDate', cur_date_param),
            # ('formulario:btnBuscar', 'Buscar'),
            ('javax.faces.ViewState', view_state_param),
            ('formulario:supportidOpciones', 'formulario:supportidOpciones')  # important
        ]))

        resp_selected_date_filter = s.post(
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        return s, resp_selected_date_filter

    def process_company_for_correspondence(
            self,
            s: MySession,
            resp_logged_in: Response,
            company: Company,
            is_multicontract: bool) -> bool:

        if is_multicontract:
            ok, s, resp_comp_selected, company, _ = self._open_resp_company_selected(company)
            # not logged in - return empty list of accounts
            # then they will be marked as scraped by state resetter
            if not ok:
                return False
        else:
            resp_comp_selected = resp_logged_in

        organization_title = company.title
        organization = self.basic_get_organization(organization_title)  # type: Optional[DBOrganization]

        if not organization:
            self.logger.error("process_company_for_correspondence: no organization_saved with title '{}'. "
                              "Can't continue. Abort".format(organization_title))
            return False

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=85  # 3 months with padding
        )

        self.logger.info("{}: download correspondence from {} to {}".format(
            organization.NameOriginal,
            date_from_str,
            self.date_to_str
        ))

        view_state_param = parse_helpers.get_view_state_param(resp_comp_selected.text)

        req_corr_filter_form_params = OrderedDict([
            ('formCabecera_SUBMIT', '1'),
            ('formCabecera:_link_hidden_', ''),
            ('formCabecera:_idcl', 'formCabecera:alnk_correspondencia'),
            # rO0ABXVyABNbTGphdmEubGFuZy5PYmplY3Q7kM5YnxBzKWwCAAB4cAAAAAN0AAhfaWQyNTQ4MXB0ACIvanNwL0JFUFJfUG9zaWNpb25HbG9iYWxJbmljaW8uanNw
            ('javax.faces.ViewState', view_state_param)
        ])

        # When clicked on e-Correspondencia link
        resp_corr_filter_form = s.post(
            urllib.parse.urljoin(self.base_url, 'BEPRJ001/jsp/BEPR_PosicionGlobalInicio.faces'),
            data=req_corr_filter_form_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_for_corr = parse_helpers_receipts.get_accounts_for_correspondence(
            resp_corr_filter_form.text,
            self.iban_country_code
        )  # type: List[AccountForCorrespondence]

        self.logger.info('{}: got {} accounts to download correspondence: {}'.format(
            organization.NameOriginal,
            len(accounts_for_corr),
            [acc.account_no for acc in accounts_for_corr]
        ))

        # Necessary for the next steps or will lose the session/can't filter by dates
        s, resp_selected_date_filter = self._click_select_date_filter(s, resp_corr_filter_form)

        resp_prev = resp_selected_date_filter

        for acc in accounts_for_corr:
            # Only serial processing is possible
            # Need to download PDFs while filtered correspondence for the account
            resp_prev = self.download_account_correspondence(
                s,
                organization,
                acc,
                date_from,
                self.date_to,
                resp_prev,
            )
        return True

    def _click_select_account_from_dropdown(
            self,
            s: MySession,
            resp_prev: Response,
            id_cuenta_param: str,
            date_from: datetime,
            date_to: datetime) -> Tuple[MySession, Response]:

        view_state_param = parse_helpers.get_view_state_param(resp_prev.text)

        req_url = urllib.parse.urljoin(self.base_url, 'BEPRJ001/jsp/BEPR_eCorrespondencia_LST.faces?javax.portlet.faces.DirectLink=true')
        req_params = parse_helpers_receipts.default_corr_filter_req_params()
        req_params.update(OrderedDict([
            ('AJAXREQUEST', '_viewRoot'),
            ('formulario:idCuenta', id_cuenta_param),  # 20801206315500001480
            ('formulario:fechaDesdeInputDate', date_from.strftime('%d-%m-%Y')),  # '03-06-2020'
            ('formulario:fechaDesdeInputCurrentDate', date_from.strftime('%m/%Y')),  # '06/2020'
            ('formulario:fechaHastaInputDate', date_to.strftime('%d-%m-%Y')),  # 02-08-2020
            ('formulario:fechaHastaInputCurrentDate', date_to.strftime('%m/%Y')),
            ('javax.faces.ViewState', view_state_param),
            ('formulario:supportidCuenta', 'formulario:supportidCuenta')  # important
        ]))

        resp_selected_account = s.post(
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        return s, resp_selected_account

    def _download_correspondence_pdf(
            self,
            s: MySession,
            corr_parsed: CorrespondenceDocParsed,
            req_corr_filtered_params: dict,
            resp_corr_filtered: Response) -> Tuple[bool, MySession, bytes]:
        """Returns the last resp to provide """

        corr_ix = corr_parsed.extra['ix']

        req_pre_pdf_url = urllib.parse.urljoin(self.base_url, 'BEPRJ001/jsp/BEPR_eCorrespondencia_LST.faces'
                           '?javax.portlet.faces.DirectLink=true')

        req_pre_pdf_params = req_corr_filtered_params.copy()
        req_pre_pdf_params['AJAXREQUEST'] = '_viewRoot'
        req_pre_pdf_params['formulario:idOpcionesSeleccion'] = 'NINGUNO'
        req_pre_pdf_params['formulario:tablaResultados:{}:hiddenNumSecuencia'.format(corr_ix)] = (
            corr_parsed.extra['num_secuencia_param']
        )
        req_pre_pdf_params['javax.faces.ViewState'] = parse_helpers.get_view_state_param(resp_corr_filtered.text)

        req_pre_pdf_params['formulario:tablaResultados:{}:lnkMarcarDescargarDoc'.format(corr_ix)] = (
            'formulario:tablaResultados:{}:lnkMarcarDescargarDoc'.format(corr_ix)
        )
        if 'formulario:btnBuscar' in req_pre_pdf_params:
            del req_pre_pdf_params['formulario:btnBuscar']

        resp_pre_pdf = s.post(
            req_pre_pdf_url,
            data=req_pre_pdf_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        res_prev = resp_pre_pdf
        resp_maybe_pdf = Response()
        for i in range(1, 11):
            req_pdf_params = req_corr_filtered_params.copy()
            req_pdf_params['formulario:idOpcionesSeleccion'] = 'NINGUNO'
            req_pdf_params['formulario:tablaResultados:{}:hiddenNumSecuencia'.format(corr_ix)] = (
                corr_parsed.extra['num_secuencia_param']
            )
            req_pdf_params[
                'formulario:btnDescargarDoc'] = 'Submit Query'  # for pageformulario:btnRecargarPagina	"Submit Query"
            if 'formulario:btnBuscar' in req_pdf_params:
                del req_pdf_params['formulario:btnBuscar']

            req_pdf_params['javax.faces.ViewState'] = parse_helpers.get_view_state_param(res_prev.text)

            self.logger.info('{}: att #{}: download corr with ix={}'.format(
                corr_parsed.account_no,
                i,
                corr_parsed.extra['ix']
            ))
            resp_maybe_pdf = s.post(
                urllib.parse.urljoin(self.base_url, 'BEPRJ001/jsp/BEPR_eCorrespondencia_LST.faces'),
                data=req_pdf_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
            )
            # Check: is it PDF or HTML resp
            view_state_param = parse_helpers.get_view_state_param(resp_maybe_pdf.text)
            if view_state_param:
                res_prev = resp_maybe_pdf
                continue
            break
        else:
            self.logger.error(
                "{}: corr ix={}: couldn't download correspondence PDF after several attempts".format(
                    corr_parsed.account_no,
                    corr_ix
                )
            )
            return False, s, b''

        pdf_content = resp_maybe_pdf.content

        return True, s, pdf_content

    def download_account_correspondence(
            self,
            s: MySession,
            organization: DBOrganization,
            account_for_corr: AccountForCorrespondence,
            date_from: datetime,
            date_to: datetime,
            resp_corresp_filtered_i: Response) -> Response:

        view_state_param = parse_helpers.get_view_state_param(resp_corresp_filtered_i.text)
        organization_name = organization.NameOriginal
        account_no = account_for_corr.account_no

        fin_ent_account_id = account_no  # same
        if not self.basic_should_download_correspondence_for_account(fin_ent_account_id):
            return resp_corresp_filtered_i

        if not view_state_param:
            self.logger.error("{}: {}: can't get view_state_param. Abort. RESPONSE prev:\n{}".format(
                organization_name,
                account_no,
                resp_corresp_filtered_i.text
            ))
            return resp_corresp_filtered_i

        s, resp_selected_account = self._click_select_account_from_dropdown(
            s,
            resp_corresp_filtered_i,
            account_for_corr.id_cuenta_param,
            date_from,
            date_to,
        )

        view_state_param2 = parse_helpers.get_view_state_param(resp_selected_account.text)
        # Only DESC order is available
        req_corresp_filtered_params = parse_helpers_receipts.default_corr_filter_req_params()
        req_corresp_filtered_params.update(OrderedDict([
            ('formulario:idCuenta', account_for_corr.id_cuenta_param),  # 20801206315500001480
            ('formulario:fechaDesdeInputDate', date_from.strftime('%d-%m-%Y')),  # '03-06-2020'
            ('formulario:fechaDesdeInputCurrentDate', date_from.strftime('%m/%Y')),  # '06/2020'
            ('formulario:fechaHastaInputDate', date_to.strftime('%d-%m-%Y')),  # 02-08-2020
            ('formulario:fechaHastaInputCurrentDate', date_to.strftime('%m/%Y')),
            ('formulario:btnBuscar', 'Buscar'),
            ('javax.faces.ViewState', view_state_param2),
        ]))

        resp_corresp_filtered = s.post(
            urllib.parse.urljoin(self.base_url, 'BEPRJ001/jsp/BEPR_eCorrespondencia_LST.faces'),
            data=req_corresp_filtered_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_selected_account.url
            }),
            proxies=self.req_proxies
        )

        self.logger.info('{}: get correspondence from list for account {}'.format(
            organization_name,
            account_no
        ))

        corrs_with_contents_desc = []  # type: List[Tuple[CorrespondenceDocParsed, bytes]]
        resp_corresp_filtered_i = resp_corresp_filtered
        for page_ix in range(1, 100):  # avoid inf loop
            # 50 docs per page
            corrs_parsed_desc = parse_helpers_receipts.get_correspondence_from_list(
                resp_corresp_filtered_i.text,
                account_no,
                self.logger
            )  # type: List[CorrespondenceDocParsed]

            self.logger.info('{}: {}: page #{}: download PDFs'.format(
                organization_name,
                account_no,
                page_ix
            ))
            for i, corr_parsed in enumerate(corrs_parsed_desc):
                try:
                    ok, s, doc_pdf_content = self._download_correspondence_pdf(
                        s,
                        corr_parsed,
                        req_corresp_filtered_params,
                        resp_corresp_filtered_i
                    )
                    if not ok:
                        self.logger.error("{}: {}: can't download correspondence PDF. Skip".format(
                            organization_name,
                            corr_parsed,
                        ))
                        continue

                    corrs_with_contents_desc.append((corr_parsed, doc_pdf_content))
                except:
                    self.logger.error("{}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                        corr_parsed,
                        traceback.format_exc()
                    ))
            # / end of for i, corr in enumerate(corr_parsed_asc)

            # From
            # <td class=" dr-dscr-button rich-datascr-button" onclick="Event.fire(this, 'rich:datascroller:onscroll', {'page': 'fastforward'});">»</td>
            if "{'page': 'fastforward'}" not in resp_corresp_filtered_i.text:
                self.logger.info('{}: {}: no more pages with correspondence'.format(
                    organization_name,
                    account_no
                ))
                break

            # Open next page
            req_corr_next_page_params = req_corresp_filtered_params.copy()
            del req_corr_next_page_params['formulario:btnBuscar']
            req_corr_next_page_params['AJAXREQUEST'] = '_viewRoot'
            req_corr_next_page_params['formulario:eCorrespondenciaScroller'] = 'fastforward'
            req_corr_next_page_params['javax.faces.ViewState'] = parse_helpers.get_view_state_param(
                resp_corresp_filtered_i.text)
            resp_corresp_filtered_i = s.post(
                urllib.parse.urljoin(self.base_url, 'BEPRJ001/jsp/BEPR_eCorrespondencia_LST.faces?javax.portlet.faces.DirectLink=true'),
                data=req_corr_next_page_params,
                headers=self.basic_req_headers_updated({
                    'Referer': resp_corresp_filtered_i.url  # with flow_execution_key
                }),
                proxies=self.req_proxies,
            )
            pass
        # / end of for page_ix in range(1, 100)

        self.logger.info('{}: {}: insert scraped correspondence: total {} docs'.format(
            organization_name,
            account_no,
            len(corrs_with_contents_desc)
        ))
        corrs_with_contents_asc = corrs_with_contents_desc[::-1]
        # Insert all docs in ASC order
        for corr_parsed, doc_pdf_content in corrs_with_contents_asc:
            document_text = pdf_funcs.get_text(doc_pdf_content)
            product_id = corr_parsed.account_no  # 'ES7020482178763400008898'

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
                corr_scraped
            )

            if should_add:
                # documents_scraped.append(corr_scraped_upd)  # not used
                self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)

        return resp_corresp_filtered_i  # for the next correct view_state_param
