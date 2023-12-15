import random
import time
import urllib.parse
from collections import OrderedDict
from threading import Lock
from typing import Dict, List, Tuple

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import AccountParsed, AccountScraped, ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.ing_scraper import parse_helpers

__version__ = '3.10.0'

__changelog__ = """
3.10.0
use account-level result_codes
3.9.0
call basic_upload_movements_scraped with date_from_str
3.8.0
skip inactive accounts
3.7.0
use basic_new_session
upd type hints
fmt
3.6.0
use basic_get_date_from
3.5.0
new login method (now supports both: new and previous)
increased timeouts
parse_helpers: get_view_state, get_login_enter_uname_url, get_login_enter_passw_url
3.4.0
increased timeout at login step
better credentials error detector to avoid false positives if request is timed out
parse_helpers: get_accounts_parsed: more strict parsing to avoid parsing errs in some cases
3.3.0
basic_movements_scraped_from_movements_parsed: new format of the result 
3.2.0
view_state_param_num_start_scrape_account to support IngMulticontractScraper
3.1.0
bugfix: handle is_credentials_error, is_logged (were ignored before)
process_contract
time.time() instead of datetime in cookies funcs
remove unused code
3.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
2.1.0
login: handle redirect to err page after first login page (login unknown error)
2.0.0
basic_movements_scraped_from_movements_parsed
OperationalDatePosition, KeyValue support
1.0.0
basic_set_movements_scraping_finished
basic_upload_movements_scraped
value_date = operational_date by default
0.4.0
is_credentials_error impl
0.3.0
check correctly is_logged for multicontract
0.2.0
impl for user access: serial scraping
0.1.0
movements parsed
"""

lock = Lock()

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:53.0) Gecko/20100101 Firefox/53.0'

IS_LOGGED_IN_MARKERS = [
    '<span id="j_id38">Desconectar</span>',
    'Seleccione el negocio con el que desea operar'
]

IS_CREDENTIALS_ERROR_MARKERS = [
    'Otras formas de acceso',
    'Borrar'
]


class IngScraper(BasicScraper):
    """
    Partially implemented:
        - one contract implementation;
        - log in for both access types
    """
    scraper_name = 'IngScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        # to set before each account processing
        self.view_state_param_num_start_scrape_account = 3
        # global counter of opened pages
        self.view_state_param_num = self.view_state_param_num_start_scrape_account
        self.req_headers = {'User-Agent': USER_AGENT}
        self.is_login_sca = False  # the flag corresponds to new (login_sca) or old login methods
        self.update_inactive_accounts = False

    def _view_state_param(self) -> str:
        return '!{}'.format(self.view_state_param_num)

    def _next_view_state_param(self) -> str:
        """Increase view state num and return it as param"""
        with lock:
            self.view_state_param_num += 1
        return self._view_state_param()

    def _set_necessary_cookies(self, s: MySession) -> MySession:
        cc = {
            'ingSmePixelRepo': 'comercial',
            's_cc': 'true',
            's_gts': '1',
            's_mca': 'Direct',
            's_sq': '[[B]]',
            's_nr': str(int(time.time()) * 1000),
        }

        for c, v in cc.items():
            s.cookies.set(c, v, domain='.ingdirect.es', path='/')

        return s

    def _set_necessary_cookies_after_logged_in(self, s: MySession) -> MySession:
        cc = {
            'ICO_auth': '1',
        }

        for c, v in cc.items():
            s.cookies.set(c, v, domain='.ingdirect.es', path='/')

        return s

    def login(self) -> Tuple[MySession, Response, bool, bool]:
        """
        Handles both types of access:
            Acceso para clientes
            Acceso para usuarios sin firma

        steps:
            req1 - open init page to get cookies and get params
            req2 - post data at first step (username first and second)
            req3 - post encoded password

        Login supports new (logic_sca) method and previous (login_n) -
        these methods named by their urls
        """

        s = self.basic_new_session()

        req1_init_url = 'https://ing.ingdirect.es/SME/Transactional/faces/default'

        # get JSESSIONID only
        resp1_init = s.get(
            req1_init_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        s = self._set_necessary_cookies(s)

        req2_enter_uname_url = parse_helpers.get_login_enter_uname_url(resp1_init.text, resp1_init.url)

        # DETECT NEW LOGIN METHOD
        if 'login-sca' in req2_enter_uname_url:
            self.is_login_sca = True

        req2_enter_uname_headers = self.basic_req_headers_updated({'Referer': resp1_init.url})
        if not self.is_login_sca:
            req2_enter_uname_headers['Tr-XHR-Message'] = 'true'

        req2_viewstate_param = parse_helpers.get_view_state(resp1_init.text)

        req2_enter_uname_params = OrderedDict([
            ('doConsultantLogin', ''),
            ('documentNumber', ''),
            ('documentType', '0'),
            ('birthDateDay', ''),
            ('birthDateMonth', ''),
            ('birthDateYear', ''),
            ('consultantDocumentNumber', ''),
            ('consultantDocumentType', '0'),
            ('consultantCif', ''),
            ('org.apache.myfaces.trinidad.faces.FORM', 'clientID_loginForm'),
            ('_noJavaScript', 'false'),
            ('javax.faces.ViewState', req2_viewstate_param),
            ('source', ''),
        ])

        if not self.is_login_sca:
            req2_enter_uname_params['event'] = 'autosub'
            req2_enter_uname_params['partial'] = 'true'

        if self.access_type == 'Acceso para usuarios sin firma':
            req2_enter_uname_params['consultantDocumentNumber'] = self.username
            req2_enter_uname_params['consultantCif'] = self.username_second
            req2_enter_uname_params['source'] = 'doConsultantLogin'

        elif self.access_type == 'Acceso para clientes':
            req2_enter_uname_params['documentNumber'] = self.username
            req2_enter_uname_params['birthDateDay'] = self.username_second[:2]
            req2_enter_uname_params['birthDateMonth'] = self.username_second[2:4]
            req2_enter_uname_params['birthDateYear'] = self.username_second[-4:]
            req2_enter_uname_params['source'] = 'doLogin'

        else:
            raise Exception('Unknown access_type: {}'.format(self.access_type))

        resp2_enter_uname = s.post(
            req2_enter_uname_url,
            data=req2_enter_uname_params,
            headers=req2_enter_uname_headers,
            proxies=self.req_proxies,
            timeout=20
        )

        # Can't log in due to unknown reason
        # Redirect to page contains:
        # Ups!
        # Lo sentimos, parece que no ha sido posible realizar la operación. Le recomendamos intentarlo
        # de nuevo en unos minutos. En caso de que el error continúe, le atenderemos en el 91 206 66 88.
        if '<redirect>/SME/Transactional/faces/error</redirect>' in resp2_enter_uname.text:
            is_credentials_error = False
            is_logged = False
            return s, resp2_enter_uname, is_logged, is_credentials_error

        req3_enter_passw_url = parse_helpers.get_login_enter_passw_url(
            resp2_enter_uname.text,
            resp2_enter_uname.url
        )

        req3_enter_passw_headers = self.basic_req_headers_updated({'Referer': resp2_enter_uname.url})
        req3_viewstate_param = parse_helpers.get_view_state(resp2_enter_uname.text)  # was resp1

        passw_security = parse_helpers.build_login_passw_params_from_resp(resp2_enter_uname.text,
                                                                          self.userpass)

        # new req params for .../sme-validate-sca-login.xhtml
        req3_enter_passw_params = OrderedDict([
            ('fromOlvidoCliente', ''),
            ('security', passw_security),
            ('org.apache.myfaces.trinidad.faces.FORM', 'formSCA'),
            ('_noJavaScript', 'false'),
            ('javax.faces.ViewState', req3_viewstate_param),
            ('source', 'security')
        ])

        # redefine for older login
        if not self.is_login_sca:
            req3_enter_passw_params = OrderedDict([
                ('documentType', '0'),
                ('birthDateDay', ''),
                ('birthDateMonth', ''),
                ('birthDateYear', ''),
                ('fromOlvidoCliente', ''),
                ('isConsultantAccess', ''),
                ('security', passw_security),
                ('consultantDocumentType', '0'),
                ('org.apache.myfaces.trinidad.faces.FORM', 'clientID_loginForm'),
                ('_noJavaScript', 'false'),
                ('javax.faces.ViewState', req3_viewstate_param),
                ('source', 'security')
            ])

            if self.access_type == 'Acceso para clientes':
                req3_enter_passw_params['documentNumber'] = self.username
                req3_enter_passw_params['birthDateDay'] = self.username_second[:2]
                req3_enter_passw_params['birthDateMonth'] = self.username_second[2:4]

        time.sleep(1 + random.random())

        resp3_enter_passw = s.post(
            req3_enter_passw_url,
            data=req3_enter_passw_params,
            headers=req3_enter_passw_headers,
            proxies=self.req_proxies,
            timeout=30  # to avoid 'Ups!' instead of accs at Home page in personal area
        )

        is_logged = any(m in resp3_enter_passw.text for m in IS_LOGGED_IN_MARKERS)

        # Borrar means that we are still at password page
        # There are no other markers of wrong password
        is_credentials_error = (
                any(m in resp3_enter_passw.text for m in IS_CREDENTIALS_ERROR_MARKERS)
                and not is_logged  # handle false positive 'Borrar aviso'
        )

        s = self._set_necessary_cookies_after_logged_in(s)

        return s, resp3_enter_passw, is_logged, is_credentials_error

    def process_contract(self, s: MySession, resp_logged_in: Response) -> bool:
        """
        in some cases (cif-based login) the page doesn't contain accounts info - just stubs
        """
        organization_title = parse_helpers.get_organization_title(resp_logged_in.text)
        self.logger.info("Process contract '{}'".format(organization_title))

        accounts_parsed = parse_helpers.get_accounts_parsed(
            resp_logged_in.text
        )  # type: List[AccountParsed]

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(organization_title, acc_parsed)
            for acc_parsed in accounts_parsed
        ]

        accounts_scraped_dict = self.basic_gen_accounts_scraped_dict(accounts_scraped)

        self.logger.info('Company {} has accounts {}'.format(organization_title, accounts_scraped))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        # only serial processing allowed
        for acc_parsed in accounts_parsed:
            # need to reset counter before each 'process_account' or will fail
            self.view_state_param_num = self.view_state_param_num_start_scrape_account
            self.process_account(s, resp_logged_in, acc_parsed, accounts_scraped_dict)

        return True

    def process_account(self,
                        s: MySession,
                        resp_logged_in: Response,
                        account_parsed: AccountParsed,
                        accounts_scraped_dict: Dict[str, AccountScraped]) -> bool:

        fin_ent_account_id = account_no = account_parsed['account_no']

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        action_req1_url, _ = extract.build_req_params_from_form_html(resp_logged_in.text, 'formulario')
        if 'home' not in action_req1_url:
            self.basic_log_wrong_layout(
                resp_logged_in,
                '{}: wrong action_req1_url: {}. Exit'.format(
                    fin_ent_account_id,
                    action_req1_url
                )
            )
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
            return False

        # open account page with movements'
        req1_url = urllib.parse.urljoin(resp_logged_in.url, action_req1_url)

        req1_params = OrderedDict([
            ('redirRedID', ''),
            ('redirAlertCod', ''),
            ('alertTU', ''),
            ('alertTD', ''),
            ('opType', ''),
            ('linkMessage', ''),
            ('codeLink', ''),
            ('favoritesCodes', ''),
            ('listReceptores', ''),
            ('indexNote', ''),
            ('isClientAReceiver', ''),
            ('contNotes', 0),
            ('note_text', ''),
            ('productType', ''),
            ('docType', ''),
            ('formAperturaInclude', ''),
            ('sequencesFiles', ''),
            ('sequenceFile_1', ''),
            ('files-list', ''),
            ('actionRequestId', ''),
            ('campaignCommunicationCodeRequestId', ''),
            ('campaignCodeRequestId', ''),
            ('bannerProductTypeRequest', ''),
            ('org.apache.myfaces.trinidad.faces.FORM', 'formulario'),
            ('_noJavaScript', 'false'),
            ('javax.faces.ViewState', self._view_state_param()),
            ('source', account_parsed['id_param']),
            ('index', account_parsed['index_param']),
            ('productGroup', account_parsed['product_group_param'])  # SAV, SAV_TRANSACTIONAL
        ])

        req1_headers = self.req_headers.copy()
        req1_headers['Referer'] = resp_logged_in.url
        # failed in multicontract
        resp1 = s.post(
            req1_url,
            data=req1_params,
            headers=req1_headers,
            proxies=self.req_proxies,
            timeout=20,
        )

        req2_headers = self.req_headers.copy()
        req2_headers['Referer'] = resp1.url
        req2_headers['Tr-XHR-Message'] = 'true'

        # get excel. step1: click on excel icon (necessary)
        action_req2_url, _ = extract.build_req_params_from_form_html(resp1.text, 'formulario')

        if 'viewAccountsMovements' not in action_req2_url:
            self.basic_log_wrong_layout(
                resp1,
                '{}: wrong action_req2_url: {}. Exit'.format(
                    fin_ent_account_id,
                    action_req2_url
                )
            )
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
            return False

        req2_url = urllib.parse.urljoin(resp_logged_in.url, action_req2_url)

        req2_params = OrderedDict([
            ('loadRowDetail', ''),
            ('rowIndex', ''),
            ('loadRows', ''),
            ('showMovsRank', ''),
            ('from', date_from_str),
            ('to', self.date_to_str),
            ('amounts_from', ''),
            ('amounts_to', ''),
            ('pag1_hiddenActualPage', 1),
            ('pag1_hiddenRequestedPage', 1),
            ('org.apache.myfaces.trinidad.faces.FORM', 'formulario'),
            ('_noJavaScript', 'false'),
            ('javax.faces.ViewState', self._next_view_state_param()),
            ('source', 'showMovsRank'),
            ('event', 'autosub'),
            ('partial', 'true')
        ])

        resp2 = s.post(
            req2_url,
            data=req2_params,
            headers=req2_headers,
            proxies=self.req_proxies,
            timeout=20,
        )

        # get excel. step2: download
        req3_headers = self.req_headers.copy()
        req3_headers['Referer'] = resp1.url
        req3_headers['Connection'] = 'keep-alive'
        req3_headers['Upgrade-Insecure-Requests'] = '1'
        req3_headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'

        req3_params = OrderedDict([
            ('rowIndex', ''),
            ('comboRangos', 1),
            ('from', date_from_str),
            ('to', self.date_to_str),
            ('amounts_from', ''),
            ('amounts_to', ''),
            ('pag1_hiddenActualPage', 1),
            ('pag1_hiddenRequestedPage', 1),
            ('org.apache.myfaces.trinidad.faces.FORM', 'formulario'),
            ('_noJavaScript', 'false'),
            ('javax.faces.ViewState', self._next_view_state_param()),
            ('source', 'downloadButton')
        ])

        resp3_excel = s.post(
            req2_url,
            data=req3_params,
            headers=req1_headers,
            proxies=self.req_proxies,
            timeout=30,
        )

        movements_parsed = parse_helpers.get_movements_parsed_from_resp_excel(resp3_excel)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str
        )

        self.basic_log_process_account(account_no, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            accounts_scraped_dict[fin_ent_account_id],
            movements_scraped,
            date_from_str=date_from_str
        )
        return True

    def main(self) -> MainResult:

        s, resp_logged_in, is_logged, is_credentials_error = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url,
                                                                      resp_logged_in.text)

        self.process_contract(s, resp_logged_in)

        self.basic_log_time_spent("GET MOVEMENTS")
        return self.basic_result_success()
