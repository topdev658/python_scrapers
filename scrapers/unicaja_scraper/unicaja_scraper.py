import os
import random
import subprocess
import urllib.parse
from concurrent import futures
from typing import List, Tuple

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, ScraperParamsCommon,
    MOVEMENTS_ORDERING_TYPE_ASC, MainResult,
    DOUBLE_AUTH_REQUIRED_TYPE_COMMON,
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.unicaja_scraper import parse_helpers

__version__ = '5.4.0'

__changelog__ = """
5.5.0
call basic_upload_movements_scraped with date_from_str
5.4.0
resolved when merged 5.1.0 and 5.2.0-5.3.0
5.3.0
removed _save_n43s, _log_time_spent
process_access
5.2.0
_save_n43s
_log_time_spent (to allow changes by children)
_upload_accounts_scrape (to allow changes by children)
5.1.0
login: handle univia.unicajabanco.es subdomain
5.0.0
renamed from caja_espana_scraper to unicaja_scraper
4.12.0
renamed to download_correspondence()
4.11.0
skip inactive accounts
4.10.0
process_contract: added download_company_documents
4.9.1
parse_helpers: get_movements_parsed_from_excel_resp: 
  don't decode file_content for logging to handle all possible cases 
4.9.0
more double auth detectors
4.8.1
aligned double auth msg
4.8.0
use basic_new_session
parse_helpers: get_accounts_parsed: handle new layout
4.7.0
login: interrupt if can't get correct page data (to avoid false-positive cred errs)
4.6.0
MySession with self.logger
upd type hints
4.5.0
login: detect '2fa required' reason 
4.4.0
process_account: use basic_get_date_from
4.3.0
fix login(): new _get_host()
4.2.0
updated current URL: now unicajabanco.es
4.1.0
basic_movements_scraped_from_movements_parsed: new format of the result 
4.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
3.0.0
basic_movements_scraped_from_movements_parsed
OperationalDatePosition, KeyValue support
2.1.0
basic_upload_movements_scraped
2.0.0
multicontract
1.3.0
handle cases:
    no movements
    another home page
    err parsing resp to excel
1.2.0
parse helpers: fixed org name
explicit handling exc of xls processing for debugging
1.1.1
fix parse_helpers.get_organization_title - correct regexp 
1.1.0
current_ordering=custom_types.MOVEMENTS_ORDERING_TYPE_ASC
1.0.1
scraper_name
"""

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'unicaja_encrypter.js'
))

IS_LOGGED_MARKERS = ['mero de cuenta', 'Titular contrato', 'Listado de contratos']

DOUBLE_AUTH_MARKERS = [
    'MEDIANTE CLAVE DE SEGURIDAD',
    'Esta operación requiere autenticación reforzada'
]


class UnicajaScraper(BasicScraper):
    scraper_name = 'UnicajaScraper'

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

    # to redefine from child
    def _get_host(self) -> str:
        return 'https://areaprivada.unicajabanco.es'

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()

        resp1 = s.get(
            '{}/PortalServlet'.format(self._get_host()),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # js redirect to
        req2_url_raw = extract.re_first_or_blank('url=(.*?)"', resp1.text)

        # resp1.url = "https://areaprivada.unicajabanco.es/PortalServlet?menu0=particulares&pag=1110902071492"
        req2_url = urllib.parse.urljoin(resp1.url, req2_url_raw)

        resp2 = s.get(
            req2_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        clave_des_enc_param = extract.re_first_or_blank('var claveDES = "(.*?)";', resp2.text)
        pag_param = extract.re_first_or_blank(r'pag=(\d+)', resp2.url)

        if not (clave_des_enc_param and pag_param):
            return s, resp2, False, False, "Can't get correct clave_des_enc_param, pag_param"

        password_param = self._get_encrypted(clave_des_enc_param)

        req3_url = '{}/univia/servlet/ConnectionServlet'.format(self._get_host())

        req3_params = {
            'user': '',
            'clave': '',
            'x': str(42 + random.randint(0, 10)),
            'y': str(9 + random.randint(0, 5)),
            'usuario': self.username,
            'password': password_param,
            'tipoPeticion': '1',
            'p': '1',
            'pag': pag_param,
            'tipoTeclado': 'V'
        }

        resp3 = s.post(
            req3_url,
            data=req3_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = any(marker in resp3.text for marker in IS_LOGGED_MARKERS)
        is_credentials_error = 'CODIGO DE USUARIO O CLAVE DE ACCESO ERRONEA'.lower() in resp3.text.lower()
        reason = ''
        if any(m in resp3.text for m in DOUBLE_AUTH_MARKERS):
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        # -a 31035 will be redirected to another portal: univia.unicajabanco.es
        # So, let's detect 'is_logged' by the url
        # (no useful details in the resp, but will be redirected only on successful login)
        # Then, it's still possible to use areaprivada.unicajabanco.es
        # to extract account/movement information
        if not is_logged:
            is_logged = 'univia.unicajabanco.es' in resp3.url

        return s, resp3, is_logged, is_credentials_error, reason

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        # no need to open contracts list page https://www.unicajabanco.es/univia/servlet/ControlServlet?o=cambioCon&p=1

        contracts_nums = parse_helpers.get_contracts(resp_logged_in.text)
        if not contracts_nums:
            # one contract
            self.process_contract(s, resp_logged_in, '0', is_several_contracts=False)
        else:
            self.logger.info('Got several contracts: {}'.format(contracts_nums))
            # multicontract
            if project_settings.IS_CONCURRENT_SCRAPING:
                with futures.ThreadPoolExecutor(max_workers=16) as executor:

                    futures_dict = {
                        executor.submit(self.process_contract, s,
                                        resp_logged_in, contract_num, True): contract_num
                        for contract_num in contracts_nums
                    }

                    self.logger.log_futures_exc('process_contract', futures_dict)
            else:
                for contract_num in contracts_nums:
                    self.process_contract(s, resp_logged_in, contract_num, is_several_contracts=True)

        return True

    def get_account_scraped(
            self,
            s: MySession,
            resp: Response) -> Tuple[MySession, Response, List[AccountScraped], str]:
        # first open Empresas -> Tesoreria -> Mi Tesoreria (Mis cueantas)
        resp_accounts_url = ('{}/univia/servlet/ControlServlet?o=lcta&p=1&M1=empr-tesoreria&M2=mi-tesoreria'
                             '&M3=consultas-mis-cuentas&M4=mis-cuentas-tesoreria'.format(self._get_host()))

        resp_accounts = s.get(
            resp_accounts_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        organization_title = parse_helpers.get_organization_title(resp_accounts.text)
        accounts_parsed = parse_helpers.get_accounts_parsed(resp_accounts.text)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(organization_title, acc_parsed)
            for acc_parsed in accounts_parsed
        ]

        return s, resp_accounts, accounts_scraped, organization_title

    def process_account(self, s: MySession, resp: Response, account_scraped: AccountScraped) -> bool:

        account_no = account_scraped.AccountNo
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        # open movements filter page first to get necessary post param
        req1_url = ('{}/univia/servlet/ControlServlet?o=csbcta&p=1&M1=operacion'
                    '&M2=cuentas&M3=cuentas-consultas&M4=cuentas-movcsb'.format(self._get_host()))

        resp1 = s.get(
            req1_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        ppp_param = parse_helpers.get_ppp_param_for_account_processing(resp1.text,
                                                                       account_scraped.FinancialEntityAccountId)

        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        d_from, m_from, y_from = date_from_str.split('/')
        d_to, m_to, y_to = self.date_to_str.split('/')

        req2_url = '{}/univia/servlet/ControlServlet'.format(self._get_host())

        req2_params = {
            'p': 5,  # excel
            'numMovDesdeSiguiente': 1,
            'discriminante': '00',
            'ppp': ppp_param,
            'o': 'nmcta',
            'x': 39 + random.randint(0, 10),
            'y': 14 + random.randint(0, 6),
            'diaDesde': d_from,
            'mesDesde': m_from,
            'anoDesde': y_from,
            'diaHasta': d_to,
            'mesHasta': m_to,
            'anoHasta': y_to,
        }

        resp2 = s.post(
            req2_url,
            data=req2_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            stream=True  # download file
        )

        movements_parsed, error = parse_helpers.get_movements_parsed_from_excel_resp(resp2)
        # Soft error just to send notifications
        if error:
            self.logger.error(error)

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

    def _upload_accounts_scraped(self, accounts_scraped: List[AccountScraped]):
        """Can override in children"""
        self.basic_upload_accounts_scraped(accounts_scraped)

    def process_contract(self,
                         s: MySession,
                         resp_logged_in: Response,
                         contract_num: str,
                         is_several_contracts: bool) -> bool:

        self.logger.info('Process contract #{}'.format(contract_num))

        if is_several_contracts:

            s, resp_logged_in, is_logged, is_credentials_error, _reason = self.login()
            if not is_logged:
                self.logger.error('Not logged in during contract {} processing. Exit'.format(contract_num))
                return False

            req_contract_home_url = '{}/univia/servlet/ConnectionServlet?tipoPeticion=3&numContrato={}'.format(
                self._get_host(),
                contract_num
            )
            resp_contract_home = s.get(
                req_contract_home_url,
                headers=self.req_headers,
                proxies=self.req_proxies
            )
        else:
            resp_contract_home = resp_logged_in

        s, resp_accs, accounts_scraped, organization_title = self.get_account_scraped(s, resp_contract_home)

        self.logger.info('Contract #{} ({}) has {} accounts: {}'.format(
            contract_num,
            organization_title,
            len(accounts_scraped),
            accounts_scraped
        ))

        self._upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('Contract #{}: GET BALANCES'.format(contract_num))

        # get and save movements
        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=16) as executor:

                futures_dict = {
                    executor.submit(self.process_account, s, resp_accs, account_scraped):
                        account_scraped.AccountNo
                    for account_scraped in accounts_scraped
                }

                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_scraped in accounts_scraped:
                self.process_account(s, resp_accs, account_scraped)

        self.download_correspondence(s, resp_logged_in, organization_title)

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
        self.process_access(s, resp_logged_in)
        self.basic_log_time_spent('GET ALL MOVEMENTS')

        return self.basic_result_success()
