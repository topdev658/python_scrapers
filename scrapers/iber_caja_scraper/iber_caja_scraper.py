import datetime
import random
import time
from concurrent import futures
from typing import List, Tuple
from urllib.parse import urljoin

from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (AccountScraped, MOVEMENTS_ORDERING_TYPE_ASC,
                                  ScraperParamsCommon, MainResult)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.iber_caja_scraper import parse_helpers

__version__ = '6.13.0'

__changelog__ = """
6.13.0
use account-level result_codes
6.12.0
custom s.verify (changed cert)
6.11.0
renamed to download_correspondence()
6.10.0
use update_inactive_accounts
process_account: use basic_check_account_is_active
6.9.0
download_company_documents
use parse_helpers.get_auth_param
6.8.0
use basic_new_session
upd type hints
fmt
6.7.0
use basic_get_date_from
6.6.0
future movs support
parse_helpers: changed some param names, more type hints
6.5.0
handle detected reason: LA OPERACIÓN NO SE HA REALIZADO CORRECTAMENTE
requests -> myrequests
6.4.0
login: added small delay between requests
6.3.0
more generic credentials error detector
6.2.1
fixed type hints
6.2.0
basic_movements_scraped_from_movements_parsed: new format of the result 
6.1.0
more 'wrong credentials' markers 
6.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
5.1.0
correct processing of inactive accounts
5.0.0
basic_movements_scraped_from_movements_parsed
OperationalDatePosition, KeyValue support
4.9.0
basic_upload_movements_scraped
4.8.0
handle case with minus balance for debit accounts
4.7.0
self.basic_check_is_account_inactive_by_text_signs
4.6.0
parse_helpers: parse_accounts: detect account type by descr and change balance value sign by type
4.5.0
current_ordering=custom_types.MOVEMENTS_ORDERING_TYPE_ASC
4.4.0
is_default_organization
4.3.0
from libs import myrequests as requests  # redefine requests behavior
4.2.0
date_from in upload_mov call
4.1.0
basic_log_process_acc
4.0.0
_get_date_from_for_account_str_by_fin_ent_acc_id	
upload_mov_by_fin_ent_acc_id
3.0.0
'account_iban' -> 'account_no'
2.0.0
BasicScraper integration
return codes
1.2.0
scrape_logger log in errs as methods
1.1.0
project_settings.IS_UPDATE_DB
fixed get_accounts_scraped return if is_accounts_overview_page_sign not in resp_cuentas.text (defaults returned)
type annotations
"""

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:51.0) Gecko/20100101 Firefox/51.0'
REQ_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'User-Agent': USER_AGENT,
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.5'
}

ACCOUNT_INACTIVE_SIGNS = ['CUENTA CANCELADA']

CREDENTIALS_ERROR_MARKERS = [
    'LA CLAVE DE ACCESO ESTÁ BLOQUEADA',
    # 'DATOS INCORRECTOS, CONSULTE AYUDA ACCESO',
    # 'DATOS INCORRECTOS, VUELVA A INTENTARLO',
    'DATOS INCORRECTOS'
]

DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS = 10  # offset to scrape future movements (08/01 from 05/01)


class IberCajaScraper(BasicScraper):
    scraper_name = 'IberCajaScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.date_to = self.date_to + datetime.timedelta(days=DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS)
        self.date_to_str = self.date_to.strftime(project_settings.SCRAPER_DATE_FMT)  # '30/01/2017'
        self.req_headers = {'User-Agent': USER_AGENT}
        self.update_inactive_accounts = False

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:

        s = self.basic_new_session()
        s.verify = 'www1-ibercajadirecto-com-chain.pem'
        req_url = 'https://www1.ibercajadirecto.com/ibercaja/asp/Login.asp'

        resp_login_page = s.get(
            req_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        time.sleep(0.3)

        action_url_raw, req_params_raw = parse_helpers.build_req_params_from_form_html(
            resp_login_page.text,
            'Formulario'
        )
        action_url = urljoin(resp_login_page.url, action_url_raw)

        # build final req_params_raw
        req_params = req_params_raw.copy()

        req_params['codeibd'] = self.username
        req_params['codidentific'] = self.username
        req_params['f1'] = self.userpass
        req_params['claveibd'] = self.userpass
        req_params['codetar'] = ''
        req_params['clavetar'] = ''
        # req_params['dato1'] = ''

        resp_logged = s.post(
            action_url,
            params=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = 'Cerrar' in resp_logged.text
        is_credentials_error = any(
            marker in resp_logged.text
            for marker in CREDENTIALS_ERROR_MARKERS
        )
        reason = ''

        # 'LA OPERACIÓN NO SE HA REALIZADO CORRECTAMENTE.'
        # reason may appear and then disappear without explicit reasons
        # but if it continue to appear, need to inform the customer
        # because if the scraper couldn't log in due to this reason,
        # also the customer won't log in.
        if 'LA OPERACIÓN NO SE HA REALIZADO CORRECTAMENTE.' in resp_logged.text:
            reason = ('common message "Incorrect operation" (not a credentials error).\n'
                      '<ACTION REQUIRED: if the problem persists more than a day, '
                      'pls check and confirm it using website access, maybe need to inform the bank>')

        return s, resp_logged, is_logged, is_credentials_error, reason

    def get_accounts_scraped(self,
                             s: MySession,
                             resp_logged_in: Response) -> Tuple[MySession, str, List[AccountScraped]]:

        self.logger.info('get_accounts_scraped: start')

        auth_param = parse_helpers.get_auth_param(resp_logged_in.text)

        req_headers = self.req_headers.copy()
        req_headers['Upgrade-Insecure-Requests'] = '1'
        req_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        req_headers['Connection'] = 'keep-alive'
        req_headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        req_headers['Accept-Encoding'] = 'gzip, deflate, br'
        req_headers['Accept-Language'] = 'en-US,en;q=0.5'

        req_url_menu = 'https://www1.ibercajadirecto.com/ibercaja/asp/menus/menu_inicio.asp'

        # note: during http monitoring we can see ?auth_param GET param, but this is fake, use request wo get params
        req_url_cuentas = 'https://www1.ibercajadirecto.com/ibercaja/asp/ModuloDirector.asp'

        req_headers['Referer'] = req_url_menu

        req_params_cuentas = {

            'IdOperacion': '52_0',  # '53_0' - movements
            'Entidad': '2085',
            'Canal': 'IBE',
            'Dispositivo': 'INTR',
            'Idioma': 'ES',
            'joven': '',
            'usuario': self.username,
            'entorno': 'IN',
            'tipotransferencia': 'transferenciaext',
            'MSCSAuth': auth_param,
            'VersionCabeceraBanner': 'SD',
            'Eclasificacion': '',
            'tipodeposito': '',
            'comercio': '',
        }

        resp_cuentas = s.post(
            req_url_cuentas,
            params=req_params_cuentas,
            headers=req_headers,
            proxies=self.req_proxies,
            allow_redirects=False
        )

        # check is correct page is opened
        is_accounts_overview_page_sign = '<td class="articletitle" height="25">Consulta de saldos de todas las cuentas'
        if is_accounts_overview_page_sign not in resp_cuentas.text:
            self.logger.error('Accounts page is not opened. Got {}: {}'.format(resp_cuentas.url, resp_cuentas.text))
            return s, auth_param, []

        accounts_parsed = parse_helpers.parse_accounts(resp_cuentas.text)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                self.db_customer_name,
                account_parsed,
                is_default_organization=True
            )
            for account_parsed in accounts_parsed
        ]

        self.logger.info('Accounts: {}'.format(accounts_scraped))
        self.logger.info('get_accounts_scraped: done')
        return s, auth_param, accounts_scraped

    def process_account(self, s: MySession, auth_param: str, account_scraped: AccountScraped) -> bool:

        account_no = account_scraped.AccountNo
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(account_no, date_from_str)

        date_from_day, date_from_month, date_from_year = date_from_str.split('/')
        date_to_day, date_to_month, date_to_year = self.date_to_str.split('/')

        req_headers = self.req_headers.copy()
        req_headers['Upgrade-Insecure-Requests'] = '1'
        req_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        req_headers['Connection'] = 'keep-alive'
        req_headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        req_headers['Accept-Encoding'] = 'gzip, deflate, br'
        req_headers['Accept-Language'] = 'en-US,en;q=0.5'

        req_url = ('https://www1.ibercajadirecto.com/ibercaja/asp/'
                   'ModuloDirector.asp?MSCSAuth={}'.format(auth_param))

        account_no_for_request = account_scraped.AccountNo[-20:]

        req_params = {
            'IdOperacion': '53_1',
            'Entidad': '2085',
            'Canal': 'IBE',
            'Dispositivo': 'INTR',
            'Idioma': 'ES',
            'fecha_actual': '',
            'Cuenta': account_no_for_request,
            'FechaInicioDia': date_from_day,
            'FechaInicioMes': date_from_month,
            'FechaInicioAno': date_from_year,
            'FechaFinDia': date_to_day,
            'FechaFinMes': date_to_month,
            'FechaFinAno': date_to_year,
            'AbonoCargo': 'T',
            'ImporteMinimo': '',
            'ImporteMaximo': '',
            'CodigoConcepto': '',
            'cuentaRes': account_no_for_request,
            'FechaInicioDiaRes': date_from_day,
            'FechaInicioMesRes': date_from_month,
            'FechaInicioAnoRes': date_from_year,
            'FechaFinDiaRes': date_to_day,
            'FechaFinMesRes': date_to_month,
            'FechaFinAnoRes': date_to_year,
            'AbonoCargoRes': 'T',
            'ImporteMinimoRes': '',
            'ImporteMaximoRes': '',
            'CodigoConceptoRes': '',
            'x': random.randint(40, 50),
            'y': random.randint(15, 25)

        }

        resp_movs = s.post(
            req_url,
            params=req_params,
            headers=req_headers,
            proxies=self.req_proxies,
            allow_redirects=False
        )

        if self.basic_check_is_account_inactive_by_text_signs(
                resp_movs.text,
                fin_ent_account_id,
                ACCOUNT_INACTIVE_SIGNS
        ):
            self.logger.warning('{}: "inactive" marker detected. '
                                'Account will be marked as "Possible inactive"'.format(fin_ent_account_id))
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_DISABLED_ACCOUNT)
            return False

        movements_parsed = parse_helpers.parse_movements(resp_movs.text)
        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_log_process_account(account_no, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str
        )

        return True

    def main(self) -> MainResult:
        session, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if reason:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url,
                                                                      resp_logged_in.text)

        s, auth_param, accounts_scraped = self.get_accounts_scraped(session, resp_logged_in)

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        # get and save movements
        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=16) as executor:

                futures_dict = {
                    executor.submit(self.process_account, s,
                                    auth_param, account_scraped): account_scraped.AccountNo
                    for account_scraped in accounts_scraped
                }

                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_scraped in accounts_scraped:
                self.process_account(s, auth_param, account_scraped)

        self.basic_log_time_spent('GET MOVEMENTS')
        self.download_correspondence(s, resp_logged_in)
        return self.basic_result_success()
