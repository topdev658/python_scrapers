import json
import os
import random
import subprocess
from base64 import b64decode
from collections import OrderedDict
from typing import Tuple, List

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (ScraperParamsCommon, MainResult, AccountScraped, MovementParsed,
                                  DOUBLE_AUTH_REQUIRED_TYPE_COMMON)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from .custom_types import Contract

__version__ = '2.0.0'
__changelog__ = """
2.0.0 2023.10.11
login: fixed new calls including getting value for cookie TSd4417f47075 from f5_encrypted.js
1.2.0 2023.06.28
created CREDENTIALS_ERROR_CODE and DOUBLE_AUTH_CODE
login: managed new credential error code 
1.1.0
login: added login error code for double auth
1.0.0
init
"""

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'eurocaja_rural_encrypter.js'
))

CALL_JS_ENCRYPT_LIB_FOR_COOKIE = 'node --use-strict {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'eurocaja_rural',
    'f5_encrypted.js'
))

CREDENTIALS_ERROR_CODE = '9103'

DOUBLE_AUTH_CODE = '0936'


class EurocajaRuralScraper(BasicScraper):
    scraper_name = 'EurocajaRuralScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.update_inactive_accounts = False
        self.req_headers = self.basic_req_headers_updated({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en,es-ES;q=0.8,es;q=0.5,en-US;q=0.3',
            'Connection': 'keep-alive',
            'Host': 'banking.eurocajarural.es',
            'Referer': 'https://eurocajarural.es/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        })

    def _get_encrypted(self, clave: str) -> str:
        cmd = '{} "{}" "{}"'.format(CALL_JS_ENCRYPT_LIB, clave, self.userpass)
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def _get_encrypted_cookie(self, *params) -> str:
        cmd = '{} "{}" "{}" "{}" '.format(CALL_JS_ENCRYPT_LIB_FOR_COOKIE, params[0], params[1], params[2])
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def _resp_json_decoded(self, resp: Response) -> Tuple[bool, dict]:
        resp_data_bytes = resp.json().get('dtsr', '').encode()
        if not resp_data_bytes:
            return False, {}

        decoded_bytes = b64decode(resp_data_bytes + b'========')
        data_str = (b'{' + decoded_bytes + b'}').decode()
        data_dict = json.loads(data_str)['datosCliente']
        return True, data_dict

    def _get_jsessionid(self, s: MySession) -> str:
        """Returns JSESSIONID for specific subdomain"""
        cookie = [
            c for c in s.cookies
            if c.domain == 'banking.eurocajarural.es' and c.name == 'JSESSIONID'
        ][0]
        return cookie.value

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()

        _resp_login_page = s.get(
            'https://banking.eurocajarural.es/3081/3081/#/beext/identificacion',
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        req_url_js = parse_helpers.get_url_login_js(_resp_login_page.text)

        _resp_login_page_js = s.get(
            'https://banking.eurocajarural.es' + req_url_js,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        # Necessary params to get encrypted cookie "TSc7f0f12a075" related to F5 Network anti-bot techniques
        bobcmn, con, secret = parse_helpers.get_encrypted_cookie_params(_resp_login_page.text, _resp_login_page_js.text)
        cookie = self._get_encrypted_cookie(bobcmn, con, secret)
        s.cookies.set('TSc7f0f12a075', cookie)
        _resp_login_page2 = s.get(
            'https://banking.eurocajarural.es/3081/3081/',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        aleatorioidensello_param = str(int(random.uniform(1000000000, 9999999999)))

        req_inicio_cello_params = {
            'CAJA': '3081',
            'CAMINO': '3081',
            'IDIOMA': '01',
            'ALEATORIOIDENSELLO': aleatorioidensello_param,
        }
        resp_inicio_cello = s.post(
            'https://banking.eurocajarural.es/BEWeb/3081/3081/inicio_identificacion_sello.action',
            data=req_inicio_cello_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        resp_inicio_cello_json = resp_inicio_cello.json()

        sello_param = resp_inicio_cello_json['sello']

        clave = resp_inicio_cello_json['claveCalcula']
        encrypted = self._get_encrypted(clave)

        req_login_params = OrderedDict([
            ('SELLO', sello_param),
            ('OPERACION', '0002'),
            ('BROKER', 'NO2'),
            ('PINV3', 'si'),
            ('PIN', encrypted),  # '83ecc45223b7984677518da8fd059e2c'
            ('PAN', '9999993081'),
            ('PANENT', self.username)
        ])

        resp_logged_in = s.post(
            "https://banking.eurocajarural.es/BEWeb/3081/3081/identificacion.action?CAJA=3081&CAMINO=3081&IDIOMA=01",
            data=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        resp_logged_in_json = resp_logged_in.json()

        is_logged = resp_logged_in_json.get('resultado', '') == 'OK'

        # "codigoerror": "9103",
        # "errorLogin": "Algo ha ido mal, asegúrate que has introducido correctamente tus datos."
        is_credentials_error = resp_logged_in_json.get('codigoerror', '') == CREDENTIALS_ERROR_CODE
        reason = ''

        # 'codigoerror': '0936',
        # 'textoerror': 'LA OPERATIVA REQUIERE FIRMA'
        if resp_logged_in_json.get('codigoerror', '') == DOUBLE_AUTH_CODE:
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        ok, resp_logged_in_decoded = self._resp_json_decoded(resp_logged_in)
        if not ok:
            self.basic_log_wrong_layout(resp_logged_in, "Can't get resp_logged_in_decoded")
            return False
        contracts = parse_helpers.get_contracts(resp_logged_in_decoded)
        self.logger.info('Got {} contracts: {}'.format(
            len(contracts),
            contracts
        ))

        for contract in contracts:
            self.process_contract(s, contract)

    def process_contract(self, s: MySession, contract: Contract):
        self.logger.info('Process contract {}'.format(
            contract.org_title
        ))

        req_accounts_param = OrderedDict([
            ('FIT_CTT_NOMBRE_CONTRATO', contract.org_title),  # 'HIPERMADERA TALAVERA S.L.'
            ('FIT_CTT_CONTRATO', contract.id),  # 'F4JWC'
            ('FIT_CTT_CONTRATO_CAJA', contract.nif),  # '****3343**'
            ('OPERACION', 'selContrato')
        ])

        resp_accounts = s.post(
            'https://banking.eurocajarural.es/BEWeb/3081/3081/noperCadenaSBE_d_ngCadenaSBE.action;'
            'jsessionid={}?CAJA=3081&CAMINO=3081&IDIOMA=01'.format(self._get_jsessionid(s)),
            data=req_accounts_param,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        ok, resp_accounts_decoded = self._resp_json_decoded(resp_accounts)
        if not ok:
            self.basic_log_wrong_layout(resp_accounts, "Can't get resp_accounts_decoded")
            return False

        accounts_parsed = parse_helpers.get_accounts_parsed(resp_accounts_decoded)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                contract.org_title,
                account_parsed,
            )
            for account_parsed in accounts_parsed
        ]

        self.logger.info('{}: got {} accounts: {}'.format(
            contract.org_title,
            len(accounts_scraped),
            accounts_scraped
        ))
        self.basic_log_time_spent('GET ACCOUNTS')
        self.basic_upload_accounts_scraped(accounts_scraped)

        for account_scraped in accounts_scraped:
            self.process_account(s, contract, account_scraped)

        return True

    def process_account(self, s: MySession, contract: Contract, account_scraped: AccountScraped):

        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from, date_from_str = self.basic_get_date_from_dt(fin_ent_account_id)
        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        req_movs_params = OrderedDict([
            ('OPERACION', '2992'),
            ('GCUENTA', fin_ent_account_id),  # '30810102340000111105194920'
            ('FECINI', date_from.strftime('%Y-%m-%d')),  # '2022-06-01'
            ('FECFIN', self.date_to.strftime('%Y-%m-%d')),
            ('TIPOMOV', '')
        ])

        movements_parsed = []  # type: List[MovementParsed]

        for page_ix in range(1, 101):
            self.logger.info('{}: page #{}: get movements'.format(fin_ent_account_id, page_ix))
            resp_movs_i = s.post(
                'https://banking.eurocajarural.es/BEWeb/3081/3081/oper2992_d_ngJsonSeg.action;'
                'jsessionid={}?CAJA=3081&CAMINO=3081&IDIOMA=01'.format(self._get_jsessionid(s)),
                data=req_movs_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            ok, resp_movs_i_json = self.basic_get_resp_json(
                resp_movs_i,
                err_msg="Can't get resp_movs_decoded"
            )  # no need to decode
            if not ok:
                break  # already reported

            movs_parsed_i = parse_helpers.get_movements_parsed(resp_movs_i_json)
            movements_parsed.extend(movs_parsed_i)

            pagination_key = resp_movs_i_json.get('PAGINATIONKEY')
            if not pagination_key:
                self.logger.info('{}: no more pages'.format(fin_ent_account_id))
                break

            req_movs_params['REANUDACION'] = pagination_key  # for the next page

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        return True

    def main(self) -> MainResult:

        self.logger.info('main: started')

        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()
        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp_logged_in.url, resp_logged_in.text, reason)
        self.basic_log_time_spent('GET ALL BALANCES AND MOVEMENTS')

        self.process_access(s, resp_logged_in)

        return self.basic_result_success()
