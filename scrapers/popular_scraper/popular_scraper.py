import datetime
import html
import json
import os
import random
import re
import subprocess
import time
import urllib.parse
from collections import OrderedDict
from concurrent import futures
from typing import List, Tuple

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, AccountScraped, MovementParsed, ScraperParamsCommon,
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.popular_scraper import parse_helpers

__version__ = '5.5.0'

__changelog__ = """
5.5.0
call basic_upload_movements_scraped with date_from_str
5.4.1
upd type hints
5.4.0
login: 'MOVED to Santander' detector
5.3.0
process_account: use MAX_MOVEMENTS_DATES_RANGE
5.2.0
handle_additional_login_steps if several contracts
improved parse_helpers.get_mas_tarde_params to handle cases with json resp
5.1.0
handle additional login steps when real user action required: detect it and send err msg
5.0.0
handle_additional_login_steps
4.6.0
log in additional required user actions detector
4.5.1
fixed type hints
4.5.0
basic_movements_scraped_from_movements_parsed: new format of the result
4.4.0
fix case when exact movements duplicates occur:
to avoid duplicates of the pages, we check that the whole page already was scraped
4.3.0
support for Pastor scraper
4.2.0
login: handle too long password (trim to 6 chars)
4.1.0
parse_helpers: remove 'ES' checker in account_no (they may be invalid in any case if customer uses aliases)
need to extract IBANs from another place
4.0.1
process_account: dates in err msgs
4.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
"""

NO_ACCOUNTS_SIGNS = [
    'NO EXISTEN CONTRATOS DEL GRUPO SELECCIONADO',
    'NO EXISTEN CONTRATOS PARA ESTE CLIENTE',
    'El contrato no esta activo',
    'no tiene este producto contratado',
    'no existen contratos que se puedan seleccionar'
]

ACCOUNTS_REQ_PARAM = {
    ACCOUNT_TYPE_DEBIT: 'CUE0007C',
    ACCOUNT_TYPE_CREDIT: 'CUE0019C'
}

CALL_JS_ENCRYPT_LIB = 'node {}'.format(
    os.path.join(
        project_settings.PROJECT_ROOT_PATH,
        project_settings.JS_HELPERS_FOLDER,
        'popular_encrypter.js'
    )
)

CALL_JS_CIPHER_PARAMS_LIB = 'node {}'.format(
    os.path.join(
        project_settings.PROJECT_ROOT_PATH,
        project_settings.JS_HELPERS_FOLDER,
        'popular_form_cipher.js'
    )
)

CREDENTIALS_ERROR_MARKERS = ['Identificación personal incorrecta']
MAX_MOVEMENTS_DATES_RANGE = 120  # backend restriction


class PopularScraper(BasicScraper):
    """
    Implements Usuario and Usuario delegado access types.
    Process contracts in parallel mode.
    Get balances of accounts of each contract quickly.
    Then get movements of each account of one contract in serial mode (acceptable time)
    to avoid possible bans (because the backend of this website is most strict)
    """
    scraper_name = 'PopularScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        self.req_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu '
                          'Chromium/62.0.3202.89 Chrome/62.0.3202.89 Safari/537.36'
        }

        # to redefine in child (pastor_scraper)
        self.base_url = 'https://www4.bancopopular.es/'
        self.login_url_prefix = 'https://www4.bancopopular.es/eai_logon/'
        self.should_handle_additional_login_steps = False  # handle additional user actions

    def _url(self, suffix):
        return urllib.parse.urljoin(self.base_url, suffix)

    def _get_encrypted(self, userpass) -> str:
        cmd = '{} "{}"'.format(CALL_JS_ENCRYPT_LIB, userpass)
        result_bytes = subprocess.check_output(cmd, shell=True)
        encrypted = result_bytes.decode().strip()
        return encrypted

    def _get_ciphered(self, data: dict) -> dict:
        cmd = "{} '{}'".format(CALL_JS_CIPHER_PARAMS_LIB, json.dumps(data))
        result_bytes = subprocess.check_output(cmd, shell=True)
        ciphered_str = result_bytes.decode().replace('\n', '').replace("'", '"')
        ciphered_dict = json.loads(ciphered_str)
        return ciphered_dict

    def _get_page_html_from_json_resp(self, resp: Response,
                                      caller_func: str = 'main') -> Tuple[str, bool, bool]:
        """
        Parse resp:
            extract 'page' from resp like {'page': '<DOCTYPE...', ...,}
            and is_no_accounts_sign (True if 'no accounts sign' found)

        If is_no_accounts_sign = True then no need to get 'page'
        If is_no_accounts_sign = False and no 'page' then error msg and is_success = False

        Because when backend sends response for a request which expects accounts, it will send another response:
        without 'page' key but with NO_ACCOUNTS_SIGN - this we handle here
        """

        is_no_accounts_sign = False
        is_success = True
        page_html = resp.text

        if any(sign in resp.text for sign in NO_ACCOUNTS_SIGNS):
            is_no_accounts_sign = True

        try:
            resp_json = html.unescape(resp.json())
        except Exception as exc:
            is_success = False
            self.logger.error("{}: {}: can't parse response to JSON: {}".format(
                caller_func,
                exc,
                resp.text
            ))
            return page_html, is_success, is_no_accounts_sign

        # Page can be empty exact if is_no_accounts_sign = True (no page passed from backend)
        page_html = html.unescape(resp_json.get('page', ''))

        if (not page_html) and (not is_no_accounts_sign):
            # Err only if is_no_accounts_sign = False
            is_success = False
            self.logger.error("{}: can't extract page html: {}".format(
                caller_func,
                resp.text
            ))
            return resp.text, is_success, is_no_accounts_sign

        return page_html, is_success, is_no_accounts_sign

    def login(self) -> Tuple[MySession, Response, bool, bool, str, str]:
        passw_encrypted = self._get_encrypted(self.userpass[:6])  # trim too long password
        s = self.basic_new_session()

        # req0_url = 'https://www2.bancopopular.es/empresasN'
        # req0_url = 'https://www4.bancopopular.es/eai_logon/GbpInternetLogonEAI/gbplogon?tipo_btt=em'
        req0_url = urllib.parse.urljoin(self.login_url_prefix, 'GbpInternetLogonEAI/gbplogon?tipo_btt=em')
        resp0 = s.get(
            req0_url,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        req1_url = urllib.parse.urljoin(self.login_url_prefix, 'GbpInternetLogonEAI/EstablishSession?id=login')
        _, req1_params = extract.build_req_params_from_form_html(resp0.text, 'identifica')
        req1_params['username'] = self.username
        req1_params['userpass'] = passw_encrypted

        if self.access_type == 'Usuario':
            req1_params['GL_tipoUsuario'] = 'UN'
        elif self.access_type == 'Usuario delegado':
            req1_params['GL_tipoUsuario'] = 'DE'
        else:
            return s, resp0, False, False, '', 'Unknown access type: {}'.format(self.access_type)

        resp1 = s.post(
            req1_url,
            data=req1_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req2_url = self._url('/eai_desktop/GbpInternetDesktop/EstablishSession')
        req2_headers = self.basic_req_headers_updated(
            {
                'Referer': resp1.url
            }
        )
        resp_logged_in = s.get(
            req2_url,
            headers=req2_headers,
            proxies=self.req_proxies
        )

        is_logged = 'Your login was successful' in resp1.text
        is_credentials_error = 'personal incorrecta' in resp1.text

        dse_new_desktop_session_check_param = parse_helpers.get_dse_new_desktop_session_check_param(resp_logged_in.text)
        reason = ''
        if not is_logged and 'bancosantander.es' in resp_logged_in.url:
            reason = 'MOVED to Santander. Pls, update the access'

        return s, resp_logged_in, is_logged, is_credentials_error, dse_new_desktop_session_check_param, reason

    def handle_additional_login_steps(
            self,
            s: MySession,
            resp_additional_steps_init: Response,
            dse_new_desktop_session_check_param: str) -> Tuple[MySession, Response, int, bool]:
        """
        :return: (session, response, contracts_num, is_processed)
        """

        self.logger.info('Handle additional login steps. Emulate "remind me later" action')

        page_html = parse_helpers.extract_page_html_from_json(resp_additional_steps_init.json())

        req_add_log_act_headers = self.basic_req_headers_updated({
            'Referer': resp_additional_steps_init.url,
            'requesttype': 'launcher',
            'X-Requested-With': 'XMLHttpRequest'
        })
        req_add_log_act_params = {'dse_new_desktop_session_check': dse_new_desktop_session_check_param}

        additional_login_action = parse_helpers.get_additional_login_action(page_html)
        # expect
        # https://www4.bancopopular.es/eai_desktop/GBP.0746_CI_ARP.BTT_Local.AreaPersonal/ARP0038M.transaction
        req_aditional_login_action_url = urllib.parse.urljoin(
            self.base_url,
            '/eai_desktop' + additional_login_action
        )

        resp_additional_login_action = s.post(
            req_aditional_login_action_url,
            data=req_add_log_act_params,
            headers=req_add_log_act_headers,
            proxies=self.req_proxies
        )

        page_add_log_act_html = resp_additional_login_action.text
        if 'Realizar' not in page_add_log_act_html:
            return s, resp_additional_login_action, 0, False

        req_mas_tarde_params = parse_helpers.get_mas_tarde_params(
            page_add_log_act_html,
            dse_new_desktop_session_check_param
        )
        req_mas_tarde_url = urllib.parse.urljoin(
            self.base_url,
            '/eai_desktop/GBP.0738_CI_CUE.BTT_Local.Cuentas/Request'
        )

        dynatrace_header = parse_helpers.get_dynatrace_header(req_aditional_login_action_url)
        req_mas_tarde_headers = self.basic_req_headers_updated({
            'Referer': resp_additional_steps_init.url,
            'requesttype': 'ajax',
            'X-Requested-With': 'XMLHttpRequest',
            # ARP0038M, CUE0031C
            'x-dynaTrace': 'NA={};SN=C{};TE=masTarde'.format(dynatrace_header, dynatrace_header),
            'connection': 'keep-alive',
        })
        session_resp_codes_bad_for_proxies_copy = s.resp_codes_bad_for_proxies.copy()

        s.resp_codes_bad_for_proxies = []  # allow all, it is possible to get 500

        resp_mas_tarde = s.post(
            req_mas_tarde_url,
            data=req_mas_tarde_params,
            headers=req_mas_tarde_headers,
            proxies=self.req_proxies
        )
        s.resp_codes_bad_for_proxies = session_resp_codes_bad_for_proxies_copy

        # now open contracts page again
        s, resp_contracts_list_or_contract_home, contracts_num = self.open_home_page_and_get_contracts(
            s,
            dse_new_desktop_session_check_param
        )

        return s, resp_contracts_list_or_contract_home, contracts_num, True

    def open_home_page_and_get_contracts(
            self,
            s: MySession,
            dse_new_desktop_session_check_param: str) -> Tuple[MySession, Response, int]:

        # Open home page
        req_headers = self.basic_req_headers_updated(
            {
                'X-Requested-With': 'XMLHttpRequest',
                'requesttype': 'launcher',
                'Referer': self._url('/eai_desktop/GbpInternetDesktop/EstablishSession')
            }
        )

        req_url = self._url('/eai_desktop/GBP.0738_CI_CUE.BTT_Local.Cuentas/CUE9000C.transaction')
        req_params = {'dse_new_desktop_session_check': dse_new_desktop_session_check_param}

        # If one contract - the page contains contract's home page
        # If several contracts - list of contracts
        resp = s.post(
            req_url,
            data=req_params,
            headers=req_headers,
            proxies=self.req_proxies
        )

        # One contract
        if 'Seleccione el contrato con el que quiera operar' not in resp.text:
            return s, resp, 0

        # Several contracts
        resp_page_html, _, _ = self._get_page_html_from_json_resp(resp, 'login')
        contracts_num = parse_helpers.get_contracts_num(resp_page_html)
        return s, resp, contracts_num

    def select_contract(
            self,
            s: MySession,
            resp_contracts_list_page_html: str,
            contract_num: int,
            dse_new_desktop_session_check_param) -> Tuple[MySession, Response]:

        # req_url = ('https://www4.bancopopular.es/eai_desktop/'
        #            'GBP.0738_CI_CUE.BTT_Local.Cueresp_contracts_listntas/Request')

        req_url = self._url('/eai_desktop/GBP.0738_CI_CUE.BTT_Local.Cuentas/Request')
        req_params = parse_helpers.get_select_contract_req_params(
            resp_contracts_list_page_html,
            dse_new_desktop_session_check_param,
            contract_num
        )

        req_headers = self.basic_req_headers_updated(
            {
                'requesttype': 'ajax',
                'X-Requested-With': 'XMLHttpRequest',
                'x-dynaTrace': 'NA=CUE9000C;SN=CUE9000C;TE=continuar',
                'Referer': self._url('/eai_desktop/GbpInternetDesktop/EstablishSession')
            }
        )

        resp_contract_home = s.post(
            req_url,
            json=req_params,
            headers=req_headers,
            proxies=self.req_proxies
        )

        return s, resp_contract_home

    def open_accounts_list_page(self, s, dse_new_desktop_session_check_param, accounts_type=ACCOUNT_TYPE_DEBIT):
        time.sleep(0.5 + random.random())
        self.logger.info('Open_accounts_list_page: accounts_type: {}'.format(accounts_type))
        req_headers = self.basic_req_headers_updated(
            {
                'X-Requested-With': 'XMLHttpRequest',
                'requesttype': 'launcher',
                'Referer': self._url('/eai_desktop/GbpInternetDesktop/EstablishSession')
            }
        )

        req_params = {'dse_new_desktop_session_check': dse_new_desktop_session_check_param}

        req_cuentas_url = self._url(
            '/eai_desktop/GBP.0738_CI_CUE.BTT_Local.Cuentas/{}.transaction'.format(
                ACCOUNTS_REQ_PARAM[accounts_type]
            )
        )

        resp_cuentas = s.post(
            req_cuentas_url,
            data=req_params,
            headers=req_headers,
            proxies=self.req_proxies
        )

        resp_cuentas_page_html, is_success_open, is_no_accounts_sign = self._get_page_html_from_json_resp(
            resp_cuentas,
            'open_accounts_list_page: account type {}'.format(accounts_type)
        )
        has_accounts = not is_no_accounts_sign

        return s, resp_cuentas_page_html, has_accounts, is_success_open

    def login_and_open_contract_home_page_if_several_contracts(
            self,
            contract_num: int) -> Tuple[MySession, Response, str, bool]:
        self.logger.info('Process contract #{}'.format(contract_num))

        time.sleep(random.random() * 2)
        # Log in to get new session to able process contracts in parallel mode
        s, resp_logged_in, is_logged, is_credentials_error, dse_new_desktop_session_check_param, _reason = self.login()
        if not is_logged:
            self.logger.error(
                'Not logged in while contract processing. Exit. Check response:\n{}'.format(
                    resp_logged_in.text
                )
            )
            is_success = False
            return s, resp_logged_in, dse_new_desktop_session_check_param, is_success

        s, resp_contracts_list_or_contract_home, contracts_num = self.open_home_page_and_get_contracts(
            s,
            dse_new_desktop_session_check_param
        )

        if self.should_handle_additional_login_steps:
            s, resp_contracts_list_or_contract_home, contracts_num, is_processed = \
                self.handle_additional_login_steps(
                    s,
                    resp_contracts_list_or_contract_home,
                    dse_new_desktop_session_check_param
                )
            if not is_processed:
                self.logger.error(
                    "Contract #{}. CAN'T PROCESS ADDITIONAL LOGIN STEP. "
                    "PROBABLY, REAL USER ACTION REQUIRED\nRESPONSE\n{}".format(
                        contract_num,
                        re.sub(r'\\n|\\t|\\r', '',
                               extract.remove_tags(resp_contracts_list_or_contract_home.text))))
                is_success = False
                return s, resp_logged_in, dse_new_desktop_session_check_param, is_success

        # Select contract to open accounts overview page
        resp_contracts_list_page_html, is_success, _ = self._get_page_html_from_json_resp(
            resp_contracts_list_or_contract_home,
            'process_contract'
        )
        if not is_success:
            return s, resp_logged_in, dse_new_desktop_session_check_param, is_success

        s, resp_contract_home = self.select_contract(
            s,
            resp_contracts_list_page_html,
            contract_num,
            dse_new_desktop_session_check_param
        )

        return s, resp_contract_home, dse_new_desktop_session_check_param, is_success

    def process_contract(self, s, resp_contracts_list_or_contract_home, dse_new_desktop_session_check_param,
                         contract_num: int, is_several_contracts: bool):

        is_processed_wo_errors = True  # to indicate status of debit and/or credit accounts extracting

        if is_several_contracts:
            s, resp_contract_home, dse_new_desktop_session_check_param, is_success = (
                self.login_and_open_contract_home_page_if_several_contracts(
                    contract_num
                )
            )
            if not is_success:
                return False
        else:
            # Accounts overview page already opened if one contract
            resp_contract_home = resp_contracts_list_or_contract_home

        # --- Debit accounts
        # try several times
        for _ in range(3):
            s, resp_debit_cuentas_page_html, has_accounts, is_success_open = self.open_accounts_list_page(
                s,
                dse_new_desktop_session_check_param,
                ACCOUNT_TYPE_DEBIT
            )
            if is_success_open:
                break
            time.sleep(random.random() * 2)

        accounts_debit_parsed = []  # type: List[AccountParsed]
        if is_success_open:
            if has_accounts:
                accounts_debit_parsed = parse_helpers.get_accounts_parsed(
                    resp_debit_cuentas_page_html,
                    ACCOUNT_TYPE_DEBIT
                )
            else:
                self.logger.info('Contract #{} has no debit accounts'.format(contract_num))
        else:
            self.logger.error(
                'process_contract #{}: wrong resp_debit_cuentas_page_html:\n{}'.format(
                    contract_num,
                    resp_debit_cuentas_page_html
                )
            )
            is_processed_wo_errors = False

        # --- Credit accounts
        # try several times
        for _ in range(3):
            s, resp_credit_cuentas_page_html, has_accounts, is_success_open = self.open_accounts_list_page(
                s,
                dse_new_desktop_session_check_param,
                ACCOUNT_TYPE_CREDIT
            )
            if is_success_open:
                break
            time.sleep(random.random() * 2)

        accounts_credit_parsed = []  # type: List[AccountParsed]
        if is_success_open:
            if has_accounts:
                accounts_credit_parsed = parse_helpers.get_accounts_parsed(
                    resp_credit_cuentas_page_html,
                    ACCOUNT_TYPE_CREDIT
                )
            else:
                self.logger.info('Contract #{} has no credit accounts'.format(contract_num))
        else:
            self.logger.error(
                'process_contract #{}: wrong resp_credit_cuentas_page_html:\n{}'.format(
                    contract_num,
                    resp_credit_cuentas_page_html
                )
            )
            is_processed_wo_errors = False

        # Need to process debit and credit accounts separately to keep indexes
        accounts_debit_scraped = [self.basic_account_scraped_from_account_parsed(acc_parsed['organization_title'],
                                                                                 acc_parsed)
                                  for acc_parsed in accounts_debit_parsed]

        accounts_credit_scraped = [self.basic_account_scraped_from_account_parsed(acc_parsed['organization_title'],
                                                                                  acc_parsed)
                                   for acc_parsed in accounts_credit_parsed]

        accounts_scraped = accounts_debit_scraped + accounts_credit_scraped

        organization_title = accounts_scraped[0].OrganizationName if accounts_scraped else ''
        self.logger.info(
            'Contract #{} has {} accounts: {}'.format(contract_num, len(accounts_scraped), accounts_scraped)
        )
        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        # Get and save movements (open each account in serial mode)
        for idx, account_debit_scraped in enumerate(accounts_debit_scraped):
            self.process_account(s, account_debit_scraped, dse_new_desktop_session_check_param, idx)

        for idx, account_credit_scraped in enumerate(accounts_credit_scraped):
            self.process_account(s, account_credit_scraped, dse_new_desktop_session_check_param, idx)

        return is_processed_wo_errors

    def process_account(self, s, account_scraped: AccountScraped,
                        dse_new_desktop_session_check_param, account_idx) -> bool:

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        date_from_calculated = date_funcs.get_date_from_str(self.basic_get_date_from(fin_ent_account_id))
        # respect max allowed range
        date_from = max(date_from_calculated, self.date_to - datetime.timedelta(days=MAX_MOVEMENTS_DATES_RANGE))
        date_from_str = date_from.strftime(project_settings.SCRAPER_DATE_FMT)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        # Need to reopen accounts_list_page
        s, resp_cuentas_page_html, has_accounts, is_success_open = self.open_accounts_list_page(
            s,
            dse_new_desktop_session_check_param,
            account_scraped.Type
        )

        if not has_accounts or not is_success_open:
            self.logger.error(
                'process_account: wrong resp_cuentas_page_html:\n{}. Exit'.format(resp_cuentas_page_html))
            self.basic_set_movements_scraping_finished(fin_ent_account_id)
            return False

        # Open recent movements page
        req_mov_url = self._url('/eai_desktop/GBP.0738_CI_CUE.BTT_Local.Cuentas/Request')
        if account_scraped.Type == ACCOUNT_TYPE_DEBIT:
            req_mov_params = parse_helpers.get_mov_page_req_params(
                resp_cuentas_page_html,
                dse_new_desktop_session_check_param,
                account_idx
            )
        else:
            req_mov_params = parse_helpers.get_credit_acc_mov_page_req_params(
                resp_cuentas_page_html,
                dse_new_desktop_session_check_param,
                account_idx
            )

        req_mov_headers = self.basic_req_headers_updated(
            {
                'requesttype': 'ajax',
                'X-Requested-With': 'XMLHttpRequest',
                'x-dynaTrace': 'NA={};SN={};TE={}'.format(
                    req_mov_params['dse_operationName'],
                    req_mov_params['dse_operationName'],
                    req_mov_params['dse_nextEventName']
                ),
                'Referer': self._url('/eai_desktop/GbpInternetDesktop/EstablishSession')
            }
        )
        resp_mov = s.post(
            req_mov_url,
            json=req_mov_params,
            headers=req_mov_headers,
            proxies=self.req_proxies
        )

        # Filter by dates
        resp_mov_page_html, is_success, _ = self._get_page_html_from_json_resp(resp_mov, 'process_account')
        if not is_success:
            self.logger.error('process_account: {}: wrong response:\n{}'.format(fin_ent_account_id, resp_mov.text))
            self.basic_set_movements_scraping_finished(fin_ent_account_id)
            return False

        req_mov_filtered_headers = self.basic_req_headers_updated(
            {
                'requesttype': 'ajax',
                'X-Requested-With': 'XMLHttpRequest',
                'x-dynaTrace': 'NA=CUE0014C;SN=CUE0014C;TE=buscar',
                'Referer': self._url('/eai_desktop/GbpInternetDesktop/EstablishSession')
            }
        )

        req_mov_filter_params_unciphered = parse_helpers.get_mov_filter_params(
            resp_mov_page_html,
            date_from_str,
            self.date_to_str,
            dse_new_desktop_session_check_param
        )

        req_mov_filter_params = self._get_ciphered(req_mov_filter_params_unciphered)  # type: dict
        req_mov_filter_params.pop('dse_form_cipher')
        req_mov_filter_params.pop('dse_webURL')

        # It is necessary to prepare backend for the next correct response
        resp_mov_filtered = s.post(
            req_mov_url,
            json=req_mov_filter_params,
            headers=req_mov_filtered_headers,
            proxies=self.req_proxies
        )

        req_ajax_params = OrderedDict([
            ("dse_pageId", "-1"),
            ("dse_sessionId", req_mov_filter_params['dse_sessionId']),
            ("dse_operationName", "PAG_MisCuentas$CUE0014C_Busq_MisCuentas_RelMov_tablaRes6"),
            ("dse_processorId", req_mov_filter_params['dse_processorId']),
            ("tableProperties.tableId", "CUE0014C_Busq_MisCuentas_RelMov_tablaRes6"),
            ("dse_timezone", req_mov_filter_params['dse_timezone']),
            ("pageRequest.pageEvent", "initial"),
            ("mode", "nonePageSize"),
            ("dse_new_desktop_session_check", req_mov_filter_params['dse_new_desktop_session_check'])
        ])

        movements_parsed_desc_all = []  # type: List[MovementParsed]
        while True:
            resp_ajax = s.post(
                self._url('/eai_desktop/GBP.0738_CI_CUE.BTT_Local.Cuentas/Ajax'),
                json=req_ajax_params,
                headers=req_mov_filtered_headers,
                proxies=self.req_proxies
            )

            try:
                resp_json = resp_ajax.json()
            except Exception as exc:
                self.logger.error(
                    "{}: dates from {} to {}: can't parse JSON from response. "
                    "Skip movements uploading.\nEXC:{}\n\nRESPONSE:\n{}".format(
                        fin_ent_account_id,
                        date_from_str,
                        self.date_to_str,
                        exc,
                        resp_json.text
                    ))
                self.basic_set_movements_scraping_finished(fin_ent_account_id)
                return False

            movements_parsed_from_json = parse_helpers.get_movements_parsed(resp_json)

            # When iterate over pages,
            # you will receive first page again after last page.
            # It is possible when last page contains exact 20 movs.
            # In this case to avoid duplicates of the pages, we check that the whole page already was scraped
            if all(mov in movements_parsed_desc_all for mov in movements_parsed_from_json):
                break

            movements_parsed_desc_all.extend(movements_parsed_from_json)

            if len(movements_parsed_from_json) < 20:
                break

            # set this after first loop iteration to iterate over pages
            req_ajax_params["pageRequest.pageEvent"] = "next"

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_desc_all,
            date_from_str
        )
        self.basic_log_process_account(account_scraped.AccountNo, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        return True

    def main(self):

        # Log in once to check is correct password
        s, resp_logged_in, is_logged, is_credentials_error, dse_new_desktop_session_check_param, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp_logged_in.url, resp_logged_in.text, reason)

        s, resp_contracts_list_or_contract_home, contracts_num = self.open_home_page_and_get_contracts(
            s,
            dse_new_desktop_session_check_param
        )

        if '"page_name":"LoginConfig"' in resp_contracts_list_or_contract_home.text:
            self.should_handle_additional_login_steps = True

            s, resp_contracts_list_or_contract_home, contracts_num, is_processed = \
                self.handle_additional_login_steps(
                    s,
                    resp_contracts_list_or_contract_home,
                    dse_new_desktop_session_check_param
                )
            if not is_processed:
                return self.basic_result_not_logged_in_due_unknown_reason(
                    resp_contracts_list_or_contract_home.url,
                    re.sub(r'\\n|\\t|\\r', '', extract.remove_tags(resp_contracts_list_or_contract_home.text))
                    + "\n\n== CAN'T PROCESS ADDITIONAL LOGIN STEP. PROBABLY, REAL USER ACTION REQUIRED =="
                )

        if not contracts_num:
            # One contract
            self.logger.info('Found one contract')
            self.process_contract(
                s,
                resp_contracts_list_or_contract_home,
                dse_new_desktop_session_check_param,
                0,
                False
            )
        else:
            # Several contracts
            self.logger.info('Found several contracts: {}'.format(contracts_num))
            if project_settings.IS_CONCURRENT_SCRAPING:
                # process each contract
                # with different logged in response (not session, but response with auth params)
                self.logger.info('Run concurrent contract processings')

                with futures.ThreadPoolExecutor(contracts_num) as executor:
                    futures_dict = {
                        executor.submit(self.process_contract,
                                        s,
                                        resp_contracts_list_or_contract_home,
                                        dse_new_desktop_session_check_param,
                                        idx,
                                        True): idx
                        for idx, contract in enumerate(range(contracts_num))
                    }
                    self.logger.log_futures_exc('process_contract', futures_dict)
            else:
                self.logger.info('Run serial contract processing from different sessions')
                for idx, contract in enumerate(range(contracts_num)):
                    self.process_contract(
                        s,
                        resp_contracts_list_or_contract_home,
                        dse_new_desktop_session_check_param,
                        idx,
                        True
                    )

        self.basic_log_time_spent('GET ALL BALANCES AND MOVEMENTS')
        return self.basic_result_success()
