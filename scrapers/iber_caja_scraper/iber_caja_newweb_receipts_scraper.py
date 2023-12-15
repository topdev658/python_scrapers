import base64
import traceback
from collections import OrderedDict
from typing import List, Tuple, Optional

from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession
from project import settings
from project.custom_types import (
    CorrespondenceDocScraped, CorrespondenceDocParsed, DBOrganization, PDF_UNKNOWN_ACCOUNT_NO
)
from . import parse_helpers_receipts_newweb
from .custom_types import Contract
from .iber_caja_newweb_scraper import IberCajaScraper, DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS

__version__ = '2.0.0'

__changelog__ = """
2.0.0 2023.09.09
process_company_for_correspondence, _download_correspondence_pdf: 
  changed partial url from 'bancadigitalweb' to 'banca-digital-apigw'
1.3.0
set empty 'ProductId' as PDF_UNKNOWN_ACCOUNT_NO
1.2.0
use basic_should_download_correspondence_for_account
upd log msg
1.1.0
parse_helpers_receipts_newweb: _get_account_no: handle more cases
1.0.0
init
"""

# Extra offset bcs IberCaja's date_to is a future date
DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS = (
        settings.DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
        + DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS
)


class IberCajaReceiptsScraper(IberCajaScraper):
    scraper_name = 'IberCajaReceiptsScraper'

    def _corr_str(self, corr: CorrespondenceDocParsed) -> str:
        return '{}@{}'.format(corr.amount, corr.operation_date)

    def download_correspondence(
            self,
            s: MySession,
            contract: Contract) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Implements the documents downloading from corr mailbox.
        It gets the pdf files, saves them to the "receipts folder"
        and inserts the documents data in _TesoraliaDocuments table.

        Redefines download_documents method to provide real results
        """

        if not self.basic_should_download_correspondence():
            return False, []

        self.logger.info('{}: download correspondence'.format(contract.org_title))
        self.process_company_for_correspondence(s, contract)
        return True, []  # no correspondence required in the main scraper

    def process_company_for_correspondence(self, s: MySession, contract: Contract) -> bool:
        org_title = contract.org_title
        organization = self.basic_get_organization(org_title)  # type: Optional[DBOrganization]

        if not organization:
            self.logger.error("process_company_for_correspondence: no organization_saved with title '{}'. "
                              "Can't continue. Abort".format(org_title))
            return False
        org_name = organization.Name

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=120  # tested up to 4 months
        )

        self.logger.info("{}: download correspondence from {} to {}".format(
            org_name,
            date_from_str,
            self.date_to_str
        ))

        req_corr_url = ('https://banca.ibercaja.es/omnicanalidad/canales/banca-digital-apigw/'
                        'v1/api/Correspondencia/correspondencia')

        corrs_parsed_asc = []  # type: List[CorrespondenceDocParsed]
        for page_ix in range(1, 100):
            self.logger.info('{}: download correspondence from page #{}'.format(org_name, page_ix))
            req_corr_params = OrderedDict([
                ("columnaOrd", 1),
                ("agrupacion", []),
                ("cuentas", []),
                ("fechaDesde", date_from.strftime('%d/%m/%Y')),
                ("fechaHasta", self.date_to.strftime('%d/%m/%Y')),
                ("filtroDestacados", False),
                ("filtroOtrosDocumentos", None),
                ("importeDesde", 0),
                ("importeHasta", 999999),
                ("leido", None),
                ("orden", 0),  # 1 - DESC
                ("paginaAMostrar", page_ix),
            ])

            resp_corr_i = s.post(
                req_corr_url,
                json=req_corr_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
                verify=False
            )

            try:
                resp_corr_i_json = resp_corr_i.json()
            except Exception as _e:
                self.basic_log_wrong_layout(
                    resp_corr_i,
                    "{}: invalid resp_corr_i".format(org_name)
                )
                # To process as much as possible parsed from prev pages
                break

            corrs_parsed_asc_i = parse_helpers_receipts_newweb.get_correspondence_from_list(
                resp_corr_i_json
            )

            corrs_parsed_asc.extend(corrs_parsed_asc_i)

            if page_ix >= resp_corr_i_json['total_Paginas_Todos']:
                self.logger.info('{}: no more pages with correspondence'.format(org_name))
                break

        self.logger.info('{}: got {} correspondence docs for accounts: {}'.format(
            org_name,
            len(corrs_parsed_asc),
            sorted(list({acc.account_no for acc in corrs_parsed_asc}))
        ))

        for corr_parsed in corrs_parsed_asc:
            _ok = self.process_correspondence_document(
                s,
                organization,
                corr_parsed,
            )

        return True

    def _download_correspondence_pdf(
            self,
            s: MySession,
            corr: CorrespondenceDocParsed) -> Tuple[bool, bytes]:

        try:
            corr_str = self._corr_str(corr)
            req_url = ('https://banca.ibercaja.es/omnicanalidad/canales/banca-digital-apigw/'
                       'v1/api/Correspondencia/getdocumento')
            req_params = {'CodigoReferencia': [corr.extra['cod_ref_param']]}
            for i in range(1, 4):
                self.logger.info('att #{}: download {}'.format(
                    i,
                    corr_str
                ))
                resp_containing_pdf = s.post(
                    req_url,
                    json=req_params,
                    headers=self.req_headers,
                    proxies=self.req_proxies,
                )
                if resp_containing_pdf.status_code == 200:
                    break
            else:
                self.logger.error(
                    "{}: {}: couldn't download correspondence PDF after several attempts".format(
                        corr.account_no,
                        corr
                    )
                )
                return False, b''

            pdf_b64encoded = resp_containing_pdf.json()['documento']
            pdf_content = base64.b64decode(pdf_b64encoded)

            return True, pdf_content
        except:
            self.logger.error("{}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                corr,
                traceback.format_exc()
            ))
        return False, b''

    def process_correspondence_document(
            self,
            s: MySession,
            organization: DBOrganization,
            corr_parsed: CorrespondenceDocParsed) -> bool:

        fin_ent_account_id = corr_parsed.account_no
        if not self.basic_should_download_correspondence_for_account(fin_ent_account_id):
            return True

        self.logger.info('Process correspondence {}'.format(self._corr_str(corr_parsed)))

        ok, doc_pdf_content = self._download_correspondence_pdf(s, corr_parsed)
        if not ok:
            return False  # already reported

        document_text = pdf_funcs.get_text(doc_pdf_content)
        # When there is no account associated to the PDF, set 'product_id' as PDF_UNKNOWN_ACCOUNT_NO
        product_id = corr_parsed.account_no if corr_parsed.account_no != '' else PDF_UNKNOWN_ACCOUNT_NO

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

        corr_scraped_upd, should_save = self.basic_check_correspondence_doc_to_add(corr_parsed, corr_scraped)
        if should_save:
            self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)

        return True
