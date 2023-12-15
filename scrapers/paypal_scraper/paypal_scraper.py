import random
import time
from collections import OrderedDict
from datetime import datetime
from typing import List, Tuple, Optional

from custom_libs import extract
from custom_libs import requests_helpers
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    ScraperParamsCommon, MainResult, AccountScraped, MovementParsed,
    DOUBLE_AUTH_REQUIRED_TYPE_COOKIE
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from .environs import ENVS, Env

__version__ = '2.8.0'
__changelog__ = """
2.8.0
login: return resp_dashboard only if logged in
2.7.0
login: upd captcha detection
2.6.0
use environs.Env struct
2.5.0
Extra login step to handle phone confirmation request
2.4.0
Envs as dicts
more delays
2.3.0
MOVS_RESCRAPE_OFFSET = 2
use parse_helpers.recalc_mov_temp_balances_from_account_bal
2.2.0
use ENVS instead of cookies 
2.1.0
MOVS_RESCRAPE_OFFSET shorter than default
2.0.0
process_accounts: get movs for all currencies at once to obtain conversion transactions
extract 'secondaryTransactions' (conversion) 
1.0.0
init
"""

CAPTCHA_REASON = 'Redirected to captcha validation page. Should retry later'
WRONG_CREDENTIALS_MARKER = 'Alguno de sus datos no es correcto.'
# No conversion submovements from last month or older than 2 weeks? (see Udemy -29.98 USD 29/10/2021)
# thus, don't try to get old movs by default
MOVS_RESCRAPE_OFFSET = 2


class PayPalScraper(BasicScraper):
    scraper_name = 'PayPalScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.req_proxies = project_settings.DEFAULT_PROXIES[:1]  # 1st 8115

    def _load_all_noscript_images(self, s: MySession, resp_init: Response) -> str:
        """Load all images from <noscript> sections to pass auth validation
        :return err str
        """
        noscript_img_urls = parse_helpers.get_noscript_img_urls(resp_init.text)
        if not noscript_img_urls:
            return "Can't extract noscript_img_urls"
        for img_url in noscript_img_urls:
            _resp = s.get(
                img_url,
                headers=self.req_headers,
                proxies=self.req_proxies
            )
        return ''

    def _set_env(self, s: MySession) -> Tuple[bool, MySession]:
        env = ENVS.get(self.db_financial_entity_access_id)  # type: Optional[Env]
        if not env:
            return False, s
        self.logger.info('Set confirmed environment for access {}'.format(
            self.db_financial_entity_access_id
        ))
        s = requests_helpers.update_mass_cookies(s, env.cookies, '.paypal.com')
        self.req_headers = self.basic_req_headers_updated({
            'User-Agent': env.user_agent
        })
        return True, s

    def login_attempt(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()
        ok, s = self._set_env(s)
        if not ok:
            return s, Response(), False, False, DOUBLE_AUTH_REQUIRED_TYPE_COOKIE

        resp_init = s.get(
            'https://www.paypal.com/es/signin',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        _, req_params = extract.build_req_params_from_form_html_patched(
            resp_init.text,
            form_name='login'
        )
        assert req_params['login_email'] == self.username
        req_params['login_password'] = self.userpass

        err = self._load_all_noscript_images(s, resp_init)
        if err:
            return s, resp_init, False, False, err

        time.sleep(3 + random.random())

        resp_logged_in = s.post(
            'https://www.paypal.com/es/signin',
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        reason = ''
        is_credentials_error = WRONG_CREDENTIALS_MARKER in resp_logged_in.text
        if is_credentials_error:
            return s, resp_logged_in, False, is_credentials_error, reason

        if 'https://www.paypal.com/signin/phone-confirmation/loadPrimaryPhone?intent=business' in resp_logged_in.text:
            self.logger.info('Phone confirmation request detected. Skipping')
        time.sleep(2 + random.random())

        # Just open it directly to pass through 'phone number confirmation' step (and maybe other unnecessary steps)
        resp_dashboard = s.get(
            'https://www.paypal.com/mep/dashboard',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = 'dashboard' in resp_dashboard.url
        if ('Pregunta de seguridad</h1>' in resp_logged_in.text
                and 'recaptcha/recaptcha_v2.html' in resp_logged_in.text):
            reason = CAPTCHA_REASON

        return s, resp_dashboard if is_logged else resp_logged_in, is_logged, is_credentials_error, reason

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        # Initial assignment for linters
        s, resp_logged_in, is_logged, is_credentials_error, reason = (self.basic_new_session(), Response(),
                                                                      False, False, '')
        for att in range(1, 3):
            self.logger.info('Login attempt #{}'.format(att))
            s, resp_logged_in, is_logged, is_credentials_error, reason = self.login_attempt()
            if reason == CAPTCHA_REASON and att < 2:
                self.logger.warning('{}. Wait and retry'.format(reason))
                time.sleep(10 + random.random() * 2)
                continue
            break

        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:

        accounts_parsed = parse_helpers.get_accounts_parsed(resp_logged_in.text, self.username)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                self.db_customer_name,
                acc_parsed,
                account_no_format=acc_parsed['account_no_format'],
                is_default_organization=True
            )
            for acc_parsed in accounts_parsed
        ]

        self.logger.info('Got {} accounts: {}'.format(len(accounts_scraped), accounts_scraped))
        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        self.process_accounts(s, accounts_scraped)

        return True

    def process_accounts(self, s: MySession, accounts_scraped: List[AccountScraped]) -> bool:
        """Gets all movements of all currencies in one list to obtain
        valid temp_balances of submovements (secondaryTransactions) which are conversion transactions
        between own currency-divided accounts (USD to EUR and so on).
        Then calls process_account with those movs_parsed
        """

        accounts_scraped_active = [
            acc for acc
            in accounts_scraped
            if self.basic_check_account_is_active(acc.FinancialEntityAccountId)
        ]
        if not accounts_scraped_active:
            return True

        date_from = None  # type: Optional[datetime]
        date_from_str = ''

        # Get the youngest date_from for all accounts (general account divided by currency)
        # It is necessary because movements belonging to one account can be displayed in another,
        # thus, to get all movements properly, we need to get them for all currencies at once
        # and then link to appropriate account by currency
        for acc in accounts_scraped:
            if not self.basic_check_account_is_active(acc.FinancialEntityAccountId):
                continue

            fin_ent_account_id = acc.FinancialEntityAccountId

            date_from_i, date_from_str_i = self.basic_get_date_from_dt(
                fin_ent_account_id,
                rescraping_offset=MOVS_RESCRAPE_OFFSET
            )
            if not date_from:
                date_from, date_from_str = date_from_i, date_from_str_i
                continue
            if date_from and date_from_i > date_from:
                date_from, date_from_str = date_from_i, date_from_str_i
                continue

        assert date_from

        self.basic_log_process_account('ALL CURRENCIES', date_from_str)

        # str(date_from.day) just to get '8' instead of '08' for 08/10/2021 (see req_params)
        # Tricky thing: month index starts from 0
        d_from, m_from, y_from = str(date_from.day), str(date_from.month - 1), str(date_from.year)
        d_to, m_to, y_to = str(self.date_to.day), str(self.date_to.month - 1), str(self.date_to.year)

        movements_parsed_desc = []  # type: List[MovementParsed]
        next_page_token = ''
        referer = 'https://www.paypal.com/activities/?fromDate={}&toDate={}'.format(
            date_from.strftime('%Y-%m-%d'),  # 2021-09-01
            self.date_to.strftime('%Y-%m-%d')
        )
        for page_ix in range(1, 101):  # avoid inf loop
            self.logger.info('download movements from page #{}'.format(page_ix))
            req_params = OrderedDict([
                ('need_shipping_info', 'true'),
                ('need_actions', 'true'),
                ('sort', 'time_created'),
                ('entrypoint', ''),
                ('limit', ''),
                ('next_page_token', next_page_token),
                ('client', 'biztransactions'),
                ('transactiontype', 'ALL_TRANSACTIONS'),
                ('archive', 'ACTIVE_TRANSACTIONS'),
                # Need to filter all at once to get valid temp_balances
                # of subtransactions, which are mostly exchange transactions between accounts
                ('currency', 'ALL_TRANSACTIONS_CURRENCY'),
                ('fromdate_day', d_from),
                ('fromdate_month', m_from),  # '8', not '08'
                ('fromdate_year', y_from),
                ('todate_day', d_to),
                ('todate_month', m_to),
                ('todate_year', y_to)
            ])

            resp_movs_i = s.get(
                'https://www.paypal.com/listing/transactions/activity',
                params=req_params,
                headers=self.basic_req_headers_updated({
                    'X-REQUESTED-WITH': 'XHR',
                    'Referer': referer
                }),
                proxies=self.req_proxies
            )

            try:
                resp_movs_i_json = resp_movs_i.json()
            except Exception as _e:
                self.basic_log_wrong_layout(
                    resp_movs_i,
                    "can't get resp_movs_i_json. Break pagination"
                )
                break

            movs_parsed_i = parse_helpers.get_movements_parsed(resp_movs_i_json)
            movements_parsed_desc.extend(movs_parsed_i)

            # Early stop, no 'nextpageurl' field
            if not movs_parsed_i:
                break

            try:
                next_page_token = resp_movs_i_json['data']['nextpageurl']
            except Exception as _e:
                self.basic_log_wrong_layout(
                    resp_movs_i,
                    "can't get next page url. Break pagination"
                )
                break

            if not next_page_token:
                self.logger.info('no more pages with movements')
                break
            time.sleep(0.5 * (1 + random.random()))

        for account_scraped in accounts_scraped:
            self.process_account(
                account_scraped,
                movements_parsed_desc,
                date_from_str
            )

        return True

    def process_account(
            self,
            account_scraped: AccountScraped,
            movements_parsed_desc: List[MovementParsed],
            date_from_str: str) -> bool:
        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        acc_currency = account_scraped.Currency

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_desc,
            date_from_str
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        movements_parsed_desc_currency = [
            mov for mov
            in movements_parsed_desc
            if mov['currency'] == acc_currency
        ]

        # Works only if -t (date_to) == today
        if self.date_to.date() == datetime.utcnow().date():
            movements_parsed_desc_currency_recalculated_balances = \
                parse_helpers.recalc_mov_temp_balances_from_account_bal(
                    account_scraped.Balance,
                    movements_parsed_desc_currency
                )
        else:
            movements_parsed_desc_currency_recalculated_balances = movements_parsed_desc_currency

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_desc_currency_recalculated_balances,
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
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error(last_resp=resp_logged_in)

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        self.process_access(s, resp_logged_in)
        self.basic_log_time_spent('GET MOVEMENTS')

        return self.basic_result_success()
