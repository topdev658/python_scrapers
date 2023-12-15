import datetime
import random
import threading
import time
import urllib.parse
from concurrent import futures
from typing import Dict, Tuple

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (AccountScraped, MOVEMENTS_ORDERING_TYPE_ASC,
                                  ScraperParamsCommon, MainResult)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from .laboral_kutxa_scraper import LaboralKutxaScraper

__version__ = '7.0.0'

__changelog__ = """
7.0.0
renamed from laboral_kutxa_scraper.py scraper deprecated not used any more by any access
6.16.0
use account-level result_codes
6.15.0
'success' flag for basic_set_movements_scraping_finished when it is necessary
6.14.0
call basic_upload_movements_scraped with date_from_str
6.13.2
parse_helpers: get_movements_parsed_from_excel: upd log msg, wrn -> info
6.13.1
custom_types: fixed typing
6.13.0
integrated LaboralKutxaNewWebScraper
6.12.0
process_company_one_of_one: check for wrong layout
renamed some vars
6.11.0
renamed to download_correspondence()
6.10.0
skip inactive accounts
6.9.0
download_company_documents
6.8.0
support for foreign currency accounts (USD)
6.7.0
use basic_new_session
upd type hints
fmt
6.6.0
open_one_acc_movements_excel_and_upload:
  timeout=60 for excel req w/ movs to retrieve many movements (-u 239163 -a 11806)
  fixed req params (removed redundant commas)
  use build_req_params_from_form_html_patched
  use basic_get_date_from
more type hints
use myrequests instead of requests pseudo
process_company_one_of_many:
  req_params.get('Id') instead of exception handling
parse_helpers: renamed func params
parse_helpers: parse_movements_from_resp_excel: more informative err report
6.5.0
scrape accounts with marker 'libreta'
6.4.0
scrape accounts with marker 'crédito de pago aplazado'
added logs when skip account
6.3.0
basic_movements_scraped_from_movements_parsed: new format of the result 
6.2.0
parse_helpers: parse_movements_from_resp_excel: re-calculate temp_balances of the movements since the last movement 
    if saldo initial == 0, because most probably it is wrong saldo initial in the response
6.1.0
parse_helpers: added CUENTA INEXISTENTE handler
6.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
5.0.0
basic_movements_scraped_from_movements_parsed
OperationalDatePosition, KeyValue support
4.3.0
basic_upload_movements_scraped
4.2.0
get_companies_tuples
process_company_one_of_many: several attempts to log in and open list of companies
process max 4 company (contract) in parallel mode to avoid cancelling of sessions
4.1.1
delete test list of comp ids
4.1.0
parse_helpers: for credit acc extract company title from alt section below
4.0.0
extract credit accounts too
"""

lock = threading.Lock()

# Error del Servicio (Cod. 65059) - website down
# Error del Servicio (Cod. 5) - the company is turned off by the customed
RESP_ERR_SIGNS = [
    'Error del Servicio (Cod. 65059)',
    'No hay conexiones disponibles con el host',
]
IS_COMPANY_TURNED_OFF_SIGN = 'Error del Servicio (Cod. 5)'

WRONG_CREDENTIALS_MARKERS = [
    'meta name="CodError" content="50002"',  # wrong username
    'meta name="CodError" content="50014"',  # wrong password
]


class LaboralKutxaScraper(BasicScraper):
    """need to use Referer in req_headers"""

    scraper_name = 'LaboralKutxaScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.__scraper_params = scraper_params_common  # memo to invoke LaboralKutxaNewWebScraper
        self.__proxies = proxies
        # will be used to pass account details to mov extraction funcs in parallel mode
        self.accounts = {}  # type: Dict[str, AccountScraped]
        self.update_inactive_accounts = False

    def _update_self_accounts(self, cuenta_param: str, account_scraped: AccountScraped) -> None:
        with lock:
            self.accounts[cuenta_param] = account_scraped

    def login(self) -> Tuple[MySession, Response, bool, bool]:

        s = self.basic_new_session()

        req_url = 'https://lknet.laboralkutxa.com/logon/checklogin.asp'
        req_params = {
            'usuario': self.username,
            'password': self.userpass
        }

        resp = self.basic_req_post(
            s,
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            logger_info='login',
            err_signs=RESP_ERR_SIGNS
        )

        is_logged = '/nuevoacceso/' in resp.text

        is_credentials_error = any(m in resp.text for m in WRONG_CREDENTIALS_MARKERS)

        return s, resp, is_logged, is_credentials_error

    def open_user_companies_page(
            self,
            s: MySession,
            resp_logged_in: Response) -> Tuple[MySession, Response]:

        req_link = extract.re_first_or_blank(
            '<frame src="(/nuevoacceso/entrar.*?)"',
            resp_logged_in.text
        )

        req_url = urllib.parse.urljoin(resp_logged_in.url, req_link)

        # need to use Referer
        req_headers = {
            'User-Agent': project_settings.DEFAULT_USER_AGENT,
            'Referer': resp_logged_in.url,
        }

        resp = self.basic_req_get(
            s,
            req_url,
            headers=req_headers,
            proxies=self.req_proxies,
            logger_info='open_user_companies_page',
            err_signs=RESP_ERR_SIGNS
        )

        return s, resp

    def process_page_with_accounts_details_select_form(
            self,
            s: MySession,
            resp_comp_init_page_with_acc_overview: Response,
            session_req_param_id: str) -> bool:

        if IS_COMPANY_TURNED_OFF_SIGN in resp_comp_init_page_with_acc_overview.text:
            return False

        self.get_and_upload_accounts_balances(s, resp_comp_init_page_with_acc_overview,
                                              session_req_param_id)

        self.get_and_upload_movements(s, resp_comp_init_page_with_acc_overview,
                                      session_req_param_id)
        return True

    def get_and_upload_accounts_balances(
            self,
            s: MySession,
            resp_comp_init_page_with_acc_overview: Response,
            session_req_param_id: str) -> bool:

        # open page_with_accounts_details_select_form
        req_url = 'https://lknet.laboralkutxa.com/Consultas/C011.asp?Id={}&opcion=C'.format(
            session_req_param_id)

        req_headers = {
            'User-Agent': project_settings.DEFAULT_USER_AGENT,
            'Referer': resp_comp_init_page_with_acc_overview.url,
        }

        resp = self.basic_req_get(
            s,
            req_url,
            headers=req_headers,
            proxies=self.req_proxies,
            logger_info='{}: get_and_upload_accounts_balances'.format(session_req_param_id),
            err_signs=RESP_ERR_SIGNS
        )

        # ['0200001612@01@020.0.00161.2', ...]
        cuenta_params = parse_helpers.get_cuentas_prestamos_params(resp.text)
        cuentas_count = len(cuenta_params)

        if project_settings.IS_CONCURRENT_SCRAPING:
            if cuentas_count:
                with futures.ThreadPoolExecutor(max_workers=cuentas_count) as executor:
                    futures_dict = {
                        executor.submit(
                            self.open_one_acc_details_page_and_upload,
                            s,
                            resp,
                            cuenta_param): cuenta_param
                        for cuenta_param in cuenta_params
                    }
                    self.logger.log_futures_exc('open_one_acc_details_page_and_upload',
                                                futures_dict)
        else:
            for cuenta_param in cuenta_params:
                self.open_one_acc_details_page_and_upload(s, resp, cuenta_param)

        return True

    def open_one_acc_details_page_and_upload(
            self,
            s: MySession,
            resp_page_with_accounts_details_select_form: Response,
            cuenta_param: str) -> bool:

        req_url = 'https://lknet.laboralkutxa.com/Consultas/C011_2.asp'

        req_headers = {
            'User-Agent': project_settings.DEFAULT_USER_AGENT,
            'Referer': resp_page_with_accounts_details_select_form.url
        }

        _action_link, req_params = extract.build_req_params_from_form_html(
            resp_page_with_accounts_details_select_form.text,
            "frm"
        )

        req_params['lcuenta'] = cuenta_param

        resp = self.basic_req_post(
            s,
            req_url,
            data=req_params,
            headers=req_headers,
            proxies=self.req_proxies,
            logger_info='{}: open_one_acc_details_page_and_upload'.format(cuenta_param),
            err_signs=RESP_ERR_SIGNS
        )

        account_parsed, is_cuenta = parse_helpers.get_account_parsed(resp.text)
        if not is_cuenta:
            self.logger.info(
                '{} is not a valid account to process '
                '(neither debit nor credit account). Skip'.format(
                    account_parsed['financial_entity_account_id']
                )
            )
            return False

        account_scraped = self.basic_account_scraped_from_account_parsed(
            account_parsed['organization_title'],
            account_parsed
        )

        self._update_self_accounts(cuenta_param, account_scraped)

        self.basic_upload_accounts_scraped([account_scraped])
        self.basic_log_time_spent('GET BALANCE: {}'.format(account_scraped.FinancialEntityAccountId))

        return True

    def get_and_upload_movements(
            self,
            s: MySession,
            resp_comp_init_page_with_acc_overview: Response,
            session_req_param_id: str) -> None:

        # open page_with_movements_form (with selector of account)
        req_url = 'https://lknet.laboralkutxa.com/Consultas/C020_Sel.asp?Id={}&DesdeMenu=**'.format(
            session_req_param_id)

        req_headers = {
            'User-Agent': project_settings.DEFAULT_USER_AGENT,
            'Referer': resp_comp_init_page_with_acc_overview.url,
        }

        resp = self.basic_req_get(
            s,
            req_url,
            headers=req_headers,
            proxies=self.req_proxies,
            err_signs=RESP_ERR_SIGNS,
            logger_info='{}: get_and_upload_movements'.format(session_req_param_id)
        )

        # ['0200001612@01@020.0.00161.2', ...]
        cuentas_params = parse_helpers.get_cuentas_prestamos_params(resp.text)
        cuentas_count = len(cuentas_params)

        if project_settings.IS_CONCURRENT_SCRAPING:
            if cuentas_count:
                with futures.ThreadPoolExecutor(max_workers=cuentas_count) as executor:
                    futures_dict = {
                        executor.submit(self.process_account,
                                        s,
                                        resp, cuenta_param): cuenta_param
                        for cuenta_param in cuentas_params
                    }
                    self.logger.log_futures_exc(
                        'open_one_acc_movements_excel_and_upload',
                        futures_dict
                    )
        else:
            for cuenta_param in cuentas_params:
                self.process_account(s, resp, cuenta_param)

    def process_account(
            self,
            s: MySession,
            resp_page_with_mov_form: Response,
            cuenta_param: str) -> bool:
        """
        :param s
        :param resp_page_with_mov_form
        :param cuenta_param: like '0200001612@01@020.0.00161.2'
        """

        # It is possible that account_scraped not saved
        # because Prestamo detected during account details page processing
        # No account_scraped? - it is not a Cuenta -> skip
        account_scraped = self.accounts.get(cuenta_param)
        if not account_scraped:
            return True

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        account_no = account_scraped.AccountNo

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        req_url = 'https://lknet.laboralkutxa.com/Consultas/C020_CuentasExcel.asp'
        req_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': project_settings.DEFAULT_USER_AGENT,
            'Referer': resp_page_with_mov_form.url
        }

        # invalid req link due to broken page layout
        _, req_params = extract.build_req_params_from_form_html_patched(
            resp_page_with_mov_form.text,
            "formCambioCuenta"
        )

        # Foreign currency
        if account_scraped.Currency != 'EUR':
            # Note:
            # The request to foreign currency account returns all recent movements
            # since the begging of the year. For now (2020-06) there is no way
            # to reproduce a request for filtered movements because
            # this request is for the old backend.
            req_url = 'https://lknet.laboralkutxa.com/Consultas/C020_Divisas.asp'

        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        d_from, m_from, y_from = date_from_str.split('/')
        d_to, m_to, y_to = self.date_to_str.split('/')

        req_params['txtExcel'] = '0'
        req_params['lcuenta'] = cuenta_param
        req_params['FECHAINICIO'] = date_from_str.replace('/', '')
        req_params['FECHAFIN'] = self.date_to_str.replace('/', '')  # '10052017'
        req_params['cuentaA'] = cuenta_param
        req_params['fechas'] = 'F'
        req_params['diadesde'] = d_from
        req_params['mesdesde'] = m_from
        req_params['yeardesde'] = y_from
        req_params['diahasta'] = d_to
        req_params['meshasta'] = m_to
        req_params['yearhasta'] = y_to

        # Excel for EUR, but html recent movs for USD
        resp_movs = self.basic_req_post(
            s,
            req_url,
            data=req_params,
            headers=req_headers,
            proxies=self.req_proxies,
            timeout=60,  # ! important for -u 239163 -a 11806, ES3630350175851750014781
            err_signs=RESP_ERR_SIGNS,
            logger_info='{}: open_one_acc_movements_excel_and_upload'.format(cuenta_param)
        )

        if account_scraped.Currency == 'EUR':
            resp_movs_excel = resp_movs
        else:
            req_url_xls = 'https://lknet.laboralkutxa.com/Consultas/C020_DivisasXLS.asp'
            _, req_xls_params = extract.build_req_params_from_form_html_patched(resp_movs.text, 'xls')
            req_headers['Referer'] = resp_movs.url
            resp_movs_excel = self.basic_req_post(
                s,
                req_url_xls,
                data=req_xls_params,
                headers=req_headers,
                proxies=self.req_proxies,
                timeout=60,  # ! important for -u 239163 -a 11806, ES3630350175851750014781
                err_signs=RESP_ERR_SIGNS,
                logger_info='{}: open_one_acc_movements_excel_and_upload: '
                            'resp_movs_excel for foreign currency acc'.format(cuenta_param)
            )

        # handle error excel gen if no movements
        if 'Se ha producido un error en la generaci&oacute;n de la hoja Excel.' in resp_movs_excel.text:
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.SUCCESS)
            return True

        movements_parsed = parse_helpers.get_movements_parsed_from_excel(
            resp_movs_excel.text,
            fin_ent_account_id,
            is_foreign_currency=account_scraped.Currency != 'EUR',
            logger=self.logger,
        )

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_log_process_account(account_no, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )
        return True

    def process_company_one_of_many(self, company_tuple: Tuple[str, str]) -> bool:
        """need to log in again to process each company"""

        company_page_id = company_tuple[0]
        company_page_title = company_tuple[1]
        resp = Response()  # suppress linter's warnings
        for i in range(3):
            s, resp, is_logged, is_credentials_error = self.login()
            if is_logged:
                break
            time.sleep(0.5 + random.random())
        else:
            self.logger.info("Can't log in for company {}:\nRESP:\n{}".format(company_page_title, resp.text))
            return False

        time.sleep(0.2 + random.random())  # delay to avoid log in errors

        resp_companies = Response()  # suppress linter's warnings
        for i in range(3):
            s, resp_companies = self.open_user_companies_page(s, resp)
            action_link, req_params = extract.build_req_params_from_form_html(
                resp_companies.text,
                'form'
            )

            session_req_param_id = req_params.get('Id', '')  # type: str
            if session_req_param_id:
                break
            else:
                time.sleep(0.5 + random.random())
        else:
            self.logger.info("Can't get correct resp_companies "
                             "for company {}:\nRESP:\n{}".format(company_page_title, resp_companies.text))
            return False

        req_params['txtgrd_fc'] = ''

        req_params['txtgrd_gl'] = ''

        # UIEventCollector.serialize() -> txtgrd_mm=@@0,1494177032375,0
        now_formatted = int(
            round(datetime.datetime.timestamp(datetime.datetime.now()), 3) * 1000
        )

        req_params['txtgrd_mm'] = '@@0,{},0'.format(now_formatted)
        req_params['dnicif'] = company_page_id

        # expect "eligeNif.asp"
        req_url = urllib.parse.urljoin(resp_companies.url, action_link)

        req_headers = {
            'User-Agent': project_settings.DEFAULT_USER_AGENT,
            'Referer': resp_companies.url,
        }

        # no iban here, need to open details of each account
        resp_comp_init_page_with_acc_overview = self.basic_req_post(
            s,
            req_url,
            data=req_params,
            headers=req_headers,
            proxies=self.req_proxies,
            err_signs=RESP_ERR_SIGNS,
            logger_info='{}: process_company_one_of_many'.format(company_page_title)
        )

        # parse it later
        # account_parsed_init = parse_helpers.get_accounts_parsed_init(
        #   resp_comp_init_page_with_acc_overview.text)

        is_processed = self.process_page_with_accounts_details_select_form(
            s,
            resp_comp_init_page_with_acc_overview,
            session_req_param_id
        )

        if not is_processed:
            self.logger.warning(
                "FinEntity-level error when process company with id {}. "
                "Possible reason: the company is turned off by the customer".format(company_page_title)
            )

        return True

    def process_company_one_of_one(self, s: MySession, resp_logged_in: Response) -> Tuple[bool, bool]:
        """:returns (is_success, is_newweb_detected)"""
        req_link = extract.re_first_or_blank(
            '<frame src="(/logon/rsalogin.*?)"',
            resp_logged_in.text
        )

        if not req_link:
            # '/logon/newuser.asp' istead of expected for old web '/logon/rsalogin.asp'
            self.logger.info('Only the new web access is allowed. Will process it now')
            if '/logon/newuser.asp' in resp_logged_in.text:
                return False, True

            self.basic_log_wrong_layout(
                resp_logged_in,
                "process_company_one_of_one: can't get req_link. Abort"
            )
            return False, False

        req_url = urllib.parse.urljoin(resp_logged_in.url, req_link)

        # need to use Referer
        req_headers = {
            'User-Agent': project_settings.DEFAULT_USER_AGENT,
            'Referer': resp_logged_in.url,
        }

        resp = self.basic_req_get(
            s,
            req_url,
            headers=req_headers,
            proxies=self.req_proxies,
            err_signs=RESP_ERR_SIGNS,
            logger_info='{}: process_company_one_of_one'.format(req_link)
        )

        action_url_raw, req_params = extract.build_req_params_from_form_html(resp.text, 'frm')

        req_params['txtgrd_fc'] = ''
        req_params['txtgrd_gl'] = ''

        # UIEventCollector.serialize() -> txtgrd_mm=@@0,1494177032375,0
        now_formatted = int(round(datetime.datetime.timestamp(datetime.datetime.now()), 3) * 1000)
        req_params['txtgrd_mm'] = '@@0,{},0'.format(now_formatted)

        # req_params['dnicif'] = company_page_id

        req_url = urllib.parse.urljoin(resp.url, action_url_raw)  # expect "eligeNif.asp"

        req_headers = {
            'User-Agent': project_settings.DEFAULT_USER_AGENT,
            'Referer': resp.url,
        }

        # no iban here, need to open details of each account
        resp_comp_init_page_with_acc_overview = self.basic_req_post(
            s,
            req_url,
            data=req_params,
            headers=req_headers,
            proxies=self.req_proxies,
            err_signs=RESP_ERR_SIGNS,
            logger_info='{}: process_company_one_of_one'.format(req_link)
        )

        session_req_param_id = req_params['Id']  # type: str
        # parse it later
        # account_parsed_init = parse_helpers.get_accounts_parsed_init(resp_comp_init_page_with_acc_overview.text)

        is_processed = self.process_page_with_accounts_details_select_form(
            s,
            resp_comp_init_page_with_acc_overview,
            session_req_param_id
        )

        if not is_processed:
            self.logger.warning(
                "FinEntity-level error when process one-of one company. "
                "Possible reason: the company is turned off by the customer")

        return True, False

    def main(self) -> MainResult:

        s, resp_logged_in, is_logged, is_credentials_error = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(
                resp_logged_in.url,
                resp_logged_in.text
            )

        s, resp_companies = self.open_user_companies_page(s, resp_logged_in)

        companies_tuples = parse_helpers.get_companies_tuples(resp_companies.text)
        companies_count = len(companies_tuples)

        # several companies per user account
        if project_settings.IS_CONCURRENT_SCRAPING:
            if companies_count:
                with futures.ThreadPoolExecutor(max_workers=4) as executor:
                    futures_dict = {
                        executor.submit(self.process_company_one_of_many,
                                        company_tuple): company_tuple[1]
                        for company_tuple in companies_tuples
                    }
                    self.logger.log_futures_exc('process_company', futures_dict)
        else:
            for company_tuple in companies_tuples:
                self.process_company_one_of_many(company_tuple)

        # one company per user account
        if companies_count == 0:
            ok, is_newweb_detected = self.process_company_one_of_one(s, resp_logged_in)
            if not ok and is_newweb_detected:
                # Process new web (particulares only?)
                scraper_newweb = LaboralKutxaBancaOnlineScraper(
                    scraper_params_common=self.__scraper_params,
                    proxies=self.__proxies
                )
                return scraper_newweb.main()

        self.basic_log_time_spent('GET MOVEMENTS OF ALL COMPANIES')

        self.download_correspondence(s, companies_count)

        return self.basic_result_success()
