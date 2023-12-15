from collections import OrderedDict
from datetime import datetime, timedelta
from typing import List, Set

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult, AccountScraped
from . import parse_helpers_n43
from .bankinter_scraper import BankinterScraper
from .custom_types import Company

__version__ = '1.9.0'
__changelog__ = """
1.9.0
download_n43_file: activate 'Con movimientos automaticos' option for downloaded file
1.8.0
CANT_DOWNLOAD_N43_MARKERS
1.7.1
upd log msg
1.7.0
process also multi-currency accounts
1.6.0
fin_ent_account_id_to_get_dates_and_status
1.5.0
encode resp_n43.content
more log msgs
custom max_offset
fmt
1.4.0
main: don't check for get_n43_last_successful_result_date_of_access() 
  (now implemented in self.basic_scrape_for_n43())
1.3.0
use basic_save_n43s
1.2.0
use basic_scrape_for_n43
self.fin_entity_name
1.1.1
upd log msg
1.1.0
check is_active_account
1.0.0
init
"""

MAX_OFFSET_DAYS = 75
CANT_DOWNLOAD_N43_MARKERS = [
    'No ha sido posible generar el fichero debido al excesivo volumen de movimientos que contiene'
]

class BankinterN43Scraper(BankinterScraper):
    """Handles different formats of fin_ent_account_ids.
    For N43 filtering:
    ['01280526500007565001', '01280526510032321001']
    but accounts_parsed are
    [{'account_no': 'ES6201280526190500007565', 'financial_entity_account_id': '01280526500007565',...},
    {'account_no': 'ES8101280526140510032321', 'financial_entity_account_id': '01280526510032321',...}]
    Meantime, GetLastStatementDateFromAccount_N43 uses a format like account_no[4:]:
    '01280526190500007565'
    """

    fin_entity_name = 'BANKINTER'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BankinterN43Scraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)
        self.__date_to = date_funcs.today() - timedelta(days=1)
        self.__date_to_str = self.__date_to.strftime('%d/%m/%Y')

    def process_access_for_n43(self, s: MySession, resp_logged_in: Response) -> bool:
        companies = self.get_companies(s, resp_logged_in)
        self.logger.info('Got {} companies (contracts): {}'.format(
            len(companies),
            [c.title for c in companies]
        ))
        for company in companies:
            ok = self.process_company_for_n43(s, company)
            if not ok:
                return False
        return True

    def _open_filter_form(self, s: MySession) -> Response:
        req_filter_form_url = "https://empresas.bankinter.com/www/es-es/cgi/empresas+cuentas+credito_mov_fichero"
        resp_filter_form = s.get(req_filter_form_url, headers=self.req_headers, proxies=self.req_proxies)
        return resp_filter_form

    def _drop_currency_suffix_from_fin_ent_acc_id(self, fin_ent_acc_id: str) -> str:
        """01287681550060322EUR -> 01287681550060322"""
        return extract.re_first_or_blank(r'\d+', fin_ent_acc_id)

    def _get_accounts_scraped_with_only_one_submulti(
            self,
            resp_company: Response,
            company: Company) -> List[AccountScraped]:
        """Gets all accounts_scraped including multi-currency sub-accounts
        but then keeps only 1 sub per parent fin_ent_account_id (drops other children).
        It is necessary to keep only 1 multi-currency sub-account to pass
        further validation in process_account_for_n43 if found
        suitable fin_ent_account_id_for_n43.
        Because, in the end, N43 contains all movs for all multi-currency sub-accounts at once.
        """
        # Including multi-currency sub-accounts
        accounts_scraped_all = self.get_accounts_scraped(resp_company, company)

        # Keep only 1 multicurrency_subaccount to get valid fin_ent_account_id_for_43 later
        accounts_scraped = []  # type: List[AccountScraped]

        # account_no has no currency suffix
        account_nos_processed = set()  # type: Set[str]
        for acc in accounts_scraped_all:
            # 01287681550060322EUR -> 01287681550060322
            account_no = acc.AccountNo
            if account_no in account_nos_processed:
                continue
            accounts_scraped.append(acc)
            account_nos_processed.add(account_no)
        return accounts_scraped

    def process_company_for_n43(self, s: MySession, company: Company) -> bool:
        self.logger.info('{}: process_company_for_n43'.format(company.title))
        ok, s, resp_company = self._open_company_page(s, company)
        if not ok:
            return False  # already reported

        accounts_scraped = self._get_accounts_scraped_with_only_one_submulti(resp_company, company)

        resp_filter_form = self._open_filter_form(s)
        fin_ent_account_ids_for_n43 = parse_helpers_n43.get_fin_ent_account_ids_for_n43(resp_filter_form.text)
        self.logger.info('{}: got {} account(s): {}'.format(
            company.title,
            len(fin_ent_account_ids_for_n43),
            fin_ent_account_ids_for_n43
        ))
        for acc_id_for_n43 in fin_ent_account_ids_for_n43:
            ok = self.process_account_for_n43(s, company.title, acc_id_for_n43, accounts_scraped)
            if not ok:
                return False
        return True

    def process_account_for_n43(
            self,
            s: MySession,
            org_title: str,
            fin_ent_account_id_for_n43: str,
            accounts_scraped: List[AccountScraped]) -> bool:

        # Get fin_ent_account_id to get dates and status
        # due to unaligned formats
        # of fin_ent_account_id_for_n43 and fin_ent_account_id_to_get_dates_and_status
        accs = [
            acc for acc in accounts_scraped
            if (self._drop_currency_suffix_from_fin_ent_acc_id(acc.FinancialEntityAccountId)
                in fin_ent_account_id_for_n43)
        ]
        if len(accs) != 1:
            self.logger.error("{}: {}: can't find suitable account_scraped from {}".format(
                org_title,
                fin_ent_account_id_for_n43,
                accounts_scraped
            ))
            return False

        # account_no has no currency suffix, 'ES0301280744430100011522' -> '01280744430100011522'
        fin_ent_account_id_to_get_dates_and_status = accs[0].AccountNo[4:]

        self.logger.info('{}: {}: got suitable fin_ent_account_id to get dates and status: {}'.format(
            org_title,
            fin_ent_account_id_for_n43,
            fin_ent_account_id_to_get_dates_and_status
        ))

        date_from, date_to, is_active_account = self.basic_get_n43_dates_and_account_status(
            fin_ent_account_id_to_get_dates_and_status,
            org_title=org_title,
            max_offset=MAX_OFFSET_DAYS
        )
        if not is_active_account:
            return True  # already reported

        ok = self.download_n43_file(s, fin_ent_account_id_for_n43, date_from, date_to)
        return ok

    def download_n43_file(
            self,
            s: MySession,
            fin_ent_account_id: str,
            date_from: datetime,
            date_to: datetime) -> bool:
        req_n4_url = "https://empresas.bankinter.com/www/es-es/cgi/empresas+movsafichero"
        df, mf, yf = date_from.strftime('%d/%m/%Y').split('/')
        dt, mt, yt = date_to.strftime('%d/%m/%Y').split('/')
        req_params = OrderedDict([
            ('CUENTA', fin_ent_account_id),  # '01287611100001666', 01280560100048767 (but sends '01280560100048767001')
            ('PRODUCTO', 'CCR'),
            ('YL0300E-DD-EMISION', df),  # '18'
            ('YL0300E-MM-EMISION', mf),  # '1'
            ('YL0300E-AA-EMISION', yf[-2:]),  # '21'
            ('YL0300E-DD-FINAL', dt),
            ('YL0300E-MM-FINAL', mt),
            ('YL0300E-AA-FINAL', yt[-2:]),
            ('YL0300E-DISPONIB', '8')
        ])
        resp_n43 = s.post(
            req_n4_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if not n43_funcs.validate(resp_n43.content):
            if 'NO HAY INFORMACION' in resp_n43.text:
                return True  # no data
            for marker in CANT_DOWNLOAD_N43_MARKERS:
                if marker in resp_n43.text:
                    self.logger.error("{}: can't download N43: {}. Skip".format(fin_ent_account_id, marker))
                    return False
            self.basic_log_wrong_layout(
                resp_n43,
                "{}: got invalid resp_n43".format(fin_ent_account_id)
            )
            return False

        self.n43_contents.append(resp_n43.text.encode('UTF-8'))

        self.logger.info('{}: downloaded N43 file with movements from {} to {}'.format(
            fin_ent_account_id,
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        ))
        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        ok = self.process_access_for_n43(s, resp_logged_in)

        if ok:
            self.basic_save_n43s(
                self.fin_entity_name,
                self.n43_contents
            )

        self.basic_log_time_spent('GET N43')

        if not ok:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
