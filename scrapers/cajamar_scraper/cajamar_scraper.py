import datetime
import os
import random
import re
import subprocess
import time
from collections import OrderedDict
from concurrent import futures
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin

from custom_libs import date_funcs
from custom_libs import requests_helpers
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, MOVEMENTS_ORDERING_TYPE_ASC, DOUBLE_AUTH_REQUIRED_TYPE_COMMON,
    MovementParsed, ScraperParamsCommon, MainResult, PASSWORD_CHANGE_TYPE_COMMON
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from .environ_cookies import ENVIRON_COOKIES

__version__ = '6.10.0'

__changelog__ = """
6.10.0 2023.11.13
new method logout
added LOGGED_OUT_MARKER 
process_account: logout method call to avoid concurrence error
6.9.0 2023.10.30
added PASSWORD_CHANGE_MARKER
login: managed password change detection
6.8.0 2023.04.24
_get_encrypted: added encrypted text check to detect encryption errors when credentials have special characters
6.7.0
_delay
_get_op_code
_open_mov_filter_page: several attempts
upd log msg
6.6.0
use ENVIRON_COOKIES
upd 2fa markers
6.5.0
upd log for 2FA
add PIN_2FA
6.4.0
use account-level result_codes
6.3.0
Upd 'need to update the password' detector
6.2.0
call basic_upload_movements_scraped with date_from_str
6.1.0
parse_helpers: get_accounts_parsed: 
  use 'saldo contable' as acc balance instead of 'disponible' 
  because it fits to movements' temp balances
6.0.0
new web
5.17.0
parse_helpers: get_movements_parsed: replace 'new line' separators in descr 
5.16.0
cap_param for all reqs
hooks for req_params and urls
5.15.0
login: detect 'need to update password'
5.14.0
renamed to download_correspondence()
5.13.0
get_accounts_scraped: handle pages with details w/o currency (use default with warn msg)
5.12.0
skip inactive accounts
"""

CALL_JS_CAJAMAR_ENCRYPT_LIB = 'node {}'.format(
    os.path.join(
        project_settings.PROJECT_ROOT_PATH,
        project_settings.JS_HELPERS_FOLDER,
        'cajamar_encrypter.js'
    )
)

CREDENTIALS_ERROR_MARKERS = [
    'digo de usuario o la contrase',
    'acceder-a-banca-electronica-reintentar',
    '/clave-bloqueada',
    # Account is blocked, consider this case as a credentials error:
    # "You have exceeded the number of retry allowed to your personal
    # key card or code received on your mobile.
    # Go to your office to unlock the service or call ...
    # if you have a card from our entity."
    'Acuda a su oficina para desbloquear el servicio'
]
PIN_2FA = [
    'Introduzca la clave que ha recibido por SMS',
    'Por su seguridad, siguiendo la directiva europea PSD2, ',
    'desde el 14 de septiembre del 2019, es necesario que confirme el acceso al servicio de banca a distancia.',
    'Introduzca su PIN personal de FirmaM\xF3vil para completar la operaci\xF3n en el dispositivo',
]

PASSWORD_CHANGE_MARKER = 'Recomendaciones para su nueva contrase'

LOGGED_OUT_MARKER = 'W_C_AVISO_LOGOFF_BE'

class CajamarScraper(BasicScraper):
    scraper_name = 'CajamarScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        # to redefine in child (caixaltea_scraper)
        self.base_url = 'https://www.cajamar.es/'
        self.env_cookies_domain = '.cajamar.es'
        self.entidad_param = '3058'
        self.custom_login_req_params = {}  # type: Dict[str, str]
        # set True (for auto) or path to cert (for manual)
        self.ssl_cert = True  # type: Union[bool, str]
        self.update_inactive_accounts = False
        self.req_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0'
        }

    def _url(self, suffix: str) -> str:
        return urljoin(self.base_url, suffix)

    def _get_encrypted(self, text: str, salt: str) -> str:
        cmd = '{} "{}" "{}"'.format(CALL_JS_CAJAMAR_ENCRYPT_LIB, text, salt)
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        # Text with some special characters ('$') are not encrypted correctly.
        # These special characters work without escaping: '@', '_', '-', '\'. If they are escaped will not work.
        # Encrypted text length must be 4*(text before encrypt.length).
        # If encrypted text is shorter escape text and encrypt again
        # -a 26003 example:
        # DB password text: A4k8Km$N43pU   -> 0bb93ea4abd47ea5aeb6cdd8 (truncates from $ and returns shorter encrypted text)
        # re.escape text:   A4k8Km\\$N43pU -> 0bb13ca5aed37ba7abb1ced63d93dab23aa52ca3fed94dc5
        if len(text_encrypted) != len(text)*4:
            self.logger.info('Text encrypted does not match with text length. Escape text to call js encrypter')
            cmd = '{} "{}" "{}"'.format(CALL_JS_CAJAMAR_ENCRYPT_LIB, re.escape(text), salt)
            result_bytes = subprocess.check_output(cmd, shell=True)
            text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def _delay(self, minimal=0.5) -> None:
        time.sleep(minimal + random.random())

    def _timestamp(self) -> int:
        return int(datetime.datetime.now().timestamp() * 1000)

    def _acc_alias_param(self, account_no: str) -> str:
        t = account_no
        # -a 3831  '096927200805903' -> '96927200805903' -- 14 chars
        # -a 17710 '009810210800058' ->  '9810210800058' -- 13 chars
        alias = (t[8:12] + t[14:18] + '0' + t[18:]).lstrip('0')
        return alias

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:

        is_logged = False
        is_credentials_error = False

        req_url_init_page = self._url('es/comun/')

        s = self.basic_new_session()
        resp_login_page = s.get(
            req_url_init_page,
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=self.ssl_cert
        )

        environ_cookies = ENVIRON_COOKIES.get(self.db_financial_entity_access_id)  # type: Optional[str]
        if environ_cookies:
            self.logger.info('Set confirmed environment cookies for access {}'.format(
                self.db_financial_entity_access_id
            ))
            s = requests_helpers.update_mass_cookies_from_str(s, environ_cookies, self.env_cookies_domain)
        else:
            self.logger.warning('No environ cookies provided. May cause 2FA')

        encrypt_salt = parse_helpers.get_salt(resp_login_page.text)

        if not encrypt_salt:
            reason = "Can't get correct encrypt_salt"
            return s, resp_login_page, is_logged, is_credentials_error, reason

        username_encrypted = self._get_encrypted(self.username, encrypt_salt)
        userpass_encrypted = self._get_encrypted(self.userpass, encrypt_salt)

        req_url_login = self._url('BE/ServletOperation')
        req_params_login = {
            'CHANNEL': 'WEB',
            'ENTIDAD': self.entidad_param,
            'OP_CODE': 'O_LOGON_LDAP_BE_v1',
            'MODEL': 'FullModel',
            'LANGUAGE': 'esp',
            'LOCHUA': 'Fire#52#1366#0768',
            'SISTEMAO': 'NOW',
            'NUME': username_encrypted,
            'PASSWORD': userpass_encrypted,
            # 'OPER': '8:S_C_GENERAL_v1',
            'OPER': '0',
            'SESION': self._timestamp(),
            'VERSION': '2',
            'ZKENABLED': "true",
        }

        req_params_login.update(self.custom_login_req_params)

        resp_logged_in = s.post(
            req_url_login,
            params=req_params_login,
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=self.ssl_cert
        )

        is_logged = 'Cuentas' in resp_logged_in.text
        is_credentials_error = any(m in resp_logged_in.text for m in CREDENTIALS_ERROR_MARKERS)
        is_2fa_error = any(m in resp_logged_in.text for m in PIN_2FA)
        reason = ''
        # Introduzca la clave que ha recibido por SMS en su teléfono móvil acabado en 966
        if is_2fa_error:
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON
        if PASSWORD_CHANGE_MARKER in resp_logged_in.text:
            reason = PASSWORD_CHANGE_TYPE_COMMON
        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def logout(self, s: MySession, account_no: str) -> bool:
        """Need to log out to avoid ERR_CANT_LOGIN_CONCURRENTLY"""
        self.logger.info('{}: logout on account thread'.format(account_no))

        req_url_logout = self._url('BE/ServletOperation')
        req_params_logout = {
            'OP_CODE': 'S_LOGOFF',
            'CHANNEL': 'WEB',
            'MODEL': 'FullModel',
            'SERV': '0',
            'CODIGOAVISO': '990800',
            'INVITADO': '',
            'OBSERVACIONES': 'Desconexion+-+DELETED'
        }
        resp_logged_out = s.post(
            req_url_logout,
            params=req_params_logout,
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=self.ssl_cert
        )
        is_logged_out = LOGGED_OUT_MARKER in resp_logged_out.text

        if is_logged_out:
            self.logger.info("{}: logged out successfully".format(account_no))
        else:
            self.basic_log_wrong_layout(resp_logged_out, "{}: can't log out".format(account_no))

        return is_logged_out


    def get_accounts_scraped(
            self,
            s: MySession,
            resp_logged_in: Response) -> Tuple[bool, MySession, Response, str, List[AccountScraped], str]:
        """:return (is_success, session, resp_accs, cap_param, accs_scraped, organization_title"""

        req_url = self._url('BE/ServletOperation')
        cap_param = parse_helpers.get_cap_param(resp_logged_in.text)
        if not cap_param:
            self.basic_log_wrong_layout(resp_logged_in, "Can't get cap_param. Abort")
            return False, s, resp_logged_in, '', [], ''

        req_params_accs = {
            'CHANNEL': 'WEB',
            'MODEL': 'FullModel',
            'OP_CODE': "S_C_GENERAL_v1",
            'SERV': '8',
            'NOMBRE_OPERACION': 'S_C_GENERAL_v1',
            'CAP': cap_param
        }
        resp_accs = s.post(
            req_url,
            data=req_params_accs,
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=self.ssl_cert
        )

        org_title = parse_helpers.get_org_title(resp_logged_in.text)
        accounts_parsed, err = parse_helpers.get_accounts_parsed(resp_accs.text)
        if err:
            self.basic_log_wrong_layout(resp_accs, err)
            return False, s, resp_accs, cap_param, [], org_title

        if not org_title:
            self.basic_log_wrong_layout(resp_accs, "Can't extract org_title. Abort")
            return False, s, resp_accs, cap_param, [], ''

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(org_title, account_parsed)
            for account_parsed in accounts_parsed
        ]

        self.logger.info('Got {} accounts: {}'.format(len(accounts_scraped), accounts_scraped))
        return True, s, resp_accs, cap_param, accounts_scraped, org_title

    # new web
    def _req_movs_url(self, _s: MySession):
        req_url = self._url('BE/ServletOperation')
        return req_url

    def _get_op_code(self, s: MySession, fin_ent_account_id: str, dtid_param: str) -> Tuple[bool, str]:
        """Resp with OP_CODE necessary to filter by dates.
        See dev_n43/15_resp_opcode.html
        """
        req_op_code_url = self._url('BE/zkau')
        req_op_code_params = OrderedDict([
            ('dtid', dtid_param),  # 'z_sh40'   # z_jFQw9FCsV0UmZGYMaJXW5g
            ('cmd_0', 'onSubmit'),
            ('uuid_0', 'formulario'),
            ('data_0', '{"":"true|ACEPTAR|true|_self"}')
        ])
        resp_op_code = s.post(
            req_op_code_url,
            data=req_op_code_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=self.ssl_cert,
        )

        # 'O_A_PETIC_EXTRACTO1614939326395-S_A_PETICANUL_EXTRACTO_v1¬1614939326419'
        op_code_param = parse_helpers.get_op_code(resp_op_code.text)

        if not op_code_param:
            self.basic_log_wrong_layout(
                resp_op_code,
                "{}: can't extract op_code_param".format(fin_ent_account_id)
            )
            return False, ''

        return True, op_code_param

    def _req_movs_params(
            self,
            account_scraped: AccountScraped,
            op_code_param: str,
            date_from: datetime.datetime,
            date_to: datetime.datetime) -> Dict[str, str]:
        req_params = OrderedDict([
            ('CHANNEL', 'WEB'),
            ('MODEL', 'FullModel'),
            ('OP_CODE', op_code_param),
            ('CURRENT_NODE', 'W_S_MOV_NCTA'),
            ('REACTION_CODE', 'ACEPTAR'),
            # 191910210801218, 740127200002016
            ('NCTA_ALIAS', self._acc_alias_param(account_scraped.AccountNo)),
            ('MOV_TRAMOS', '2'),
            ('OP_MOV', '3'),
            ('NUMO', '16'),
            ('FINI', date_from.strftime('%d%m%Y')),
            ('FFIN', date_to.strftime('%d%m%Y')),
        ])
        return req_params

    def _open_mov_filter_page(
            self,
            s: MySession,
            cap_param: str,
            account_scraped: AccountScraped) -> Tuple[bool, MySession, str]:
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        req_url = self._url('BE/ServletOperation')

        req_params = {
            'CHANNEL': 'WEB',
            'MODEL': 'FullModel',
            'OP_CODE': 'O_C_MOV_NCTA_v1',
            'SERV': '12',
            'NOMBRE_OPERACION': 'O_C_MOV_NCTA_v1',
            'NCTA_PREV': self._acc_alias_param(account_scraped.AccountNo),
            'CAP': cap_param,
        }

        ok = False
        op_code = ''
        resp_mov_filter_page = Response()
        for att in range(1, 5):
            self._delay(minimal=att)
            resp_mov_filter_page = s.post(
                req_url,
                data=req_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
                verify=self.ssl_cert
            )

            dtid_param = parse_helpers.get_dt_param(resp_mov_filter_page.text)
            self.logger.info('{}: att #{}: resp_mov_filter_page: got dtid_param={}'.format(
                fin_ent_account_id,
                att,
                dtid_param
            ))

            ok, op_code = self._get_op_code(s, fin_ent_account_id, dtid_param=dtid_param)
            if ok:
                break

            self.logger.warning(
                "{}: att#{}: can't open valid resp_mov_filter_page "
                "(failed related op_code). Retry".format(
                    fin_ent_account_id,
                    att,
                )
            )
        else:
            self.basic_log_wrong_layout(
                resp_mov_filter_page,
                "{}: can't open valid resp_mov_filter_page after several attempts".format(
                    fin_ent_account_id
                )
            )

        return ok, s, op_code

    def get_movements_parsed(
            self,
            s: MySession,
            cap_param: str,
            account_scraped: AccountScraped,
            date_from: datetime.datetime,
            date_to: datetime.datetime) -> Tuple[bool, MySession, List[MovementParsed]]:
        ok, s, op_code_param = self._open_mov_filter_page(s, cap_param, account_scraped)
        if not ok:
            return False, s, []  # already reported

        req_movs_params = self._req_movs_params(
            account_scraped,
            op_code_param,
            date_from,
            date_to
        )

        req_movs_url = self._req_movs_url(s)

        # All movements at once
        resp_movs = s.post(
            req_movs_url,
            data=req_movs_params,
            headers=self.basic_req_headers_updated({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://www.grupocooperativocajamar.es/BE/ServletOperation'
            }),
            proxies=self.req_proxies,
            verify=self.ssl_cert,
            timeout=60  # for many movs, -a 17710 acc ..0058
        )
        if 'NO SE HA PODIDO REALIZAR LA OPERAC' in resp_movs.text:
            self.logger.error("Can't get valid resp_movs. Check req_params: {}. Abort".format(
                req_movs_params
            ))
            return False, s, []
        # detect case if the bank doesn't return too many movements
        if ('La consulta realizada tiene demasiados movimientos. Por favor, acote el intervalo de fechas consultado'
                in resp_movs.text):
            return False, s, []

        movements_parsed_asc = parse_helpers.get_movements_parsed(resp_movs.text)
        return True, s, movements_parsed_asc

    def process_account(self, s: MySession, cap_param: str, account_scraped: AccountScraped):

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        self._delay()  # to make calls with diff time

        if project_settings.IS_CONCURRENT_SCRAPING:
            s, _, is_logged, _, _ = self.login()

            if not is_logged:
                self.logger.error('{}: not logged in during process_account. '
                                  'Exit with err'.format(account_scraped.AccountNo))
                self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_CANT_LOGIN_CONCURRENTLY)
                return False
        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        date_from = date_funcs.get_date_from_str(date_from_str)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        ok, s, movements_parsed = self.get_movements_parsed(
            s,
            cap_param,
            account_scraped,
            date_from,
            self.date_to
        )

        # too wide date range -> get movements one by one day
        if not ok:
            self.logger.info('{}: probably, too wide date interval detected. Extract movements '
                             'day by day (it is slow but reliable)'.format(fin_ent_account_id))
            # explicitly reset movements_parsed
            movements_parsed = []
            date_from_to = date_from - datetime.timedelta(days=1)
            while date_from_to < self.date_to:
                date_from_to_str = date_funcs.convert_dt_to_scraper_date_type1(date_from_to)
                self.logger.info('{}: extract movements of {}'.format(
                    fin_ent_account_id,
                    date_from_to_str
                ))
                date_from_to = date_from_to + datetime.timedelta(days=1)
                ok, s, movements_parsed_i = self.get_movements_parsed(
                    s,
                    cap_param,
                    account_scraped,
                    date_from_to,
                    date_from_to
                )
                if not ok:
                    self.logger.error("{}: can't extract movements even with 1 day interval. Failed at {}. Skip".format(
                        fin_ent_account_id,
                        date_from_to_str
                    ))
                    self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_BREAKING_CONDITIONS)
                    self.logout(s, fin_ent_account_id)
                    return False

                movements_parsed.extend(movements_parsed_i)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )
        self.logout(s, fin_ent_account_id)
        return True

    def main(self) -> MainResult:
        self.logger.info('main: started')

        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        ok, s, resp, cap_param, accounts_scraped, org_title = self.get_accounts_scraped(s, resp_logged_in)

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        if not ok:
            return self.basic_result_common_scraping_error()  # already reported

        # get and save movements
        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=4) as executor:

                futures_dict = {
                    executor.submit(self.process_account, s, cap_param, account_scraped):
                        account_scraped.AccountNo
                    for account_scraped in accounts_scraped
                }

                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_scraped in accounts_scraped:
                self.process_account(s, cap_param, account_scraped)

        self.basic_log_time_spent('GET MOVEMENTS')

        self.download_correspondence(s, org_title)

        return self.basic_result_success()
