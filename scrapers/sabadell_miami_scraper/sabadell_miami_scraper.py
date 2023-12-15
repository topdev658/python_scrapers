import re
import time
from collections import OrderedDict
from typing import Tuple, List
from urllib.parse import quote, urljoin, urlparse

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (ACCOUNT_NO_TYPE_UNKNOWN, ScraperParamsCommon, MainResult)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.sabadell_miami_scraper import parse_helpers

__version__ = '2.4.0'
__changelog__ = """
2.4.0
parse_helpers: get_accounts_parsed_wo_balance for layouts with one or many accounts (different)
2.3.0
use account-level result_codes
2.2.0
call basic_upload_movements_scraped with date_from_str
2.1.1
parse_helpers: fixed typing
2.1.0
parse_helpers: get_account_parsed: more places to get currency, suitable for Sabadell UK (child)
2.0.0
properties and methods to use in children (SabadellUKScraper for now)
1.1.0
use basic_new_session
upd type hints
fmt
1.0.0
init
"""

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0'


class SabadellMiamiScraper(BasicScraper):
    scraper_name = 'SabadellMiamiScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.req_headers = {'User-Agent': USER_AGENT}
        self.base_url = 'https://www.bancosabadellmiami.com/txbsmi/'
        self.init_url = 'https://www.bancosabadellmiami.com/cs/Satellite/BSMiami/Empresas/4000002921912/es/'
        self.req_param_date_fmt = '%m/%d/%Y'
        self.movement_date_fmt = '%m/%d/%Y'
        self.country_code = 'USA'

    def _get_accounts_parsed_wo_balance_from_dropdown(self, resp_accounts: Response) -> List[dict]:
        accs_wo_balance = parse_helpers.get_accounts_parsed_wo_balance(resp_accounts.text)
        return accs_wo_balance

    def login(self) -> Tuple[MySession, Response, bool, bool]:
        s = self.basic_new_session()

        # Get initial cookies
        resp_init = s.get(
            self.init_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # From StaticFiles/GrupoBS/js/commons.js:setJSESSIONID_JBSWL()
        s.cookies.set(
            'JSESSIONID_JBSWL',
            s.cookies.get('JSESSIONID')[:24] + str(int(time.time() * 1000)),
            domain=urlparse(self.base_url).netloc,
            path='/'
        )

        req_params = {
            "evision.userLang": "",
            "evision.RSADeviceFso": "",
            "evision.RSADevicePrint": quote(
                'version=2'
                '&pm_fpua=mozilla/5.0 (x11; ubuntu; linux x86_64; rv:69.0) '
                'gecko/20100101 firefox/69.0|5.0 (X11)|Linux x86_64'
                '&pm_fpsc=24|1600|900|868&pm_fpsw=&pm_fptz=3&pm_fpln=lang=en-US|syslang=|userlang='
                '&pm_fpjv=0&pm_fpco=1&pm_fpasw=&pm_fpan=Netscape&pm_fpacn=Mozilla&pm_fpol=true&pm_fposp=&pm_fpup='
                '&pm_fpsaw=1600&pm_fpspd=24&pm_fpsbd=&pm_fpsdx=&pm_fpsdy=&pm_fpslx=&pm_fpsly=&pm_fpsfse=&pm_fpsui='
            ),
            "evision.csid": s.cookies.get('JSESSIONID_JBSWL'),
            "locale": "es",
            "j_password": self.userpass,
            "j_username": self.username,
            "j_pwd": ""
        }

        resp_logged_in = s.post(
            urljoin(self.base_url, 'j_spring_security_check'),
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_credentials_error = 'El usuario o contraseña introducidos no son correctos' in resp_logged_in.text
        is_logged = 'Saldos y movimientos' in resp_logged_in.text
        return s, resp_logged_in, is_logged, is_credentials_error

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        # Saldos y movimientos menu
        resp_accounts = s.get(
            urljoin(self.base_url, 'accountmovements.html'),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_parsed_wo_balance = self._get_accounts_parsed_wo_balance_from_dropdown(resp_accounts)

        for account_parsed_wo_balance in accounts_parsed_wo_balance:
            self.process_account(s, account_parsed_wo_balance)

        return True

    def process_account(self, s: MySession,
                        account_parsed_wo_balance: dict) -> bool:

        fin_ent_account_id = account_parsed_wo_balance['account_no']
        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        # To get execution param for multi-account accesses
        resp_accounts = s.get(
            urljoin(self.base_url, 'accountmovements.html'),
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        execution_param = extract.re_first_or_blank(r'execution=(e\d+s\d+)', resp_accounts.text)

        req_movs_filtered_url = urljoin(self.base_url, 'accountmovements.html')
        req_movs_filtered_data = OrderedDict([
            ('accountNumber', account_parsed_wo_balance['account_req_param']),
            ('dateCombo', '-1'),
            ('dateOption', '1'),
            ('dateFrom', date_funcs.convert_date_str(date_from_str, self.req_param_date_fmt)),
            ('dateTo', date_funcs.convert_date_str(self.date_to_str, self.req_param_date_fmt)),  # '09/01/2019')
            ('formatOption', '0'),
            ('_eventId_aceptar', 'Aceptar'),
        ])

        resp_movs_filtered = s.post(
            req_movs_filtered_url,
            params={'execution': execution_param},
            data=req_movs_filtered_data,
            headers=self.basic_req_headers_updated({
                'DNT': '1',
                'Referer': resp_accounts.url
            }),
            proxies=self.req_proxies
        )

        account_parsed = parse_helpers.get_account_parsed(resp_movs_filtered.text, account_parsed_wo_balance)
        if not account_parsed:
            self.basic_log_wrong_layout(resp_movs_filtered, "Can't get account_parsed. Skip")
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
            return False

        account_scraped = self.basic_account_scraped_from_account_parsed(
            account_parsed['organization_title'],
            account_parsed,
            country_code=self.country_code,
            account_no_format=ACCOUNT_NO_TYPE_UNKNOWN
        )

        self.basic_log_time_spent('GET BALANCES')
        self.basic_upload_accounts_scraped([account_scraped])
        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        # 1st page
        movements_parsed = parse_helpers.get_movements_parsed(
            resp_movs_filtered.text,
            self.movement_date_fmt
        )
        resp_prev = resp_movs_filtered
        for page_ix in range(2, 100):  # max 2000 movs
            if '20 más' not in resp_prev.text:
                break
            # e1s2..e1s3..
            self.logger.info('{}: get movs from page {}'.format(fin_ent_account_id, page_ix))
            execution_param = re.sub(r's\d+', 's{}'.format(page_ix), execution_param)

            resp_movs_filtered_i = s.post(
                req_movs_filtered_url,
                params={'execution': execution_param},
                data={'_eventId_siguiente': '20 más'},
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            movements_parsed_i = parse_helpers.get_movements_parsed(
                resp_movs_filtered_i.text,
                self.movement_date_fmt
            )
            if movements_parsed_i:
                self.logger.info('{}: page {}: oldest mov date {} of {}'.format(
                    fin_ent_account_id,
                    page_ix,
                    movements_parsed_i[-1]['operation_date'],
                    date_from_str
                ))
            movements_parsed.extend(movements_parsed_i)
            resp_prev = resp_movs_filtered_i

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
        s, resp_logged_in, is_logged, is_credentials_error = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url, resp_logged_in.text)

        self.process_access(s, resp_logged_in)

        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
