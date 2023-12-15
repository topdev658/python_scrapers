import traceback
from collections import OrderedDict
from typing import List, Tuple

from custom_libs import iban_builder
from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession
from project.custom_types import CorrespondenceDocParsed
from project.custom_types import CorrespondenceDocScraped
from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
from . import parse_helpers_receipts
from .custom_types import OrganizationFromDropdown
from .deutschebank_scraper import DeutscheBankScraper

__version__ = '3.1.0'

__changelog__ = """
3.1.0
use basic_should_download_correspondence_for_account
upd log msg
3.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
2.2.0
correspondence: currency field support
2.1.0
use project-level DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
2.0.0
use basic funcs for correspondence
use project types
DocumentScraped: upd field (DocumentDate: datetime)
1.0.0
impl correspondence downloading
"""


def account_no_to_fin_ent_id(account_no: str) -> str:
    return account_no[-20:]


class DeutscheBankReceiptsScraper(DeutscheBankScraper):
    scraper_name = 'DeutscheBankReceiptsScraper'

    def download_correspondence(
            self,
            s: MySession) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Implements the documents downloading from correspondence mailbox.
        It gets the pdf files, saves them to the "receipts folder"
        and inserts the documents data in _TesoraliaDocuments table.

        Redefines download_documents method to provide real results

        For all organizations
        """

        if not self.basic_should_download_correspondence():
            return False, []

        # Open filter form
        resp_filter_form = s.get(
            'https://www.deutschebank-dbdirect.com/dbDirectServerApp/ECDL?ACCION=DBDIRECT.DESCAPDF.INICIO',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        organizations = parse_helpers_receipts.get_organizations(
            resp_filter_form.text
        )  # type: List[OrganizationFromDropdown]

        for organization_from_dropdown in organizations:
            self.download_org_correspondence(s, organization_from_dropdown)
        return True, []  # unused

    def _get_correspondence_documents(
            self,
            s: MySession,
            organization_from_dropdown: OrganizationFromDropdown,
            date_from_str: str,
            date_to_str: str) -> List[CorrespondenceDocParsed]:

        organization_title = organization_from_dropdown.title
        req_corresp_filtered_url = ('https://www.deutschebank-dbdirect.com/dbDirectServerApp/ECDL'
                                    '?ACCION=DBDIRECT.DESCAPDF.CONSULTA&PORTAL_LANGUAGE=ES')
        req_corresp_filtered_params = OrderedDict([
            ('CIA', organization_from_dropdown.req_param),  # '3253688GAMBASTAR, S.L'
            ('CIA_GRUPO', organization_from_dropdown.req_param),  # '3253688GAMBASTAR, S.L'
            ('FECHADES', date_from_str.replace('/', '.')),  # '20.05.2020'
            ('FECHAHAS', date_to_str.replace('/', '.')),  # '30.06.2020'
            ('IMPORDES', ''),
            ('IMPORHAS', ''),
            ('SELECCION', '1'),
            ('FORMULARIO', ''),
            ('DOCUMENTO', ''),
            ('PRODUCTO', ''),
            ('DOCUID_SP', ''),
            ('DETALLE_OCULTO', 'Abrir pdf'),
            ('POS', ''),
            ('VISIBLE', ''),
            ('TRANSID', '000000000000000000'),
            ('DATCIA', ''),
            ('DATFORM', ''),
            ('FRM_DISABLED', ''),
        ])
        resp_corresp_filtered = s.post(
            req_corresp_filtered_url,
            data=req_corresp_filtered_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        # 45 docs per page
        corr_parsed_desc = []  # type: List[CorrespondenceDocParsed]

        resp_prev = resp_corresp_filtered
        for page_num in range(1, 21):
            self.logger.info('{}: get correspondence from page {}'.format(
                organization_title,
                page_num
            ))

            corr_parsed_i = parse_helpers_receipts.get_corespondence_from_list(resp_prev.text)
            corr_parsed_desc.extend(corr_parsed_i)

            has_next_page = 'SIGUIENTE' in resp_prev.text
            if not has_next_page:
                break

            # Next page params
            req_corresp_filtered_params['AQNUPGDE'] = ''

            resp_next = s.post(
                'https://www.deutschebank-dbdirect.com/dbDirectServerApp/ECDL?ACCION=DBDIRECT.DESCAPDF.PAGINAR'
                '&TECLA=F8&PORTAL_LANGUAGE=ES&PORTAL_LANGUAGE=ES&PORTAL_LANGUAGE=ES',
                data=req_corresp_filtered_params,
                headers=self.basic_req_headers_updated({
                    'Referer': resp_prev.url
                }),
                proxies=self.req_proxies
            )
            resp_prev = resp_next

        corr_parsed_asc = corr_parsed_desc[::-1]
        return corr_parsed_asc

    def _download_correspondence_pdf(
            self,
            s: MySession,
            corr: CorrespondenceDocParsed) -> Tuple[bool, MySession, bytes]:

        req_step1_url = 'https://www.deutschebank-dbdirect.com/dbDirectServerApp/ECDL'
        req_step1_params = OrderedDict([
            ('ACCION', 'DBDIRECT.DESCAPDF.DETALLE'),
            ('DOCID', corr.extra['doc_id']),
            ('PORTAL_LANGUAGE', 'ES')
        ])

        resp_pdf_step1 = s.post(
            req_step1_url,
            params=req_step1_params,
            data={},  # req_all_docs_params: OrderedDict
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        req_pdf_params = OrderedDict([
            ('ACCION', 'DBDIRECT.DESCAPDF.ABRIRPDF'),
            ('DOCUID_SP', ''),
            ('PORTAL_LANGUAGE', 'ES')
        ])

        resp_pdf = s.get(
            'https://www.deutschebank-dbdirect.com/dbDirectServerApp/ECDL',
            params=req_pdf_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_pdf_step1.url
            }),
            proxies=self.req_proxies,
            stream=True
        )

        resp_pdf_content = resp_pdf.content
        if not resp_pdf_content:
            self.basic_log_wrong_layout(resp_pdf, "{}: can't download PDF (empty content)".format(corr))
            return False, s, b''

        return True, s, resp_pdf_content

    def download_org_correspondence(
            self,
            s: MySession,
            organization_from_dropdown: OrganizationFromDropdown):
        """For each organization"""

        organization_title = organization_from_dropdown.title
        organization = self.basic_get_organization(organization_title)

        if not organization:
            self.logger.error("download_correspondence: no organization_saved with title '{}'. "
                              "Can't continue. Abort".format(organization_title))
            return False, []

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=365
        )

        self.logger.info("{}: download correspondence from {} to {}".format(
            organization.Name,
            date_from_str,
            self.date_to_str
        ))

        corrs_parsed = self._get_correspondence_documents(
            s,
            organization_from_dropdown,
            date_from_str,
            self.date_to_str
        )  # type: List[CorrespondenceDocParsed]

        self.logger.info('{}: got {} correspondence docs for accounts: {}'.format(
            organization.Name,
            len(corrs_parsed),
            sorted(list({acc.account_no for acc in corrs_parsed}))
        ))

        corrs_scraped = []  # type: List[CorrespondenceDocScraped]
        for i, corr_parsed in enumerate(corrs_parsed):

            # fin_ent_account_id = 00190087434010030443 when account_no = ES7800190087434010030443
            fin_ent_account_id = account_no_to_fin_ent_id(corr_parsed.account_no)
            if not self.basic_should_download_correspondence_for_account(fin_ent_account_id):
                continue

            try:
                ok, s, doc_pdf_content = self._download_correspondence_pdf(s, corr_parsed)
                if not ok:
                    self.logger.error("{}: {}: can't download correspondence PDF. Skip".format(
                        organization_title,
                        corr_parsed,
                    ))
                    continue

                document_text = pdf_funcs.get_text(doc_pdf_content)
                product_id = iban_builder.build_iban('ES', corr_parsed.account_no)

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

            except:
                self.logger.error("{}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                    corr_parsed,
                    traceback.format_exc()
                ))

        return True, corrs_scraped
