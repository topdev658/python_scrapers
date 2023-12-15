import datetime
import os
import random
import subprocess
import time
from concurrent import futures
from typing import Tuple

from custom_libs import date_funcs
from custom_libs.myrequests import MySession, Response
from custom_libs.requests_helpers import update_mass_cookies
from project import settings as project_settings
from project.custom_types import AccountScraped, ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.openbank_scraper import parse_helpers

__version__ = '5.4.0'

__changelog__ = """
5.4.0
call basic_upload_movements_scraped with date_from_str
5.3.0
skip inactive accounts
5.2.0
use basic_new_session
upd type hints
fmt
5.1.0
use basic_get_date_from
impl pagination(emulate it using day-by-day filtering)
parse_helpers: fmt
5.0.0
new scraper based on rest api
4.2.0
basic_movements_scraped_from_movements_parsed: new format of the result 
4.1.1
more log info 
4.1.0
process_account: more attempts to switch to correct account
4.0.1
process_account: dates in err msgs
4.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str

"""

CALL_JS_ENCRYPT_LIB_SESSION = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'openbank_session_encrypter.js'
))

# UNUSED for now but kept in the code to use if necessary
# CALL_JS_ENCRYPT_LIB_COKIEBITE = 'node {}'.format(os.path.join(
#     project_settings.PROJECT_ROOT_PATH,
#     project_settings.JS_HELPERS_FOLDER,
#     'openbank_cookiebite_encrypter.js'
# ))


PARAM_DATE_FMT = '%Y-%m-%d'
MAX_MOVS_PER_PAGE = 25


class OpenbankScraper(BasicScraper):
    scraper_name = 'OpenbankScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.req_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0'
        }
        self.auth_token = ''
        self.update_inactive_accounts = False

    def _get_encrypted(self, cmd: str) -> str:
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def login(self) -> Tuple[MySession, Response, bool, bool]:
        s = self.basic_new_session()
        req_init_url = 'https://www.openbank.es/es/'

        # initial cookies
        resp_init = s.get(
            req_init_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_login_url = 'https://api.openbank.es/authenticationcomposite/login'
        nu_data_session_param = self._get_encrypted(CALL_JS_ENCRYPT_LIB_SESSION)

        # unnecessary for now
        # cookiebite = self._get_encrypted(CALL_JS_ENCRYPT_LIB_COKIEBITE)

        s = update_mass_cookies(s, {
            'ndsid': nu_data_session_param,
            # 'ok-cookiebite': cookiebite,
        }, '.openbank.es')

        req_login_params = {
            "document": self.username,
            "password": self.userpass,
            "osVersion": "X11",
            "documentType": "N",
            # can be found in one of js scripts by userIpAddress:"83.40.205.30"
            "userIpAddress": "83.40.205.30",
            "context": "",  # form input nds-pmd, can use ""
            "nuDataSession": nu_data_session_param,  # 'ndsa08a0hzpxw018jnw7pkrk'
            "uuid": "925446813",  # const, related to webbrowser
            "webDeviceInfo": {
                "version": self.req_headers['User-Agent']
            },
            "force": True
        }

        req_headers = self.basic_req_headers_updated(
            {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Origin': 'https://www.openbank.es',
                'Referer': 'https://www.openbank.es/',
                'Connection': 'keep-alive',
                'version': '3'
            }
        )

        resp_login = s.post(
            req_login_url,
            json=req_login_params,
            proxies=self.req_proxies,
            headers=req_headers
        )

        resp_login_json = resp_login.json()

        is_logged = 'tokenCredential' in resp_login_json
        is_credentials_error = 'bad.input.credentials.incorrect' in resp_login.text

        self.auth_token = resp_login_json.get('tokenCredential', '')

        return s, resp_login, is_logged, is_credentials_error

    def process_contract(self, s: MySession) -> bool:

        req_pos_glob_headers = self.basic_req_headers_updated({
            'openBankAuthToken': self.auth_token,
            'version': '5',
            'Accept': 'application/json',
            'Origin': 'https://clientes.openbank.es',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://clientes.openbank.es/myprofile/global',
            'Connection': 'keep-alive'
        })

        req_pos_glob_url = ('https://api.openbank.es/posicion-global-total'
                            '?listaSolicitada=TODOS&indicadorSaldoPreTarj=false')

        resp_pos_glob = s.get(
            req_pos_glob_url,
            headers=req_pos_glob_headers,
            proxies=self.req_proxies
        )

        accounts_parsed = parse_helpers.get_accounts_parsed_from_json(resp_pos_glob.json())

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                acc_parsed['organization_title'],
                acc_parsed
            )
            for acc_parsed in accounts_parsed
        ]

        self.logger.info('Got accounts: {}'.format(accounts_scraped))
        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        # get and save movements
        # 'and accounts_scraped' to avoid exception in max_workers=len(accounts_scraped)
        if project_settings.IS_CONCURRENT_SCRAPING and accounts_scraped:
            with futures.ThreadPoolExecutor(max_workers=4) as executor:

                futures_dict = {
                    executor.submit(self.process_account, s, account_scraped):
                        account_scraped.AccountNo
                    for account_scraped in accounts_scraped
                }

                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_scraped in accounts_scraped:
                self.process_account(s, account_scraped)

        return True

    def process_account(self, s: MySession, account_scraped: AccountScraped) -> bool:
        account_no = account_scraped.AccountNo
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        date_from = date_funcs.get_date_from_str(date_from_str)  # type: datetime.datetime

        self.basic_log_process_account(account_no, date_from_str)

        req_headers = self.basic_req_headers_updated({
            'openBankAuthToken': self.auth_token,
            'Accept': 'application/json',
            'Origin': 'https://clientes.openbank.es',
        })

        numero_contrato_param = fin_ent_account_id[-7:]  # '4385403'
        producto_param = fin_ent_account_id[-10:-7]  # '044'

        req_movs_url = 'https://api.openbank.es/my-money/cuentas/movimientos'

        req_movs_params = {
            'fechaDesde': date_from.strftime(PARAM_DATE_FMT),
            'fechaHasta': self.date_to.strftime(PARAM_DATE_FMT),
            'numeroContrato': numero_contrato_param,
            'producto': producto_param,
        }

        resp_movs = s.get(
            req_movs_url,
            params=req_movs_params,
            headers=req_headers,
            proxies=self.req_proxies
        )
        resp_movs_json = resp_movs.json()
        movements_parsed_desc = parse_helpers.get_movements_parsed_from_json(resp_movs_json)

        if len(movements_parsed_desc) >= MAX_MOVS_PER_PAGE:
            # More than 1 page, but
            # the pagination is broken at fin entity web app layer (returns err).
            # Scrape day by day to emulate the pagination.
            # NOTE: if there are > 25 movements during a day, then it'll fail too.

            # FOR DB customer 154853: fin_entity_access 6137: ES1900730100510446612999
            # https://api.openbank.es/my-money/cuentas/movimientos?producto=044&numeroContrato=6612999&fechaDesde=2019-06-01&fechaHasta=2019-06-28&diaMovimiento=7&situacion=3&importeCuenta=0.00&divisaCuenta=EUR&numeroMovimiento=1&centroOperacion=0100&empresaOperacion=0073&codigoTerminal=BH119&numeroDgo=2985&fechaAlta=2019-06-25&discriminacionOperacion=PAGINACION

            #  -u 173761 -a 10104 - ES5700730100570444385677
            # http://api.openbank.es/my-money/cuentas/movimientos?
            # producto=044
            # &numeroContrato=4385677
            # &fechaDesde=2019-10-10
            # &fechaHasta=2019-11-04
            # &diaMovimiento=11
            # &situacion=3
            # &importeCuenta=0.00
            # &divisaCuenta=EUR
            # &numeroMovimiento=1
            # &centroOperacion=0100
            # &empresaOperacion=0073
            # &codigoTerminal=  // BROKEN, must be non-empty
            # &numeroDgo=491421
            # &fechaAlta=2019-10-25
            # &discriminacionOperacion=PAGINACION
            self.logger.info('{}: got more than 1 page with movements. '
                             'Scrape day by day'.format(fin_ent_account_id))
            movements_parsed_desc = []
            for i in range((self.date_to - date_from).days + 1):
                date_i = self.date_to - datetime.timedelta(days=i)
                date_i_param = date_i.strftime(PARAM_DATE_FMT)
                req_movs_i_params = {
                    'fechaDesde': date_i_param,
                    'fechaHasta': date_i_param,
                    'numeroContrato': numero_contrato_param,
                    'producto': producto_param,
                }

                # max 25 movs per page DESC (MAX_MOVS_PER_PAGE)
                resp_movs_i = s.get(
                    req_movs_url,
                    params=req_movs_i_params,
                    headers=req_headers,
                    proxies=self.req_proxies
                )

                movements_parsed_i = parse_helpers.get_movements_parsed_from_json(resp_movs_i.json())
                self.logger.info('{}: got {} movs from {}'.format(
                    fin_ent_account_id,
                    len(movements_parsed_i),
                    date_i_param
                ))
                movements_parsed_desc.extend(movements_parsed_i)
                time.sleep(0.05 * (1 + random.random()))

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_desc,
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
        s, resp_logged_in, is_logged, is_credentials_error = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url, resp_logged_in.text)

        self.process_contract(s)

        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
