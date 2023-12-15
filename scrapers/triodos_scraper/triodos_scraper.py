import html
import random
import time
from collections import OrderedDict
from concurrent import futures
from typing import Dict, List, Tuple

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, ScraperParamsCommon, MovementParsed,
    MainResult, DOUBLE_AUTH_REQUIRED_TYPE_COMMON
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.triodos_scraper import parse_helpers

__version__ = '4.12.0'

__changelog__ = """
4.12.0
more CREDENTIALS_ERROR_MARKERS
4.11.0
_get_movs_i: upd pagination
4.10.0
call basic_upload_movements_scraped with date_from_str
4.9.1
increased timeout
4.9.0
only serial processing for accounts at contract/company level
open_contract_home_page_and_process: detect lost session and re-login when it's required
4.8.0
process_account: several attempts to get valid resp_movs_i
parse_helpers: get_movements_parsed: check for valid parsing results
_get_movs_from_first_page
_get_movs_i
manual req_movs_i_url instead of extracted from the page to avoid missed pages
4.7.0
skip inactive accounts
4.6.0
aligned double auth msg
4.5.0
use basic_new_session
upd type hints
fmt
4.4.0
use basic_get_date_from
4.3.0
sms auth detector, login err reason
4.2.1
upd user agent to pass auth step
4.2.0
more credentials error markers
4.1.0
basic_movements_scraped_from_movements_parsed: new format of the result
4.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
3.0.0
basic_movements_scraped_from_movements_parsed
OperationalDatePosition, KeyValue support
2.2.0
basic_upload_movements_scraped
2.1.0
extract correct balances (saldo dispuesto) of credit accounts
2.0.0
multicontract implemented
1.1.1
reformatted
1.1.0
is_credentials_error impl
org title correct
1.0.2
fixed organization title extraction
1.0.1
removed redundant commented code
1.0.0
basic impl
0.0.1
logged in
"""

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'

CREDENTIALS_ERROR_MARKERS = [
    'USUARIO BLOQUEADO. POR FAVOR, CONTACTE CON SU OFICINA',
    'Si no recuerda su contras',
    'NO HAY CUENTAS NI TARJETAS ASOCIADAS AL CONTRATO DE BE',
    'Por favor, introduce de nuevo tu usuario y/o la contrase',
]


def delay() -> None:
    time.sleep(0.1 + random.random())


class TriodosScraper(BasicScraper):
    scraper_name = 'TriodosScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.req_headers = {'User-Agent': USER_AGENT}
        self.update_inactive_accounts = False

    def _req_headers(self, headers_additional: Dict[str, str]) -> Dict[str, str]:
        """Returns self.req_header, updated by headers_additional

        Example:
            resp = s.get(url, headers=self._req_headers({'Referer': resp_logged_in.url}))
        """
        return self.basic_req_headers_updated(headers_additional)

    def _is_logged_in(self, resp: Response) -> bool:
        is_logged_in = 'Desconectar' in resp.text
        return is_logged_in

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:

        s = self.basic_new_session()

        req0_url = 'https://www.triodos.es/es/particulares/'
        resp0 = s.get(
            req0_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        delay()

        req1_url = 'https://www.triodos.es/es/particulares/como-operar/bienvenido-oficina-internet/'
        resp1 = s.get(
            req1_url,
            headers=self._req_headers({'Referer': resp0.url}),
            proxies=self.req_proxies
        )

        s.cookies.set('cookie_aceptacion', 'true', domain='www.triodos.es')

        delay()

        req2_url = 'https://banking.triodos.es/triodos-be/login.sec'

        resp2 = s.get(
            req2_url,
            headers=self._req_headers({'Referer': resp1.url}),
            proxies=self.req_proxies
        )

        delay()

        req3_url = 'https://banking.triodos.es/triodos-be/j_security_check'
        req3_data = OrderedDict([
            ('j_username', self.username),
            ('j_password', self.userpass)
        ])

        resp3 = s.post(
            req3_url,
            data=req3_data,
            headers=self._req_headers({'Referer': resp2.url}),
            proxies=self.req_proxies
        )

        is_logged = self._is_logged_in(resp3)
        reason = ''
        if 'verificar tu identidad a través del SMS que has recibido en tu móvil' in resp3.text:
            is_logged = False
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON
        is_credentials_error = any(marker in resp3.text for marker in CREDENTIALS_ERROR_MARKERS)

        return s, resp3, is_logged, is_credentials_error, reason

    def _get_and_save_accounts_scraped(
            self,
            s: MySession,
            resp_contract_home: Response,
            organization_title: str) -> List[AccountScraped]:

        # debit accounts
        accounts_parsed = parse_helpers.get_debit_accounts_parsed(resp_contract_home.text)

        # credit accounts - extract from credit account overview page to get correct balances
        if 'Ir a cuentas de cr&eacute;dito' in resp_contract_home.text:
            token = parse_helpers.get_token(resp_contract_home.text)
            req_url = 'https://banking.triodos.es/triodos-be/getpartialpositioncreditaccount.do?token={}'.format(token)
            resp_debit_accs_overview = s.get(
                req_url,
                headers=self._req_headers({'Referer': resp_contract_home.url}),
                proxies=self.req_proxies
            )

            accounts_parsed += parse_helpers.get_credit_accounts_parsed(resp_debit_accs_overview.text)

        accounts_scraped = [self.basic_account_scraped_from_account_parsed(organization_title, acc_parsed)
                            for acc_parsed in accounts_parsed]

        self.logger.info('Contract {} has accounts {}'.format(organization_title, accounts_scraped))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        return accounts_scraped

    def open_contract_home_page_and_process(
            self,
            s: MySession,
            resp_logged_in: Response,
            n_contracts: int,
            contract_id: str) -> bool:

        must_relogin = False
        for att in range(2):
            # open new session on concurrent scraping to avoid collisions
            if (project_settings.IS_CONCURRENT_SCRAPING and n_contracts > 1) or must_relogin:
                time.sleep(0.5 + random.random())
                s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()
                # No real 'credentials error', just abort
                if not is_logged:
                    self.logger.error(
                        "{}: can't login to process contract/company. Wrong credentials detected. "
                        "The access will not be marked as inactive. Abort".format(contract_id)
                    )
                    return False

            self.logger.info('Open contract home page: {}'.format(contract_id))

            delay()
            token = parse_helpers.get_token(resp_logged_in.text)
            req_url = 'https://banking.triodos.es/triodos-be/PBE_contract_set'

            req_params = OrderedDict([
                ('j_contract', contract_id),
                ('token', token)
            ])

            resp_contract_home = s.post(
                req_url,
                data=req_params,
                headers=self._req_headers({'Referer': resp_logged_in.url}),
                proxies=self.req_proxies,
                timeout=60,
            )

            # might lost session during concurrent processing
            is_still_logged = self._is_logged_in(resp_contract_home)
            if is_still_logged:
                break
            self.logger.warning('{}: lost session detected. Re-login'.format(contract_id))
            must_relogin = True
            time.sleep(5 + random.random())
        else:
            self.logger.error("{}: lost session detected. Can't re-login. Abort".format(contract_id))
            return False

        self.process_contract(s, resp_contract_home, contract_id)
        return True

    def process_contract(self, s: MySession, resp_contract_home: Response, contract_id='no ID') -> bool:
        """Get accounts_scraped, save them and call process_account"""

        organization_title = parse_helpers.get_organization_title(resp_contract_home.text)
        if not organization_title:
            self.basic_log_wrong_layout(resp_contract_home, "Can't get organization_title")
            return False

        self.logger.info('Process contract: {} ({})'.format(organization_title, contract_id))

        accounts_scraped = self._get_and_save_accounts_scraped(s, resp_contract_home, organization_title)
        # Only serial processing at contract/company level is allowed,
        # otherwise they can affect each other during pagination
        # and some pages will be lost
        for account_scraped in accounts_scraped:
            self.process_account(s, resp_contract_home, account_scraped)
        return True

    def _get_movs_from_first_page(
            self,
            s: MySession,
            resp_contract_home: Response,
            account_scraped: AccountScraped) -> Tuple[MySession, Response, List[MovementParsed]]:
        """Open filtered by dates movements with token from home page"""

        date_from_str = self.basic_get_date_from(account_scraped.FinancialEntityAccountId)

        token = parse_helpers.get_token(resp_contract_home.text)

        req_url = 'https://banking.triodos.es/triodos-be/getmovementsaccount.do'
        req_params = OrderedDict([
            ('selectAccount', account_scraped.AccountNo[4:]),
            ('methodController', 'getAccountMovementsByPeriod'),
            ('fromDate', date_from_str),
            ('toDate', self.date_to_str),
            ('token', token)
        ])

        resp_movs = s.post(
            req_url,
            data=req_params,
            headers=self._req_headers({'Referer': resp_contract_home.url}),
            proxies=self.req_proxies
        )
        ok, movs_parsed = parse_helpers.get_movements_parsed(resp_movs.text)
        if not ok:
            self.basic_log_wrong_layout(resp_movs, "_get_movs_from_first_page: invalid resp_movs")
        return s, resp_movs, movs_parsed

    def _get_movs_i(
            self,
            s: MySession,
            resp_prev: Response,
            page_ix: int) -> Tuple[bool, MySession, Response, List[MovementParsed]]:
        """:returns (has_movs_i, session, resp_movs_next, movs_parsed)"""

        # has_next, req_url = parse_helpers.get_next_movs_url(resp_prev.text, resp_prev.url)

        # Ver más
        has_movs_i = '>Siguiente</a>' in resp_prev.text or 'id="next">Ver m' in resp_prev.text

        if not has_movs_i:
            return False, s, Response(), []

        req_movs_i_url = ('https://banking.triodos.es/triodos-be/getmovementsaccount.do'
                          '?page={}&methodController=getAccountMovementsByPeriod'.format(page_ix))

        resp_movs_i = s.get(
            req_movs_i_url,
            headers=self._req_headers({'Referer': resp_prev.url}),
            proxies=self.req_proxies
        )

        ok, movs_parsed = parse_helpers.get_movements_parsed(resp_movs_i.text)
        if not ok:
            self.basic_log_wrong_layout(resp_movs_i, "_get_movs_from_next_page: invalid resp_movs_i")
        return True, s, resp_movs_i, movs_parsed

    def process_account(self,
                        s: MySession,
                        resp_contract_home: Response,
                        account_scraped: AccountScraped) -> bool:
        """Open first page with movements and then one by one next pages"""
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(account_scraped.FinancialEntityAccountId)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        self.logger.info("{}: page 1: get movements".format(fin_ent_account_id))

        time.sleep(0.1)
        s, resp_prev, movements_parsed = self._get_movs_from_first_page(
            s,
            resp_contract_home,
            account_scraped
        )
        has_movs_i = True

        # Pagination
        for page_ix in range(1, 100):  # avoid inf loop
            if not has_movs_i:
                self.logger.info('{}: no more pages with movements'.format(fin_ent_account_id))
                break

            resp_movs_i = Response()  # for linter
            # Several attempts to get valid resp_movs_i
            for att in range(1, 4):
                delay()  # 0.1+
                has_movs_i, s, resp_movs_i, movs_parsed_i = self._get_movs_i(s, resp_prev, page_ix)

                if not has_movs_i:
                    break  # no more pages with movs

                self.logger.info("{}: page {}: att #{}: get movements".format(
                    fin_ent_account_id,
                    page_ix + 1,
                    att
                ))

                if movs_parsed_i:
                    break  # successful attempt

                # If has_next_page but no movs - it's most probably err resp, retry
                self.logger.warning(
                    "{}: page {}: att #{}: expected but didn't get movements_parsed. Retry".format(
                        fin_ent_account_id,
                        page_ix + 1,
                        att
                    ))
            else:  # of `for att in range`
                self.basic_log_wrong_layout(resp_movs_i, "{}: page {}: invalid resp_movs_i".format(
                    fin_ent_account_id,
                    page_ix + 1
                ))
                break  # interrupt `for page_ix in range`
            # / end of `for att in range`

            movements_parsed += movs_parsed_i
            resp_prev = resp_movs_i

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str
        )

        self.basic_log_process_account(account_scraped.AccountNo, date_from_str, movements_scraped)

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

        # one contract: no need to open contract home page - already there
        if 'Selección de contrato' not in html.unescape(resp_logged_in.text):
            self.process_contract(s, resp_logged_in)
        # multicontract
        else:
            contract_ids = parse_helpers.get_contracts_ids(resp_logged_in.text)
            n_contacts = len(contract_ids)

            if project_settings.IS_CONCURRENT_SCRAPING and contract_ids:
                with futures.ThreadPoolExecutor(max_workers=n_contacts) as executor:

                    futures_dict = {
                        executor.submit(self.open_contract_home_page_and_process,
                                        s, resp_logged_in, n_contacts, contract_id): contract_id
                        for contract_id in contract_ids
                    }

                    self.logger.log_futures_exc('open_contract_home_page_and_process', futures_dict)
            else:
                for contract_id in contract_ids:
                    self.open_contract_home_page_and_process(s, resp_logged_in, n_contacts, contract_id)

        self.basic_log_time_spent('GET ALL BALANCES AND MOVEMENTS')
        return self.basic_result_success()
