import datetime
import random
import time
from concurrent import futures
from typing import Dict, List, Optional, Tuple

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    AccountParsed, AccountScraped, MOVEMENTS_ORDERING_TYPE_ASC, MovementParsed,
    ScraperParamsCommon, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_COMMON
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.bankinter_scraper import login_helper
from scrapers.bankinter_scraper import parse_helpers
from scrapers.bankinter_scraper.custom_types import Company

__version__ = '9.45.0'

__changelog__ = """
9.45.0 2023.06.23
process_company: refactored accounts_scraped_all
9.44.0
process_account, process_account_multicurrency:
    check if download link params should be parsed
9.43.0
upd LOGGED_IN_MARKERS
9.42.0
process_account_multicurrency: 
  upd logic for date_from_minimal 
  (max of date_from for all sub-accounts without other modifications)
9.41.0
use account-level result_codes
9.40.0
call basic_upload_movements_scraped with date_from_str
9.39.0
login: handle 'wrong credentials' case: silent redirection to /secure
9.38.0
upd DOUBLE_AUTH_MARKERS
removed old changelog
9.37.1
upd log msg
9.37.0
get_accounts_scraped (for children)
9.36.0
_open_company_page: added switch to transfers if needed
_open_transfers_company_page
9.35.0
use parse_helpers.has_cuentas_table for better 'no accounts' detection
9.34.0
renamed methods: 
  process_contract -> process_company
  process_user_account -> get_companies
9.33.2
parse_helpers: fixed typing
9.33.1
NO_ACCOUNTS_MARKER
9.33.0
process_contract: log wrong layout if there are no accounts
9.32.1
upd log msg: aligned "can't log in"
9.32.0
SERVICE_UNAVAILABLE_MARKER
9.31.0
MAX_CONCURRENT_WORKERS = 4 (8 brought auth failures - detected for many accs of -a 22475)
9.30.0
renamed to download_correspondence()
9.29.0
login: more double auth markers, set is_logged = False when 2fa detected
9.28.0
skip inactive accounts
9.27.0
download_company_documents
9.26.0
parse_helpers: get_movements_parsed_from_html_resp_multicurrency:
  handle complementary sub-accounts
9.25.1
more double auth markers
9.25.0
parse_helpers: get_accounts_parsed: upd for the new layout
9.24.0
use MAX_OFFSET for movements
9.23.1
aligned double auth msg
9.23.0
use basic_new_session
upd type hints
custom type Company
9.22.0
unsupported access type detection (only Empresas is implemented)
disabled credentials == wrong credentials detector - enabled again
  (was disabled since 9.17.0)
login_helpers: more strict check by the length of encoder_js_script_str 
9.21.0
login: 2fa detector, n_credentials_errors
login_helper: longer delays if failed
9.20.0
basic_get_date_from: call with max_autoincreasing_offset for better balance integrity fixes 
9.19.0
disabled is_credentials_error (always False)
9.18.1
removed dev-only try/except
9.18.0
process_account_multicurrency: min date_from restriction
  (look at the comment with the reason in the func)
9.17.0
login_helper: check for non-blank login_req_token 
 to avoid false positive credentials errors  
9.16.0
don't use _reorder_today_movements: not confirmed (ES0601289408970500004232)
9.15.0
removed unused _extract_resp_excel_w_movements
process_account, process_account_multicurrency: 
  download_receipts only after successful upload_movements_scraped
parse_helpers: _reorder_today_movements
"""

MAX_AUTOINCREASING_OFFSET_DAYS = 90
MAX_OFFSET = 90
MAX_ALLOWED_MOVEMENTS_PER_PAGE = 135
MAX_CONCURRENT_WORKERS = 4

CREDENTIALS_ERROR_MARKERS = [
    # commented since 9.13.0 in attempt to avoid false-positive detections,
    # restored since 9.22.0 - this is not the reason
    # 'Como medida de seguridad, ...
    'sus claves de conexión han sido desactivadas',
    'Usuario o contraseña incorrectos',
]

DOUBLE_AUTH_MARKERS = [
    'Por motivos de seguridad, es necesario que introduzca una coordenada para completar la conexión',
    'Por motivos de seguridad, para completar la conexión le vamos a enviar un código por sms',
    'Según normativa PSD2 vigente, <b>es obligatorio</b> tener activo un <b>segundo factor de firma de seguridad</b>; para recibir la clave OTP (One Time Password) <b>necesitamos que nos informe su preferencia de firma.',
    # 'será necesario un código enviado por SMS al teléfono'
    'introduzca la clave de 6 dígitos que le hemos enviado a su correo electrónico y pulse',
]

LOGGED_IN_MARKERS = [
    '/www/es-es/cgi/empresas+logout',
    '/www/es-es/cgi/empresas+cuentas+integral',
    'Información personal',
]

SERVICE_UNAVAILABLE_MARKER = 'Servicio temporalmente no disponible'

NO_ACCOUNTS_MARKER = 'NO TIENE CUENTAS'


class BankinterScraper(BasicScraper):
    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BankinterScraper') -> None:

        self.scraper_name = scraper_name
        super().__init__(scraper_params_common, proxies)
        self.update_inactive_accounts = False

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        if self.access_type != "Empresas":
            return (self.basic_new_session(), Response(), False, False,
                    'Unsupported access type "{}"'.format(self.access_type))

        # Due to previous false-positive 'wrong credentials' detections
        # we'll be trying to login at least `n_login_attempts`
        # to be sure that getting an 'credentials error' on each attempt
        n_login_attempts = 2
        n_credentials_errors = 0

        # Suppress linter warnings
        session = self.basic_new_session()
        resp_logged_in = Response()
        is_logged = False
        reason = ''

        for i in range(n_login_attempts):
            if i > 0:
                time.sleep(5 + random.random())
            session, resp_logged_in = login_helper.login(self.logger, self.username, self.userpass, self.req_proxies)
            is_logged = any(m in resp_logged_in.text for m in LOGGED_IN_MARKERS)
            if is_logged:
                break
            is_credentials_error = (
                    any(m in resp_logged_in.text for m in CREDENTIALS_ERROR_MARKERS)
                    # Silent redirection to the new login page - means wrong creds
                    # while an attempt to login from the new page would display 'Credenciales invalidas'
                    or ('location.href="/secure"' in resp_logged_in.text
                        and 'empresas.bankinter.com/www/es-es/cgi/empresas+login' in resp_logged_in.url)
            )
            if not is_credentials_error:
                break
            # Increase the counter, don't return is_credentials_error immediately
            n_credentials_errors += 1

        if any(m in resp_logged_in.text for m in DOUBLE_AUTH_MARKERS):
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON
            is_logged = False

        if CREDENTIALS_ERROR_MARKERS[0] in resp_logged_in.text:
            self.logger.info('DISABLED CREDENTIALS DETECTED')

        if not is_logged and SERVICE_UNAVAILABLE_MARKER in resp_logged_in.text:
            reason = 'Service is temporarily unavailable. Try later'

        return session, resp_logged_in, is_logged, n_credentials_errors == n_login_attempts, reason

    def _open_company_page(
            self,
            s: MySession,
            company: Company,
            fin_ent_account_id='') -> Tuple[bool, MySession, Response]:
        """:return (is_success, session, resp_company)"""
        resp_company = s.get(company.url,
                             headers=self.req_headers,
                             proxies=self.req_proxies)

        if resp_company.status_code != 200:
            if fin_ent_account_id:
                msg = 'Error opening company {} while processing account {}'.format(
                    company,
                    fin_ent_account_id
                )
            else:
                msg = 'Error opening company {}'.format(company)
            self.logger.error(msg)
            return False, s, resp_company

        # switch to position global explicitly to avoid pos multiempresa
        req_pos_global_url = 'https://empresas.bankinter.com/www/es-es/cgi/empresas+cuentas+integral'
        if 'transferencias' in company.url:
            req_pos_global_url = 'https://empresas.bankinter.com/www/es-es/cgi/empresas+pagos+transferencias_recibidas'

        req_pos_global_params = {
            'CUENTA': '',
            'cuenta_seleccionada': '',
            'ind_extracto': '2',
            'cambio_tipo_posicion': 'S'
        }
        resp_pos_global = s.post(
            req_pos_global_url,
            data=req_pos_global_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if resp_pos_global.status_code != 200:
            if fin_ent_account_id:
                msg = 'Error switch to position global for {} while processing account {}'.format(
                    company,
                    fin_ent_account_id
                )
            else:
                msg = 'Error switch to position global for {}'.format(company)
            self.logger.error(msg)
            return False, s, resp_company

        return True, s, resp_pos_global

    def _login_and_open_company_page(
            self,
            company: Company,
            fin_ent_account_id='') -> Tuple[bool, MySession, Response]:
        """Open to get accounts or(and) even to process account
        :return (is_success, session, response_company)
        """

        if fin_ent_account_id:
            self.logger.info('Log in: company {} account {}'.format(
                company.title,
                fin_ent_account_id
            ))
        else:
            self.logger.info('Log in: company {}'.format(company.title))

        s, resp_logged_in, is_logged, is_credentials_error, _reason = self.login()

        if not is_logged:
            msg_note = ('\n(NOTE: this is not real credentials error because was logged in initially)\n'
                        if is_credentials_error
                        else '')
            msg_prefix = '{}: '.format(fin_ent_account_id) if fin_ent_account_id else ''

            self.logger.error(
                "{}: can't log in for contract/company processing: {}. Skip."
                '{}'
                '\nRESPONSE TEXT:\n{}'.format(
                    msg_prefix,
                    company,
                    msg_note,
                    extract.text_wo_scripts_and_tags(resp_logged_in.text)
                )
            )

            return False, s, resp_logged_in

        ok, s, resp_company = self._open_company_page(s, company, fin_ent_account_id)

        return ok, s, resp_company

    def get_companies(self, s: MySession, resp_logged_in: Response) -> List[Company]:

        self.logger.info('Get companies')

        url_position_global = 'https://empresas.bankinter.com/www/es-es/cgi/empresas+cuentas+integral'
        if resp_logged_in.url != url_position_global:
            resp_logged_in = s.get(url_position_global, headers=self.req_headers, proxies=self.req_proxies)

        companies = parse_helpers.get_companies_parsed(resp_logged_in.text, resp_logged_in.url)
        return companies

    def _get_fin_ent_account_id_parent(self, account_parsed_multicurrency_dict: dict) -> str:
        """For multi-currency accounts. Extracts data from any first account"""
        fid = list(account_parsed_multicurrency_dict.values())[0]['fin_ent_account_id_parent']
        return fid

    def get_accounts_scraped(
            self,
            resp_company: Response,
            company: Company) -> List[AccountScraped]:
        """:returns accounts_scraped + subaccounts_multicurrency_scraped"""
        # Get one-currency accounts
        accounts_parsed = parse_helpers.get_accounts_parsed(resp_company.text)
        accounts_scraped = [self.basic_account_scraped_from_account_parsed(company.title, acc_parsed)
                            for acc_parsed in accounts_parsed]

        # Get multi-currency accounts
        # Each subaccount_parsed_for_specific_currency contains fin_ent_account_id_parent (w/o currency)
        # [{parent_2_subaccounts_parsed_for_each_currency}, {parent_2_subaccounts_parsed_for_each_currency}, ...]
        accounts_multicurrency_parsed = parse_helpers.get_accounts_multicurrency_parsed(
            resp_company.text
        )  # type: List[Dict[str, AccountParsed]]

        # Flat list, just for uploading, not for movements extraction
        subaccounts_multicurrency_scraped = [
            self.basic_account_scraped_from_account_parsed(company.title, subaccounts_parsed)
            for account_parsed_multicurrency in accounts_multicurrency_parsed
            for subaccounts_parsed in account_parsed_multicurrency.values()
        ]  # type: List[AccountScraped]

        accounts_scraped_all = accounts_scraped + subaccounts_multicurrency_scraped
        if not accounts_scraped_all:
            self.logger.warning('{}: suspicious results: no accounts_scraped_all. RESPONSE:\n{}\n{}'.format(
                company.title,
                resp_company.url,
                resp_company.text
            ))
        return accounts_scraped_all

    def process_company(self, s: MySession, company: Company, is_need_new_session: bool) -> bool:
        """
        get accounts and upload them
        then for each account run 'process account' to get movements
        """

        self.logger.info('Process company: {}'.format(company))

        if is_need_new_session:
            ok, s, resp_company = self._login_and_open_company_page(company)
        else:
            ok, s, resp_company = self._open_company_page(s, company)

        if not ok:
            # already logged
            return False

        # Get one-currency accounts
        accounts_parsed = parse_helpers.get_accounts_parsed(resp_company.text)
        accounts_scraped = [self.basic_account_scraped_from_account_parsed(company.title, acc_parsed)
                            for acc_parsed in accounts_parsed]

        # Get multi-currency accounts
        # Each subaccount_parsed_for_specific_currency contains fin_ent_account_id_parent (w/o currency)
        # [{parent_2_subaccounts_parsed_for_each_currency}, {parent_2_subaccounts_parsed_for_each_currency}, ...]
        accounts_multicurrency_parsed = parse_helpers.get_accounts_multicurrency_parsed(
            resp_company.text
        )  # type: List[Dict[str, AccountParsed]]

        # Flat list, just for uploading, not for movements extraction
        subaccounts_multicurrency_scraped = [
            self.basic_account_scraped_from_account_parsed(company.title, subaccounts_parsed)
            for account_parsed_multicurrency in accounts_multicurrency_parsed
            for subaccounts_parsed in account_parsed_multicurrency.values()
        ]  # type: List[AccountScraped]

        accounts_scraped_all = accounts_scraped + subaccounts_multicurrency_scraped

        is_need_new_session_for_each_account_processing = len(accounts_scraped_all) > 1

        # -a 28139
        # TELECOMUNICACION E INSTALACION -- NO_ACCOUNTS_MARKER
        # LANDATA COMMUNICACIONES DE EMPR -- no 'Cuentas' table
        if not accounts_scraped_all:
            if NO_ACCOUNTS_MARKER in resp_company.text or \
                    not parse_helpers.has_cuentas_table(resp_company.text):
                self.logger.info("{}: 'no accounts' marker detected".format(company.title))
            else:
                self.basic_log_wrong_layout(
                    resp_company,
                    '{}: suspicious results: no accounts found'.format(company.title)
                )

        self.logger.info('{} has {} accounts: {}'.format(
            company.title,
            len(accounts_scraped_all),
            accounts_scraped_all,
        ))

        self.basic_upload_accounts_scraped(accounts_scraped_all)
        self.basic_log_time_spent('GET BALANCES')

        # Should use individual session for each account to get movements

        # Process one-currency accounts
        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:

                futures_dict = {
                    executor.submit(
                        self.process_account,
                        s,
                        resp_company,
                        company,
                        account_scraped,
                        is_need_new_session_for_each_account_processing
                    ): account_scraped.FinancialEntityAccountId
                    for account_scraped in accounts_scraped
                }

                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_scraped in accounts_scraped:
                self.process_account(
                    s,
                    resp_company,
                    company,
                    account_scraped,
                    is_need_new_session_for_each_account_processing
                )

        # Process multi-currency accounts
        subaccounts_multicurrency_scraped_dict = self.basic_gen_accounts_scraped_dict(
            subaccounts_multicurrency_scraped
        )

        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:

                futures_dict = {
                    executor.submit(
                        self.process_account_multicurrency,
                        s,
                        resp_company,
                        company,
                        account_parsed_multicurrency_dict,
                        subaccounts_multicurrency_scraped_dict,
                        is_need_new_session_for_each_account_processing
                    ): self._get_fin_ent_account_id_parent(account_parsed_multicurrency_dict)
                    for account_parsed_multicurrency_dict in accounts_multicurrency_parsed
                    if account_parsed_multicurrency_dict
                }

                self.logger.log_futures_exc('process_account_multicurrency', futures_dict)
        else:
            for account_parsed_multicurrency_dict in accounts_multicurrency_parsed:
                self.process_account_multicurrency(
                    s,
                    resp_company,
                    company,
                    account_parsed_multicurrency_dict,
                    subaccounts_multicurrency_scraped_dict,
                    is_need_new_session_for_each_account_processing
                )

        self.download_correspondence(s, company.title)
        return True

    def _extract_resp_html_w_movements(
            self,
            s: MySession,
            resp_company: Response,
            company: Company,
            fin_ent_account_id: str,
            is_need_new_session: bool,
            date_from_str='') -> Tuple[Optional[str], str]:
        """:returns: (joined html texts of pages with movements, date_from_str)"""

        if is_need_new_session:
            ok, s, resp_company = self._login_and_open_company_page(company, fin_ent_account_id)
            if not ok:
                return None, ''

        if not date_from_str:
            date_from_str = self.basic_get_date_from(
                fin_ent_account_id,
                max_autoincreasing_offset=MAX_AUTOINCREASING_OFFSET_DAYS,
                max_offset=MAX_OFFSET
            )

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        day_from, month_from, year_from = date_from_str.split('/')
        day_to, month_to, year_to = self.date_to_str.split('/')

        req_params = {
            'CUENTA': fin_ent_account_id,
            'YG0400E-DD-EMISION': day_from,
            'YG0400E-MM-EMISION': month_from,
            'YG0400E-SS-EMISION': year_from[:2],
            'YG0400E-AA-EMISION': year_from[2:],
            'YG0400E-DD-EMISION-H': day_to,
            'YG0400E-MM-EMISION-H': month_to,
            'YG0400E-SS-EMISION-H': year_to[:2],
            'YG0400E-AA-EMISION-H': year_to[2:],
            'YG0400E-TIPO-CONSULTA': 'D',  # or 'H'
            'YG0400E-DIVISA': '',
            'YG0400E-MODALIDAD': 'T',
            'tramoCons': '',  # Todos los tramos
            'YG0400E-TIPO-MVTO': 'A',
            'YG0400E-IMPT-DESDE': '',
            'YG0400E-IMPT-HASTA': '',
            'YG0400E-CONCEPTO': '',
            'detalle': 'N',
            'tip_mov': ''
        }

        req_url = 'https://empresas.bankinter.com/www/es-es/cgi/empresas+cuentas+credito_movimientos2'

        has_next_movements = True
        resp_text = ""

        page_ix = 0
        while has_next_movements:
            time.sleep(0.1)
            page_ix += 1

            self.logger.info('{}: open page {} with movements'.format(
                fin_ent_account_id,
                page_ix
            ))

            resp_movs_i = Response()  # suppress linter warnings
            for _ in range(3):
                resp_movs_i = s.post(
                    req_url,
                    data=req_params,
                    headers=self.req_headers,
                    proxies=self.req_proxies,
                    timeout=30,
                )

                if resp_movs_i.status_code == 200:
                    break
            else:
                msg = "{}: dates from {} to {} : error: can't get html with movements\nResponse:\n{}".format(
                    fin_ent_account_id,
                    date_from_str,
                    self.date_to_str,
                    resp_movs_i.text
                )
                self.logger.error(msg)
                # DAF: if fails once we return None :-> So we are prefering None
                # than an incomplete list of movements
                return None, date_from_str

            resp_text += "\r\n" + resp_movs_i.text

            has_next_movements = '<button type="submit">Siguiente</button>' in resp_movs_i.text
            if has_next_movements:
                # req_params['tramoCons'] = "Todos los tramos"
                form_sg_val = extract.re_last_or_blank(
                    '(?si)<input name="form-sg" type="hidden" value="([^"]*)"',
                    resp_movs_i.text
                )
                if form_sg_val:
                    req_params['form-sg'] = form_sg_val
                req_params['ROW'] = "NEXT"

        return resp_text, date_from_str

    def process_account(self,
                        s: MySession,
                        resp_company: Response,
                        company: Company,
                        account_scraped: AccountScraped,
                        is_need_new_session: bool) -> bool:
        """
        Log in again to process each account in different session
        get movements and upload them (if is_need_new_session = True)
        If one account of company, then is_need_new_session = False
        """

        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        self.logger.info('Process_account: {}'.format(fin_ent_account_id))

        resp_movs_text, date_from_str = self._extract_resp_html_w_movements(
            s,
            resp_company,
            company,
            fin_ent_account_id,
            is_need_new_session
        )

        if not resp_movs_text:
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
            return False

        movements_parsed = parse_helpers.get_movements_parsed_from_html_resp(
            resp_movs_text,
            self.basic_should_download_receipts(account_scraped)
        )

        movements_scraped, movements_parsed_filtered = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        ok = self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        if ok:
            self.download_receipts(
                s,
                account_scraped,
                movements_scraped,
                movements_parsed_filtered
            )

        return True

    def process_account_multicurrency(
            self,
            s: MySession,
            resp_company: Response,
            company: Company,
            account_parsed_multicurrency_dict: Dict[str, AccountParsed],
            subaccounts_multicurrency_scraped_dict: Dict[str, AccountScraped],
            is_need_new_session: bool) -> bool:

        if not account_parsed_multicurrency_dict:
            return True

        # Get fin_ent_account_id_parent from any parsed subaccount
        fin_ent_account_id_parent = self._get_fin_ent_account_id_parent(account_parsed_multicurrency_dict)
        self.logger.info('Process multi-currency account: {}'.format(fin_ent_account_id_parent))

        # Skip multi-currency account only if all sub-accounts marked as 'inactive'
        is_active = any(self.basic_check_account_is_active(acc['financial_entity_account_id'])
                        for acc in account_parsed_multicurrency_dict.values())
        if not is_active:
            return True
        self.logger.info('Active sub-accounts detected: process all of {}'.format(
            account_parsed_multicurrency_dict
        ))

        # Get date_from as the latest (max) date_from of sub-accounts
        # (the scraper extracts movements of all sub-accounts by one request).
        # Why max? Because it means that we already launched the scraper at that day
        # and can go on with incremental scraping since that day (with offset)
        date_from_minimal = date_funcs.offset_dt(MAX_OFFSET)
        include_link_data_dict = {}
        for acc_parsed in account_parsed_multicurrency_dict.values():
            date_from, _ = self.basic_get_date_from_dt(
                acc_parsed['financial_entity_account_id'],
                max_autoincreasing_offset=MAX_AUTOINCREASING_OFFSET_DAYS
            )
            # Get the latest date_from of all sub-accounts
            date_from_minimal = max(date_from, date_from_minimal)

            # Get account scraped information to parse download link params
            subaccount_scraped_multicurrency = subaccounts_multicurrency_scraped_dict[
                acc_parsed['financial_entity_account_id']]
            include_link_data = self.basic_should_download_receipts(subaccount_scraped_multicurrency)
            include_link_data_dict[subaccount_scraped_multicurrency.Currency] = include_link_data


        date_from_minimal_str = date_funcs.convert_dt_to_scraper_date_type1(date_from_minimal)

        resp_text, date_from_str = self._extract_resp_html_w_movements(
            s,
            resp_company,
            company,
            fin_ent_account_id_parent,
            is_need_new_session,
            date_from_minimal_str
        )

        if not resp_text:
            self.basic_set_movements_scraping_finished(fin_ent_account_id_parent, result_codes.ERR_UNEXPECTED_RESPONSE)
            return False

        # dict with currency code as key and list of movements as val
        movements_parsed_multicurrency = parse_helpers.get_movements_parsed_from_html_resp_multicurrency(
            resp_text,
            fin_ent_account_id_parent,
            self.logger,
            include_link_data_dict,
        )  # type: Dict[str, List[MovementParsed]]

        for currency, movements_parsed in movements_parsed_multicurrency.items():

            movements_scraped, movements_parsed_filtered = self.basic_movements_scraped_from_movements_parsed(
                movements_parsed,
                date_from_str,
                current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
            )

            subaccount_scraped = subaccounts_multicurrency_scraped_dict[
                account_parsed_multicurrency_dict[currency]['financial_entity_account_id']
            ]  # type: AccountScraped

            self.basic_log_process_account(subaccount_scraped.FinancialEntityAccountId,
                                           date_from_str, movements_scraped)

            ok = self.basic_upload_movements_scraped(
                subaccount_scraped,
                movements_scraped,
                date_from_str=date_from_str
            )

            if ok:
                self.download_receipts(
                    s,
                    subaccount_scraped,
                    movements_scraped,
                    movements_parsed_filtered
                )

        return True

    def main(self) -> MainResult:

        session, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        companies = self.get_companies(session, resp_logged_in)
        self.logger.info('Got companies (contracts): {}'.format(companies))

        # need to open each company from unique session to avoid collisions
        is_need_new_session_for_each_company_processing = len(companies) > 1

        # can process companies (get accounts_scraped) using one session
        if project_settings.IS_CONCURRENT_SCRAPING and companies:
            with futures.ThreadPoolExecutor(MAX_CONCURRENT_WORKERS) as executor:
                futures_dict = {
                    executor.submit(self.process_company,
                                    session, company,
                                    is_need_new_session_for_each_company_processing): company.title
                    for company in companies
                }
                self.logger.log_futures_exc('process_company', futures_dict)
        else:
            for company in companies:
                self.process_company(session, company, is_need_new_session_for_each_company_processing)

        self.basic_log_time_spent('GET ALL BALANCES AND MOVEMENTS')
        return self.basic_result_success()
