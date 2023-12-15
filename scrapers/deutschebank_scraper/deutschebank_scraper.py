import random
import time
import traceback
from collections import OrderedDict
from concurrent import futures
from typing import List, Optional, Tuple

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, MovementParsed,
    ScraperParamsCommon, MainResult,
    DOUBLE_AUTH_REQUIRED_TYPE_OTP
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.deutschebank_scraper import parse_helpers

__version__ = '4.13.0'

__changelog__ = """
4.13.0
use account-level result_codes
4.12.0
call basic_upload_movements_scraped with date_from_str
4.11.1
upd log msg (fixed typing)
4.11.0
'new password required' detector: moved upper
4.10.0
renamed to download_correspondence()
4.9.0
skip inactive accounts
4.8.0
err instead of exn if unknown access type 
4.7.0
download_company_documents
4.6.0
login: upd req headers
'new password required' detector
4.5.1
aligned double auth msg
4.5.0
use basic_new_session
upd type hints
4.4.0
upd CREDENTIALS_ERROR_MARKERS
4.3.0
login: return reasons, 2FA detector
4.2.0
auth in 2 steps, authentication_id_param
use basic_get_date_from
4.1.0
_do_req_excel_and_get_movs_parsed: req_excel: timeout=30 to handle many movs 
  (for -u 89911 -a 10933 acc ES9700190301114010045704)
4.0.0
new login and logout methods
more type hints
3.3.0
handle unimplemented access type: raise exception with access type info
3.2.0
basic_movements_scraped_from_movements_parsed: new format of the result 
3.1.2
upd msg on not logged in due to unknown reason
3.1.1
process_account: dates in err msgs
3.1.0
_do_req_excel_and_get_movs_parsed: several attepts to download movements
msg upd
3.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
2.0.0
basic_movements_scraped_from_movements_parsed
OperationalDatePosition, KeyValue support
"""

ACCOUNT_INACTIVE_SIGNS = ['CUENTA CANCELADA']
CREDENTIALS_ERROR_MARKERS = [
    'INCORRECTO / INACTIVO',
    'Los datos no son correctos'
]


class DeutscheBankScraper(BasicScraper):
    scraper_name = 'DeutscheBankScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.req_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0'
        }
        self.update_inactive_accounts = False

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()
        reason = ''

        if self.access_type != 'db-direct empresas':
            return s, Response(), False, False, 'Unimplemented access type: {}'.format(self.access_type)

        req_init_url = 'https://www.deutschebank-dbdirect.com/portalserver/dbdirect/inicio'
        resp_init = s.get(
            req_init_url,
            proxies=self.req_proxies,
            headers=self.req_headers
        )

        # expect response
        # {"responseData":{"authentications":{"authentication":[
        # {"device":"PWD","document":null,
        # "id":"aaf328ca-b66d-4155-807d-2de545cc01e6","status":null,
        # "user":"B.CHIVA@AZULEJOS.HALCON.ES"}]},
        # "messages":null,
        # "postmarkData":null,
        # "signedAuth":null},
        # "result":{"error":null,"result":"OK"}}
        req_first_step_params = {"requestData": {"user": self.username}}
        resp_login_first_step = s.post(
            'https://www.deutschebank-dbdirect.com/portalserver/services/'
            'rest/dbdirect/psd2/getAuthenticationMethods',
            json=req_first_step_params,
            headers=self.basic_req_headers_updated({'Content-Type': 'application/json'}),
            proxies=self.req_proxies,
        )

        authentication_id_param = extract.re_first_or_blank(r'"id"\s*:\s*"(.*?)"',
                                                            resp_login_first_step.text)
        if not authentication_id_param:
            return s, resp_login_first_step, False, False, "Can't parse authentication_id_param"

        if '"device":"PWD"' not in resp_login_first_step.text:
            # not implemented for now
            return s, resp_login_first_step, False, False, DOUBLE_AUTH_REQUIRED_TYPE_OTP

        req_login_params = OrderedDict([
            ('customerId', self.username),
            ('customWord', self.userpass),
            ('customWordNew', ''),
            ('customWordConfirm', ''),
            ('authenticationId', authentication_id_param),
            ('action', 'normal')
        ])

        resp_login = s.post(
            'https://www.deutschebank-dbdirect.com/portalserver/j_spring_security_check',
            data=req_login_params,
            proxies=self.req_proxies,
            headers=self.basic_req_headers_updated({
                'DNT': '1'
            })
        )

        # La contraseña ha caducado. Por favor, informe una nueva.
        if ('ha caducado. Por favor, informe una nueva.' in resp_login.text
                or 'H666' in resp_login.text):
            reason = 'Password should be updated. Pls, inform the customer'
            return s, resp_login, False, False, reason

        # need to open for further processing
        resp_home = s.get(
            'https://www.deutschebank-dbdirect.com/portalserver/dbdirect/dbdirectpage',
            proxies=self.req_proxies,
            headers=self.req_headers
        )

        is_logged = '"welcome"' in resp_login.text
        if 'Su sesión anterior no se ha finalizado correctamente' in resp_login.text:
            reason = ('=== PROBABLE REASON: PREVIOUS USER SESSION IS OPENED OR WAS CLOSED INCORRECTLY '
                      '(BY THE CUSTOMER OR DUE TO ABORTED SCRAPING JOB). '
                      'TRY TO RE-SCRAPE IN 10-15 MIN ===')
            return s, resp_login, is_logged, False, reason

        is_credentials_error = any(m in resp_login.text for m in CREDENTIALS_ERROR_MARKERS)
        return s, resp_login, is_logged, is_credentials_error, reason

    def logout(self, s: Optional[MySession]) -> Optional[Response]:
        if not s:
            return None

        req_headers = self.req_headers.copy()
        req_headers['X-Requested-With'] = 'XMLHttpRequest'

        # 500 code was removed - it's expectable code
        s.resp_codes_bad_for_proxies = [502, 503, 504, 403, None]
        req1_url = 'https://www.deutschebank-dbdirect.com/portalserver/services/rest/dbdirect/session'

        resp1 = s.delete(
            req1_url,
            headers=req_headers,
            proxies=self.req_proxies
        )

        req2_url = 'https://www.deutschebank-dbdirect.com/portalserver/rest/loginLogout'

        resp2 = s.delete(
            req2_url,
            headers=req_headers,
            proxies=self.req_proxies
        )

        self.logger.info('Logged out')
        return resp2

    def get_accounts(self, s: MySession) -> Tuple[MySession, List[AccountScraped], bool]:
        """
        Use Saldo contable/Book balance (<last date>) (third column) to get balances

        :return (session, accounts_scraped, is_success)
        """

        self.logger.info('get_accounts')
        time.sleep(1 + random.random())

        acc_req_url_real = ('https://www.deutschebank-dbdirect.com/dbdirect.accountinfo/'
                            'go_balances_searcher.do?initialSearch=yes')

        resp_accounts_overview = s.get(
            acc_req_url_real,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        accounts_parsed = parse_helpers.parse_accounts_overview(resp_accounts_overview.text)

        if len(accounts_parsed) == 0:
            self.logger.error(
                "Error. Didn't find accounts. "
                "Check the layout.\nRESPONSE:\n{}".format(resp_accounts_overview.text)
            )
            return s, [], False

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(acc_parsed['company_title'], acc_parsed)
            for acc_parsed in accounts_parsed
        ]

        return s, accounts_scraped, True

    def _do_req_excel_and_get_movs_parsed(
            self,
            s: MySession,
            req_params: dict) -> Tuple[MySession, bytes, List[MovementParsed], Optional[Exception]]:
        movements_parsed = []  # type: List[MovementParsed]
        exception = None
        content = b''
        for _ in range(3):
            resp_excel = s.post(
                'https://www.deutschebank-dbdirect.com/dbdirect.accountinfo/search_extract_download.do',
                params=req_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
                timeout=30,
                stream=True  # for excel processing
            )
            content = resp_excel.raw.read()
            try:
                movements_parsed = parse_helpers.parse_movements_from_resp_excel(content)
                exception = None
                break
            except Exception as exc:
                exception = exc
                time.sleep(0.5 + random.random())

        return s, content, movements_parsed, exception

    def process_account(self, s: MySession, account_scraped: AccountScraped) -> bool:
        """
        open movements filter page for easy paralleling
        extract and save movements
        """

        account_no = account_scraped.AccountNo
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        # First open mov filter page to detect is account canceled
        if len(fin_ent_account_id) == 20:
            fin_ent_account_id_for_req = fin_ent_account_id
        # fin ent 0032594052032724 -> 00190032594052032724
        elif len(fin_ent_account_id) == 16:
            fin_ent_account_id_for_req = '0019' + fin_ent_account_id
        else:
            # note: possible error
            fin_ent_account_id_for_req = fin_ent_account_id
        req_mov_filter_url = ('https://www.deutschebank-dbdirect.com/dbdirect.accountinfo/go_extract_searcher.do'
                              '?backButton=true&initialSearch=yes&accountId={}').format(fin_ent_account_id_for_req)

        resp_movs_filter = s.get(
            req_mov_filter_url,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        is_inactive = self.basic_check_is_account_inactive_by_text_signs(
            resp_movs_filter.text,
            fin_ent_account_id,
            ACCOUNT_INACTIVE_SIGNS
        )

        if is_inactive:
            self.logger.info('Account {} is inactive. No movements. Skip'.format(fin_ent_account_id))
            # to mark as 'mov scraping finished' and avoid state reset
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_DISABLED_ACCOUNT)
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        self.basic_log_process_account(account_no, date_from_str)

        req_params = {
            'advancedSearch': False,
            'enterprise': '*ALL*',
            'accountId': fin_ent_account_id_for_req,
            'dateFrom': date_from_str.replace('/', '.'),  # 01/02/2017 -> 01.02.2017
            'dateTo': self.date_to_str.replace('/', '.'),
            'searchDateOrder': 'searchDateOrderDesc',
            'searchStatementType': 'extract.all',
            'searchFamily': None,
            'searchImportOperator': None,
            'searchImportQuantity': None
        }

        # First open html movements filtered to get possible information about dates restrictions
        # bcs we can't get correct excel if date_from < some available_date_from
        resp_movs_filtered = s.post(
            'https://www.deutschebank-dbdirect.com/dbdirect.accountinfo/search_extract.do',
            params=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        new_date_from_str = parse_helpers.get_new_date_from_if_restrictions(resp_movs_filtered.text)
        if new_date_from_str:
            req_params['dateFrom'] = new_date_from_str

        self.logger.info('{}: parse movements from excel'.format(account_no))
        s, content, movements_parsed, exception = self._do_req_excel_and_get_movs_parsed(s, req_params)
        if exception:
            self.logger.error(
                '{}: dates from {} to {}: !!! EXCEPTION !!! while trying extract movements:\n{}\nRESPONSE:\n{!r}.'
                '\nPossible reason: there are no movements since date_from. CHECK MANUALLY'.format(
                    fin_ent_account_id,
                    date_from_str,
                    self.date_to_str,
                    exception,
                    content
                )
            )
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
            return False

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str
        )

        self.basic_log_process_account(account_no, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )
        return True

    def main(self) -> MainResult:

        s = None
        is_success = True
        try:
            s, resp, is_logged, is_credentials_error, reason = self.login()

            if is_credentials_error:
                return self.basic_result_credentials_error()

            if not is_logged:
                return self.basic_result_not_logged_in_due_reason(
                    resp.url,
                    resp.text,
                    reason
                )

            s, accounts_scraped, is_success = self.get_accounts(s)
            self.basic_upload_accounts_scraped(accounts_scraped)
            self.basic_log_time_spent('GET BALANCES')
            self.download_correspondence(s)

            if project_settings.IS_CONCURRENT_SCRAPING:
                with futures.ThreadPoolExecutor(max_workers=16) as executor:

                    futures_dict = {executor.submit(self.process_account,
                                                    s, account): account.AccountNo
                                    for account in accounts_scraped}

                    self.logger.log_futures_exc('process_account', futures_dict)
            else:
                for account in accounts_scraped:
                    self.process_account(s, account)

            self.basic_log_time_spent('GET MOVEMENTS')

        except Exception as exc:
            self.logger.error('main: EXCEPTION: {}'.format(traceback.format_exc()))
            is_success = False
        finally:
            resp_logged_out_optional = self.logout(s)

        if is_success:
            return self.basic_result_success()
        else:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None
