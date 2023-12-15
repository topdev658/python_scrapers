import os
import random
import subprocess
import time
import urllib.parse
from concurrent import futures
from typing import Dict, List, Tuple

from deprecated import deprecated

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (AccountParsed, AccountScraped,
                                  MovementParsed, ScraperParamsCommon, MainResult)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from . import req_helpers

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'liberbank_encrypter.js'
))

__version__ = '7.14.0'

__changelog__ = """
7.14.0
more CREDENTIALS_ERROR_MARKERS
7.13.0
call basic_upload_movements_scraped with date_from_str
7.12.0
renamed to download_correspondence()
7.11.0
use only serial scraping for receipts_scraper 
(it's necessary for receipt downloading)
7.10.1
deprecations marked
7.10.0
download_receipts
7.9.0
skip inactive accounts
7.8.0
download_company_documents
7.7.0
USD accs support
7.6.1
more cred err markers, suitable for CastillaLaManchaLiberbankScraper
7.6.0
use basic_new_session
upd type hints
fmt
7.5.0
use basic_get_date_from
7.3.1
fixed type hints
7.3.0
added more credentials error markers
7.2.0
basic_movements_scraped_from_movements_parsed: new format of the result 
7.1.0
added 'blocked user' detection as credentials error
7.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
6.0.0
parse movements from excel
5.0.0
basic_movements_scraped_from_movements_parsed
OperationalDatePosition, KeyValue support
4.8.0
fix signs of movements
4.7.0
basic_upload_movements_scraped
4.6.0
use self._get_movements_parsed() instead of self.get_movements_parsed_func
4.5.0
get_movements_parsed_func as property
4.4.1
reformat
test
4.4.0
len(accounts_scraped) in futures
4.3.0
params -> data in req
better err cred detection
4.2.0
from libs import myrequests as requests  # redefine requests behavior
4.1.0
date_from in upload_mov call
4.0.2
basic_log_process_account in the beginning of process_account
4.0.1
correct fin_ent_acc_id
4.0.0
_get_date_from_for_account_str_by_fin_ent_acc_id	
upload_mov_by_fin_ent_acc_id
3.0.0
'account_iban' -> 'account_no'
2.1.0
request.compat -> urlib.parse for type checking
2.0.0
BasicScraper integration
return codes
1.1.0
project_settings.IS_UPDATE_DB
1.0.0
stable
handling err response during parallel scraping (reopen if necessary)
1.0.0b2
get login form params from resp to log in diff accs
fix get_accounts_parsed in parse_helpers
1.0.0b
need to check credit accounts balance (can be placed in other place instead of dedit accouns)
"""

CREDENTIALS_ERROR_MARKERS = [
    'DE USUARIO O ALIAS DE FORMA INCORRECTA',
    'secreto introducido no es correcto',
    'Usuario bloqueado',
    'El usuario está bloqueado de forma anómala',
    'CLIENTE DADO DE BAJA',
    'Número de usuario no autorizado a ejecutar esta operación',  # CastillaLaManchaLiberbank
    'Credenciales incorrectas',
]


class LiberbankScraper(BasicScraper):
    """Many sessions not allowed"""

    scraper_name = 'LiberbankScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.update_inactive_accounts = False

    def _get_encrypted(self, clave: str) -> str:
        cmd = '{} "{}" "{}"'.format(CALL_JS_ENCRYPT_LIB, clave, self.userpass)
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def login(self) -> Tuple[MySession, Response, bool, bool, str, str]:
        """:returns (s, resp3, is_logged, is_credentials_error, caja_param, camino_param.upper())"""
        s = self.basic_new_session()

        req1_url = ('https://bancaadistancia.liberbank.es/'
                    'BEWeb/2048/W048/inicio_identificacion.action'
                    '?App=SI&fromapplication=iphone&IDIOMA=01&PAN=&USER=')

        resp1 = s.get(
            req1_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req2_url = ('https://bancaadistancia.liberbank.es/'
                    'BEWeb/2048/W066/inicio_identificacion_selloXML.action')
        resp2 = s.get(
            req2_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        sello = extract.re_first_or_blank('<SELLO>(.*?)</SELLO>', resp2.text)
        clave = extract.re_first_or_blank('<CLAVE>(.*?)</CLAVE>', resp2.text)

        # USE https://bancaadistancia.liberbank.es/W066/js/MOD3.js <-- func MOD here
        # and https://bancaadistancia.liberbank.es/W066/js/LOGIN2.js
        # ...
        #    formulario.PIN.value = MOD(clave, formulario.PIN1.value);
        # ...
        pin = self._get_encrypted(clave)

        req3_url = ('https://bancaadistancia.liberbank.es/'
                    'BEWeb/2048/W066/identificacion.action')
        _, req3_params = extract.build_req_params_from_form_html(resp1.text, 'formu')

        req3_params['App'] = ''
        req3_params['SELLO'] = sello
        req3_params['PIN'] = pin
        req3_params['PAN'] = self.username
        req3_params['PIN1'] = self.userpass

        resp3 = s.post(
            req3_url,
            data=req3_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = 'psoperarConValor_COMUN.action' in resp3.text
        is_credentials_error = any(m.lower() in resp3.text.lower() for m in CREDENTIALS_ERROR_MARKERS)

        _, _, _, _, caja_param, camino_param, _ = resp3.url.split('/')

        return s, resp3, is_logged, is_credentials_error, caja_param, camino_param.upper()

    def get_accounts_scraped(
            self,
            s: MySession,
            resp: Response) -> Tuple[MySession, Response,
                                     List[AccountParsed], List[AccountScraped], str]:

        self.logger.info('get_accounts_scraped: start')

        req_link = extract.re_first_or_blank('var url="(.*?)"', resp.text)
        req_url = urllib.parse.urljoin(resp.url, req_link)

        resp = s.get(
            req_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_parsed = parse_helpers.get_accounts_parsed_v2(self.logger, resp.text)
        company_title = parse_helpers.get_company_title(resp.text)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(company_title, account_parsed)
            for account_parsed in accounts_parsed
        ]

        self.logger.info('Accounts: {}'.format(accounts_scraped))
        self.logger.info('get_accounts_scraped: done')

        return s, resp, accounts_parsed, accounts_scraped, company_title

    def process_account(
            self,
            s: MySession,
            resp_accs: Response,
            accounts_scraped_dict: Dict[str, AccountScraped],
            account_parsed: AccountParsed,
            caja_param: str,
            camino_param: str,
            company_title: str) -> bool:

        fin_ent_account_id = account_parsed['financial_entity_account_id']
        account_scraped = accounts_scraped_dict[fin_ent_account_id]

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        movements_parsed_desc = []  # type: List[MovementParsed]
        codreanud_param = ''
        resp_movs_i = Response()

        # Pagination
        for page_ix in range(100):  # avoid inf loop
            llamada_param = None

            # loop to handle error responses during parallel scraping
            for attempt in range(10):
                self.logger.info('{}: page {}: att #{}: get movements'.format(
                    fin_ent_account_id,
                    page_ix + 1,
                    attempt,
                ))
                req_mov_url, req_movs_params = req_helpers.req_params_movs_debit_account(
                    account_parsed,
                    date_from_str,
                    self.date_to_str,
                    caja_param,
                    camino_param,
                    resp_accs,
                    llamada_param
                )
                if page_ix:
                    req_movs_params['CODREANUD'] = codreanud_param
                    req_movs_params['OPERACION'] = '1004'
                    req_movs_params['IND_DATOS'] = str(page_ix)

                resp_movs_i = s.post(
                    req_mov_url,
                    data=req_movs_params,
                    headers=self.req_headers,
                    proxies=self.req_proxies
                )

                # response with err info, need to repeat request
                if 'podido realizar. Reintentar una vez. Si persiste, reiniciar la llamada' in resp_movs_i.text:
                    llamada_param = parse_helpers.get_llamada_param(resp_movs_i.text)
                    time.sleep(0.5 + 0.5 * random.random())
                    continue

                break
            else:
                self.basic_log_wrong_layout(resp_movs_i, "{}: page {}: can't get correct resp_movs_i".format(
                    fin_ent_account_id,
                    page_ix + 1
                ))
            # / end of attempt loop

            movements_parsed_i = []  # type: List[MovementParsed]
            if ('NO HAY MOVIMIENTOS EN EL PERIODO INDICADO' in resp_movs_i.text
                    or 'No hay movimientos para el periodo indicado' in resp_movs_i.text):
                self.logger.info('{}: found "no movements" marker'.format(fin_ent_account_id))
            else:
                movements_parsed_i = parse_helpers.get_movements_parsed(resp_movs_i.text)

            if not movements_parsed_i:
                break

            movements_parsed_desc.extend(movements_parsed_i)

            codreanud_param = parse_helpers.get_pagination_codreanud_param(resp_movs_i.text)
            if not codreanud_param:
                self.logger.info('{}: no more pages with movements'.format(fin_ent_account_id))
                break

        # / end of pagination

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_desc,
            date_from_str
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)
        ok = self.basic_upload_movements_scraped(
            self.basic_account_scraped_from_account_parsed(company_title, account_parsed),
            movements_scraped,
            date_from_str=date_from_str
        )

        # Early check up
        if not ok and self.basic_should_download_receipts(account_scraped):
            self.logger.warning('{}: got an err for movements_scraped. '
                                'Will not download receipts. Abort'.format(fin_ent_account_id))
            return False

        movements_parsed_asc = list(reversed(movements_parsed_desc))

        self.download_receipts(
            s,
            account_scraped=account_scraped,
            movements_scraped=movements_scraped,
            movements_parsed=movements_parsed_asc,
            resp_mov_filtered=resp_movs_i,
            caja_param=caja_param
        )
        return True

    @deprecated
    def process_account_excel(self,
                              s: MySession,
                              resp_accs: Response,
                              accounts_scraped_dict: Dict[str, AccountScraped],
                              account_parsed: AccountParsed,
                              caja_param: str,
                              camino_param: str,
                              company_title: str) -> bool:

        fin_ent_account_id = account_parsed['financial_entity_account_id']

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        llamada_param = None
        # loop to handle error responses during parallel scraping
        while True:
            req_mov_url, req_mov_params = req_helpers.req_params_movs_debit_account(
                account_parsed,
                date_from_str,
                self.date_to_str,
                caja_param,
                camino_param,
                resp_accs,
                llamada_param
            )

            resp_mov = s.post(
                req_mov_url,
                data=req_mov_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            # response with err info, need to repeat request
            if 'podido realizar. Reintentar una vez. Si persiste, reiniciar la llamada' in resp_mov.text:
                llamada_param = parse_helpers.get_llamada_param(resp_mov.text)
                time.sleep(0.1)
                continue

            break

        llamada_param = None
        # loop to handle error responses during parallel scraping
        while True:
            req_excel_url, req_excel_params = req_helpers.req_params_movs_excel(
                resp_mov,
                account_parsed,
                date_from_str,
                self.date_to_str,
                llamada_param
            )

            resp_excel = s.post(
                req_excel_url,
                data=req_excel_params,
                headers=self.basic_req_headers_updated({
                    'Referer': resp_mov.url,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }),
                proxies=self.req_proxies
            )

            # response with err info, need to repeat request
            if 'podido realizar. Reintentar una vez. Si persiste, reiniciar la llamada' in resp_excel.text:
                llamada_param = parse_helpers.get_llamada_param(resp_excel.text)
                time.sleep(0.1)
                continue

            break

        if ('NO HAY MOVIMIENTOS EN EL PERIODO INDICADO' in resp_excel.text
                or 'No hay movimientos para el periodo indicado' in resp_excel.text):
            self.logger.info('{}: found "no movements" marker'.format(fin_ent_account_id))
            movements_parsed = []  # type: List[MovementParsed]
        else:
            movements_parsed = parse_helpers.get_movements_parsed_from_excel_html(resp_excel.text)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            self.basic_account_scraped_from_account_parsed(company_title, account_parsed),
            movements_scraped,
            date_from_str=date_from_str
        )
        return True

    def main(self) -> MainResult:
        self.logger.info('main: started')
        s, resp_logged_in, is_logged, is_credentials_error, caja_param, camino_param = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url,
                                                                      resp_logged_in.text)
        s, resp_accs, accounts_parsed, accounts_scraped, company_title = self.get_accounts_scraped(
            s,
            resp_logged_in
        )
        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        accounts_scraped_dict = \
            self.basic_gen_accounts_scraped_dict(accounts_scraped)  # type: Dict[str, AccountScraped]

        # Get and save movements:
        # receipt scraper requires serial processing,
        # otherwise it can't correctly download movements receipts
        # (concurrently processed accounts spoil each other, -a 24432)
        if project_settings.IS_CONCURRENT_SCRAPING and not self.is_receipts_scraper:
            if accounts_scraped:
                with futures.ThreadPoolExecutor(max_workers=len(accounts_parsed)) as executor:
                    futures_dict = {
                        executor.submit(self.process_account, s, resp_accs,
                                        accounts_scraped_dict, account_parsed, caja_param,
                                        camino_param, company_title): account_parsed['account_no']
                        for account_parsed in accounts_parsed
                    }

                    self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_parsed in accounts_parsed:
                self.process_account(s, resp_accs, accounts_scraped_dict, account_parsed,
                                     caja_param, camino_param, company_title)

        self.basic_log_time_spent('GET MOVEMENTS')
        self.download_correspondence(s, resp_logged_in, company_title, caja_param, camino_param)

        return self.basic_result_success()
