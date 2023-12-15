from collections import OrderedDict
from typing import Tuple, List

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import DOUBLE_AUTH_REQUIRED_TYPE_COMMON
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from .custom_types import AccountExtracted

__version__ = '1.1.0'

__changelog__ = """
1.1.0 2023.03.29
added DOUBLE_AUTH_MARKER
1.0.0
refactored
0.3.0
modify process_accounts for process all accounts
0.2.0
Add
3_resp_count
process_accounts
process_account
0.1.0
Add login
Add parse_helpers_n43
Add 1_resp_init_login.html
Add 2_resp_global_position.html
"""

WRONG_CREDENTIALS_MARKERS = [
    'ERROR CLAUS o CODI SMS',
]
DOUBLE_AUTH_MARKERS = [
    'Revise la informaci&#243;n recibida en su m&#243;vil.',
    'debemos verificar mediante un mensaje a su m&#243;vil su identidad',
    'Confirme que es usted quien intenta acceder a CAIXAGUISSONA',
]


class CaixaGuissonaScraper(BasicScraper):
    scraper_name = 'CaixaGuissonaScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    def login(self) -> Tuple[MySession, Response, bool, bool, str, str]:
        s = self.basic_new_session()
        req_init_url = 'https://www.caixaguissona.com/'
        self.logger.info('login: open home page: start')
        resp_init = s.get(req_init_url, headers=self.req_headers, proxies=self.req_proxies)
        self.logger.info('login: open home page: done')

        token = parse_helpers.get_verification_token(resp_init.text)

        req_params = OrderedDict([
            ('user', self.username),
            ('pwd', self.userpass[:8]),
            ('__RequestVerificationToken', token)
        ])

        req_login_url = 'https://www.caixaguissona.com/es/public/home'
        self.logger.info('login: auth req: start')
        resp_logged_in = s.post(
            req_login_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        self.logger.info('login: auth req: done')
        is_logged = 'SALIR' in resp_logged_in.text

        is_credentials_error = any(m in resp_logged_in.text for m in WRONG_CREDENTIALS_MARKERS)
        reason = ''

        if any(m in resp_logged_in.text for m in DOUBLE_AUTH_MARKERS):
            is_logged = False
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        return s, resp_logged_in, is_logged, is_credentials_error, reason, token

    def _get_accounts_extracted(self, resp_logged_in: Response) -> Tuple[bool, List[AccountExtracted]]:
        """Can be used from children"""
        accounts = parse_helpers.get_accounts_extracted(resp_logged_in.text)
        if not accounts:
            self.basic_log_wrong_layout(
                resp_logged_in,
                "Can't get accounts_extracted"
            )
            return False, accounts
        self.logger.info('Got {} accounts: {}'.format(
            len(accounts),
            accounts
        ))
        return True, accounts

    def process_accounts(
            self,
            s: MySession,
            resp_global: Response,
            token: str) -> bool:
        """Process_accounts (draft)"""
        ok, accounts = self._get_accounts_extracted(resp_global)
        if not ok:
            return False
        for account in accounts:
            self.logger.info('{} ({}): PROCESS ACCOUNT'.format(
                account.account_no,
                account.account_alias))
            _ok = self.process_account(s, account, token)
            ...
            self.logger.info('PROCESS ACCOUNT SUCCESS')
        return True

    def process_account(
            self,
            s: MySession,
            account: AccountExtracted,
            token: str) -> bool:
        """Process one account (draft)"""

        req_account_url = 'https://www.caixaguissona.com/es/private/listaccountdetails'
        req_params = OrderedDict([
            ('accountNumber', account.account_no),
            ('referencia', account.reference),
            ('__RequestVerificationToken', token)
        ])
        _resp_account_details = s.post(
            req_account_url,
            req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        ...
        return True

    def main(self) -> MainResult:
        return self.basic_result_success()
