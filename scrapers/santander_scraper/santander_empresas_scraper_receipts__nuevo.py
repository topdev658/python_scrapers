import traceback
from collections import OrderedDict
from typing import List, Tuple

from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, MovementParsed, MovementScraped,
    ScraperParamsCommon, PDF_UNKNOWN_ACCOUNT_NO
)
from project.custom_types import CorrespondenceDocScraped, CorrespondenceDocParsed
from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
from . import parse_helpers_nuevo_receipts
from . import receipts_helpers
from .custom_types import OrganizationParsed
from .santander_empresas_scraper import DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS
from .santander_empresas_scraper__nuevo import SantanderEmpresasNuevoScraper

__version__ = '4.7.0'
__changelog__ = """
4.7.0 2023.07.11
download_correspondence_one_company: removed organization DB check to download all available correspondence files
4.6.0 2023.07.03
download_correspondence_one_company: added 'refresh' call to avoid session expiration into correspondence download
4.5.0 2023.06.13
download_correspondence_one_company: removed duplicated call to basic_should_download_correspondence method
4.4.0
set empty 'ProductId' as PDF_UNKNOWN_ACCOUNT_NO
4.3.0
use basic_should_download_correspondence_for_account
upd log msg
4.2.0
self._product_to_fin_ent_id
4.1.0
correspondence: product_to_fin_ent_id, parse_helpers: handle empty product_id (-a 26813)
4.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
3.6.0
date_from: use increasing offset from default future date_to
3.5.0
correspondence: currency field support
3.4.0
use project-level offset for corr
3.3.0
download_correspondence_one_company: handle company with correspondence for the customer 
parse_helpers_nuevo_receipts: get_correspondence_from_list: more try/except for
3.2.0
_download_correspondence_pdf: correct headers for multi-contract accesses
3.1.0
parse_helpers: get_organizations_parsed: handle exn
log warn if no organization (was err)
3.0.1
upd log msg
3.0.0
correspondence downloading
2.1.2
more type hints
2.1.1
new imports (renamed files)
2.1.0
parse_helpers: get_movements_parsed: set num_movement
receipt_helpers: use num_movement
2.0.0
download_receipts:
  use basic_download_receipts_common
receipt_helpers: 
  removed download_receipt
  use new basic_save_receipt_pdf_and_update_db
1.0.0
init
"""


class SantanderEmpresasNuevoReceiptsScraper(SantanderEmpresasNuevoScraper):
    """
    Implements download_receipts for multi-contract accesses
    """

    CONCURRENT_PDF_SCRAPING_EXECUTORS = 1

    scraper_name = 'SantanderEmpresasNuevoReceiptsScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.is_receipts_scraper = True

    @staticmethod
    def _product_to_fin_ent_id(product_id: str) -> str:
        """For correspondence
        ES6800496738531030617076 -> 0049 6738 51 2516180464
        """
        if not product_id:
            return ''
        return '{} {} {} {}'.format(
            product_id[-20:-16],
            product_id[-16:-12],
            product_id[-12:-10],
            product_id[-10:]
        )

    def download_receipts(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            movements_scraped: List[MovementScraped],
            movements_parsed: List[MovementParsed]) -> Tuple[bool, List[MovementScraped]]:

        return self.basic_download_receipts_common(
            s,
            account_scraped,
            movements_scraped,
            movements_parsed,
            meta={'scraper': self}
        )

    def download_movement_receipt(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            movement_scraped: MovementScraped,
            movement_parsed: MovementParsed,
            meta: dict) -> str:
        return receipts_helpers.download_movement_receipt(
            s,
            account_scraped,
            movement_scraped,
            movement_parsed,
            meta
        )

    def _download_correspondence_pdf(
            self,
            s: MySession,
            corr_parsed: CorrespondenceDocParsed) -> Tuple[bool, MySession, bytes]:

        extra = corr_parsed.extra
        req_url = ('https://empresas3.gruposantander.es/paas/api/nwe-usuario-api/v1/comunication/{}'.format(
            extra['document']
        ))

        # ('documentType=SCC_COMUNICADOS'
        #  '&documentManagement=SCConDemand'
        #  '&document=PI_Ba3750100010117442ab1ebc10200'
        #  '&documentCode=00016076173870542'
        #  '&documentId=00003870'
        #  '&shippingDate=2020-08-31')

        req_params = OrderedDict([
            ('documentType', extra['documentType']),  # 'SCC_COMUNICADOS'
            ('documentManagement', extra['documentManagement']),  # 'SCConDemand'
            ('document', extra['document']),  # 'PI_Ba3750100010117442ab1ebc10200',
            ('documentCode', extra['documentCode']),  # '00016076173870542',
            ('documentId', extra['documentId']),  # '00003870',
            ('shippingDate', extra['date']),  # '2020-08-31'
        ])

        resp_pdf = s.get(
            req_url,
            params=req_params,
            headers=self.basic_req_headers_updated({
                'Content-Type': 'application/json',  # even for PDF
                'x-frame-channel': 'EMP',
                'x-user-language': 'es_ES'  # critical for multi-contract accesses
            }),
            proxies=self.req_proxies,
            stream=True
        )

        resp_pdf_content = resp_pdf.content
        if not resp_pdf_content or resp_pdf.status_code == 400:
            self.basic_log_wrong_layout(resp_pdf, "{}: can't download PDF. RESPONSE:\n{}".format(
                corr_parsed,
                resp_pdf.text
            ))
            return False, s, b''

        return True, s, resp_pdf.content

    def download_correspondence(self, s: MySession) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        ok, s, organizations_parsed = self._get_organizations(s)
        if not ok:
            return False, []  # already logged
        for org_parsed in organizations_parsed:
            self.download_correspondence_one_company(
                s,
                org_parsed,
            )
        return True, []  # not used

    def download_correspondence_one_company(
            self,
            s: MySession,
            organization_parsed: OrganizationParsed) -> Tuple[bool, List[CorrespondenceDocScraped]]:

        organization_title = organization_parsed.title

        ok, s = self._refresh_session(s, organization_title)
        if not ok:
            return False, []  # already reported

        if not organization_title:
            self.logger.warning("download_correspondence_one_company: "
                                "no organization_title '{}'. "
                                "Can't continue. Skip organization".format(organization_title))
            return False, []

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            # increased offset from default future date_to, similar to IberCaja
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS + DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS,
            max_offset=85  # 3 months with padding
        )

        self.logger.info("{}: download correspondence from {} to {}".format(
            organization_title,
            date_from_str,
            self.date_to_str
        ))

        corrs_scraped = []  # type: List[CorrespondenceDocScraped]
        # Also works for branches (filiales)
        req_corrs_url = (
            'https://empresas3.gruposantander.es/paas/api/nwe-usuario-api/v2/comunication'
            '?pagination.limit=10'  # default 10
            '&pagination.offset=1'
            '&beginDate={}'
            '&endDate={}'
            '&categoryCode=0000'
            '&categoryBankCode=0049'
            '&orderType=D'
            '&ascOrder=true'  # 'true'/'false'
            '&personCode={}'  # 179869
            '&personType={}'  # J
        ).format(
            date_from.strftime('%Y-%m-%d'),
            self.date_to.strftime('%Y-%m-%d'),
            organization_parsed.personCode,
            organization_parsed.personType
        )
        for page_ix in range(1, 100):
            self.logger.info('{}: page {}: download correspondence'.format(
                organization_title,
                page_ix
            ))

            # 403 w/o proxy rotation
            resp_codes_bad_for_proxies = s.resp_codes_bad_for_proxies.copy()
            s.resp_codes_bad_for_proxies = [500, 502, 503, 504, None]  # except 403
            resp_corrs_i = s.get(
                req_corrs_url,
                headers=self.basic_req_headers_updated({
                    'Content-Type': 'application/json',
                    'x-frame-channel': 'EMP',
                    'x-user-language': 'es_ES'
                }),
                proxies=self.req_proxies
            )
            s.resp_codes_bad_for_proxies = resp_codes_bad_for_proxies

            if resp_corrs_i.status_code == 403 and 'Operation no authorized for user' in resp_corrs_i.text:
                self.logger.warning('{}: correspondence downloading forbidden for the customer'.format(
                    organization_title
                ))
                return False, []

            if resp_corrs_i.status_code == 204 and resp_corrs_i.text == '':
                self.logger.info('{}: no correspondence during {} - {}.'.format(
                    organization_title,
                    date_from,
                    self.date_to
                ))
                return True, []
            try:
                resp_corrs_i_json = resp_corrs_i.json()
            except:
                self.logger.error("{}: page {}: can't get resp_corrs_i_json. Abort. RESPONSE:\n{}".format(
                    organization_title,
                    page_ix,
                    resp_corrs_i.text
                ))
                return False, corrs_scraped

            corrs_parsed_asc = parse_helpers_nuevo_receipts.get_correspondence_from_list(
                resp_corrs_i_json,
                organization_title,
                self.logger,
            )

            self.logger.info('{}: page #{}: got {} correspondence docs for accounts: {}'.format(
                organization_title,
                page_ix,
                len(corrs_parsed_asc),
                sorted(list({acc.account_no for acc in corrs_parsed_asc}))
            ))

            for i, corr_parsed in enumerate(corrs_parsed_asc):

                fin_ent_account_id = self._product_to_fin_ent_id(corr_parsed.account_no)
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

                    pdf_text = pdf_funcs.get_text(doc_pdf_content)
                    # When there is no account associated to the PDF, set 'product_id' as PDF_UNKNOWN_ACCOUNT_NO
                    product_id = corr_parsed.account_no if corr_parsed.account_no != '' else PDF_UNKNOWN_ACCOUNT_NO

                    # There are no amount date in the list,
                    # so, we'll try to get it from PDF
                    amount = parse_helpers_nuevo_receipts.get_amount_from_pdf_text(pdf_text)
                    corr_parsed = corr_parsed._replace(
                        amount=amount
                    )

                    corr_scraped = CorrespondenceDocScraped(
                        CustomerId=self.db_customer_id,
                        OrganizationId='',  # not necessary
                        FinancialEntityId=self.db_financial_entity_id,
                        ProductId=product_id,
                        ProductType='',
                        DocumentDate=corr_parsed.operation_date,
                        Description=corr_parsed.descr,
                        DocumentType=corr_parsed.type,
                        DocumentText=pdf_text,
                        # Need to use Checksum to compare with PDFs from receipts
                        # - probably, this will not work due to double conversion.
                        # Use double-converted bytes->str->bytes to avoid
                        # hidden symbols which give different checksum for
                        # different days.
                        Checksum=pdf_funcs.calc_checksum(pdf_text.strip().encode('utf8')),
                        AccountId=None,  # Account DB Id
                        StatementId=None,
                        Amount=corr_parsed.amount,
                        Currency=corr_parsed.currency,
                    )
                    corr_scraped_upd, should_add = self.basic_check_correspondence_doc_to_add(
                        corr_parsed,
                        corr_scraped,
                        product_to_fin_ent_fn=self._product_to_fin_ent_id
                    )

                    if should_add:
                        corrs_scraped.append(corr_scraped_upd)
                        self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)

                except:
                    self.logger.error("{}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                        corr_parsed,
                        traceback.format_exc()
                    ))
            # end for i, corr in enumerate(corrs_asc)

            next_page_url = resp_corrs_i_json.get('_links', {}).get('next', {}).get('href', '')
            if not next_page_url:
                break
            req_corrs_url = next_page_url

        return True, corrs_scraped
