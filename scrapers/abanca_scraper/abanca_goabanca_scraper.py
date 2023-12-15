import random
import time
from typing import Dict, Tuple, List

from custom_libs import requests_helpers
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import AccountScraped, DOUBLE_AUTH_REQUIRED_TYPE_COOKIE
from project.custom_types import ScraperParamsCommon, MainResult, MovementParsed
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers_goabanca
from .custom_types import ContractGoAbanca
from .environs import Env, ENVS, ENV_DEFAULT

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""


def delay() -> None:
    time.sleep(0.1 + random.random())


class AbancaGoAbancaScraper(BasicScraper):
    scraper_name = 'AbancaGoAbancaScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        # Common headers for all reqs, then need to use set_env_headers
        self.req_headers = self.basic_req_headers_updated({
            'X-APPLICATION-ID': 'BE',
            'X-CHANNEL-KEY': 'B',
        })

        # Any IP is allowed, but this one was used for confirmation
        # self.req_proxies = [
        #     {
        #         'http': 'http://:@192.168.195.114:8120',
        #         'https': 'http://:@192.168.195.114:8120'
        #     },
        # ]

        self.access_token = ''  # will set if logged in

    def set_env_headers(self):
        """Set custom headers (usually User-Agent)"""
        env = ENVS.get(self.db_financial_entity_access_id, ENV_DEFAULT)  # type: Env
        self.logger.info('Set confirmed environment headers for access {}'.format(
            self.db_financial_entity_access_id
        ))
        self.req_headers = self.basic_req_headers_updated(env.headers)

    def set_env_cookies(self, s: MySession) -> MySession:
        env = ENVS.get(self.db_financial_entity_access_id, ENV_DEFAULT)  # type: Env
        self.logger.info('Set confirmed environment cookies for access {}'.format(
            self.db_financial_entity_access_id
        ))
        s = requests_helpers.update_mass_cookies(s, env.cookies, '.novobanco.es')
        return s

    def _auth_headers(self, extra_headers: Dict[str, str] = None) -> Dict[str, str]:
        """Auth headers for each portal request"""
        headers = self.basic_req_headers_updated({
            'Authorization': 'Bearer {}'.format(self.access_token)
        })
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()
        s = self.set_env_cookies(s)
        self.set_env_headers()

        req_params = {
            'grant_type': 'password',
            'username': self.username,
            'password': self.userpass,
        }

        resp_logged_in = s.post(
            'https://empresas-go.abanca.com/auth-server/oauth/token',
            data=req_params,
            headers=self.basic_req_headers_updated({
                # 'YmFua2luZ19jbGllbnQ6c2VjcmV0MQ==' == base64('banking_client:secret1')
                'Authorization': 'Basic YmFua2luZ19jbGllbnQ6c2VjcmV0MQ=='
            }),
            proxies=self.req_proxies
        )
        try:
            resp_logged_in_json = resp_logged_in.json()
        except Exception as _e:
            reason = "Can't get resp_logged_in_json"
            return s, resp_logged_in, False, False, reason

        is_logged = 'access_token' in resp_logged_in.text
        is_credentials_error = 'Los datos de acceso introducidos no son correctos' in resp_logged_in.text
        reason = ''

        if is_logged:
            self.access_token = resp_logged_in_json['access_token']

        if 'LA OPERATIVA REQUIERE FIRMA' in resp_logged_in.text:
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COOKIE

        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def process_access(self, s: MySession) -> bool:
        resp_me = s.get(
            'https://empresas-go.abanca.com/api-users/users/me',
            headers=self._auth_headers(),
            proxies=self.req_proxies
        )

        ok, resp_me_json = self.basic_get_resp_json(
            resp_me,
            "Can't get resp_me. Abort"
        )
        if not ok:
            return False  # already reported

        ok, contracts = parse_helpers_goabanca.get_contracts(resp_me_json)
        if not ok:
            self.basic_log_wrong_layout(resp_me, "Can't get contracts. Abort")
            return False

        delay()
        for contract in contracts:
            self.process_contract(s, contract)
        return True

    def process_contract(self, s: MySession, contract: ContractGoAbanca) -> bool:
        org_title = contract.org_title
        self.logger.info('Process contract: {}'.format(org_title))
        resp_accs = s.get(
            'https://empresas-go.abanca.com/api-accounts/accounts',
            headers=self._auth_headers(extra_headers={
                'X-USER-PROFILE-ID': contract.profile_id_param
            }),
            proxies=self.req_proxies
        )
        ok, resp_accs_json = self.basic_get_resp_json(
            resp_accs,
            "Can't get resp_accs_json. Skip"
        )
        if not ok:
            return False  # already reported

        ok, accounts_parsed = parse_helpers_goabanca.get_accounts_parsed(resp_accs_json)
        if not ok:
            self.basic_log_wrong_layout(
                resp_accs,
                "Can't get accounts_parsed"
            )

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                org_title,
                acc
            )
            for acc in accounts_parsed
        ]
        self.logger.info('{}: got {} accounts: {}'.format(
            org_title,
            len(accounts_scraped),
            accounts_scraped
        ))
        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        for account_scraped in accounts_scraped:
            self.process_account(
                s,
                contract,
                account_scraped
            )

        return True

    def process_account(
            self,
            s: MySession,
            contract: ContractGoAbanca,
            account_scraped: AccountScraped) -> bool:
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from, date_from_str = self.basic_get_date_from_dt(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        req_movs_url = 'https://empresas-go.abanca.com/api-accounts/accounts/{}/movements'.format(
            fin_ent_account_id
        )

        req_movs_params = {
            'dateFrom': date_from.strftime('%Y%m%d'),  # '20201201'
            'dateTo': self.date_to.strftime('%Y%m%d'),  # '20201223',
        }

        movements_parsed_desc = []  # type: List[MovementParsed]
        next_page_key = ''
        for page_ix in range(1, 101):  # avoid inf loop
            self.logger.info('{}: page #{}: get movements'.format(
                fin_ent_account_id,
                page_ix
            ))
            if next_page_key:
                req_movs_params['paginationKey'] = next_page_key

            resp_movs_i = s.get(
                req_movs_url,
                params=req_movs_params,
                headers=self._auth_headers(extra_headers={
                    'X-USER-PROFILE-ID': contract.profile_id_param
                }),
                proxies=self.req_proxies
            )

            ok, resp_movs_i_json = self.basic_get_resp_json(
                resp_movs_i,
                "{}: can't get resp_movs_i_json. Skip".format(fin_ent_account_id)
            )
            if not ok:
                break

            ok, movs_parsed_desc_i = parse_helpers_goabanca.get_movements_parsed(resp_movs_i_json)
            if not ok:
                self.basic_log_wrong_layout(
                    resp_movs_i,
                    "{}: can't get movements_parsed. Skip".format(fin_ent_account_id)
                )
                break
            movements_parsed_desc.extend(movs_parsed_desc_i)
            ok, has_next_page, next_page_key = parse_helpers_goabanca.get_next_page_key(resp_movs_i_json)
            if not ok:
                self.basic_log_wrong_layout(
                    resp_movs_i,
                    "{}: can't get next_page_key. Skip".format(fin_ent_account_id)
                )
                break
            if not has_next_page:
                self.logger.info('{}: page #{}: no more pages with movements'.format(
                    fin_ent_account_id,
                    page_ix
                ))
                break

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_desc,
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
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        self.process_access(s)

        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
