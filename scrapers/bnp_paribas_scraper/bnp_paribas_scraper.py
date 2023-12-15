import urllib.parse
from typing import Tuple

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (AccountScraped, ScraperParamsCommon,
                                  MainResult, DOUBLE_AUTH_REQUIRED_TYPE_OTP)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.bnp_paribas_scraper import login_helpers
from scrapers.bnp_paribas_scraper import parse_helpers

__version__ = '2.2.0'

__changelog__ = """
2.2.0
call basic_upload_movements_scraped with date_from_str
2.1.0
skip inactive accounts
2.0.0
2fa required by default - can't process
1.6.0
detect 'change the password' action and return as a reason
1.5.0
process_contract: try resp.json()
1.4.0
use basic_new_session
upd type hints
1.3.0
use basic_get_date_from
fmt
1.2.0
unsupported access type detector
1.1.0
parse_helpers: get_accounts_parsed: upd markers to get correct accounts  
1.0.1
upd comments
1.0.0
init
"""

IS_LOGGED_MARKERS = ['/sommaire/PseDisconnection']

# Handle different languages:
# Your identification is wrong. Please renew your data entry'
# Votre identification est erronée. Merci de renouveler votre saisie
CREDENTIALS_ERROR_MARKER = 'Information</span></h2><p class="message">AMDP-900'


class BNPParibasScraper(BasicScraper):
    """Website restriction: the scraper can scrape movements not older than 3 months"""
    scraper_name = 'BNPParibasScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.update_inactive_accounts = False

    def _get_encrypted(self, s: MySession, resp_init: Response, userpass: str) -> str:
        """
        Download gridpass img
        Get map digit to code
        Then build userpass_encypted
        """

        gridpass_tiles_to_codes = parse_helpers.get_gridpass_tile_to_code(resp_init.text)

        gridpass_img_src = parse_helpers.get_gridpass_img_src(resp_init.text)
        gridpass_img_url = urllib.parse.urljoin(resp_init.url, gridpass_img_src)

        resp_gridpass_img = s.get(
            gridpass_img_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        self.logger.info('Detect digits_to_codes on graphical gridpass')
        digits_to_codes = login_helpers.get_digits_to_codes(
            resp_gridpass_img.content,
            gridpass_tiles_to_codes
        )

        pass_encrypted = ''
        for digit_str in userpass:
            digit = int(digit_str)
            digit_encrypted = digits_to_codes[digit]
            pass_encrypted += digit_encrypted

        return pass_encrypted

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()

        # VB: 12.09.2020 PREVIOUS METHODS ARE NOT AVAILABLE ANY MORE
        return s, Response(), False, False, DOUBLE_AUTH_REQUIRED_TYPE_OTP

        # DEAD CODE NOW
        req_url_init = 'https://secure1.entreprises.bnpparibas.net/sommaire/jsp/identification.jsp'
        resp_init = s.get(
            req_url_init,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        pass_encrypted = self._get_encrypted(s, resp_init, self.userpass)

        req_login_url = 'https://secure1.entreprises.bnpparibas.net/sommaire/PseMenuServlet'
        req_login_params = {
            'txtAuthentMode': 'PASSWORD',
            'BEFORE_LOGIN_REQUEST': '',
            'txtPwdUserId': self.username,
            'gridpass_hidden_input': pass_encrypted
        }

        resp_logged_in = s.post(
            req_login_url,
            data=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20
        )

        is_logged = any(m in resp_logged_in.text for m in IS_LOGGED_MARKERS)
        is_credentials_error = CREDENTIALS_ERROR_MARKER in resp_logged_in.text

        reason = ''
        if 'Modifier votre mot de passe' in resp_logged_in.text:
            reason = 'Website requires to change the password. Pls, inform the customer. Finishing now'

        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def process_contract(self, s: MySession, resp: Response) -> bool:

        self.logger.info('Process contract')
        resp_accounts_url = ('https://secure1.entreprises.bnpparibas.net/'
                             'NCCPresentationWeb/e10_soldes/liste_soldes.do')

        req_headers = self.basic_req_headers_updated(
            {'X-Requested-With': 'XMLHttpRequest'}
        )

        resp_accounts = s.get(
            resp_accounts_url,
            headers=req_headers,
            proxies=self.req_proxies
        )

        try:
            resp_accounts_json = resp_accounts.json()
        except Exception as e:
            self.logger.error("Can't parse resp_accounts: {}. Abort. RESPONSE:\n{}".format(
                e,
                resp_accounts.text
            ))
            return False

        accounts_parsed = parse_helpers.get_accounts_parsed(resp_accounts_json)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                self.db_customer_name,
                acc_parsed,
                country_code=acc_parsed['country_code'],
                is_default_organization=True
            )
            for acc_parsed in accounts_parsed
        ]
        self.logger.info('Contract has accounts: {}'.format(accounts_scraped))
        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET ACCOUNTS')

        # serial processing
        # not tested on several accs
        for account_scraped in accounts_scraped:
            self.process_account(s, resp_accounts, account_scraped)

        return True

    def process_account(self,
                        s: MySession,
                        resp: Response,
                        account_scraped: AccountScraped) -> bool:

        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        d_from, m_from, y_from = date_from_str.split('/')

        date_from_for_movs = '{}{}{}'.format(y_from, m_from, d_from)  # 20180801
        date_to_for_movs = self.date_to.strftime('%Y%m%d')

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        # not necessary to set pagination, req_movs will extract all movs
        # pagination in web:
        # https://secure1.entreprises.bnpparibas.net/NCCPresentationWeb/
        # m99_pagination/setStatutPagination.do?
        # ecran=e11_releve_op&nbEntreesParPage=50&numPage=1

        req_mov_init_url = ('https://secure1.entreprises.bnpparibas.net/'
                            'NCCPresentationWeb/e11_releve_op/init.do')
        req_mov_init_params = {
            'identifiant': fin_ent_account_id,
            'typeSolde': 'C',
            'typeDate': 'D',
            'typeReleve': 'Comptable',
            'dateMin': date_from_for_movs,
            'dateMax': date_to_for_movs,
            'e10': 'true',
        }

        # necessary or resp_mov will fail
        resp_mov_init = s.post(
            req_mov_init_url,
            data=req_mov_init_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # extracts more than 20 movs (all)
        req_mov_params = {
            'identifiant': fin_ent_account_id,
            'typeSolde': 'C',
            'typeReleve': 'Previsionnel',
            'typeDate': 'O',
            'dateMin': date_from_for_movs,
            'dateMax': date_to_for_movs,
            'ajax': 'true',
        }

        req_mov_url = ('https://secure1.entreprises.bnpparibas.net/'
                       'NCCPresentationWeb/e11_releve_op/listeOperations.do')

        req_headers = self.basic_req_headers_updated(
            {'X-Requested-With': 'XMLHttpRequest'}
        )

        resp_mov = s.get(
            req_mov_url,
            params=req_mov_params,
            headers=req_headers,
            proxies=self.req_proxies
        )

        resp_json = resp_mov.json()
        is_all_movs = resp_json['libellesComplets'] is True
        if not is_all_movs:
            self.logger.error(
                "{}: can't extract all movements at once for date_from={} date_to={}. "
                "Pls, USE SHORTER TIME FRAME to extract movements".format(
                    fin_ent_account_id,
                    date_from_str,
                    self.date_to_str
                ))
            return False

        movements_parsed = parse_helpers.get_movements_parsed(resp_mov.json(),
                                                              account_scraped.Balance)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )
        return True

    def main(self) -> MainResult:
        if self.access_type != 'Password':
            self.logger.error("Unsupported access type '{}'. Abort".format(
                self.access_type
            ))
            return self.basic_result_common_scraping_error()

        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        self.process_contract(s, resp_logged_in)

        self.basic_log_time_spent('GET ALL MOVEMENTS')

        return self.basic_result_success()
