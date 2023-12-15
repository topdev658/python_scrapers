import random
import time
import traceback
from typing import List, Tuple, Dict
from datetime import datetime
from collections import OrderedDict

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, MovementParsed, MovementScraped,
    ScraperParamsCommon, CorrespondenceDocScraped,
    DBOrganization, CorrespondenceDocParsed

)
from .sabadell_scraper import SabadellScraper
from . import parse_helpers_receipts
from .custom_types import AccountForCorrespondence
from custom_libs import pdf_funcs


__version__ = '5.7.0'

__changelog__ = """
5.7.0 2023.05.23
download_movement_receipt: added log when the movement_parsed has not receipt to download
5.6.0 2023.05.17
download_receipts: deleted variable DOWNLOAD_RECEIPTS_FOR_ACCESSES with hardcoded access whith receipts download 
configured as it is configured at DB level.
5.5.0
removed call to basic_save_receipt_pdf_and_update_db 
(only basic_save_receipt_pdf_as_correspondence is needed now) 
5.4.0
check for ok after basic_save_receipt_pdf_as_correspondence
5.3.0
process_correspondence_document: handle bad PDF (non-PDF doc)
5.2.0
save receipt metadata with checksum
5.1.0
basic_save_receipt_pdf_as_correspondence: saves file as corr (was only 'update db')
5.0.1
basic_save_receipt_pdf_as_correspondence: named arg 
5.0.0
upd init, scraper_name as cls prop
4.6.0
download_correspondence: 
  re-login to find all available accounts for correspondence from all contracts (-a 31134)
4.5.1
upd log msg
4.5.0
basic_save_receipt_pdf_as_correspondence: only_update_db=True
4.4.0
use basic_save_receipt_pdf_as_correspondence
4.3.0
moved DOWNLOAD_RECEIPTS_FOR_ACCESSES to accesses_allowed_receipts module 
4.2.0
more DOWNLOAD_RECEIPTS_FOR_ACCESSES
4.1.0
use basic_should_download_correspondence_for_account
upd log msgs
4.0.0
correspondence downloading support
3.5.1
upd log msg
3.5.0
set flag is_receipts_scraper (used by basic_get_movements_parsed_w_extra_details)  
3.4.1
fixed log msg
3.4.0
download_movement_receipt: increased timeout
CONCURRENT_PDF_SCRAPING_EXECUTORS = 4
3.3.0
download_movement_receipt: upd req params
parse_helpers: parse_movements_from_html: receipt_params as ord dict
3.2.0
several attempts to download pdf 
upd log msg (align with others)
more details if bad content-type
3.1.2
upd type hints
3.1.1
download_movement_receipt: inc timeout
3.1.0
CONCURRENT_PDF_SCRAPING_EXECUTORS = 8
fmt
3.0.0
download_receipts: use basic_download_receipts_common
download_movement_receipt: 
  always returns str
  use new basic_save_receipt_pdf_and_update_db
parse_helpers: removed earlier unused get_receipt_text_fitz
parse_helpers: removed unused get_receipt_text_faster_fitz
call basic_update_db_with_receipt_pdf_info with text as is (no replacement for quotes needed)
2.0.2
FIXME notes
2.0.1
DAF: download_movement_receipt: process downloaded pdf receipt only if Content-Type='application/pdf', bcs some 
'text/html' responses was saved as pdf file. 
2.0.0
download_receipts: changed return types to provide compat with BasicScraper
1.2.2
download_receipts:
    receipt_description: default list of ''
    set fields explicitly for movs_w_extracted_info
1.2.1
fmt, todos
1.2.0
DAF:
modified download_movement_receipt to:
- extract all the content from the downloaded pdf and save it to the movements table 
  (StatementReceiptDescription field)
- return a dict with that content to extract additional information from it by the scraping process later.
modified download_receipts to return a List of MovementScrapedWExtractedInfo: MovementScraped plus the pdf receipt
content data (receipt_description)
parse_helper: added functions using the pymupdf module to extract pdf contents: get_receipt_text_fitz, 
get_receipt_text_fitz_low, get_concept_from_receipt 
1.1.1
reformatted
1.1.0
DAF: added receipt downloading in parallel mode to improve scraping speed. 
Set CONCURRENT_PDF_SCRAPING_EXECUTORS = 4
1.0.1
reformatted
1.0.0
init
"""

USER_AGENT = ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.22 '
              '(KHTML, like Gecko) Chrome/25.0.1364.97 Safari/537.22')


# TODO VB: impl concurrent correspondence scraping
class SabadellReceiptsScraper(SabadellScraper):
    CONCURRENT_PDF_SCRAPING_EXECUTORS = 4

    scraper_name = 'SabadellReceiptsScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.is_receipts_scraper = True

    def download_receipts(self, s: MySession,
                          account_scraped: AccountScraped,
                          movements_scraped: List[MovementScraped],
                          movements_parsed: List[MovementParsed],
                          referer: str) -> Tuple[bool, List[MovementScraped]]:

        return self.basic_download_receipts_common(
            s,
            account_scraped,
            movements_scraped,
            movements_parsed,
            meta={'referer': referer}
        )

    def download_movement_receipt(self,
                                  s: MySession,
                                  account_scraped: AccountScraped,
                                  movement_scraped: MovementScraped,
                                  movement_parsed: MovementParsed,
                                  meta: dict) -> str:

        referer = meta['referer']  # type: str

        if not movement_parsed['may_have_receipt']:
            self.logger.info('{}: the movement has not receipt to download: date {}, pos #{}, amount {}. Skip'.format(
                account_scraped.FinancialEntityAccountId,
                movement_scraped.OperationalDate,
                movement_scraped.OperationalDatePosition,
                movement_scraped.Amount
            ))
            return ''

        self.logger.info('Download receipts for mov {}'.format(movement_parsed))
        try:
            """
            https://www.bancsabadell.com/txempbs/CUExtractOperationsQueryNew.dataMovement.bs
            ?productCode=0
            &sessionDate.day=10&sessionDate.month=12
            &sessionDate.year=2018
            &valueDate.day=10&valueDate.month=12
            &valueDate.year=2018&movementDate.day=10
            &movementDate.month=12
            &movementDate.year=2018
            &timeStamp=20181210154151655455
            &existDocument=S
            &account.bank=0081
            &account.branch=0250
            &account.checkDigit=91
            &account.accountNumber=0001844594
            &amount.currency=EUR
            &amount.value=20,00
            &balance=45.849,97
            &apuntNumber=834491655455
            &referencor=091401EURLICOM 2018-12-10-15.37.36.647066        000030004617595
            &concept=
            &conceptCode=409
            """
            resp_pdf = Response()
            for attempt in range(1, 3):
                req_url = ('https://www.bancsabadell.com/'
                           'txempbs/CUExtractOperationsQueryNew.dataMovement.bs')

                req_params = movement_parsed['receipt_params']
                # Since 09/2020
                if 'balance' in req_params:
                    del req_params['balance']
                if 'apuntNumber' in req_params:
                    del req_params['apuntNumber']

                resp_pdf = s.post(
                    req_url,
                    data=req_params,
                    headers=self.basic_req_headers_updated({'Referer': referer}),
                    proxies=self.req_proxies,
                    timeout=60,
                    stream=True
                )

                if resp_pdf.headers.get('Content-Type') != 'application/pdf':
                    self.logger.warning(
                        "{}: attempt #{}: {}: can't download pdf: BAD Content-Type {}"
                        "\nReceipt params: {}\nRESPONSE:\n{}".format(
                            account_scraped.AccountNo,
                            attempt,
                            movement_parsed['operation_date'],
                            resp_pdf.headers['Content-Type'],
                            movement_parsed['receipt_params'],
                            resp_pdf.text
                        )
                    )
                    time.sleep(0.5 + random.random())
                    continue
                break
            else:
                self.logger.error(
                    "{}: {}: can't download pdf: BAD Content-Type {}"
                    "\nReceipt params: {}"
                    "\nRESPONSE:\n{}".format(
                        account_scraped.AccountNo,
                        movement_parsed['operation_date'],
                        resp_pdf.headers['Content-Type'],
                        movement_parsed['receipt_params'],
                        resp_pdf.text
                    )
                )
                return ''

            # IMPORTANT:
            # The code below means that the receipt PDF will be saved to "receipts" folder
            # but its metadata will be saved
            # to _TesoraliaDocuments table using basic_save_receipt_pdf_as_correspondence.
            # This is a special case for Sabadell.
            #
            # The task
            # BR:
            # 1. If possible, it is best that the PDF is not duplicated in the receipts
            #  folder and in the correspondence folder, because the query will show duplicate PDFs to the client.
            # 2. The best thing would be to save the receipts of the acceo -a 30623
            #  in the "receipts" folder and store the metadata in the _TesoraliaDocuments table,
            #  and the other non-SABADELL PDFs save them in the "correspondence" folder
            #  and store the metadata in the _Tesoraliadocuments table.
            #
            # VB: UPD 2022.01 (aligned with other receipt scrapers):
            # - saves receipts as correspondence (file + metadata in DB)
            # - saves receipt metadata in DB (w/o pdf)

            ok, receipt_parsed_text, checksum = self.basic_save_receipt_pdf_as_correspondence(
                account_scraped,
                movement_scraped,
                resp_pdf.content,
            )

            return receipt_parsed_text

        except:
            self.logger.error("{}: {}: can't download pdf: HANDLED EXCEPTION\n{}".format(
                account_scraped.FinancialEntityAccountId,
                movement_parsed['operation_date'],
                traceback.format_exc()
            ))
            return ''

    def download_correspondence(self, s: MySession) -> Tuple[bool, List[CorrespondenceDocScraped]]:

        if not self.basic_should_download_correspondence():
            return False, []

        time.sleep(1 + random.random())

        # Need to re-login to be at the page where all contracts and accounts are available
        # otherwise, only last contract account will be available
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        # Actually, it's unexpected to get such errors here..
        if is_credentials_error:
            self.basic_result_credentials_error()
            return False, []

        if not is_logged:
            self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )
            return False, []

        resp_corr_form = s.get(
            'https://www.bancsabadell.com/txempbs/SVGetMail.initSearcher.bs',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        orgs_and_accounts_for_corr = parse_helpers_receipts.get_orgs_and_accounts_for_correspondence(
            resp_corr_form.text
        )  # type: Dict[str, List[AccountForCorrespondence]]

        self.logger.info('Got {} available accounts for correspondence (all contracts): {}'.format(
            sum([len(v) for v in orgs_and_accounts_for_corr.values()]),
            orgs_and_accounts_for_corr,
        ))

        for org_title, accounts_for_corr in orgs_and_accounts_for_corr.items():
            self.process_org_for_correspondence(
                s,
                org_title,
                accounts_for_corr
            )
        return True, []  # results are not used

    def process_org_for_correspondence(
            self,
            s: MySession,
            org_title: str,
            accounts_for_corr: List[AccountForCorrespondence]):

        organization = self.basic_get_organization(org_title)

        if not organization:
            self.logger.warning("download_correspondence: no organization_saved with title '{}'. "
                                "Can't continue. Skip organization".format(org_title))
            return False, []

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=project_settings.DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=360  # 1 year with padding
        )

        self.logger.info("{}: download correspondence from {} to {}".format(
            organization.Name,
            date_from_str,
            self.date_to_str
        ))

        self.logger.info('{}: got {} accounts to download correspondence:: {}'.format(
            organization.Name,
            len(accounts_for_corr),
            accounts_for_corr
        ))

        for acc in accounts_for_corr:
            # Only serial processing is possible
            # Need to download PDFs while filtered correspondence for the account
            self.process_account_for_correspondence(
                s,
                org_title,
                organization,
                acc,
                date_from,
                self.date_to,
            )

    def process_account_for_correspondence(
            self,
            s: MySession,
            org_title_scraped: str,
            organization: DBOrganization,
            account_for_corr: AccountForCorrespondence,
            date_from: datetime,
            date_to: datetime) -> bool:
        """

        :param s: ...
        :param org_title_scraped: it's used as req param,
            can be slightly different to organization.Name
        :param organization: saved DBOrganization
        :param account_for_corr: ...
        :param date_from: ...
        :param date_to: ...
        :return: is_success
        """

        # For ES0900815182590001030609 req_param='5182-0001030609',
        # thus can use last 10 digits of req_param
        # due to contains.any_el_endswith used for account matching
        fin_ent_account_id_suffix = account_for_corr.req_param.split('-')[-1][-10:]
        if not self.basic_should_download_correspondence_for_account(fin_ent_account_id_suffix):
            return True

        log_prefix = '{}: {}'.format(organization.Name, account_for_corr.account_title)

        date_fmt = '%d/%m/%Y'
        date_from_str = date_from.strftime(date_fmt)
        date_to_str = date_to.strftime(date_fmt)
        df, mf, yf = date_from_str.split('/')
        dt, mt, yt = date_to_str.split('/')

        req_url = 'https://www.bancsabadell.com/txempbs/SVGetMail.query.bs'
        req_params = OrderedDict([
            ('field', 'fecha'),
            ('sorting', 'desc'),
            ('queryPagination.pageNumber', '0'),  # will be changed during the loop
            ('searchExecuted', 'true'),
            ('empresa.selectable-index', org_title_scraped),   # 'MAGAPU 2017, S.L.'
            ('contrato.selectable-index', account_for_corr.req_param),  # '0105-0002278332'
            ('intervaloMov', '-1'),
            ('opcioMoviments', '3'),
            ('dateFrom', date_from_str),  # '01/05/2021'
            ('queryParams.dateFrom.day', df),
            ('queryParams.dateFrom.month', mf),
            ('queryParams.dateFrom.year', yf),
            ('dateTo', date_to_str),  # '01/06/2021'
            ('queryParams.dateTo.day', dt),
            ('queryParams.dateTo.month', mt),
            ('queryParams.dateTo.year', yt),
            ('queryParams.type', '3'),
            ('queryParams.category', ''),
            ('queryParams.amountType', 'T'),
            ('queryParams.amountFrom.value', ''),
            ('queryParams.amountTo.value', ''),
            ('queryParams.amountFrom.currency', 'EUR'),  # always EUR even for USD accounts
            ('queryParams.amountTo.currency', 'EUR'),
            ('reference', ''),
            ('ccciban', '')
        ])

        corrs_parsed_desc = []  # type: List[CorrespondenceDocParsed]

        for page_ix in range(1, 100):  # avoid inf loop
            self.logger.info('{}: page #{}: get correspondence from the list'.format(
                log_prefix,
                page_ix
            ))
            # After the 1st page
            if page_ix > 1:
                req_url = 'https://www.bancsabadell.com/txempbs/SVGetMail.nextPage.bs'
                # For the 1st page queryPagination.pageNumber=0, then 2, 3, 4...
                req_params['queryPagination.pageNumber'] = str(page_ix)
                req_params['queryParams.dateFrom.day'] = ''
                req_params['queryParams.dateFrom.month'] = ''
                req_params['queryParams.dateFrom.year'] = ''
                req_params['queryParams.dateFrom.day'] = ''
                req_params['queryParams.dateFrom.month'] = ''
                req_params['queryParams.dateFrom.year'] = ''

            resp_corrs_filtered_i = s.post(
                req_url,
                data=req_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            # All correspondence documents at once, pagination is not required
            corrs_parsed_i = parse_helpers_receipts.get_correspondence_docs_parsed(
                resp_corrs_filtered_i.text,
                account_for_corr.req_param
            )  # type: List[CorrespondenceDocParsed]

            corrs_parsed_desc.extend(corrs_parsed_i)

            has_more_corrs = 'Siguiente >' in resp_corrs_filtered_i.text
            if not has_more_corrs:
                self.logger.info('{}: no more pages with correspondence'.format(log_prefix))
                break

        corrs_parsed_asc = list(reversed(corrs_parsed_desc))

        self.logger.info('{}: got total {} correspondence docs parsed'.format(
            log_prefix,
            len(corrs_parsed_asc)
        ))

        for i, corr_parsed in enumerate(corrs_parsed_asc):
            _ok, s = self.process_correspondence_document(
                s,
                organization,
                corr_parsed
            )
        return True

    def _download_correspondence_pdf(
            self,
            s: MySession,
            corr_parsed: CorrespondenceDocParsed) -> Tuple[bool, MySession, bytes]:
        try:
            resp_corr = s.post(
                'https://www.bancsabadell.com/txempbs/SVGetMail.invokeDownload.bs',
                data=corr_parsed.extra['req_params'],
                headers=self.req_headers
            )
            return True, s, resp_corr.content
        except:
            self.logger.error("{}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                corr_parsed,
                traceback.format_exc()
            ))
            return False, s, b''

    def process_correspondence_document(
            self,
            s: MySession,
            organization: DBOrganization,
            corr_parsed: CorrespondenceDocParsed) -> Tuple[bool, MySession]:

        self.logger.info('Process correspondence {}'.format(corr_parsed))
        ok, s, doc_pdf_content = self._download_correspondence_pdf(s, corr_parsed)
        if not ok:
            return False, s  # already reported

        try:
            document_text = pdf_funcs.get_text(doc_pdf_content)
        except RuntimeError as e:
            # this = _fitz.new_Document(filename, stream, filetype, rect, width, height, fontsize)
            # RuntimeError: no objects found
            self.logger.error("{}: can't get text from the PDF: {}\nPDF CONTENT:\n{!r}".format(
                corr_parsed,
                e,
                doc_pdf_content
            ))
            return False, s

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

        corr_scraped_upd, should_save = self.basic_check_correspondence_doc_to_add(corr_parsed, corr_scraped)
        if should_save:
            self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)

        return True, s
