from bs4 import BeautifulSoup
import os
import random
import subprocess
from typing import Tuple, Optional, Dict, List
from urllib.parse import urljoin

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, AccountParsed, ScraperParamsCommon,
    MainResult, MOVEMENTS_ORDERING_TYPE_ASC, DOUBLE_AUTH_REQUIRED_TYPE_COMMON
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from .custom_types import Contract
from .login_helpers.fingerprints import *
from .login_helpers.generate_solution import generate_solution
from .login_helpers.headers import Headers
from .login_helpers.parse_script import parse_script
from project import settings as project_settings

__version__ = '2.0.0'

__changelog__ = """
2.0.0 2023.11.08
login: fixed reese84 cookie value generation from fingerprint
1.5.0 2023.09.14
login: implemented new request to get cookie necessary for login (temporary solution)
1.4.0 2023.05.25
download_receipts and download_movement_receipt
1.3.0
call download_correspondence
1.2.1
login: detect 2FA
1.2.0
_upload_accounts_scraped (useful for children)
removed commented
1.1.0
process_access: serial processing for each account (no concurrency) 
1.0.0
"""

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'unicaja_encrypter.js'
))


DOUBLE_AUTH_MARKERS = [
    '{"tipo":"@OTP","fase":"login"}',
]


CALL_JS_GENERATE_SOLUTION_WORKING_DIR = '{}'.format(
    os.path.join(
        project_settings.PROJECT_ROOT_PATH,
        project_settings.JS_HELPERS_FOLDER,
        'unicaja',
        'solution_001',
    )
)

# You can find possible values for web_gl.vendor & web_gl.renderer in resources/gpu.json
# Possible canvas & web_gl.preset are found in README.md

# Linux example
# fingerprint = Fingerprint(
#     is_linux=True,
#     navigator=Navigator(
#         user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
#         brands_header='"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
#         hardware_concurrency=24,
#         device_memory=8,
#         languages_navigator=['en-US', 'en'],
#         languages_header='en-US,en;q=0.9',
#     ),
#     screen=Screen(3840, 2160),
#     canvas='linux_001',
#     web_gl=WebGl(
#         vendor='Google Inc. (NVIDIA Corporation)',
#         renderer='ANGLE (NVIDIA Corporation, NVIDIA GeForce RTX 3070/PCIe/SSE2, OpenGL 4.5.0)',
#         preset='linux_nvidia_001',
#     ),
# )

# Windows example
fingerprint = Fingerprint(
    is_linux=False,
    navigator=Navigator(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        brands_header='"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        hardware_concurrency=8,
        device_memory=8,
        languages_navigator=['en-US', 'en'],
        languages_header='en-US,en;q=0.9',
    ),
    screen=Screen(2560, 1440),
    canvas='windows_002',
    web_gl=WebGl(
        vendor='Google Inc. (NVIDIA)',
        renderer='ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0, D3D11)',
        preset='windows_nvidia_001',
    ),
)


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

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()
        univia_base_url = 'https://univia.unicajabanco.es/'
        # to get cookies
        headers_helper = Headers(
            user_agent=fingerprint.navigator.user_agent,
            languages=fingerprint.navigator.languages_header,
            brands=fingerprint.navigator.brands_header,
            platform=fingerprint.platform_header,
        )
        s.headers.clear()
        headers_login = headers_helper.document_get(referer=None)

        resp_login_page = s.get(
            urljoin(univia_base_url, 'login'),
            headers=headers_login,
            proxies=self.req_proxies
        )

        # Parse HTML
        html = resp_login_page.content.decode(encoding='utf-8')
        soup = BeautifulSoup(html, 'lxml')
        script_src = soup.head.select('script')[-1]['src']

        # GET /script_src
        s.headers.clear()
        headers_script = headers_helper.script_get(referer='https://univia.unicajabanco.es/login')
        resp_script = s.get(
            urljoin(univia_base_url, script_src),
            headers=headers_script,
            proxies=self.req_proxies,
        )

        js = resp_script.content.decode(encoding='utf-8')

        # Parse JS
        parse_result = parse_script(js)

        # Get /favicon.ico
        s.headers.clear()
        headers_img = headers_helper.image_get(referer='https://univia.unicajabanco.es/login')

        resp_img =  s.get(
            urljoin(univia_base_url, 'favicon.ico'),
            headers=headers_script,
            proxies=self.req_proxies,
        )

        # Generate solution.interrogation
        interrogation = generate_solution(
            script_src='https://univia.unicajabanco.es' + script_src,
            aih=parse_result.aih,
            history_len=1,
            global_variables=parse_result.global_variables,
            html=html,
            script_code=parse_result.fp_script,
            fingerprint=fingerprint,
            cwd=CALL_JS_GENERATE_SOLUTION_WORKING_DIR,
        )

        # Create POST payload
        post_payload = {
            'solution': {
                'interrogation': interrogation,
                'version': 'beta',
            },
            'old_token': None,
            'error': None,
            'performance': {
                'interrogation': random.randint(750, 950)
            }
        }

        # POST /script_src?d=host
        post_url = script_src + '?d=' + 'univia.unicajabanco.es'

        s.headers.clear()
        s.headers.update(headers_helper.xhr_post(
            referer='https://univia.unicajabanco.es/login',
            accept='application/json; charset=utf-8',
            origin='https://univia.unicajabanco.es',
        ))
        response = s.post(
            urljoin(univia_base_url, post_url),
            json=post_payload
        )
        content = response.content.decode('utf-8')

        if response.status_code == 200:
            response_json = response.json()

            cookie = response_json['token']
            renew_in_sec = response_json['renewInSec']
        else:
            response.raise_for_status()

        s.cookies.update({'reese84': cookie})

        s.headers.clear()
        s.headers.update(headers_helper.document_get(referer='https://univia.unicajabanco.es/login'))

        resp_login_w_cookie = s.get(
            urljoin(univia_base_url, 'login'),
            headers=headers_login,
            proxies=self.req_proxies
        )
        html = resp_login_w_cookie.content.decode(encoding='utf-8')

        cookie_value = cookie #'3:I/eazsXEvpoYBiTkpTe4MA==:HOD//RbOIgbCNCD+jKO4ye0heIh/ETevF5ZQknje+1fLCH8U39VdqZ73qcoP0rssMi0717N88qYZSc8zLD/DqX1OzAXbjIpbvBCjjODP/SUMViOZjqS/TWRFKXkzJCEwihKfG2J19wldlwkJSH/wOMgxgXkUTmqIvKhGQqCSHxlwrkeQXyXcg23mFy6X+Rjzz1liZEPuMRjOV825fG5CsH3JJPGhkDuHrGa7p0EG4KSLfwqmtNPXNKXsPEWaKbUGnrJfQni/tXfsY4tRZTVUtDb1kZUzVSX3wC0z8l9WtE8FMVU2Zv6UGj3f4UNi2AvBdOgOdIkUvQH9jI9s7FIkq28kqzI1gW3ufbTHLrUTu38hMFZWr0bErub2kJ0JOLiEXkB2kroUy56KEGBhGTY42iDhbNyxTP8FHJgEV2HWDPa2ztGzldlbLDw6xa+XWd4dfcjMZ8CvM3EwPcXykFPLFW9rhqSOr717ZBKesXiGAhM=:BvzI7Y4GePgFw/1AK/AdLZgldUjD37msvBPLauXoeKw='
        #cookie_domain = resp_login_cookie.json().get('cookieDomain')
        cookie_domain = '.univia.unicajabanco.es'
        s.cookies.set('reese84', cookie_value, domain=cookie_domain)

        # {"ck":"82IG39QH"}
        resp_ck = s.get(
            'https://univia.unicajabanco.es/services/rest/openapi/ck',
            headers=self.basic_req_headers_updated({
                'Accept': 'application/json, text/plain, */*',
            }),
            proxies=self.req_proxies
        )

        clave_des_enc_param = resp_ck.json()['ck']

        password_param = self._get_encrypted(clave_des_enc_param)

        req_login_params = {
            'idioma': 'es',
            'usuario': self.username,
            'password': password_param,
        }
        # 268E940BEFD6D28C  # 6E3FA084CA46AE18
        resp_login = s.post(
            'https://univia.unicajabanco.es/services/rest/autenticacion',
            data=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = bool(resp_login.json().get('tokenCSRF'))
        # '{"codigoError":"ERROR000",
        # "mensajeError":"IDENTIFICACION ERRONEA: CODIGO DE USUARIO O CLAVE DE ACCESO ERRONEA "}'
        is_credentials_error = 'IDENTIFICACION ERRONEA' in resp_login.text
        reason = ''

        if any(m in resp_login.text for m in DOUBLE_AUTH_MARKERS):
            is_logged = False
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        return s, resp_login, is_logged, is_credentials_error, reason

    def _switch_to_contract(self, s: MySession, resp_logged_in_json: dict, contract: Optional[Contract]) -> Tuple[
        bool, dict]:
        """:return (ok, resp_contract_json)"""
        if not contract:
            return True, resp_logged_in_json

        req_contact_url = 'https://univia.unicajabanco.es/services/rest/selcontrato?numcontrato={}'.format(
            contract.numcontrato_param
        )
        resp_contract = s.get(
            req_contact_url,
            headers=self.basic_req_headers_updated({
                'tokenCSRF': parse_helpers.get_csrf_token(resp_logged_in_json)
            })
        )

        ok, resp_contract_json = self.basic_get_resp_json(
            resp_contract,
            "Can't get resp_contract_json. Skip"
        )
        return ok, resp_contract_json

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        ok, resp_logged_in_json = self.basic_get_resp_json(resp_logged_in, "Can't get resp_logged_in_json. Abort")
        if not ok:
            return False

        ok, contracts = parse_helpers.get_contracts(resp_logged_in_json)
        if not ok:
            self.basic_log_wrong_layout(resp_logged_in, "Can't get contracts. Abort")
            return False

        if not contracts:
            # one contract
            self.process_contract(s, resp_logged_in_json, None)
        else:
            # multicontract
            self.logger.info('Got {} contracts: {}'.format(len(contracts), contracts))
            for contract in contracts:
                self.process_contract(s, resp_logged_in_json, contract)

        return True

    def _upload_accounts_scraped(self, accounts_scraped: List[AccountScraped]):
        """Can override in children"""
        self.basic_upload_accounts_scraped(accounts_scraped)

    def process_contract(self, s: MySession, resp_logged_in_json: dict, contract: Optional[Contract]) -> bool:

        ok, resp_contract_json = self._switch_to_contract(s, resp_logged_in_json, contract)
        if not ok:
            return False  # already reported

        org_title = parse_helpers.get_org_title(resp_contract_json)
        self.logger.info("Process contract '{}'".format(org_title))

        token = parse_helpers.get_csrf_token(resp_contract_json)

        resp_accounts = s.get(
            'https://univia.unicajabanco.es/services/rest/api/productos/listacuentas',
            headers=self.basic_req_headers_updated({
                'tokenCSRF': token,
            })
        )
        ok, resp_accounts_json = self.basic_get_resp_json(resp_accounts, "Can't get resp_account_json")
        if not ok:
            return False

        accounts_parsed = parse_helpers.get_accounts_parsed(resp_accounts_json)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(org_title, acc_parsed)
            for acc_parsed in accounts_parsed
        ]

        accounts_scraped_dict = self.basic_gen_accounts_scraped_dict(accounts_scraped)

        self.logger.info('{}: got {} accounts: {}'.format(
            org_title,
            len(accounts_scraped),
            accounts_scraped
        ))

        self._upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('{}: GET BALANCES'.format(org_title))

        for acc in accounts_parsed:
            self.process_account(
                s,
                token=token,
                org_title=org_title,
                account_parsed=acc,
                accounts_scraped_dict=accounts_scraped_dict
            )

        self.download_correspondence(s, token, org_title)

    def process_account(
            self, s: MySession,
            token: str,
            org_title: str,
            account_parsed: AccountParsed,
            accounts_scraped_dict: Dict[str, AccountScraped]) -> bool:
        fin_ent_account_id = account_parsed['financial_entity_account_id']
        account_scraped = accounts_scraped_dict[fin_ent_account_id]
        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from, date_from_str = self.basic_get_date_from_dt(fin_ent_account_id)
        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        req_movs_params = {
            'ppp': account_parsed['ppp_param'],
            'fechadesde': date_from.strftime('%Y-%m-%d'),  # '2022-02-28',
            'fechahasta': self.date_to.strftime('%Y-%m-%d'),  # '2022-06-01',
            'indOperacion': 'B',
        }
        resp_movs = s.post(
            'https://univia.unicajabanco.es/services/rest/api/cuentas/movimientos/simulaAutorizaBusqueda',
            data=req_movs_params,
            headers=self.basic_req_headers_updated({
                'tokenCSRF': token,
            }),
            proxies=self.req_proxies
        )
        ok, resp_movs_json = self.basic_get_resp_json(
            resp_movs,
            "{}: {}: can't get resp_movs_json. Skip".format(
                org_title,
                fin_ent_account_id
            )
        )
        if not ok:
            return False  # already reported

        ok, movements_parsed = parse_helpers.get_movements_parsed(resp_movs_json, account_parsed)
        if not ok:
            self.basic_log_wrong_layout(resp_movs, "{}: {}: can't get movements_parsed. Skip".format(
                org_title,
                fin_ent_account_id
            ))
            return False

        resp_movs_i_json = resp_movs_json
        for page_ix in range(2, 100):  # avoid inf loop
            next_page_num_mov_param = parse_helpers.get_next_page_num_mov_param(resp_movs_i_json)
            if not next_page_num_mov_param:
                self.logger.info('{}: {}: no more pages'.format(
                    org_title,
                    fin_ent_account_id,
                ))
                break

            self.logger.info('{}: {}: page #{}: get movements'.format(
                org_title,
                fin_ent_account_id,
                page_ix
            ))

            req_movs_i_params = {
                'ppp': account_parsed['ppp_param'],
                'nummov': next_page_num_mov_param,
                'indOperacion': 'B'
            }
            resp_movs_i = s.post(
                'https://univia.unicajabanco.es/services/rest/api/cuentas/movimientos/paginacion',
                data=req_movs_i_params,
                headers=self.basic_req_headers_updated({
                    'tokenCSRF': token,
                }),
                proxies=self.req_proxies
            )

            ok, resp_movs_i_json = self.basic_get_resp_json(
                resp_movs_i,
                "{}: {}: page #{}: can't get resp_movs_i_json. Abort pagination".format(
                    org_title,
                    fin_ent_account_id,
                    page_ix
                )
            )
            if not ok:
                break  # already reported

            ok, movements_parsed_i = parse_helpers.get_movements_parsed(resp_movs_i_json, account_parsed)
            if not ok:
                self.basic_log_wrong_layout(resp_movs, "{}: {}: page #{}: can't get movements_parsed. Skip".format(
                    org_title,
                    fin_ent_account_id,
                    page_ix
                ))
                break

            movements_parsed.extend(movements_parsed_i)
            pass

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
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
                token,
                account_scraped,
                movements_scraped,
                movements_parsed
            )
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
