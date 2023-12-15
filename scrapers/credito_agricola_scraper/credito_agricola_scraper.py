from base64 import b64encode
from collections import OrderedDict
from typing import Dict, List, Tuple

from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (ScraperParamsCommon, AccountParsed, MainResult,
                                  AccountScraped, MOVEMENTS_ORDERING_TYPE_ASC,
                                  DOUBLE_AUTH_REQUIRED_TYPE_COMMON)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.credito_agricola_scraper import parse_helpers

__version__ = '1.5.0'

__changelog__ = """
1.5.0
use account-level result_codes
1.4.0
call basic_upload_movements_scraped with date_from_str
1.3.1
req_headers: bytes to str
1.3.0
caprot-op-ctx header
resp checker for get_organization_title
logout
1.2.1
aligned double auth msg
1.2.0
use basic_new_session
upd type hints
1.1.0
handle non-200 resp_movs (check for security restrictions)
1.0.0
init
"""


class CreditoAgricolaScraper(BasicScraper):
    """It allows only one active session.
    Need to log out in the end of the scraping process
    """
    scraper_name = 'CreditoAgricolaScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self._access_token = ''

    def _date_req_fmt(self, date_str):
        """Converts 30/01/2019 -> 2019-01-30 without dt conversion"""
        d, m, y = date_str.split('/')
        return '{}-{}-{}'.format(y, m, d)

    def _parse_json(self, resp: Response, err_place='') -> Tuple[bool, dict]:
        """Parses response JSON and logs error if not a valid json"""
        is_success = True
        resp_json = {}  # type: dict
        try:
            resp_json = resp.json()
        except Exception as e:
            is_success = False
            self.logger.error("Can't parse {}. Not a JSON. RESPONSE:\n{}".format(
                err_place,
                resp.text
            ))
        return is_success, resp_json

    def _req_headers(self, on_behalf_of_param='') -> Dict[str, str]:
        """Req headers with mandatory details"""

        # See 'btoa' func in website's JS (btoa == b64encode)
        # '{"OnBehalfOf":""}' ->  'eyJPbkJlaGFsZk9mIjoiIn0='
        # '{"OnBehalfOf":"18260950"}' -> 'eyJPbkJlaGFsZk9mIjoiMTgyNjA5NTAifQ=='
        carpot_op_ctx_header = b64encode(
            '{{"OnBehalfOf":"{}"}}'.format(on_behalf_of_param).encode('utf-8')
        ).decode('utf-8')
        req_headers = self.basic_req_headers_updated({
            'Accept': 'application/json, text/plain, */*',
            'Authorization': self._access_token,
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://caonlineempresas.creditoagricola.pt/',
            'caprot-op-ctx': carpot_op_ctx_header,
        })

        return req_headers

    def login(self) -> Tuple[MySession, Response, bool, bool]:

        s = self.basic_new_session()

        # get init cookies
        resp_init = s.get(
            'https://www.creditoagricola.pt/para-a-minha-empresa',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_login_params = OrderedDict([
            ('username', self.username),
            ('password', str(self.userpass))
        ])

        resp_logged_in = s.post(
            'https://www.creditoagricola.pt/api/corporate/authentication/token',
            json=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        ok, resp_logged_in_json = self._parse_json(resp_logged_in, 'resp_logged_in')
        if not ok:
            # already reported
            return s, resp_logged_in, False, False

        access_token = parse_helpers.get_access_token(resp_logged_in_json)
        self._access_token = access_token

        is_credentials_error = 'Grant validation error' in resp_logged_in.text
        is_logged = bool(access_token)

        if is_logged:
            # Need to 'activate' the auth session
            _resp_start = s.get(
                'https://www.creditoagricola.pt/api/corporate/service/security/session/start',
                headers=self._req_headers(),
                proxies=self.req_proxies
            )

        return s, resp_logged_in, is_logged, is_credentials_error

    def process_access(self, s: MySession) -> bool:

        resp_company = s.get(
            'https://www.creditoagricola.pt/api/corporate/customer/company',
            headers=self._req_headers(),
            proxies=self.req_proxies
        )

        ok, resp_company_json = self._parse_json(resp_company, 'resp_company')
        if not ok:
            return False

        ok, organization_title = parse_helpers.get_organization_title(resp_company_json)
        if not ok:
            self.basic_log_wrong_layout(
                resp_company,
                "Can't get organization_title"
            )
            return False

        resp_accounts = s.get(
            'https://www.creditoagricola.pt/api/corporate/product/accounts/DDA',
            # also caprot-pi-ctx: eyJMb2dFbnRyeUlkIjoxOTE0OTM2MzAyfQ== from prev resp headers
            headers=self._req_headers(),
            proxies=self.req_proxies
        )

        ok, resp_accounts_json = self._parse_json(resp_accounts, 'resp_accounts')
        if not ok:
            return False

        accounts_parsed_wo_iban = parse_helpers.get_accounts_wo_iban_parsed(resp_accounts_json)

        # get IBAN for each account
        accounts_parsed = []  # type: List[AccountParsed]
        for acc_parsed_wo_iban in accounts_parsed_wo_iban:
            resp_acc_details = s.get(
                'https://www.creditoagricola.pt/api/corporate/product/account/dda/{}'.format(
                    acc_parsed_wo_iban['financial_entity_account_id']
                ),
                # also caprot-op-ctx: eyJPbkJlaGFsZk9mIjoiMTgyNjA5NTAifQ==
                headers=self._req_headers(),
                proxies=self.req_proxies
            )
            ok, resp_acc_details_json = self._parse_json(resp_acc_details, 'resp_acc_details')
            if not ok:
                return False

            account_parsed = parse_helpers.get_account_parsed(resp_acc_details_json, acc_parsed_wo_iban)
            accounts_parsed.append(account_parsed)

        accounts_scraped = [self.basic_account_scraped_from_account_parsed(
            organization_title,
            acc_parsed,
            country_code='PRT',
        ) for acc_parsed in accounts_parsed]

        self.basic_log_time_spent('GET BALANCE')
        self.logger.info("Got {} account(s) {}".format(len(accounts_scraped), accounts_scraped))
        self.basic_upload_accounts_scraped(accounts_scraped)

        for account_scraped in accounts_scraped:
            self.process_account(s, account_scraped)

        return True

    def process_account(self, s: MySession, account_scraped: AccountScraped) -> bool:
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        req_params = {
            'start_date': '{}T00:00:00+00:00'.format(self._date_req_fmt(date_from_str)),
            'end_date': '{}T23:59:59+00:00'.format(self._date_req_fmt(self.date_to_str)),
            'account_number': fin_ent_account_id
        }

        resp_movs = s.post(
            'https://www.creditoagricola.pt/api/corporate/operation/log',
            json=req_params,
            headers=self._req_headers(on_behalf_of_param=self.username),
            proxies=self.req_proxies
        )

        if resp_movs.status_code != 200:
            msg = ''
            if 'As opções de segurança não lhe permitem executar esta operação' in resp_movs.text:
                msg = '{} (?). '.format(DOUBLE_AUTH_REQUIRED_TYPE_COMMON)
            self.basic_log_wrong_layout(
                resp_movs,
                "{}: can't get movements. {}Skip.".format(fin_ent_account_id, msg)
            )
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
            return False

        ok, resp_movs_json = self._parse_json(resp_movs, 'resp_movs for {}'.format(fin_ent_account_id))
        if not ok:
            return False

        # already with ext descr
        movements_parsed = parse_helpers.get_movements_parsed(resp_movs_json)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )
        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        self.basic_update_movements_extended_descriptions_if_necessary(
            account_scraped,
            movements_scraped
        )

        return True

    def logout(self, s: MySession) -> bool:
        """Need to log out to avoid Error_Session_AlreadyActive"""
        self.logger.info('Log out')
        _resp_end = s.get(
            'https://www.creditoagricola.pt/api/corporate/service/security/session/end',
            headers=self._req_headers(on_behalf_of_param=self.username),
            proxies=self.req_proxies
        )
        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged_in, is_credentials_error = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged_in:
            return self.basic_result_not_logged_in_due_unknown_reason(
                resp_logged_in.url,
                resp_logged_in.text
            )
        try:
            self.process_access(s)

            self.basic_log_time_spent("GET MOVEMENTS")
        finally:
            self.logout(s)

        return self.basic_result_success()
