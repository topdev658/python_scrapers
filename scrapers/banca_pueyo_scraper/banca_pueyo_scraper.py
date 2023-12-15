from typing import List, Tuple

from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (AccountScraped, MOVEMENTS_ORDERING_TYPE_ASC, DOUBLE_AUTH_REQUIRED_TYPE_COMMON,
                                  ScraperParamsCommon, MainResult)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers

__version__ = '1.4.0'

__changelog__ = """
1.4.0
parse_helpers: added get_movements_parsed
process_access: process movements
1.3.0
process_access: implemented accounts_parsed and accounts_scraped
1.2.0
login: implemented 2fa error
added dev folder
1.1.0
BasicScraper integration
created scraper foundation
"""

DOUBLE_AUTH_MARKERS = [
    '"psd2scaStatus":"REQUIRED_ENABLED"',
]

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:104.0) Gecko/20100101 Firefox/104.0'


class BancaPueyoScraper(BasicScraper):
    scraper_name = "BancaPueyoScraper"

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.req_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.5',
            # 'Authorization': '',
            'User-Agent': USER_AGENT,
            'Connection': 'Keep-Alive',
        }

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:

        s = self.basic_new_session()
        reason = ''

        token_url = 'https://www.e-pueyo.com/e-pueyo2.0/prod/back/uaa/oauth/token'

        req_params = {
            'grant_type': 'password',
            'username': self.username,
            'password': self.userpass,
            'userConnectionInfo': '{"application":"web","userAgent":"Mozilla/5.0 (X11; '
                                  'Linux x86_64; rv:104.0) Gecko/20100101 Firefox/104.0",'
                                  '"geolocation":{"latitude":"0","longitude":"0"}}',
        }

        resp_token = s.post(
            token_url,
            params=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_credentials_error = 'unauthorized' in resp_token.text
        if is_credentials_error:
            is_logged = False
            return s, resp_token, is_logged, is_credentials_error, reason

        token_json = resp_token.json()
        access_token = token_json['access_token']
        bank_app = token_json['app']
        token_expires_in = token_json['expires_in']
        refresh_token = token_json['refresh_token']
        token_type = token_json['token_type']

        self.req_headers['Authorization'] = token_type.capitalize() + access_token

        user_info_url = 'https://www.e-pueyo.com/e-pueyo2.0/prod/back/services/users/v1/info'

        json_data = {
            "version": "3.0.2"
        }

        resp_user_info = s.post(
            user_info_url,
            json=json_data,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = '"AUTH_USER"' in resp_user_info.text

        if any(m in resp_user_info.text for m in DOUBLE_AUTH_MARKERS):
            is_logged = False
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        return s, resp_user_info, is_logged, is_credentials_error, reason

    def process_account(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            contract_number: str) -> bool:

        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        date_to_str = self.date_to_str or None

        movs_req_params = {
            'from': date_from_str,
            'to': date_to_str
        }
        has_more = True
        list_movements_parsed = []
        tx_id = None

        while has_more:
            movs_resp = s.get(
                'https://www.e-pueyo.com/e-pueyo2.0/prod/back/services/accounts/v2/'
                '{}/movement-extract'.format(contract_number),
                headers=self.req_headers,
                proxies=self.req_proxies,
                params=movs_req_params
            )
            movs_resp_json = movs_resp.json()

            if movs_resp.status_code == 510:
                self.logger.info("Failed to parse movements. "
                                 "Error: {}".format(movs_resp_json["error"]["message"]))
                break

            list_movements_parsed.append(parse_helpers.get_movements_parsed(movs_resp_json))

            has_more = movs_resp_json['hasMore']

            if not tx_id:
                tx_id = movs_resp_json['filter']['txId']  # for future movements pages requests
                movs_req_params = {
                    'txId': tx_id
                }

        movements_parsed = []
        for mov_list in reversed(list_movements_parsed):
            movements_parsed.extend(mov_list)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        self.basic_log_time_spent('GET MOVEMENTS')

        return True

    def process_access(self, s: MySession) -> bool:
        resp_accounts = s.get(
            'https://www.e-pueyo.com/e-pueyo2.0/prod/back/services/'
            'products/v1/global-position',
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        req_headers = {
            "Accept": "*/*",
            "User-Agent": USER_AGENT,
        }

        resp_script = s.get(
            'https://www.e-pueyo.com/82.ae12380cb3924411dce0.chunk.js',
            headers=req_headers,
            proxies=self.req_proxies,
        )

        accounts_parsed = parse_helpers.get_accounts_parsed(resp_accounts.json(), resp_script.text)

        process_accounts = [
            {
                "account": self.basic_account_scraped_from_account_parsed(
                    account_parsed['org_title'],
                    account_parsed,
                ),
                "contract_number": account_parsed['contract_number']
            }
            for account_parsed in accounts_parsed
        ]

        accounts_scraped = [
            process_account["account"]
            for process_account in process_accounts
        ]

        self.logger.info('Got {} accounts: {}'.format(
            len(accounts_scraped),
            accounts_scraped
        ))

        self.basic_log_time_spent('GET ACCOUNTS')
        self.basic_upload_accounts_scraped(accounts_scraped)

        for process_account in process_accounts:
            self.process_account(s, process_account["account"], process_account["contract_number"])

        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp_logged_in.url, resp_logged_in.text, reason)

        self.process_access(s)
        self.logger.info('Processing main()')

        return self.basic_result_success()