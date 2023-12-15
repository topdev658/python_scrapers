import random
import time
from collections import OrderedDict
from datetime import timedelta

from custom_libs import date_funcs, n43_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from . import parse_helpers
from .caixa_guissona_scraper import CaixaGuissonaScraper
from .custom_types import AccountExtracted

__version__ = '2.1.0'

__changelog__ = """
2.1.0
date_from_str 
now it only has yesterday's date
2.0.0
refactored
1.0.0
stable
0.1.0
Add
_open_file_transmission
process_download_account
download_n43
"""


class CaixaGuissonaN43Scraper(CaixaGuissonaScraper):
    scraper_name = 'CaixaGuissonaN43Scraper'
    fin_entity_name = 'CAIXA_GUISSONA'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    def _open_file_transmission_page(self, s: MySession) -> None:
        """Open the page to allow N43 downloading then"""
        req_file_transmission_url = 'https://www.caixaguissona.com/es/private/filetransmission'

        # No need the resp itself
        _resp_file_transmission = s.get(
            req_file_transmission_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        return

    def process_access_for_n43(
            self,
            s: MySession,
            resp_logged_in: Response,
            token: str) -> bool:
        ok, accounts = self._get_accounts_extracted(resp_logged_in)
        if not ok:  # already reported
            return False

        self._open_file_transmission_page(s)

        for account in accounts:
            ok = self.process_account_for_n43(s, account, token)
            if not ok:  # already reported
                return False
        return True

    def process_account_for_n43(
            self,
            s: MySession,
            account: AccountExtracted,
            token: str) -> bool:

        self.logger.info("{} ({}): START TO DOWNLOAD N43".format(
            account.account_no,
            account.account_alias
        ))

        req_file_donwload = 'https://www.caixaguissona.com/es/private/findCSB43'
        req_params = OrderedDict([
            ('accountNumber', account.account_no),
            ('__RequestVerificationToken', token)
        ])
        resp_count_details = s.post(
            req_file_donwload,
            req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        token_account = parse_helpers.get_verification_token_account(resp_count_details.text)
        ok = self.download_n43(s, token_account, account)
        if not ok:
            return False  # already reported
        return True

    def download_n43(
            self,
            s: MySession,
            token_account: str,
            account: AccountExtracted) -> bool:

        account_no = account.account_no

        req_url_download_n43 = 'https://www.caixaguissona.com/es/private/findcsb43ok'
        # ONLY yesterday files provide correct 'initial balance' (!)
        date_from = date_funcs.today() - timedelta(days=1)
        date_from_str = date_from.strftime('%d/%m/%y')
        date_to_str = date_from_str

        self.logger.info("{}: DOWNLOADING... N43 FROM {} TO {}".format(
            account_no,
            date_from_str,
            date_to_str
        ))
        req_params = OrderedDict([
            ('__RequestVerificationToken', token_account),
            ('dataInici', date_from_str),
            ('dataFi', date_to_str)
        ])
        resp_n43_file = s.post(
            req_url_download_n43,
            req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        time.sleep(1 + random.random())
        n43_text = resp_n43_file.text
        n43_content = n43_text.encode('UTF-8')

        if not (n43_text and n43_funcs.validate(n43_content)):
            self.basic_log_wrong_layout(
                resp_n43_file,
                "{}: got invalid resp_n43 (wrong N43 content)".format(account_no)
            )
            return False

        if not n43_funcs.validate_n43_structure(n43_text):
            self.logger.warning(
                "{}: N43 file with broken structure detected. Skip. CONTENT:\n{}".format(
                    account_no,
                    resp_n43_file.text,
                )
            )
            # Still True to allow download other files, because it's not a scraping error
            return True

        self.n43_contents.append(n43_content)
        self.logger.info('{}: downloaded N43 file'.format(account_no))
        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, reason, token = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        ok = self.process_access_for_n43(s, resp_logged_in, token)
        self.basic_log_time_spent('GET N43')

        if not ok:
            return self.basic_result_common_scraping_error()

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
