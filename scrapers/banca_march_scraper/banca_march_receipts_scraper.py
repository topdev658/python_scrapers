import traceback
from collections import OrderedDict
from typing import List, Tuple

from custom_libs import extract
from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession, Response
from project.custom_types import CorrespondenceDocParsed, PDF_UNKNOWN_ACCOUNT_NO
from project.custom_types import CorrespondenceDocScraped
from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
from . import parse_helpers_receipts
from .banca_march_scraper import BancaMarchScraper

__version__ = '3.2.0'

__changelog__ = """
3.2.0
set empty 'ProductId' as PDF_UNKNOWN_ACCOUNT_NO
3.1.0
use basic_should_download_correspondence_for_account
3.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
2.3.0
parse_helpers_receipts: extract currency
2.2.0
correspondence: currency field support
2.1.0
use project-level offset for corr
2.0.0
use basic funcs for correspondence
use project types
DocumentScraped: upd field (DocumentDate: datetime)
1.0.0
init
"""


class BancaMarchReceiptsScraper(BancaMarchScraper):
    scraper_name = 'BancaMarchReceiptsScraper'

    def _open_correspondence_page_init(
            self,
            s: MySession,
            date_from_str: str,
            date_to_str: str) -> Tuple[MySession, Response]:

        # Switch to Particulares view
        req_particulares_url = ('https://telemarch.bancamarch.es/htmlVersion/'
                                'XTransManager?tr=ENTORNO&num=03080&idioma=&entorno=empresa')
        resp_particulares = s.get(
            req_particulares_url,
            params=self._req_params_w_csrf_token(s),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # From  Servicios -> Correspondencia -> Consultar correspondencia
        req_corresp_filtered_url = 'https://telemarch.bancamarch.es/htmlVersion/XTransManager'
        req_corresp_filtered_params = OrderedDict([
            ('frmId', 'frmConsultaCorresponencia'),
            ('tr', 'OP'),
            ('num', '03112'),
            ('op', 'corrListado'),
            ('bb', '2'),
            ('claveContratoSip', ''),
            ('tipoDocumento3', '1'),
            ('conFechas', '1'),
            ('fechaDesde', date_from_str),  # '01/04/2020'
            ('fechaHasta', date_to_str),  # '30/05/2020'
            ('salida', 'pant'),
            ('inZip', 'false'),
            ('btnOk', 'Aceptar'),
        ])

        resp_corresp_filtered = s.get(
            req_corresp_filtered_url,
            params=self._req_params_w_csrf_token(s, req_corresp_filtered_params),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return s, resp_corresp_filtered

    def _get_correspondence_documents(
            self,
            s: MySession,
            organization_title: str,
            date_from_str: str,
            date_to_str: str) -> List[CorrespondenceDocParsed]:

        s, resp_corresp_filtered = self._open_correspondence_page_init(s, date_from_str, date_to_str)

        corr_parsed_asc = []  # type: List[CorrespondenceDocParsed]

        resp_prev = resp_corresp_filtered
        for page_num in range(1, 21):
            self.logger.info('{}: get correspondence from page {}'.format(
                organization_title,
                page_num
            ))

            pag_param = extract.form_param(resp_corresp_filtered.text, param_name="pag")
            if not pag_param:
                self.basic_log_wrong_layout(resp_prev, "{}: can't get pag_param".format(organization_title))
                break

            corr_parsed_i = parse_helpers_receipts.get_corespondence_from_list(resp_prev.text, pag_param)
            corr_parsed_asc.extend(corr_parsed_i)

            has_next_page = 'Siguiente página' in resp_prev.text  # 'Buscar correspondencia' in resp_prev.text
            if not has_next_page:
                break

            req_next_params = OrderedDict([
                ('frmId', 'frmConsultaCorresponencia'),
                ('tr', 'OP'),
                ('num', '03112'),
                ('op', 'corrMas'),
                ('codigos', '<lista/>'),
                ('pag', pag_param),
                ('inZip', 'false'),
                ('bb', '2'),
            ])

            resp_next = s.post(
                'https://telemarch.bancamarch.es/htmlVersion/XTransManager',
                data=self._req_params_w_csrf_token(s, req_next_params),
                headers=self.basic_req_headers_updated({
                    'Referer': resp_prev.url
                }),
                proxies=self.req_proxies
            )
            resp_prev = resp_next

        return corr_parsed_asc

    def _download_correspondence_pdf(
            self,
            s: MySession,
            corr: CorrespondenceDocParsed) -> Tuple[bool, MySession, bytes]:

        req_url = 'https://telemarch.bancamarch.es/htmlVersion/XTransManager'
        codigo_params = (
            '<lista>'
            '<nodo>'
            '<codigo>{}</codigo>'
            '<pdf>{}</pdf>'
            '<tipo>{}</tipo>'
            '<md5>{}</md5>'
            '</nodo>'
            '</lista>'.format(
                corr.extra['codigo_param'],
                corr.extra['pdf_param'],
                corr.extra['tipo_param'],
                corr.extra['md5_param']
            )
        )

        # _, req_pdf_params = extract.build_req_params_from_form_html_patched(
        #     resp_prev.text,
        #     form_name="frm3112"
        # )
        req_pdf_params = OrderedDict([
            ('frmId', 'frmConsultaCorresponencia'),
            ('tr', 'OP'),
            ('num', '03112'),
            ('op', 'corrDescarga'),
            ('codigos', codigo_params),
            ('pag', corr.extra['pag_param']),
            ('inZip', 'false'),
            ('bb', '3'),
        ])

        resp_pdf = s.post(
            req_url,
            data=self._req_params_w_csrf_token(s, req_pdf_params),
            headers=self.req_headers,
            proxies=self.req_proxies,
            stream=True
        )

        resp_pdf_content = resp_pdf.content
        if not resp_pdf_content:
            self.basic_log_wrong_layout(resp_pdf, "{}: can't download PDF (empty content)".format(corr))
            return False, s, b''
        # 'Ha expirado la sesión'.encode('utf-8')
        if b'Ha expirado la sesi\xc3\xb3n' in resp_pdf_content:
            self.basic_log_wrong_layout(resp_pdf, "{}: can't get correct PDF".format(corr))
            return False, s, b''

        return True, s, resp_pdf_content

    def download_correspondence(
            self,
            s: MySession,
            organization_title: str) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Implements the documents downloading from correspondence mailbox.
        It gets the pdf files, saves them to the "receipts folder"
        and inserts the documents data in _TesoraliaDocuments table.

        Redefines download_documents method to provide real results
        """

        if not self.basic_should_download_correspondence():
            return False, []

        organization = self.basic_get_organization(organization_title)
        if not organization:
            self.logger.error("download_correspondence: no organization_saved with title {}. "
                              "Can't continue. Abort".format(organization_title))
            return False, []

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
        )

        self.logger.info("{}: download correspondence from {} to {}".format(
            organization.Name,
            date_from_str,
            self.date_to_str
        ))

        corrs = self._get_correspondence_documents(
            s,
            organization.Name,
            date_from_str,
            self.date_to_str
        )  # type: List[CorrespondenceDocParsed]

        self.logger.info('{}: got {} correspondence docs for accounts: {}'.format(
            organization.NameOriginal,
            len(corrs),
            sorted(list({acc.account_no for acc in corrs}))
        ))

        documents_scraped = []  # type: List[CorrespondenceDocScraped]
        for i, corr in enumerate(corrs):

            # corr.account_no is fin_ent_account_id
            if not self.basic_should_download_correspondence_for_account(corr.account_no):
                continue

            try:
                ok, s, doc_pdf_content = self._download_correspondence_pdf(s, corr)
                if not ok:
                    self.logger.error("{}: {}: can't download correspondence PDF. Skip".format(
                        organization_title,
                        corr,
                    ))
                    continue

                document_text = pdf_funcs.get_text(doc_pdf_content)
                # When there is no account associated to the PDF, set 'product_id' as PDF_UNKNOWN_ACCOUNT_NO
                product_id = corr.account_no if corr.account_no != '' else PDF_UNKNOWN_ACCOUNT_NO

                corr_scraped = CorrespondenceDocScraped(
                    CustomerId=self.db_customer_id,
                    OrganizationId=organization.Id,
                    FinancialEntityId=self.db_financial_entity_id,
                    ProductId=product_id,
                    ProductType='',
                    DocumentDate=corr.operation_date,
                    Description=corr.descr,
                    DocumentType=corr.type,
                    DocumentText=document_text,
                    # Need to use Checksum to compare with PDFs from receipts
                    Checksum=pdf_funcs.calc_checksum(bytes(document_text, 'utf-8')),
                    AccountId=None,  # Account DB Id
                    StatementId=None,
                    Amount=corr.amount,
                    Currency=corr.currency,
                )

                corr_scraped_upd, should_add = self.basic_check_correspondence_doc_to_add(
                    corr,
                    corr_scraped
                )

                if should_add:
                    documents_scraped.append(corr_scraped_upd)
                    self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)

            except:
                self.logger.error("{}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                    corr,
                    traceback.format_exc()
                ))

        return True, documents_scraped
