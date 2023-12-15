from collections import OrderedDict
from typing import List, Tuple, Optional
from urllib.parse import urljoin

from custom_libs import extract
from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    CorrespondenceDocParsed, DBOrganization
)
from project.custom_types import CorrespondenceDocScraped, AccountScraped
from . import parse_helpers_receipts
from .custom_types import AccountForCorrespondence
from .targo_scraper import TargoScraper


__version__ = '1.1.0'
__changelog__ = """
1.1.0 2023.07.10
process_company_for_correspondence, process_account_for_correspondence: upd requests url to targobank.es
1.0.0
init
"""


class TargoReceiptsScraper(TargoScraper):
    scraper_name = 'TargoReceiptsScraper'

    def download_correspondence(
            self,
            s: MySession,
            resp_logged_in: Response,
            organization_title: str,
            accounts_scraped: List[AccountScraped]) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Implements the documents downloading from corr mailbox.
        It gets the pdf files, saves them to the "receipts folder"
        and inserts the documents data in _TesoraliaDocuments table.

        Redefines download_documents method to provide real results
        """

        if not self.basic_should_download_correspondence():
            return False, []

        self.logger.info('Download correspondence')
        self.process_company_for_correspondence(s, resp_logged_in, organization_title, accounts_scraped)
        return True, []  # no correspondence required in the main scraper

    def process_company_for_correspondence(
            self,
            s: MySession,
            resp_logged_in: Response,
            organization_title: str,
            accounts_scraped: List[AccountScraped]) -> bool:

        organization = self.basic_get_organization(organization_title)  # type: Optional[DBOrganization]
        if not organization:
            self.logger.error(
                "process_company_for_correspondence: no organization_saved with title '{}'. "
                "Can't continue. Abort".format(organization_title)
            )
            return False

        resp_filter_form = s.get(
            'https://www.targobank.es/es/banque/avis_operes.aspx',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_for_corr = parse_helpers_receipts.get_accounts_for_corr(
            resp_filter_form.text,
            accounts_scraped
        )
        self.logger.info('Got {} accounts for correspondence: {}'.format(
            len(accounts_for_corr),
            accounts_for_corr
        ))
        for account_for_corr in accounts_for_corr:
            self.process_account_for_correspondence(
                s,
                organization,
                account_for_corr
            )

        return True

    def process_account_for_correspondence(
            self,
            s: MySession,
            organization: DBOrganization,
            account_for_corr: AccountForCorrespondence) -> bool:

        # open again
        resp_filter_form = s.get(
            'https://www.targobank.es/es/banque/avis_operes.aspx',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=project_settings.DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=360  # 1 year w/ padding
        )

        self.logger.info('{} process account for correspondence: dates from {} to {}'.format(
            account_for_corr.fin_ent_account_id,
            date_from_str,
            self.date_to_str
        ))

        req_corr_filtered_link, _ = extract.build_req_params_from_form_html_patched(
            resp_filter_form.text,
            form_id="P1:F"
        )

        req_corr_filtered_url = urljoin('https://www.targobank.es/es/banque/', req_corr_filtered_link)

        req_corr_filtered_params = OrderedDict([
            ('data_input_TYP%5fRCH', 'CPT'),
            ('data_input_NUM%5fCPT', account_for_corr.req_param),  # '02160585600620000397'
            ('data_input_COD%5fTYP', '   '),
            ('[t:dbt%3adate;]data_input_DAT%255fDEB', date_from_str),  # '01/10/2021'
            ('[t:dbt%3adate;]data_input_DAT%255fFIN', self.date_to_str),  # '17/10/2021'
            ('[t:dbt%3adouble;9(14)v9(2)]data_input_MNT%255fMIN', ''),
            ('[t:dbt%3adouble;9(14)v9(2)]data_input_MNT%255fMAX', ''),
            ('[t:dbt%3astring;x(40)]data_input_NUM%255fREF', ''),
            ('_FID_DoRechercher.x', '56'),
            ('_FID_DoRechercher.y', '24'),
            ('data_input_NUM%5fCPT%5fAFF', ''),
            ('data_output_MES%5fERR', ''),
            ('data_output_AFF%5fLST', 'N'),
            ('data_output_CRI%5fRECH%5fEXP', 'True'),
            ('data_LST%5fCPT_CPT_RIB%5fPRD', account_for_corr.req_param),
            # '0620000397 CUENTA CORRIENTE DE USO PRO EN USD I GAMBASTAR SL'
            ('data_LST%5fCPT_CPT_RIB%5fPRD%5fAFF', account_for_corr.account_title),
            # 'CUENTA CORRIENTE DE USO PRO EN USD I GAMBASTAR SL'
            ('data_LST%5fCPT_CPT_INT', account_for_corr.account_title),
            ('data_LST%5fCPT_CPT_NB%5fAVI', '4'),
            ('data_LST%5fCPT_CPT_RFN', 'O')
        ])

        resp_corr_filtered = s.post(
            req_corr_filtered_url,
            data=req_corr_filtered_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        corrs_parsed_desc = parse_helpers_receipts.get_correspondence_from_list(
            resp_corr_filtered.text,
            account_for_corr
        )  # type: List[CorrespondenceDocParsed]
        corrs_parsed_asc = list(reversed(corrs_parsed_desc))

        self.logger.info('{}: got {} correspondence docs for accounts: {}'.format(
            organization.Name,
            len(corrs_parsed_asc),
            corrs_parsed_asc
        ))

        for corr_parsed in corrs_parsed_asc:
            _ok = self.process_correspondence_document(
                s,
                organization,
                corr_parsed,
            )
        return True

    def process_correspondence_document(
            self,
            s: MySession,
            organization: DBOrganization,
            corr_parsed: CorrespondenceDocParsed) -> bool:

        fin_ent_account_id = corr_parsed.account_no
        if not self.basic_should_download_correspondence_for_account(fin_ent_account_id):
            return True

        self.logger.info("{}: process correspondence '{}' @ {}".format(
            fin_ent_account_id,
            corr_parsed.descr,
            corr_parsed.operation_date.strftime(project_settings.SCRAPER_DATE_FMT)
        ))

        pdf_link = corr_parsed.extra['pdf_link']
        if not pdf_link:
            self.logger.error("{}: can't download PDF. No 'pdf_link': {}".format(
                fin_ent_account_id,
                corr_parsed
            ))
            return False

        resp_pdf = s.get(
            urljoin('https://www.targobank.es/', pdf_link),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        doc_pdf_content = resp_pdf.content

        document_text = pdf_funcs.get_text(doc_pdf_content)

        corr_scraped = CorrespondenceDocScraped(
            CustomerId=self.db_customer_id,
            OrganizationId=organization.Id,
            FinancialEntityId=self.db_financial_entity_id,
            ProductId=fin_ent_account_id,
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

        corr_scraped_upd, should_save = self.basic_check_correspondence_doc_to_add(
            corr_parsed,
            corr_scraped
        )
        if should_save:
            self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)

        return True
