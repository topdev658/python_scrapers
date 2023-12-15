import os
import time
import subprocess
import urllib.parse
from collections import OrderedDict
from typing import Dict, List, Tuple

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    AccountParsed, AccountScraped, MOVEMENTS_ORDERING_TYPE_DESC,
    MovementParsed, ScraperParamsCommon, MainResult,
    DOUBLE_AUTH_REQUIRED_TYPE_OTP, BLOCKED_USER_TYPE_COMMON
)
from scrapers.caixa_geral.caixa_geral_scraper import CaixaGeralScraper
from scrapers.caja_ingenieros_scraper_from_caixa_geral import (
    parse_helpers as ci_parse_helpers
)

__version__ = '3.2.0'

__changelog__ = """
3.2.0 2023.09.27
login: managed blocked user  
3.1.0 2023.09.26
CALL_JS_ENCRYPT_LIB_FOR_COOKIE added --use-strict to execute f5_encryted.js with node 4.2.6 at 
linux server and prevent error 'Block-scoped declarations not yet supported outside strict mode' 
throwed by 'let' declaration 
3.0.0 2023.09.26
login: fixed new calls including geting value for cookie TSd4417f47075 from f5_encrypted.js
2.0.0 2023.04.24
_scrape_and_get_movements_parsed: get movements information from html instead EXCEL,
added pagination, more movements button and retrieve href for PDF document download. 
1.11.0
_scrape_and_get_movements_parsed: req timeout = 60
1.10.0
use account-level result_codes
1.9.0
call basic_upload_movements_scraped with date_from_str
1.8.0
double auth detector
1.7.0
use basic_new_session
upd type hints
1.6.0
process_account: use _check_selected_account
_get_selected_account_id
parse_helpers: get_selected_account_id
1.5.0
login: fixed returned vars on cred err
more type hints
use basic_get_date_from
upd credentials error detection
1.4.0
mov excel manual params (previous were parsed from the resp)
1.3.0
basic_movements_scraped_from_movements_parsed: new format of the result 
1.2.0
can scrape more than MAX_MOVEMENTS_PER_REQUEST (150 now)
1.1.2
removed commented code
updated comments
1.1.1
failed attempt warning msg (not error)
1.1.0
removed company_title - use default
removed manual req_mov_excel_params
1.0.0
Inherits many from CaixaGeralScraper
"""

CALL_JS_ENCRYPT_LIB_FOR_PASSWORD = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'caja_ingenieros',
    'encode.js'
))

CALL_JS_ENCRYPT_LIB_FOR_COOKIE = 'node --use-strict {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'caja_ingenieros',
    'f5_encrypted.js'
))

MAX_MOVEMENTS_PER_REQUEST = 150
CREDENTIALS_ERROR_MARKERS = [
    'El código de usuario o clave de acceso son erróneos',
    'Usuario o clave incorrecto'
]

DOUBLE_AUTH_MARKER = 'SMS firma'

BLOCKED_USER_MARKERS = [
    'Tu Banca ONLINE/MOBILE se ha bloqueado por excesivos intentos de clave de acceso errónea'
]

class CajaIngenierosScraper(CaixaGeralScraper):
    """Inherits basic approach from CaixaGeralScraper (caja, camino params, auth encrypter),
    but redefines all scraping methods (include main)
    Only serial scrapng allowed"""

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='CajaIngenierosScraper',
                 website='https://be.caja-ingenieros.es',
                 camino_param='6025',
                 caja_param='3025') -> None:
        self.req_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
            'Connection': 'keep-alive',
        }

        super().__init__(scraper_params_common,
                         proxies,
                         scraper_name,
                         website,
                         camino_param,
                         caja_param)

    def _auth_url(self) -> str:
        return '{}/BEWeb/{}/{}/'.format(self.website, self.caja_param, self.camino_param)

    def _authreq_post_params(self, pin: str, sello_param: str, random_param: str) -> Dict[str, str]:
        return {
            'PAN': str(self.username).upper(),
            'PIN': pin,
            'OPERACION': '0002',
            'IDIOMA': '01',
            'CAJA': self.caja_param,
            'SELLO': sello_param,
            'IDEN': '',
            'PINV2': 'si',
            'NUMV': pin,
            'INILOGIN': 'S',
            'PUESTO': ['', ''],
            'OPERADOR': ['', ''],
            'EASYCODE': ['', ''],
            'BROKER': 'SI',
            'OPGENERICA': ['', ''],
            'GENERICA': 'S',
            'DEDONDE': ['GENE', 'GENE'],
            'ACCSS': 'FUSION',
            'REFDESDE': ['', ''],
            'RANDOM': random_param,
            'PERR_AUX': ''
        }

    def _get_encrypted_pass(self, params) -> str:
        cmd = '{} "{}" "{}" "{}"'.format(CALL_JS_ENCRYPT_LIB_FOR_PASSWORD, params[0], params[1], params[2])
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def _get_encrypted_cookie(self, *params) -> str:
        cmd = '{} "{}" "{}" "{}" '.format(CALL_JS_ENCRYPT_LIB_FOR_COOKIE, params[0], params[1], params[2])
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted


    def _movreq_post_params(self, basic_params: dict, date_from_str: str, date_to_str: str) -> dict:
        params = basic_params.copy()

        date_from_str_wo_slashes = date_from_str.replace('/', '')
        date_to_str_wo_slashes = date_to_str.replace('/', '')

        params['fecha-ini'] = date_from_str
        params['FINI'] = date_from_str_wo_slashes
        params['fecha-fin'] = self.date_to_str
        params['FFIN'] = date_to_str_wo_slashes
        params['FDES'] = date_from_str_wo_slashes
        params['FHAS'] = date_to_str_wo_slashes
        params['orden'] = 'ascendente'  # should be by default, but we repeat to be sure
        params['periodo'] = 'entrefechas'  # should be by default, but we repeat to be sure
        return params

    def login(self) -> Tuple[MySession, Response, bool, bool, str, str, str]:
        """:return (s, resp_logged_in, is_logged, is_cred_err, reason, llamada_par, cliente_par"""
        s = self.basic_new_session()
        # resp = s.get(
        #     url='https://www.caixaenginyers.com/es/',
        #     headers=self.req_headers,
        #     proxies=self.req_proxies,
        # )

        # to get cookies
        params = {
            'DEDONDE': 'GENE',
            'IDIOMA': '02'
        }
        resp1 = s.get(
            url=self._auth_url() + 'CABEm_0_fusionRestyling.action',
            headers=self.req_headers,
            params=params,
            proxies=self.req_proxies,
        )

        referer = str(resp1.url)

        random_param = extract.re_first_or_blank(r'(?s)<input\s*.*?name="RANDOM"\s*.*?value="(.*?)"', resp1.text)
        req2_url = extract.re_first_or_blank('urlSello2 = \"(.+)\"', resp1.text)
        req3_url = extract.re_first_or_blank('action=\"(.+?)\"', resp1.text)

        resp2 = s.get(
            url=self.website + req2_url,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        sello = extract.re_first_or_blank('<SELLO>(.*?)</SELLO>', resp2.text)
        clave_calcula_param = extract.re_first_or_blank('<CLAVE>(.*?)</CLAVE>', resp2.text)

        req_params = clave_calcula_param.split('|')
        req_params.append(self.userpass)
        pin = self._get_encrypted_pass(req_params)

        # {'PUESTO': '', 'CAJA': '3025', 'EASYCODE': '', 'DEDONDE': '', 'IDIOMA': '01', 'ACCSS': 'FUSION',
        # 'OPERADOR': '', 'NUMV': '4a032b20793f0a3cf69ca0c771649cbe', 'PINV2': 'si', 'PAN': 'F5509136701',
        # 'IDEN': '', 'PIN': '4a032b20793f0a3cf69ca0c771649cbe', 'SELLO': '2018.06.08.14.19.54', 'BROKER': 'SI',
        # 'OPERACION': '0002'}
        req3_params = self._authreq_post_params(pin, sello, random_param)
        resp3 = s.post(
            url=self.website + req3_url,
            data=req3_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        self.req_headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            'Referer': referer
        })

        bobcmn = extract.re_first_or_blank('bobcmn\".*?\"(.*?)\"', resp3.text)
        con = extract.re_first_or_blank('\"(0.*?)\"', resp3.text)
        req_url_js = extract.re_first_or_blank('type="text/javascript" src="(.*?)"',resp3.text)
        resp4 = s.get(
            url=urllib.parse.urljoin(self.website, req_url_js),
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        secret = extract.re_first_or_blank(r'(?s)delete Number.*?\"(.*?)\"',resp4.text)
        cookie = self._get_encrypted_cookie(bobcmn, con, secret)
        s.cookies.set('TSd4417f47075', cookie)

        reason = ''
        # {'PUESTO': '', 'BROKER': 'SI', 'ACCSS': 'FUSION', 'DESCGENE': '', 'CAJA': '3025', 'LLAMADA':
        # 'D242A7X0C750W0X5C0C4', 'DEDONDE': '', 'OPERACION': 'FSETM', 'IDIOMA': '01', 'OPERAC': '0000', 'IDEN': '',
        # 'OPERACREAL': '', 'CTASEL': '', 'CLIENTE': '3025146996', 'OPEINI2': '', 'SELLO': '2018.06.08.14.22.02',
        # 'OPEINI': '', 'CTAFOR': '', 'OPERADOR': '', 'NUMV': '33f537d08ec6f9496a784c573b9e8497', 'EASYCODE': ''}
        req5_data = resp3.request.body
        resp5 = s.post(
            url=resp3.url,
            headers=self.req_headers,
            files={'_pd': req5_data}
        )
        if (any(m in resp5.text for m in BLOCKED_USER_MARKERS)):
            reason = BLOCKED_USER_TYPE_COMMON
            is_logged = False
            is_credentials_error = False
            return s, resp5, is_logged, is_credentials_error, reason, '', ''

        req6_href, req6_params = extract.build_req_params_from_form_html(resp5.text, 'Cliente')
        req6_url = urllib.parse.urljoin(self._auth_url(), req6_href)
        resp6 = s.post(
            req6_url,
            data=req6_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        supframebe_url = extract.re_first_or_blank(r'(?si)<frame.*?supframeBE.*?src="(.*?)"', resp6.text)
        req7_url = urllib.parse.urljoin(self.website, supframebe_url)
        resp7 = s.get(
            url=req7_url,
            headers=self.req_headers,
        )

        if 'psFSETm_COMUN.action' not in req6_url:
            is_logged = False
            is_credentials_error = any(m in resp4.text for m in CREDENTIALS_ERROR_MARKERS)
            if DOUBLE_AUTH_MARKER in resp6.text:
                reason = DOUBLE_AUTH_REQUIRED_TYPE_OTP
            return s, resp6, is_logged, is_credentials_error, reason, '', ''

        is_logged = 'not0000_m_0TRE' in resp6.text
        is_credentials_error = any(m in resp6.text for m in CREDENTIALS_ERROR_MARKERS)
        if DOUBLE_AUTH_MARKER in resp6.text:
            reason = DOUBLE_AUTH_REQUIRED_TYPE_OTP

        llamada_param = req6_params['LLAMADA']
        cliente_param = req6_params['CLIENTE']

        return s, resp6, is_logged, is_credentials_error, reason, llamada_param, cliente_param

    # Implemented request to get contract but not used.
    # It will be the beginning for contract switching.
    def get_contracts(self, cliente_param, llamada_param, resp4, s):
        req_href = extract.re_first_or_blank('(?si)not0000_m_0TRE.*?\?', resp4.text).replace('\?', '')
        req_url = urllib.parse.urljoin(self._auth_url(), req_href)
        req_contracts_params = {
            "OPERACION": "not0000_m_0TRE",
            "IDIOMA": "02",
            "OPERAC": "1004",
            "LLAMADA": llamada_param,
            "CLIENTE": cliente_param,
            "CAJA": self.caja_param,
            "CAMINO": self.camino_param,
            "DATOPEINI2": "",
            "DATOSOPEINI": "",
            "DESCGENE": "",
            "DEDONDE": "GENE",
            "OPGENERICA": "",
            "ACCSS": "FUSION",
            "APN": "no",
            "REFDESDE": "",
            "certBody": "",
            "INILOGIN": "S",
            "IGNORA_TEST": ""
        }
        resp_contracts = s.post(
            req_url,
            data=req_contracts_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

    def _get_accounts_parsed(
            self,
            s: MySession,
            resp_logged_in: Response,
            llamada_param: str,
            cliente_param: str) -> List[AccountParsed]:
        company_title = ''

        # https://be.caja-ingenieros.es/BEWeb/3025/6025/not7327_d_0GNRL.action;jsessionid
        # =4198EDA7C430EE17131089BB95D7E11B.lima
        req_position_global_url = self._auth_url() + 'not7327_d_0GNRL.action'

        req_position_global_params = {
            'LLAMADA': llamada_param,
            'CLIENTE': cliente_param,
            'IDIOMA': '01',
            'CAJA': self.caja_param,
            'OPERAC': '1004',
            'CTASEL': '',
            'CTAFOR': '',
            'CAMINO': self.camino_param,
            'OPERACION': 'PSGL',
            'OPERACREAL': '7327',
            'CODREANUDA': '',  # ++++++++++++++++++++ in the raw req params
            'TIPE': '2',
            'DEDONDE': 'PSGL'
        }

        resp_position_global = s.post(
            req_position_global_url,
            data=req_position_global_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_parsed = ci_parse_helpers.get_accounts_parsed(resp_position_global.text, self.logger)
        return accounts_parsed

    def get_accounts_scraped(
            self,
            s: MySession,
            resp_logged_in: Response,
            llamada_param: str,
            cliente_param: str) -> Tuple[MySession, List[AccountParsed], List[AccountScraped]]:

        self.logger.info('get_accounts_scraped: start')
        accounts_parsed = self._get_accounts_parsed(s, resp_logged_in, llamada_param, cliente_param)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                self.db_customer_name,
                account_parsed,
                is_default_organization=True
            )
            for account_parsed in accounts_parsed
        ]

        self.logger.info('get_accounts_scraped: extracted {}'.format(accounts_scraped))

        return s, accounts_parsed, accounts_scraped

    def _get_selected_account_id(self, resp_text: str) -> str:
        """Set specific function here, can redefine in a child"""
        return ci_parse_helpers.get_selected_account_id(resp_text)

    # renamed to avoid shadowing of _get_movements_parsed of parent class_
    def _scrape_and_get_movements_parsed(
            self,
            s: MySession,
            resp_logged_in: Response,
            account_parsed: AccountParsed,
            date_from_str: str,
            date_to_str: str) -> Tuple[List[MovementParsed], bool]:
        account_no = account_parsed['account_no']
        fin_ent_account_id = account_parsed['financial_entity_account_id']

        self.basic_log_process_account(account_no, date_from_str, date_to_str=date_to_str)

        # Paginated html list
        req_mov_url = urllib.parse.urljoin(resp_logged_in.url, account_parsed['mov_req_url_raw'])
        req_mov_params = self._movreq_post_params(account_parsed['mov_req_params'], date_from_str, date_to_str)

        time.sleep(5)

        req_mov_table_params_manual = OrderedDict([
            ('LLAMADA', req_mov_params['LLAMADA']),
            ('CLIENTE', req_mov_params['CLIENTE']),
            ('IDIOMA', '01'),
            ('CAJA', '3025'),
            ('OPERAC', '8490'),
            ('CTASEL', ''),
            ('CTAFOR', ''),
            ('CODRETROCESO', ''),
            ('MODO_INTERMEDIO', ''),
            ('PAGINAACTUAL', ''),
            ('fecha-fin', date_to_str),
            ('FHAS', req_mov_params['FHAS']),
            ('FFIN', req_mov_params['FFIN']),
            ('orden', 'ascendente'),
            ('datosEnvioSeleccion', ''),
            ('FINI', req_mov_params['FINI']),
            ('PAGINAANTERIOR', ''),
            ('CAPITAL', ''),
            ('periodo', 'entrefechas'),
            ('NCTA', req_mov_params['NCTA']),
            ('cuentaFormateadaGCUENTA', req_mov_params['cuentaFormateadaGCUENTA']),
            ('FDES', req_mov_params['FDES']),
            ('GCUENTA', req_mov_params['GCUENTA']),
            ('CODAVANCE', ''),
            ('TIENEFILTRO', 'S'),
            ('fecha-ini', date_from_str),
        ])

        # Several attempts to get correct response w/ movements
        is_no_movements_sign = False
        # resp_mov_excel = Response()
        # max 150 movements since date_from
        resp_mov_table = s.post(
            # req_mov_excel_url,
            "https://be.caja-ingenieros.es/BEWeb/3025/6025/not9765_d_0GNRL.action",
            data=req_mov_table_params_manual,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=30
        )

        if 'NO EXISTEN MOVIMIENTOS EN LAS FECHAS SOLICITADAS' in resp_mov_table.text:
            self.logger.info("Got 'no movements' message")
            is_no_movements_sign = True
            self.logger.error("{}: No movements:\n{}".format(
                fin_ent_account_id,
                resp_mov_table,
            ))
            return [], False

        if is_no_movements_sign:
            movements_parsed = []  # type: List[MovementParsed]

        else:
            movements_parsed = ci_parse_helpers.get_movements_parsed(
                resp_mov_table.text,
                fin_ent_account_id,
                self.logger
            )

            if 'Ver más movimientos' in resp_mov_table.text:
                more_movements_param = "002"
                paginator = "001"
                while more_movements_param:
                    req_headers = self.req_headers.copy()
                    req_headers['Content-Type'] = 'application/x-www-form-urlencoded'
                    req_headers['Accept'] = '*/*'
                    req_headers['Accept-Encoding'] = 'gzip, deflate, br'

                    req_mov_more_str = 'LLAMADA={}&' \
                                        'CLIENTE={}&' \
                                        'IDIOMA=01&' \
                                        'CAJA=3025&' \
                                        'OPERAC=9765&' \
                                        'CTASEL=&' \
                                        'CTAFOR=&' \
                                        'NCTA={}&' \
                                        'GCUENTA={}&' \
                                        'cuentaFormateadaGCUENTA={}&' \
                                        'FINI={}' \
                                        '&FFIN={}' \
                                        '&CAPITAL=&' \
                                        'TIENEFILTRO=N&datosEnvioSeleccion=&' \
                                        'CODAVANCE={}' \
                                        '&CODRETROCESO=&' \
                                        'PAGINAACTUAL={}&' \
                                        'PAGINAANTERIOR={}&' \
                                        'NOPE=&' \
                                        '=Ver+más+movimientos&' \
                                        'CODREANUDA=+{}'.format(
                        req_mov_params['LLAMADA'],
                        req_mov_params['CLIENTE'],
                        req_mov_params['NCTA'],
                        req_mov_params['GCUENTA'],
                        req_mov_params['cuentaFormateadaGCUENTA'],
                        req_mov_params['FINI'],
                        req_mov_params['FFIN'],
                        more_movements_param,
                        paginator,
                        paginator,
                        more_movements_param
                    )

                    resp_mov_more = s.post(
                        "https://be.caja-ingenieros.es/BEWeb/3025/6025/vrsnot9765_d_AJX_0AJX.action",
                        data=req_mov_more_str,
                        headers=req_headers,
                        proxies=self.req_proxies,
                    )

                    resp_mov_more_str = resp_mov_more.text\
                        .replace('\r', '')\
                        .replace('\n', '')\
                        .replace('\t', '')\
                        .replace('\\t', '').replace('\\n', '').replace('\\r', '')

                    old_movements_parsed, more_movements_param, paginator = ci_parse_helpers.parse_more_movements(resp_mov_more_str, fin_ent_account_id, self.logger)
                    movements_parsed.extend(old_movements_parsed)

                    if len(movements_parsed) >= MAX_MOVEMENTS_PER_REQUEST:
                        break

        return movements_parsed, True

    def process_account(
            self,
            s: MySession,
            resp_logged_in: Response,
            account_parsed: AccountParsed) -> bool:

        account_no = account_parsed['account_no']
        fin_ent_account_id = account_parsed['financial_entity_account_id']

        date_to_str = self.date_to_str  # will be changed on next loop step
        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        # Scrape several times to get all movements
        # loop w/ changing date_from, date_to
        movements_parsed = []  # type: List[MovementParsed]
        while True:
            movements_parsed_loop_step, is_success = self._scrape_and_get_movements_parsed(
                s,
                resp_logged_in,
                account_parsed,
                date_from_str,
                date_to_str
            )
            # may bring integrity error in rare cases
            # if happens, use contains.uniq_tail
            for mov in movements_parsed_loop_step:
                if mov not in movements_parsed:
                    movements_parsed.append(mov)

            if len(movements_parsed_loop_step) >= MAX_MOVEMENTS_PER_REQUEST:
                date_to_str = movements_parsed_loop_step[-1]['operation_date']
                continue

            break

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_DESC
        )

        account_scraped = self.basic_account_scraped_from_account_parsed(self.db_customer_name, account_parsed)
        self.basic_log_process_account(account_no, date_from_str, movements_scraped)
        ok = self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        if ok:
            movements_parsed_asc = movements_parsed[::-1]
            self.download_receipts(
                s,
                account_scraped,
                movements_scraped,
                movements_parsed_asc
            )
        return is_success

    def main(self) -> MainResult:

        s, resp_logged_in, is_logged, is_credentials_error, reason, self.llamada_param, self.cliente_param = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        s, accounts_parsed, accounts_scraped = self.get_accounts_scraped(
            s,
            resp_logged_in,
            self.llamada_param,
            self.cliente_param
        )

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        # only serial processing allowed
        for account_parsed in accounts_parsed:
            self.process_account(s, resp_logged_in, account_parsed)

        self.basic_log_time_spent('GET MOVEMENTS')
        ok = self.download_correspondence(s)
        return self.basic_result_success()
