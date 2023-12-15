import random
import threading
import time
from collections import OrderedDict
from typing import Dict, List, Tuple
from urllib.parse import quote

from custom_libs import date_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, MovementParsed,
    ScraperParamsCommon, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_COMMON, BLOCKED_USER_TYPE_COMMON,
    DOBLE_AUTH_TYPE_WITH_DEACTIVATION
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.sabadell_scraper import parse_helpers
from .custom_types import AccountFromDropdown

__version__ = '16.8.0'

__changelog__ = """
16.8.0 2023.07.31
login: added control to detect accesses with deactivate2FA to avoid blocking them
16.7.0 2023.07.17
deleted useless hardcode RESCRAPING_OFFSET_CUSTOM
_rescraping_offset: deleted deprecated method
process_account: deleted _rescraping_offset method call
16.6.0
added BLOCKED_USER_MARKERS
login: blocked user detector
16.5.0
get_accounts_scraped: use convert_accs_from_dropdown_to_parsed as a fallback approach
16.4.1
deleted not used hardcoded access id for pecunpay
16.4.0
login: open new home page when logged in
16.3.0
changed access type
16.2.1
upd log msgs
16.2.0
use default max offset for movements (89 days from settings)
16.1.0
use account-level result_codes
16.0.0
upd init, scraper_name as cls prop
15.10.0
__current_company_param -> _current_company_param to use in children
15.9.0
main: checks results of process_companies and download_correspondence 
 and returns basic_err on failures 
15.8.0
more CREDENTIALS_ERROR_MARKERS
15.7.0
call basic_upload_movements_scraped with date_from_str
15.6.0
_req_movs_filter_params with optional date_to_str param (suitable for n43)
15.5.0
correspondence support
15.4.0
upd RESCRAPING_OFFSET_CUSTOM (added 30623)
15.3.0
process_account: check basic_is_in_process_only_accounts
15.2.0
RESCRAPING_OFFSET_CUSTOM
15.1.0
More 'wrong credentials' markers
15.0.0
use basic_get_movements_parsed_w_extra_details
14.10.0
login: separate 'Usuario DNI' and 'CAL' access types
14.9.1
convert req params to str (for linters mostly)
14.9.0
process_companies: return is_success based on all companies' results (useful for N43 scraper)
14.8.0
parse_helpers: get_accounts_parsed: use convert.to_currency_code to handle more cases
14.7.0
trim password to appropriate size
14.6.1
relogin_if_lost_session: fixed is_aborted_session
process_account: fixed pagination
14.6.0
explicit method relogin_if_lost_session 
14.5.0
process_account: 
  less attempts if got wrong resp
  upd log msgs
14.4.1
process_account: fixed resp validation
14.4.0
skip inactive accounts
14.3.0
double auth detector
more credentials error markers
fmt
14.2.0
_switch_to_company: re-implemented with the new login method
process_company, process_access: check for successful company switching
14.1.0
login: userpass.upper() (-a 7471)
14.0.0
new login method
_get_random_key
13.4.0
login: several attempts if got unknown reason
13.3.1
more log msgs
13.3.0
use basic_new_session
upd type hints
fmt
13.2.0
MAX_OFFSET_FOR_MOVEMENTS
more ABORTED_SESSION_MARKERS
13.1.1
MOV_DETAILS_MAX_WORKERS = 4 for stability
13.1.0
process_account: 
  early return if didn't uploaded movs for an account,
  it prevents errs for next accounts from the list
get_accounts_scraped: warning instead of err if no position global permissions
MOV_DETAILS_MAX_WORKERS = 8
13.0.0
process_account: re-login if the session was aborted due to long scraping time
  (example: receipts -u 298570 -a 17301)
_get_companies (contracts)
_switch_to_company
__current_company_param
"""

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:69.0)'

# saldo y movimientos menu
URL_DATES_FILTER_WITH_ACCOUNTS_DROPDOWN = 'https://www.bancsabadell.com/txempbs/CUExtractOperationsQueryNew.init.bs'

REQUEST_TIMEOUT = 30

CREDENTIALS_ERROR_MARKERS = [
    # old before 04/2020
    'El usuario o contraseña introducidos no son correctos',
    'El USUARIO o el CÓDIGO DE ACCESO introducidos no son correctos',
    # Contain unprintable symbols:
    # '[{"result":"CDSO032: Lo sentimos! Por motivos de seguridad, no podemos seguir con el proceso."}]',
    '"result":"CDSO032',
    # [{"result":"CDSO033: Los datos introducidos no son correctos"}]', -a 26807
    '"result":"CDSO033',
    'Los datos introducidos no son correctos',  # generic
]

ABORTED_SESSION_MARKERS = [
    'Acceso empresas',
    'Por motivos de seguridad hemos cerrado su sesión'
]

BLOCKED_USER_MARKERS = [
    # Â¡Vaya! tu acceso a banca a distancia estÃ¡ bloqueado; no te preocupes, llÃ¡manos y lo solucionamos."}]'
    '"result":"Z23233',
    '"result":"Z67273',
    'acceso a banca a distancia estÃ¡ bloqueado', # generic
    # Ups! Tu acceso a la banca online estÃ¡ bloqueado. Por favor, llÃ¡manos para que lo solucionemos.
    '"result":"Z24726',
    'acceso a la banca online estÃ¡ bloqueado', # generic
]

MOV_DETAILS_MAX_WORKERS = 4

DEVICE_PRINT = (
    'version=2'
    '&pm_fpua=mozilla/5.0 (x11; ubuntu; linux x86_64; rv:69.0) '
    'gecko/20100101 firefox/69.0|5.0 (X11)|Linux x86_64'
    '&pm_fpsc=24|1600|900|868&pm_fpsw=&pm_fptz=3&pm_fpln=lang=en-US|syslang=|userlang='
    '&pm_fpjv=0&pm_fpco=1&pm_fpasw=&pm_fpan=Netscape&pm_fpacn=Mozilla&pm_fpol=true&pm_fposp=&pm_fpup='
    '&pm_fpsaw=1600&pm_fpspd=24&pm_fpsbd=&pm_fpsdx=&pm_fpsdy=&pm_fpslx=&pm_fpsly=&pm_fpsfse=&pm_fpsui='
)


class SabadellScraper(BasicScraper):
    """
    current problem: can't post several filters data from one session
    several sessions for one user is not allowed? (check from different browsers)
    """

    scraper_name = 'SabadellScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        self.day_to, self.month_to, self.year_to = self.date_to_str.split('/')  # type: Tuple[str, str, str]
        self.started_datetime_for_db = date_funcs.now_for_db()

        self.req_proxies = proxies
        self.req_headers = {'User-Agent': USER_AGENT}
        self.lock = threading.Lock()
        # Safe because there is no parallel execution
        # at company/contract level.
        # Need to re-login implementation
        self._current_company_param = {}  # type: dict
        self.update_inactive_accounts = False

    def _get_random_key(self, s: MySession) -> str:
        """Similar to web page action
        from dev/encrypt_func.js
        """
        jsess = s.cookies.get('JSESSIONID')
        rand = ''.join(str(random.randint(0, 9)) for _ in range(10))
        now = int(time.time() * 1000)
        return '{}{}{}'.format(jsess[:7], rand, now)

    def _req_get(self,
                 s: MySession,
                 url: str,
                 timeout=REQUEST_TIMEOUT) -> Tuple[MySession, Response]:
        """increased timeout, 10 (default) not enough"""
        resp = s.get(url, headers=self.req_headers, proxies=self.req_proxies, timeout=timeout)
        return s, resp

    def _req_post(self,
                  s: MySession,
                  url: str,
                  params: Dict[str, str],
                  timeout=REQUEST_TIMEOUT) -> Tuple[MySession, Response]:
        """increased timeout, 10 (default) not enough"""
        resp = s.post(
            url,
            data=params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=timeout
        )
        return s, resp

    def _is_logged(self, resp_ajax: Response, resp_logged_in: Response) -> bool:
        """To be used from login() and switch_to_company()"""
        return ('[{"result":"OK"}]' in resp_ajax.text) and ('Saldo y movimientos' in resp_logged_in.text)

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:

        # For a linter
        s = MySession()
        resp_logged_in = Response()
        is_logged = False
        is_credentials_error = False
        reason = ''

        # Customers sometimes provide passwords with extra chars: trim them
        if self.access_type == 'CAL':
            self.userpass = self.userpass[:6]
        else:
            self.userpass = self.userpass[:8]

        for i in range(project_settings.LOGIN_ATTEMPTS):
            s = self.basic_new_session()

            s, _ = self._req_get(
                s,
                'https://www.bancsabadell.com/cs/Satellite/SabAtl/Empresas/1191332202619/es/'
            )
            time.sleep(0.2)

            s.cookies.set(
                'JSESSIONID_JBSWL',
                s.cookies.get('JSESSIONID')[:24] + str(int(time.time() * 1000)),
                domain='.bancsabadell.com',
                path='/'
            )

            req_params = OrderedDict([
                ('language', 'CAS'),
                ('evision.userLang', ''),
                ('evision.RSADeviceFso', ''),
                ('evision.RSADevicePrint', quote(DEVICE_PRINT)),
                # 'E71DB00B4024633DCF86BAA11586633149734'
                ('evision.csid', s.cookies.get('JSESSIONID_JBSWL')),
                ('evision.deviceTokenCookie', ''),  # 185.74.81.117.1582903969936
                ('userNIF', ''),
                ('pinNIF', self.userpass),
                ('pinCIF', ''),
                ('userDNI', ''),
                ('pin', self.userpass.upper()),  # -a 7471, trim to 8 chars -a 28109
                ('userCard', ''),
                ('injvalrnd', 'false'),
                ('injextrnd', ''),
                ('inputAtributes0', 'false'),
                ('inputAtributes1', 'en-US'),
                ('inputAtributes2', '24'),
                ('inputAtributes3', ''),
                ('inputAtributes4', '4'),
                ('inputAtributes5', '1600,900'),
                ('inputAtributes6', '-180'),
                ('inputAtributes7', ''),  # Europe/Madrid
                ('inputAtributes8', 'Linux x86_64'),
                ('inputAtributes9', 'Intel Open Source Technology Center~Mesa DRI Intel(R) Ivybridge Mobile '),
                ('inputAtributes10', 'false'),
                ('inputAtributes11', '0,false,false')
            ])

            username_up = self.username.upper()

            if self.access_type == 'Usuario (DNI)':
                self.logger.info("'Usuario (DNI)' access type detected")  # OK
                req_params['userNIF'] = username_up
                req_params['userDNI'] = username_up
            elif self.access_type == 'CAL':
                self.logger.info("'CAL' access type detected")  # OK
                req_params['userCIF'] = username_up
                req_params['userDNI'] = username_up
            elif self.access_type == 'T. Sec./U. Cons.':
                self.logger.info("'T. Sec./U. Cons.' access type detected")
                req_params['userCard'] = username_up
            else:
                return (s, Response(), False, False,
                        'UNSUPPORTED access type: {}. Abort'.format(self.access_type))

            req_ajax_url = 'https://www.bancsabadell.com/txempbs/LoginDNISCA.doLogin.bs?language=CAS&key={}'.format(
                self._get_random_key(s)
            )
            resp_ajax = s.post(
                req_ajax_url,
                data=req_params,
                headers=self.basic_req_headers_updated({
                    'XMLHttpRequest': 'XMLHttpRequest'
                }),
                proxies=self.req_proxies,
                timeout=REQUEST_TIMEOUT
            )

            if '"result":"SCA"' in resp_ajax.text:
                resp_logged_in = resp_ajax  # for err msg
                # Control to avoid blocking access when we detect 2FA, as for -a 38219 (AYTO ALMERIA)
                if self.db_connector.get_deactivate_2fa(self.db_financial_entity_access_id):
                    reason = DOBLE_AUTH_TYPE_WITH_DEACTIVATION
                else:
                    reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON
                break

            # '...JBSWL=E4104054321587371136357'
            req_url = 'https://www.bancsabadell.com/txempbs/LoginDNISCA.setLogged.bs?language=CAS&key={}'.format(
                self._get_random_key(s)
            )
            s, resp_logged_in = self._req_post(s, req_url, req_params)

            if (any(m in resp_ajax.text for m in BLOCKED_USER_MARKERS)
                or any(m in resp_logged_in.text for m in BLOCKED_USER_MARKERS)):
                reason = BLOCKED_USER_TYPE_COMMON

            is_logged = self._is_logged(resp_ajax, resp_logged_in)
            is_credentials_error = (any(m in resp_ajax.text for m in CREDENTIALS_ERROR_MARKERS)
                                    or any(m in resp_logged_in.text for m in CREDENTIALS_ERROR_MARKERS))

            if is_logged or is_credentials_error or reason:
                break

            # Can't log in. Unknown reason
            self.logger.warning("Can't log in due to unknown reason (sometimes due to website errs). "
                                "Retry #{}".format(i + 1))
            time.sleep(5 + random.random() * 3)  # 5-7 sec

        if is_logged:
            # to be able to switch contracts
            resp_logged_in = s.get(
                'https://www.bancsabadell.com/txempbs/LoginDNISCA.initPageLoginDNINewLanding.bs',
                headers=self.req_headers,
                proxies=self.req_proxies,
                timeout=REQUEST_TIMEOUT
            )

        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def relogin_if_lost_session(self, s: MySession, resp_prev: Response, msg_prefix: str) -> Tuple[
        bool, MySession, bool]:
        """:returns (is_aborted_session, session, is_relogined)
                where is_aborted_session means that the scraper couldn't re-login
                and the caller will abort the scraping process
        """
        is_relogined = False
        is_aborted_session = False
        # The session has been aborted - re-login now
        if any(m in resp_prev.text for m in ABORTED_SESSION_MARKERS):
            time.sleep(0.5 + 0.5 * random.random())
            self.logger.info("{}: aborted session detected. Re-login".format(
                msg_prefix
            ))
            s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()
            is_relogined = True
            if not is_logged:
                # Failed re-login attempt
                self.logger.error("{}: can't re-login to restore the session. Skip".format(
                    msg_prefix
                ))
                is_aborted_session = True
                return is_aborted_session, s, is_relogined
            # Continue the loop when re-login attempt is successful
            if self._current_company_param:

                s, resp_subcontract_logged_in, is_logged2 = self._switch_to_company(
                    s,
                    self._current_company_param
                )
                if not is_logged2:
                    self.logger.error(
                        "{}: can't switch to company {} after successful re-login attempt. "
                        "Abort. RESPONSE:\n{}".format(
                            msg_prefix,
                            self._current_company_param,
                            resp_subcontract_logged_in.text
                        )
                    )
                    is_aborted_session = True
                    return is_aborted_session, s, is_relogined
        return is_aborted_session, s, is_relogined

    def _get_companies(self, s: MySession) -> Tuple[MySession, List[dict]]:
        req_url = 'https://www.bancsabadell.com/txempbs/LoginDNISCA.initGetContracts.bs'
        s, resp = self._req_post(s, req_url, {})

        # get list of companies - nums of contracts
        companies_params = parse_helpers.get_companies_params(resp.text)
        return s, companies_params

    def _switch_to_company(self, s: MySession, company_param: dict) -> Tuple[MySession, Response, bool]:
        self.logger.info('SWITCH TO COMPANY/CONTRACT: {}'.format(company_param))

        req_comp_login_form_url = 'https://www.bancsabadell.com/txempbs/LoginDNISCA.initLogout.bs'

        req_comp_login_form_params = {
            'userContract': company_param['userContract'],
            'userDNI': self.username,
            'contrato': company_param['contrato'],
        }

        # subcontract login page
        s, _resp_login_form = self._req_post(s, req_comp_login_form_url, req_comp_login_form_params)

        req_comp_login_params = {
            'userContract': company_param['userContract'],
            'userDNI': self.username,
            'language': 'CAS',
            'pin': self.userpass.upper(),
            'pinNIF': self.userpass,
        }

        req_comp_login_ajax_url = 'https://www.bancsabadell.com/txempbs/LoginDNISCA.doLogin.bs'
        resp_ajax = s.post(
            req_comp_login_ajax_url,
            data=req_comp_login_params,
            headers=self.basic_req_headers_updated({
                'XMLHttpRequest': 'XMLHttpRequest'
            }),
            proxies=self.req_proxies,
            timeout=REQUEST_TIMEOUT
        )

        req_login_url = 'https://www.bancsabadell.com/txempbs/LoginDNISCA.setLogged.bs'

        s, resp_comp_logged_in = self._req_post(
            s,
            req_login_url,
            req_comp_login_params
        )

        is_logged = self._is_logged(resp_ajax, resp_comp_logged_in)

        return s, resp_comp_logged_in, is_logged

    def process_companies(self, s: MySession, resp_logged_in: Response) -> bool:
        results = []  # type: List[bool]

        # process default company
        result = self.process_company(s, resp_logged_in)
        results.append(result)

        # several contracts

        if 'javascript:loginContrato();' in resp_logged_in.text:
            s, companies_params = self._get_companies(s)
            for company_param in companies_params[1:]:
                s, resp_subcontract_logged_in, is_logged = self._switch_to_company(s, company_param)
                if not is_logged:
                    self.logger.error(
                        "Can't switch to company {}. Abort. RESPONSE:\n{}".format(
                            company_param,
                            resp_subcontract_logged_in.text
                        )
                    )
                    return False
                self._current_company_param = company_param
                result = self.process_company(s, resp_subcontract_logged_in)
                results.append(result)
        return all(results)

    def _get_accounts_from_dropdown(self, s: MySession) -> Tuple[MySession, List[AccountFromDropdown]]:

        time.sleep(0.1)
        s, resp_page_with_accounts = self._req_get(s, URL_DATES_FILTER_WITH_ACCOUNTS_DROPDOWN)

        accounts_parsed_from_dropdown = parse_helpers.get_accounts_from_dropdown(
            resp_page_with_accounts.text
        )  # type: List[AccountFromDropdown]

        return s, accounts_parsed_from_dropdown

    def process_company(self, s: MySession, resp: Response) -> bool:

        company_str = self._current_company_param or 'DEFAULT'
        self.logger.info('PROCESS COMPANY/CONTRACT: {}'.format(company_str))

        s, accounts_from_dropdown = self._get_accounts_from_dropdown(s)
        self.logger.info('Got {} accounts_from_dropdown: {}'.format(
            len(accounts_from_dropdown),
            accounts_from_dropdown
        ))

        ok, s, accounts_scraped = self.get_accounts_scraped(s, accounts_from_dropdown)
        if not ok:
            # already reported
            return False

        self.logger.info('Got {} accounts: {}'.format(
            len(accounts_scraped),
            accounts_scraped
        ))

        self.basic_upload_accounts_scraped(accounts_scraped)

        # Use it for basic_upload_movements_scraped
        accounts_scraped_dict = {account_scraped.FinancialEntityAccountId: account_scraped
                                 for account_scraped in accounts_scraped}  # type: Dict[str, AccountScraped]

        self.basic_log_time_spent('GET BALANCES')

        # Serial processing in any case
        for account_from_dropdown in accounts_from_dropdown:
            ok, s = self.process_account(
                s,
                resp,
                account_from_dropdown,
                accounts_scraped_dict
            )
            time.sleep(0.1)

        self.basic_log_time_spent('GET MOVEMENTS')
        return True

    def get_accounts_scraped(
            self,
            s: MySession,
            accounts_from_dropdown: List[AccountFromDropdown]) -> Tuple[bool, MySession, List[AccountScraped]]:
        # https://www.bancsabadell.com/txempbs/CUGlobalPositionNew.init.bs?key=E71DB0015246586831587384220785
        # '58E4AB077159533581587401017342'
        # req_url = extract.get_link_by_text(resp_prev.text, resp_prev.url, 'Posición global')
        req_pos_global_url = 'https://www.bancsabadell.com/txempbs/CUGlobalPositionNew.init.bs?key={}'.format(
            self._get_random_key(s)
        )
        s, resp_pos_global = self._req_get(s, req_pos_global_url)

        accounts_parsed = parse_helpers.get_accounts_parsed(resp_pos_global.text)

        # Some accesses have broken Positon global (restricted access?) - it's empty, see -a 9131
        if not resp_pos_global.text:
            self.logger.info("get_accounts_scraped: 'Position global' page is empty. Try fallback method")
            accounts_parsed = parse_helpers.convert_accs_from_dropdown_to_parsed(accounts_from_dropdown)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(acc['organization_title'], acc)
            for acc in accounts_parsed
        ]
        if (not accounts_scraped) and ('No hay permisos para realizar la operación' in resp_pos_global.text):
            self.logger.warning("Can't get accounts_scraped: no permissions for 'Position global'. Abort")
            return False, s, accounts_scraped

        return True, s, accounts_scraped

    def _req_movs_filter_params(
            self,
            account_from_dropdown: AccountFromDropdown,
            date_from_str: str,
            date_to_str: str = None) -> Dict[str, str]:
        """Dates in dd/mm/yyyy fmt"""
        if not date_to_str:
            date_to_str = self.date_to_str
        day_to, month_to, year_to = date_to_str.split('/')

        day_from, month_from, year_from = date_from_str.split('/')
        params = OrderedDict([
            ('orderAccount.selectable-index', str(account_from_dropdown.idx)),
            ('purpose.handle', ''),
            ('dateMovFrom2', date_from_str),
            ('dateMovTo2', date_to_str),
            ('r0', 'yes'),
            ('amountFromAux.value', ''),
            ('amountToAux.value', ''),
            ('amountFrom.value', ''),
            ('amountTo.value', ''),
            ('chargeType', ''),
            ('inputComponentsForm:cpIn_radioButton_3_componentHelpAuxError', ''),
            ('inputComponentsForm:cpIn_radioButton_3_componentHelpAuxHelp', ''),
            ('reference', ''),
            ('lastMovements', ''),
            ('selectedCriteria', 'Desde {} hasta {}.'.format(date_from_str, self.date_to_str)),
            ('selectedAmounts', ''),
            ('dateMovFrom.day', day_from),
            ('dateMovFrom.month', month_from),
            ('dateMovFrom.year', year_from),
            ('dateMovTo.day', day_to),
            ('dateMovTo.month', month_to),
            ('dateMovTo.year', year_to),
            ('dateValueFrom.day', ''),
            ('dateValueFrom.month', ''),
            ('dateValueFrom.year', ''),
            ('dateValueTo.day', ''),
            ('dateValueTo.month', ''),
            ('dateValueTo.year', ''),
            ('CUExtractOperationsQuery.paginationRows', '200')
        ])
        return params

    def _filter_movs_with_attempts(
            self,
            s: MySession,
            fin_ent_account_id: str,
            page_ix: int,
            req_movs_url: str,
            req_movs_params: Dict[str, str]) -> Tuple[bool, MySession, Response]:
        """:returns (is_success, session, resp)"""
        resp_movs_i = Response()
        for attempt in range(1, 6):  # avoid inf loop
            msg_prefix = '{}: page {}: att #{}'.format(fin_ent_account_id, page_ix, attempt)
            self.logger.info('{}: post req to be able get HTML response'.format(msg_prefix))
            s, resp_movs_i = self._req_post(s, req_movs_url, req_movs_params, timeout=REQUEST_TIMEOUT * 2)

            # Check for correct response, it is possible to get None here or empty response text
            if resp_movs_i.status_code is None or not resp_movs_i.text:
                self.logger.warning('{}: no response html. Retry'.format(msg_prefix))
                time.sleep(1 + random.random())
                # open page with filter, can do mov request only after this one
                s, resp = self._req_get(s, URL_DATES_FILTER_WITH_ACCOUNTS_DROPDOWN)
                continue
            is_aborted_session, s, is_relogined = self.relogin_if_lost_session(
                s,
                resp_movs_i,
                msg_prefix
            )
            if is_aborted_session:
                False, s, Response()
            if is_relogined:
                # open page with filter, can do mov request only after this one
                s, resp = self._req_get(s, URL_DATES_FILTER_WITH_ACCOUNTS_DROPDOWN)
                continue
            break
        else:
            self.logger.error(
                "{}: page {}: can't get resp_movs_i after several attempts. RESPONSE\n{}".format(
                    fin_ent_account_id,
                    page_ix,
                    resp_movs_i.text
                )
            )
            return False, s, Response()
        # success
        return True, s, resp_movs_i

    def process_account(
            self,
            s: MySession,
            resp_prev: Response,
            account_from_dropdown: AccountFromDropdown,
            accounts_scraped_dict: Dict[str, AccountScraped]) -> Tuple[bool, MySession]:
        """
        Get account movements only because balances got from mobile verison
        to handle case when there are no account balance if there are no movements in the period
        parse and save
        """

        # account_no = account_parsed_from_dropdown['account_no']
        fin_ent_account_id = account_from_dropdown.account_no
        if fin_ent_account_id not in accounts_scraped_dict:
            self.logger.error("{}: can't find the key in accounts_scraped_dict. There are {}. Skip".format(
                fin_ent_account_id,
                list(accounts_scraped_dict.keys())
            ))
            return False, s

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True, s

        if not self.basic_is_in_process_only_accounts(fin_ent_account_id):
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.SKIPPED_EXPLICITLY)
            return True, s  # already reported

        account_scraped = accounts_scraped_dict[fin_ent_account_id]
        # open page with filter, can do mov request only from this page
        s, resp = self._req_get(s, URL_DATES_FILTER_WITH_ACCOUNTS_DROPDOWN)

        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        # DAF: Because of the info about receipts is not included in excel file, we dont download excel anymore. Now
        # we parse html responses
        # req1_url = 'https://www.bancsabadell.com/txempbs/CUExtractOperationsQueryNew.accountDataToQuery.bs?excel&'
        # DAF: 'CUExtractOperationsQuery.paginationRows': 20 is the default value
        # But we use 100 to improve performance. 200 works here and show 200 movements (if exist)
        # First we request CUExtractOperationsQueryNew.accountDataToQuery.bs,
        # And after that, we continue requesting CUExtractOperationsQueryNew.next.bs while is not the last movement

        # https://www.bancsabadell.com/txempbs/CUMovementsQuery.initGetMovements.bs
        req_movs_page1_url = 'https://www.bancsabadell.com/txempbs/CUExtractOperationsQueryNew.accountDataToQuery.bs?'
        req_movs_page1_params = self._req_movs_filter_params(account_from_dropdown, date_from_str)

        req_movs_next_url = 'https://www.bancsabadell.com/txempbs/CUExtractOperationsQueryNew.next.bs'
        req_movs_next_params = OrderedDict([
            ('owner', ''),
            ('orderAccount.selectable-index', str(account_from_dropdown.idx)),
            ('selectedCriteria', 'Desde {} hasta {}.'.format(date_from_str, self.date_to_str)),
            ('selectedAmounts', ''),
            ('selectedPurpose', ''),
            ('selectedReference', ''),
            ('CUExtractOperationsQuery.paginationRows', '20')
        ])

        is_last_movements = False
        movements_parsed = []
        resp_movs_i = Response()  # suppress linter warnings

        req_movs_i_url = req_movs_page1_url
        req_movs_i_params = req_movs_page1_params

        # Pagination
        for page_ix in range(1, 101):  # avoid inf loop
            if is_last_movements:
                self.logger.info('{}: no more pages with movs'.format(
                    fin_ent_account_id
                ))
                break

            self.logger.info('{}: page {}: get movements'.format(fin_ent_account_id, page_ix))

            # Get resp_mov_i,
            # handle case when session response empty due to multiple requests
            ok, s, resp_movs_i = self._filter_movs_with_attempts(
                s,
                fin_ent_account_id,
                page_ix,
                req_movs_i_url,
                req_movs_i_params
            )
            if not ok:
                break  # already reported

            movements_parsed_i, is_too_many_movements, is_last_movements = \
                parse_helpers.parse_movements_from_html(resp_movs_i.text)
            if movements_parsed_i:
                self.logger.info('{}: page {}: got movements from date {} (need from {})'.format(
                    fin_ent_account_id,
                    page_ix,
                    movements_parsed_i[-1]['operation_date'],
                    date_from_str))

            movements_parsed.extend(movements_parsed_i)

            if is_too_many_movements:
                self.logger.warning(
                    '{}: page {}: TOO MANY MOVEMENTS. RE-SCRAPE ONE MORE TIME TO GET ALL RECENT MOVEMENTS'.format(
                        fin_ent_account_id,
                        page_ix,
                    )
                )

            # Prepare for the next page
            req_movs_i_url = req_movs_next_url
            req_movs_i_params = req_movs_next_params

        # / end of while (not is_last_movements) and (not is_aborted_session)

        movements_parsed_extra_details = movements_parsed
        if self.basic_should_scrape_extended_descriptions():
            movements_parsed_extra_details = self.basic_get_movements_parsed_w_extra_details(
                s,
                movements_parsed,
                account_scraped,
                date_from_str,
                n_mov_details_workers=MOV_DETAILS_MAX_WORKERS,
            )

        movements_scraped, movements_parsed_filtered = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_extra_details,
            date_from_str
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        ok = self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )
        if not ok:
            # Early return if didn't upload the movements.
            # It prevents errs for next accounts from the list
            return False, s

        _, movements_scraped_w_receipts_info = self.download_receipts(
            s,
            account_scraped,
            movements_scraped,
            movements_parsed_filtered,
            resp_movs_i.url
        )

        self.basic_set_movement_scraped_references(
            account_scraped,
            movements_scraped_w_receipts_info,
            parse_helpers.parse_reference_from_receipt
        )

        return True, s

    def process_movement(
            self,
            s: MySession,
            movement_parsed: MovementParsed,
            fin_ent_account_id: str,
            meta: dict = None) -> MovementParsed:

        mov_str = self.basic_mov_parsed_str(movement_parsed)
        self.logger.info("{}: process {}".format(
            fin_ent_account_id,
            mov_str,
        ))

        movement_parsed_extra_details = movement_parsed.copy()
        if not movement_parsed['mov_details_req_params']:
            movement_parsed_extra_details['description_extended'] = movement_parsed_extra_details['description']
            return movement_parsed_extra_details

        req_mov_url = ('https://www.bancsabadell.com/txempbs/CUExtractOperationsQueryNew.movementDetail.bs?{}'.format(
            movement_parsed['mov_details_req_params']
        ))
        resp_mov_details = s.post(
            req_mov_url,
            headers=self.req_headers,
            proxies=self.req_proxies,
            stream=False
        )

        movement_parsed_extra_details['description_extended'] = parse_helpers.get_description_extended(
            resp_mov_details.text,
            movement_parsed
        )

        return movement_parsed_extra_details

    def main(self) -> MainResult:
        # desktop regular website usage
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        ok1 = self.process_companies(s, resp_logged_in)
        ok2, _ = self.download_correspondence(s)
        if not (ok1 and ok2):
            return self.basic_result_common_scraping_error()

        return self.basic_result_success()
