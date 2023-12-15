import subprocess
from collections import OrderedDict
from typing import Dict, Tuple, Optional, List
import json
import os

from custom_libs import date_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, MovementParsed,
    ScraperParamsCommon, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_COMMON
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.santander_scraper import parse_helpers_particulares
from .santander_empresas_scraper import USER_AGENT

__version__ = '2.11.0'

__changelog__ = """
2.11.0
use basic_is_in_process_only_accounts
2.10.0
call basic_upload_movements_scraped with date_from_str
2.9.0
more WRONG_CREDENTIALS_MARKERS
login: 
  upd auth (new endpoints, upd reqs)
  upd 2fa notif
upd req urls (accouns, movs)
2.8.0
upd req urls
2.7.1
_session_token: correct assignment from headers
2.7.0
upd login (w/ encryption)
_get_encrypted
2.6.1
fixed typing
2.6.0
skip inactive accounts
2.5.0
upd login method
upd process_access (new api endpoint)
parse_helpers: get_accounts_parsed_nuevo: upd for the new layout
2.4.0
session_token
2.3.0
upd wrong credentials detector
2.2.0
double auth detector
removed several attempts (no need)
2.1.0
several login attempts to handle temporary unknown reason 
2.0.0
impl for new website
1.4.1
use basic_new_session
"""

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'santander_particulares_encrypter.js'
))

WRONG_CREDENTIALS_MARKERS = [
    'ERROR_LOGIN',
    'Invalid credentials',
]


class SantanderParticularesScraper(BasicScraper):
    scraper_name = 'SantanderParticularesScraperNewWeb'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.req_headers = {'User-Agent': USER_AGENT}
        self._auth_token = ''
        self._sid = ''
        self._company_title = ''
        self._session_token = ''
        self.update_inactive_accounts = False

    def _now(self) -> str:
        return str(int(date_funcs.now().timestamp() * 1000))

    def _auth_headers(self, s: MySession, is_json=True, extra: Dict[str, str] = None) -> Dict[str, str]:
        req_headers = self.basic_req_headers_updated({
            'Authorization': 'Bearer {}'.format(self._auth_token),
            'session-ID': self._sid,
            'X-ClientId': 'nhb',
            'X-Santander-Channel': 'INT'
        })
        if self._session_token:
            req_headers['sessionToken'] = self._session_token
        if is_json:
            req_headers['Content-Type'] = 'application/json'
            req_headers['Accept'] = 'application/json, text/plain, */*'
        if extra:
            req_headers.update(extra)
        return req_headers

    def _get_encrypted(self, public_key: str, msg: str) -> str:
        cmd = """{} "{}" '{}'""".format(CALL_JS_ENCRYPT_LIB, public_key, msg)
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        self.logger.info('Regular web site: new auth method for particulares: start')
        s = self.basic_new_session()

        reason = ''

        resp_init = s.get(
            'https://particulares.bancosantander.es/login/',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # S - CIF, N - NIF
        document_type = 'S' if 'CIF' in self.access_type else 'N'

        # to get encrypt_key
        resp_config = s.get(
            'https://particulares.bancosantander.es/login/config.json',
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        encrypt_key = resp_config.json()['login_post_pk']

        # 1581972172983
        now = self._now()
        # UPD:
        # dev/202103/login.main.js
        # var e = new Date;
        # return sessionStorage.getItem('utag7') || sessionStorage.setItem('utag7',
        # e.getTime().toString(16).concat(Math.random().toString(36).substring(7)).toUpperCase()
        # ),
        # "17054F65480", "17056E2538B" ->  '1739BFC2A50UOXZIP'
        # UOXZIP - 'random' suffix
        csid = '{:02x}UOXZIP'.format(int(now)).upper()

        encrypt_data = OrderedDict([
            ("connectionTime", now),
            ("remember", False),
            ("csid", csid),
            ("documentNumber", self.username),
            ("documentType", document_type),
            ("password", self.userpass),
            ("terminalId", "Linux")
        ])
        encrypt_data_jstr = json.dumps(encrypt_data)
        key = self._get_encrypted(
            encrypt_key,
            encrypt_data_jstr
        )

        req_auth_url = 'https://particulares.bancosantander.es/v1/hb/entry/auth'
        req_auth_params = {"key": key}

        # Main login action is here
        resp_auth = s.post(
            req_auth_url,
            json=req_auth_params,
            headers=self.basic_req_headers_updated({
                "X-ClientId": "nhb",
                "X-Santander-Channel": "INT",
                'Referer': resp_init.url
            }),
            proxies=self.req_proxies
        )

        # '{"message":"Por favor introduzca de nuevo el identificador y la clave de acceso.
        # El identificador y/o la clave no son válidos.","code":"ERROR_LOGIN","type":"error"}'
        # {'type': 'error', 'message': 'Clave de acceso bloqueada. Si desea obtener una nueva clave, llame a..',
        # 'code': 'ERROR_LOGIN_BLOCKED'}
        # {"appName":"login-s","timeStamp":1627466816725,"errorName":"UNAUTHORIZED",
        # "status":401,"internalCode":401,"shortMessage":"UNAUTHORIZED","detailedMessage":"Invalid credentials"}
        is_credentials_error = any(m in resp_auth.text for m in WRONG_CREDENTIALS_MARKERS)
        if is_credentials_error:
            return s, resp_auth, False, is_credentials_error, ''

        try:
            resp_auth_json = resp_auth.json()
            self._auth_token = resp_auth_json['tokenCredential']
            self._sid = resp_auth_json['sid']
        except Exception as e:
            return s, resp_auth, False, False, "Can't get correct resp_auth.json(): {}".format(e)

        req_login_url = 'https://particulares.bancosantander.es/api/v1/hb/login'
        req_login_params = OrderedDict([
            ("connectionTime", now),
            ("remember", False),
            ("csid", csid),
            ("documentType", document_type),
            ("documentNumber", self.username.upper())
        ])
        # customer information
        resp_login = s.post(
            req_login_url,
            json=req_login_params,
            headers=self._auth_headers(s),
            proxies=self.req_proxies
        )

        try:
            resp_login_json = resp_login.json()
            self._company_title = resp_login_json['customer']['fullName']
            self._session_token = resp_login_json['sessionToken']
        except Exception as e:
            return s, resp_login, False, False, "Can't get organization title: {}".format(e)
        # Necessary to pass req_check
        _resp_nbn = s.get(
            'https://particulares.bancosantander.es/nhb/#/',
            headers=self._auth_headers(s),
            proxies=self.req_proxies
        )

        resp_check = s.get(
            'https://particulares.bancosantander.es/api/v1/hb/khi/checking',
            headers=self._auth_headers(s),
            proxies=self.req_proxies
        )
        try:
            # double auth detector
            resp_check_json = resp_check.json()
            if resp_check_json['status'] != "0":
                return s, resp_check, False, False, DOUBLE_AUTH_REQUIRED_TYPE_COMMON
        except Exception as _e:
            return s, resp_check, False, False, "Can't validate double auth status"

        is_logged = 'customer' in resp_login.text and resp_check.status_code == 200 and not reason
        # update sessionToken again (see dev/202103/nhb.main.js)
        self._session_token = resp_check.headers.get('sessionToken', '')

        return s, resp_login, is_logged, is_credentials_error, reason

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:

        req_accounts_url = 'https://particulares.bancosantander.es/api/v1/accounts'
        resp_accounts = s.get(
            req_accounts_url,
            headers=self._auth_headers(s),
            proxies=self.req_proxies
        )

        try:
            resp_accounts_json = resp_accounts.json()
        except Exception as e:
            self.logger.error("Can't get resp_accounts.json(): {}. Abort. RESPONSE:\n{}".format(
                e,
                resp_accounts.text
            ))
            return False

        accounts_parsed = parse_helpers_particulares.get_accounts_parsed_nuevo(resp_accounts_json)

        self.logger.info("Contract has accounts: {}".format(accounts_parsed))
        # Some accesses really don't have accounts, check for 'products' key
        if not accounts_parsed and ('products' not in resp_accounts_json):
            self.basic_log_wrong_layout(resp_accounts, "Expected, but couldn't extract accounts")

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                self._company_title,
                account_parsed,
                # use db customer name because of web customer name is not an organization
            ) for account_parsed in accounts_parsed
        ]

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        # Serial processing
        # not necessary to do it in parallel mode because quick 'process_account'
        for account_scraped in accounts_scraped:
            self.process_account(s, account_scraped)

        return True

    def process_account(self,
                        s: MySession,
                        account_scraped: AccountScraped) -> bool:
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_is_in_process_only_accounts(account_scraped.AccountNo):
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.SKIPPED_EXPLICITLY)
            return True  # already reported

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        req_movs_url = 'https://particulares.bancosantander.es/api/v1/accounts/statements/search'

        movements_parsed_desc = []  # type: List[MovementParsed]
        # next page param
        repo = None  # type: Optional[str]

        for i in range(1, 100):  # avoid inf loops
            self.logger.info('{}: get movs: page #{}'.format(fin_ent_account_id, i))
            req_movs_params = OrderedDict([
                ("pos", '0'),
                ("code", account_scraped.AccountNo),  # "ES2500865147320010049428"
                ("amountFrom", None),
                ("amountTo", None),
                ("concept", ""),
                ("conceptConsAv", "000"),
                ("from", date_from_str),  # "29/11/2019"
                ("to", self.date_to_str),  # "18/02/2020"
                ("all", None),
                ("statementType", "ALL"),
                ("repo", repo),
                ("uuid", None),
                ("listNonUsed", [])
            ])  # type: OrderedDict

            resp_movs = s.post(
                req_movs_url,
                json=req_movs_params,
                headers=self._auth_headers(s),
                proxies=self.req_proxies
            )

            try:
                resp_movs_json = resp_movs.json()
            except Exception as e:
                self.logger.error("{}: can't get resp_movs.json(): {}. Abort. RESPONSE:\n{}".format(
                    fin_ent_account_id,
                    e,
                    resp_movs.text
                ))
                return False

            movements_parsed_desc_i = parse_helpers_particulares.get_movements_parsed_nuevo(resp_movs_json)
            movements_parsed_desc.extend(movements_parsed_desc_i)

            has_more_movs = resp_movs_json['end'] == 'N'
            if not has_more_movs:
                break

            if has_more_movs:
                repo = resp_movs_json['repo']

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

        is_success = self.process_access(s, resp_logged_in)

        self.basic_log_time_spent('GET MOVEMENTS')

        if not is_success:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        return self.basic_result_success()
