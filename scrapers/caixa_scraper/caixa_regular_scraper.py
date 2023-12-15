import os
import random
import re
import subprocess
import threading
import time
import traceback
from collections import OrderedDict
from concurrent import futures
from typing import Dict, List, Tuple, Optional
# splitquery is hidden but can be imported
from urllib.parse import urljoin

from custom_libs import list_funcs
from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import requests_helpers
from custom_libs.extract import splitquery
from custom_libs.myrequests import MySession, Response
from custom_libs.str_funcs import fuzzy_equal
from project import settings as project_settings
from project.custom_types import (
    AccountParsed, AccountScraped, MovementParsed,
    ScraperParamsCommon, MainResult,
    DOUBLE_AUTH_REQUIRED_TYPE_COOKIE,
    DOUBLE_AUTH_REQUIRED_TYPE_COMMON,
    BLOCKED_USER_TYPE_COMMON,
    EXPIRED_USER_TYPE_COMMON,
)
from project.result_codes import ERR_CANT_SWITCH_TO_CONTRACT
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.caixa_scraper import parse_helpers_regular as parse_helpers
from scrapers.caixa_scraper import parse_helpers_regular_particulares as parse_helpers_particulares
from .custom_types import Company
from .environ_cookies import ENVIRON_COOKIES

__version__ = '7.3.0'
__changelog__ = """
7.3.0 2023.11.13
more EXPIRED_USER_MARKERS
_get_failed_login_reason: managed multiple EXPIRED_USER_MARKERS
7.2.0 2023.06.23
_additional_login_reqs: added the management of expired digital firm
7.1.0 2023.04.11
_reopen_resp_with_weblogic_session_url: get url from text instead of url of resp_logged_in
7.0.0 2023.04.10
_additional_login_reqs_for_jsp: added new additional login reqs for caixabank.es/jsp
6.12.0
added MANDATORY_MANUAL_ACTION_MARKER
_additional_login_reqs: changed 'posponerGDPR' req to skip required manual actions
6.11.0
added SUBDOMAINS
login: call _get_failed_login_reason
new _get_failed_login_reason:
6.10.0
added EXPIRED_USER_MARKERS
login: expired user detector
6.9.0
added BLOCKED_USER_MARKERS
login: blocked user detector
6.8.0
process_company: process failed account after renew the account references
6.7.0
_additional_login_reqs: added new login req for 'particulares'
6.6.0
use renamed list_funcs
6.5.0
upd mobile app 'CaixaBank Sign' request detection
6.4.0
is_valid_company: check for MANDATORY_MANUAL_ACTION_MARKERS
use basic_set_movements_scraping_finished_for_contract_accounts
6.3.0
login_to_subdomain: 
  returns ERR_NOT_LOGGED_IN_DETECTED_REASON: DOUBLE AUTH REQUIRED if no cookie is found for access 
  ENVIRON_COOKIES_DEFAULT is not used any more
login: don't use default cookie
6.2.0
use _update_related_account_info
6.1.0
_get_fin_ent_account_id to use in children
_is_valid_company: more cases
scraper_name as class prop
6.0.0
_get_and_save_movs_by_dates_for_particulares: now with extended descriptins and receipts
process_movement_new for particulares-like new movements
upd logs
5.15.0
try switching to 'old empresas view' to get earlier implemented extended descriptions
  (_switch_to_oldview_empresas_movs)
5.14.1
commented some bad working subdomains
5.14.0
_extract_companies: 
  use parse_helpers.build_next_page_w_companies_req_params for proper pagination (old and new) 
  hanging pagination loop detector
5.13.0 
_extract_companies: companies (contracts) from get_companies OR get_companies_new (support both)
5.12.0
_get_and_save_movs_by_dates_for_particulares: check for hanging loop
parse_helpers_particulares: upd req_movs_filter_by_dates_params, req_movs_next_page_params
5.11.0
call basic_upload_movements_scraped with date_from_str
5.10.0
SCRAP_MOVS_OFFSET__CUSTOM = 4
5.9.0
process_account: use parse_helpers_particulares.get_account_no_from_movs_page
  (useful for -a 30778 acc ...0006 8434)
5.8.1
upd log msgs
5.8.0
CAIXA_SIGN_APP_ACTIVATION_REQUIRED_MARKER -> DOUBLE_AUTH_REQUIRED_TYPE_COMMON
5.7.0
set_date_to_for_future_movs
5.6.0
_switch_to_company: do _additional_login_reqs for companies with enabled KYC actions
  (-a 21910, VIA CELERE GESTION DE PROYECTOS S.L.)
5.5.0
login_to_subdomain
_switch_to_company
5.4.0
updated UA (user agent) - aligned with "confirming web browser"
5.3.0
_extract_companies: upd request parameter for pagination (-a 6923)
5.2.0
use splitquery from custom_libs.extract
5.1.0
parse_helpers: get_available_company_titles
_is_valid_company using get_available_company_titles
5.0.0
use basic_get_movements_parsed_w_extra_details
4.19.0
parse_helpers_regular_particulares: upd get_account_no_from_movs_page (changed layout)
4.18.0
more COMPANY_HAS_NO_ACCOUNTS_MARKERS
renamed back to parse_helpers_regular_particulares
upd log msgs
4.17.0
upd reqs and layout for private (particulares) contracts 
    (-a 16556 FRANCISCO DE ASIS RIPOLL SOGAS, -a 6923 STIN SA)
4.16.1
upd log msgs
4.16.0
renamed to download_correspondence()
4.15.0
MOVS_MAX_OFFSET=360
4.14.0
CAIXA_SIGN_APP_ERR
4.13.0
parse_helpers_regular: get_next_page_with_accs_params_patch: 
  several places to get vals (fix acc pagination for 3rd page: -a 21910, acc ES7321009135072200157114)
more log msgs 
4.12.0
handle 'use App CaixaBank Sign' (I'll do it later, -a 11213)
4.11.0
parse_helpers_particulares: get_movements_parsed: upd amount sign detection (-a 20111)
4.10.0
parse_helpers: get_accounts_parsed:
  correct foreign currency balance from 'tesoreria' view 
4.9.0
parse_helpers: get_accounts_parsed:
  handle 'EUR' in a foreign currency description place
  fixed numero_cuenta_ix increase for some cases
4.8.0
upd pagination for account list for 'empresas' sub-contracts (with 'cuentas' view) 
4.7.0
parse helpers: currency from new layout for 'cuentas' view
handle account_alias
upd log msgs
4.6.0
use update_inactive_accounts
process_account: use basic_check_account_is_active
4.5.0
_extract_companies: impl pagination
4.4.0
parse_helpers_particulares:
  get_movements_parsed, get_account_no_from_movs_page: handle new layout
4.3.0
parse_helpers_regular: get_accounts_parsed: parse accounts from the updated 'Cuentas' view
upd log msg
4.2.0
fixed movements_w_extra_details for the first page (were w/o extra details)
4.1.0
process_company: download_company_documents
4.0.1
aligned double auth msg
4.0.0
'Particulares' subaccesses support
"""

# https://loc8.caixabank.es/
SUBDOMAINS = [
    'loc1',
    'loc2',
    'loc3',
    'loc4',
    'loc5',
    'loc6',
    'loc7',
    'loc8',
    'loc9',
    'loc10',
    'loc11',
    'loc12',
    'loc13',
    'loc14',
    'loc15',
    'loc16',
    'loc17',
    'loc18',
]

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'caixa_encrypter.js'
))

MOV_DETAILS_MAX_WORKERS = 8

# shorter offset because of needs to open each movement
# as for CaixaMobileScraper
SCRAP_MOVS_OFFSET__CUSTOM = 4
MOVS_MAX_OFFSET = 360  # 1yr - padding, tested: -a 19512 (emp), -a 20111 (partic)

MAX_MOVS_PER_PAGE = 20

# to avoid inf loops
ACCS_PAGE_NUM_MAX_LIMIT = 10
MOVS_PAGE_NUM_MAX_LIMIT = 1000

UA = 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0'

COMPANY_HAS_NO_ACCOUNTS_MARKERS = [
    '<input type="Hidden" name="WELLCOME" value="">',
    # Sometimes the customer has no permissions to see accs
    # dev_regular/empresas-no-visible-accs.png
    # dev_regular/5_resp_accs_empresas_no_visible_accs.html
    # -a 9111, ASMOVIL SAU, empreasas view
    'No dispones de cuentas visibles',
    # 5_resp_accs_particulares_no_accs.html
    # -a 9111, ASMOVIL SAU, particlares view (switched to HECTOR)
    # (to toggle empresas/particulares view click on username
    # and select necessary view from right slider)
    'Sin cuentas a la vista disponibles',
]

WEB_LOGIC_SESSION = 'WebLogicSession'
SMS_AUTH_REQUIRED_MARKER = 'Nos puedes confirmar que eres tú quien se está conectando'
CAIXA_SIGN_APP_ACTIVATION_REQUIRED_MARKER = 'Todavía no has activado CaixaBank Sign'
CAIXA_SIGN_APP_ERR = 'CaixaBank Sign app activation required'
REQUEST_ERROR_MARKER = 'Sentimos comunicarle que su petición no se ha realizado'
# some subdomains are disabled periodically and return err resp
DISABLED_SUBDOMAIN_MARKER = '<meta name="PANTALLA_DE_ERROR" content="1576"'
BLOCKED_USER_MARKER = 'Tu acceso ha sido bloqueado por razones de seguridad'
EXPIRED_USER_MARKERS = [
    'Usted no puede acceder a banca digital CaixaBankNow porque su usuario ha caducado',
    'Tu usuario ha caducado'
]

# contract-level (company-level) detections
MANDATORY_MANUAL_ACTION_MARKERS = [
    'Abre, lee y acepta los documentos',
    'Tienes información pendiente de actualizar',
]


# TODO: VB: 12/2020:
#  Each contract has 2 views:
#   - business (empresas)
#   - private (particulares).
#  By default when we select a contract, a preferred view will be opened (business or private).
#  Right now the scrapers processes a view which was opened - it brings
#  some extra complexity (different layouts, reqs, corner cases).
#  But it is possible to switch to business view and then process it,
#  because accounts of a contract are available in both views.
#  This way should be implemented.
#  Example:
#  -a 16556 FRANCISCO DE ASIS RIPOLL SOGAS:
#  accounts ES50 2100 8198 6102 0015 1457
#  ES19 2100 8198 6902 0019 2848
#   available in both: empresas (business) and particulatres (private) views
class CaixaScraper(BasicScraper):
    """It scrapes regular website.
    Implemented and tested options:
    - one and many companies per access
    - one and many accounts per company (with pagination)
    - handle results without movements
    - handle hanged loop over movements pagination
    - handle if subdomain down
    - handle redirection to another subdomain after login step
    - handle additional js-based requests after main resp_logged_in (NEW 2019-05-22)
    - handle case if was redirected from all subdomains - get it as a webbrowser (NEW 2019-05-22)
    - improved redirection and JS handlers at login step (NEW 2019-06-15)
    - optimized extra_details (extended descriptions and receipts_params) scraping:
      the scraper will scrape extra_details if it's a receipts_scraper
      or only for unambigious movements not saved in the DB
      (detect by specific unique checksums, if there are several movements with equal checksums
      then all of them will be processed for extra details)
    - carpeta access type support

    Not implemented:
    pagination over a list of accounts (no current cases)
    - it was -u 265510 -a 14503 which is not available now

    NOTE: as the CaixaMobileScraper, this scraper uses SCRAP_MOVS_OFFSET__CUSTOM
    for movements re-scraping

    This scraper doesn't demand on CaixaMobileScraper

    Similar to CaixaMobile:
    - it processes companies in parallel mode using different subdomains;
    - for each company,the scraper processes each account one by one;
    - for each account, it processes movements in parallel mode
    but with 8 (now) workers instead of 2 in CaixaMobile.
    """

    scraper_name = 'CaixaRegularScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.companies_to_scrape_idxs = [0]  # type: List[int]
        self.n_companies = 1  # at least 1 company
        self.lock = threading.Lock()
        self.req_headers = {'User-Agent': UA}
        self.update_inactive_accounts = False
        # Important field for movements processing optimization
        self.is_receipts_scraper = False
        # Allow future movements scraping when the customer required it
        self.set_date_to_for_future_movs()

    @staticmethod
    def _get_fin_ent_account_id(account_parsed: dict) -> str:
        """ES6800496738531030617076 -> ES6800496738531030617076
        Can redefine in children (Bankia from Caixa)
        """
        return account_parsed['account_no']

    def _update_related_account_info(
            self,
            account_scraped: AccountScraped,
            account_parsed: AccountParsed) -> bool:
        """To fill RelatedAccount field"""
        # For now, only former Bankia accounts require it (see bankia_from_caixa)
        return True

    def _get_username(self) -> str:
        """Can redefine in children (Bankia)"""
        return self.username

    def _get_encrypted(self, oper_param: str, a_param: str,
                       c_param: str, d_param: str, lon_param: str) -> str:
        cmd = '{} "{}" "{}" "{}" "{}" "{}" "{}"'.format(
            CALL_JS_ENCRYPT_LIB,
            oper_param,
            a_param,
            c_param,
            d_param,
            self.userpass.upper(),
            lon_param
        )
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def _is_logged_is_cred_errs(self, resp: Response) -> Tuple[bool, bool]:
        # var data="TELEFONO="+ tfno + "&TIPO_ACCESO=" + orig+ "&NOMBRE=" + "ALTUNA Y URIA S.A.";
        is_logged = ('var data="TELEFONO="+ tfno + "&TIPO_ACCESO=" + orig+ "&NOMBRE="'
                     in resp.text)
        is_credentials_error = 'Identificación incorrecta' in resp.text
        return is_logged, is_credentials_error

    # Unused now but it'd be useful for dev
    # if _reopen_resp_with_weblogic_session_url returns error responses
    def _open_main_frame(self, s: MySession, resp: Response) -> Tuple[bool, MySession, Response]:
        # Use link to web frame Inferior to be able to get company title
        # usually, no schema, domain and host in the link
        req_main_frame_link = parse_helpers.get_main_frame_link_w_websession(resp.text)

        # Open main_frame
        if not req_main_frame_link:
            self.logger.warning("Can't parse correctly WebLogicSession from page. RESPONSE:\n{}".format(
                resp.text
            ))
            return False, s, resp

        if WEB_LOGIC_SESSION not in req_main_frame_link:
            self.logger.warning("Can't parse correctly WebLogicSession from page. RESPONSE:\n{}".format(
                resp.text
            ))
            return False, s, resp

        resp_main_frame = s.get(
            urljoin(resp.url, req_main_frame_link),
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        return True, s, resp_main_frame

    def _reopen_resp_with_weblogic_session_url(
            self,
            s: MySession,
            resp: Response) -> Tuple[MySession, Response]:

        if WEB_LOGIC_SESSION in resp.url:
            self.logger.info("WebLogicSession in resp url. OK")
            return s, resp

        self.logger.info("Try to reopen resp with WebLogicSession url.")

        if WEB_LOGIC_SESSION not in resp.text:
            # not an err - it is acceptable case
            self.logger.warning("No WebLogicSession val at the page. RESPONSE:\n{}".format(
                resp.text
            ))
            return s, resp

        # Re-open resp_logged_in with WebSessionLogic from resp_logged_in2 body
        # to provide identical behavior as without additional requests
        self.logger.info("Got WebLogicSession url path in the page body. Reopen resp with it")
        # Use link to web frame Inferior to be able to get company title
        # usually, no schema, domain and host in the link
        req_main_frame_link = parse_helpers.get_main_frame_link_w_websession(resp.text)

        # 'REFVAL_COMPLEJO' means that this resp should be JS-processed, no need to reopen
        if (WEB_LOGIC_SESSION not in req_main_frame_link) and ('REFVAL_COMPLEJO' not in resp.text):
            self.logger.warning("Can't parse correctly WebLogicSession from page. RESPONSE:\n{}".format(
                resp.text
            ))
            return s, resp

        req_wls_url = urljoin(resp.url, req_main_frame_link)
        resp_w_weblogic_session = s.get(
            req_wls_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return s, resp_w_weblogic_session

    def _get_reason_from_iframe(self, s: MySession, resp: Response) -> str:
        iframe_src = extract.re_first_or_blank(
            '<iframe[^>]+name="TopDom" src="(.*?)"',
            resp.text
        )
        if not iframe_src:
            return 'Unknown action required'
        resp_iframe = s.get(
            urljoin(resp.url, iframe_src),
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        if SMS_AUTH_REQUIRED_MARKER in resp_iframe.text:
            return DOUBLE_AUTH_REQUIRED_TYPE_COOKIE
        if CAIXA_SIGN_APP_ACTIVATION_REQUIRED_MARKER in resp_iframe.text:
            self.logger.error('Detected "{}". Consider as "{}"'.format(
                CAIXA_SIGN_APP_ERR,
                DOUBLE_AUTH_REQUIRED_TYPE_COMMON
            ))
            return DOUBLE_AUTH_REQUIRED_TYPE_COMMON
        # 2019-10: most probably it's about the sms auth
        return 'Unknown action required'

    def _additional_login_reqs(
            self,
            s: MySession,
            resp_logged_in: Response) -> Tuple[MySession, Response, str]:
        """Provides JS-based clicks on POST forms
        :returns (session, resp, reason_not_logged_in)
        """
        posponerGDPR_form_name_str = 'posponerGDPR'
        expired_digital_firm_str = 'Tu firma digital de Bankia ha caducado'
        subdomain = parse_helpers.get_subdomain_of_url(resp_logged_in.url)
        if not ('PNAjuda="LGN"' in resp_logged_in.text or "PNLomilu='LGN'" in resp_logged_in.text):
            self.logger.info("{}: no markers found to do more JS-based requests".format(subdomain))
            return s, resp_logged_in, ''

        # Additional login reqs in some cases

        self.logger.info("{}: do JS-based requests after main login response".format(subdomain))

        # req_login2_params = parse_helpers.get_redirection_login2_req_params(resp_logged_in)
        req_login2_link, req_login2_params = extract.build_req_params_from_form_html_patched(
            resp_logged_in.text,
            form_re='(?si)<form.*?</form',
            is_ordered=True
        )
        resp_logged_in2 = s.post(
            urljoin(resp_logged_in.url, req_login2_link),
            data=req_login2_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_login3_link = ''
        req_login3_params = OrderedDict()  # type: Dict[str, str]
        resp_logged_in3 = Response()
        resp_prev = resp_logged_in2

        for i in range(1, 10):
            if 'formPON' in resp_prev.text:
                self.logger.info('Submit formPON')
                # expect PN=LGN&PE=12&REFVAL_COMPLEJO_5840=UE580uggfOZQTnzS6CB85gAAAWqhkNvd4GKldNJqjQI
                req_login3_link, req_login3_params = extract.build_req_params_from_form_html_patched(
                    resp_prev.text,
                    'formPON',
                    is_ordered=True
                )
                pass
            elif 'posponerKYC' in resp_prev.text:
                # Try KYC form actions
                # Action required, check for 'posponerKYC' form
                # Emulates 'Lo haré en otro momento' action (I'll do it later)
                self.logger.info("""Submit "I'll do it later" KYC form action""")
                req_login3_link, _ = extract.build_req_params_from_form_html_patched(
                    resp_prev.text,
                    'posponerKYC'
                )
                req_login3_params = OrderedDict([
                    ('PN', 'LGN'),
                    ('PE', '12'),
                    ('CLICK_ORIG', '')
                ])
                pass
            elif ('En qué móvil quieres instalar CaixaBank Sign' in resp_prev.text
                    and 'Lo haré en otro momento' in resp_prev.text):
                # Try App CaixaBank Sign actions
                # Emulates 'Lo haré en otro momento' action (I'll do it later)
                days_left = extract.re_first_or_blank(r'próximos (\d+) días', resp_prev.text) or 'unknown'
                self.logger.info(
                    """Submit "I'll do it later" for"""
                    """ "switch to App CaixaBank Sign" form ({} days left)""".format(days_left)
                )
                # process 1_31_resp_appssign_later_select.html
                req_login3_link, req_login3_params = extract.build_req_params_from_form_html_patched(
                    resp_prev.text,
                    'Continuar'
                )
                # I'll do it later
                req_login3_params['PE'] = '24'
            elif 'name="Continuar"' in resp_prev.text and len(re.findall('<form', resp_prev.text)) == 1:
                self.logger.info("Submit  'continue' form")
                req_login3_link, req_login3_params = extract.build_req_params_from_form_html_patched(
                    resp_prev.text,
                    form_name='Continuar',
                    is_ordered=True
                )
                pass
            elif 'REFVAL_COMPLEJO' in resp_prev.text and len(re.findall('<form', resp_prev.text)) == 1:
                self.logger.info('Submit one unnamed form')

                # expect REFVAL_COMPLEJO_4825
                req_login3_link, req_login3_params = extract.build_req_params_from_form_html_patched(
                    resp_prev.text,
                    form_re=r'(?si)<form.*?</form>',
                    is_ordered=True
                )
                req_login3_params['PN'] = 'LGN'
                req_login3_params['PE'] = extract.re_first_or_blank(r'PEAjuda="(\d+)"', resp_logged_in2.text)
                pass
            elif (posponerGDPR_form_name_str in resp_prev.text
                  and len(re.findall('<form.*?name="{posponerGDPR}">'.format(
                        posponerGDPR=posponerGDPR_form_name_str),
                        resp_prev.text))) == 1:
                # Skip required manual actions on login or switch to contract
                # Emulates 'Lo haré en otro momento' action (I'll do it later)
                self.logger.info("Submit {} form".format(posponerGDPR_form_name_str))

                # expect posponerGDPR
                req_login3_link, req_login3_params = extract.build_req_params_from_form_html_patched(
                    resp_prev.text,
                    form_name=posponerGDPR_form_name_str,
                    is_ordered=True
                )
                req_login3_params['PN'] = 'LGN'
                req_login3_params['PE'] = extract.re_last_or_blank(r'PE.value = "(\d+)"', resp_logged_in2.text)
                # Not mandatory parameter 'ORIGEN'
                # req_login3_params['ORIGEN'] = extract.re_last_or_blank(r'ORIGEN.value = "(\w+)"', resp_logged_in2.text)
                pass
            elif expired_digital_firm_str in resp_prev.text:
                # Detected expired digital firm
                # Emulates 'Accede a CaixaBankNow' (Access to CaixaBankNow)
                self.logger.info("Detected '{}'. Submit expired digital firm form".format(expired_digital_firm_str))

                # expect expired_digital_firm
                req_login3_link, req_login3_params = extract.build_req_params_from_form_html_patched(
                    resp_prev.text,
                    form_name='formulario',
                )
                req_login3_params['PN'] = 'LGN'
                req_login3_params['PE'] = extract.re_last_or_blank(r'PE.value\s*= "(\d+)"', resp_logged_in2.text)
                pass
            else:
                reason = self._get_reason_from_iframe(s, resp_prev)
                return s, resp_prev, reason

            resp_logged_in3 = s.post(
                urljoin(resp_prev.url, req_login3_link),
                data=req_login3_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            is_logged, is_credentials_error = self._is_logged_is_cred_errs(resp_logged_in3)
            if (not is_logged and not is_credentials_error
                    and ('REFVAL_COMPLEJO' in resp_prev.text or 'name="Continuar"' in resp_prev.text)):
                resp_prev = resp_logged_in3
                self.logger.info("Even more login step: {}".format(i))
                continue
            break

        return s, resp_logged_in3, ''

    def _login_redirect(
            self,
            s: MySession,
            resp_logged_in: Response,
            subdomain_init: str) -> Tuple[MySession, Response]:
        """Provides JS-based redirection"""

        req_redirected_url = parse_helpers.get_redirection_url(resp_logged_in.text)
        self.logger.info("login_redirect: force allowed JS-based redirection from {}".format(
            subdomain_init
        ))

        # Can be redirected to intermediate 'lo.' or to a specific 'loc...'

        resp_logged_in_redirected = s.get(
            req_redirected_url,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        self.logger.info("login_redirect: opened {}".format(resp_logged_in_redirected.url))

        return s, resp_logged_in_redirected

    def login(self, subdomain="",
              allow_redirection=False) -> Tuple[MySession, Response, bool, bool, bool, str]:
        """Log in into subdomain
        Handles cases if sudomain redirects to another - early return in this case

        :returns (session, resp_logged_in, is_logged, is_cred_err, is_redirected, reason_not_logged)
        """

        s = self.basic_new_session()

        # available after submit "Entrar" with blank username and password
        req_login_form_url = (
            'https://{}.caixabank.es/GPeticiones?'
            'PN=LGN&PE=116&IDIOMA=02&CANAL=I&DEMO=0&ENTORNO=L&ORIGEN=POR'
            '&loce=es-particulars-home-particulares-06-i01-3-E'.format(subdomain)
        )

        # from main url - it brings another login script
        # req_login_form_url = (
        #     'https://{}.caixabank.es/GPeticiones?'
        #     'PN=LGN&PE=24&IDIOMA=02&CANAL=I&DEMO=0&FLAG_BORSA=0&CS=UTF'.format(subdomain)
        # )

        resp_login_form = s.get(
            req_login_form_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        oper_param = extract.re_first_or_blank(r"revertir\('(.*?)'", resp_login_form.text)
        a_param = extract.re_first_or_blank("A.value='(.*?)'", resp_login_form.text)
        c_param = extract.re_first_or_blank("C.value='(.*?)'", resp_login_form.text)
        d_param = extract.re_first_or_blank("D.value='(.*?)'", resp_login_form.text)
        lon_param = extract.re_first_or_blank(r"validateHere\(ID,f.tmp,pin1,f.C,lgn.D,(\d+)",
                                              resp_login_form.text)

        if not (oper_param and a_param and c_param and d_param and lon_param):
            reason = "{}: can't parse correct encryption params to log in".format(subdomain)
            self.logger.warning(
                "{}. Skip subdomain {}".format(reason, subdomain)
            )
            return s, resp_login_form, False, False, True, reason

        # https://loc3.caixabank.es/GPeticiones;WebLogicSession
        # =sMXMxe1ozyHthcXrk7Qd0KWKrk7Pc502Kwrd9VFcgFPJRM_wIcsu
        # !440257436!1273488684
        action_url, _ = extract.build_req_params_from_form_html_patched(
            resp_login_form.text,
            'LGN',
            is_ordered=True
        )
        req_login_url = urljoin(resp_login_form.url, action_url)

        _seed, passw_encrypted = self._get_encrypted(
            oper_param,
            a_param,
            c_param,
            d_param,
            lon_param
        ).split()  # type: Tuple[str, str]

        req_login_params = OrderedDict([
            ('FLAG_DEMO', '0'),
            ('FLAG_PART_EMPR', 'P'),
            ('TIPUS_IDENT', '2'),
            ('D', passw_encrypted),  # encrypted userpass '745f3ca19d13411f'
            ('E', self._get_username()),
            ('PN', 'LGN'),
            ('PE', '8'),
        ])

        time.sleep(0.1)

        environ_cookies = ENVIRON_COOKIES.get(self.db_financial_entity_access_id)  # type: Optional[str]
        assert environ_cookies  # should be existing, must be checked earlier in login_to_subdomain

        self.logger.info('Set confirmed environment cookies for access {}'.format(
            self.db_financial_entity_access_id
        ))
        s = requests_helpers.update_mass_cookies_from_str(s, environ_cookies, '.caixabank.es')

        resp_logged_in = s.post(
            req_login_url,
            data=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        # Some access return different resp_logged_in.url and initial login requests are required
        # Additional login requests are required for:
        # 'https://loc6.caixabank.es/jsp/elolgnp001401.jsp?REF_STC=igaJwA4qLWQiw_DjUmV_jhBMrYaGzR_7tKSwfykjBlasw_jxO296Aw&IDIOMA=02&ENTORNO=0&CANAL=I'
        # No additional login requests are required for:
        # 'https://loc3.caixabank.es/GPeticiones;WebLogicSession=YfPg9WzyuOdBIweocU7x4R_PFcC4TgJRDaOuQsDVfoBaAzFUTkbt!1308297310!177209720'
        if 'caixabank.es/jsp' in resp_logged_in.url:
            self.logger.info("The access {} CONTAINS 'caixabank.es/jsp' with subdomain {}"
                             .format(self.db_financial_entity_access_id, subdomain))
            resp_logged_in = self._additional_login_reqs_for_jsp(resp_logged_in, s)
        else:
            self.logger.info("The access {} NOT CONTAINS 'caixabank.es/jsp' with subdomain {}"
                             .format(self.db_financial_entity_access_id, subdomain))

        # Disabled subdomain, consider as an attempt to redirection to continue with another subdomain
        # (dev_regular/1_1_resp_err_subdomain.html)
        if DISABLED_SUBDOMAIN_MARKER in resp_logged_in.text:
            return s, resp_logged_in, False, False, True, 'Disabled subdomain {}'.format(subdomain)

        # Sometimes website tries to redirect to another subdomain
        # via intermediate subdomain 'lo.caixa'.
        # If it happened - abort the scraping
        # for this subdomain to avoid the situation being redirected to
        # a subdomain where scraping already is in progress (in this case
        # it will disconnect previous working session)
        is_redirected = False
        resp_logged_in_or_redirected = resp_logged_in  # type: Response
        if 'location.replace' in resp_logged_in.text:
            if allow_redirection:
                s, resp_logged_in_or_redirected = self._login_redirect(s, resp_logged_in, subdomain)
                is_redirected = True
            else:
                redirect_url = parse_helpers.get_redirection_url(resp_logged_in.text)
                self.logger.info(
                    "Attempt to redirect to another subdomain: from {} to {}. Skip {}".format(
                        subdomain,
                        parse_helpers.get_redirection_url(resp_logged_in.text),
                        parse_helpers.get_subdomain_of_url(redirect_url)
                    )
                )
                return s, resp_logged_in, False, False, True, ''

        # Early detection
        _is_logged, is_credentials_error = self._is_logged_is_cred_errs(resp_logged_in_or_redirected)
        if is_credentials_error:
            return s, resp_logged_in_or_redirected, False, is_credentials_error, is_redirected, ''

        # Carpeta support (optional login step)
        resp_carpeta = resp_logged_in_or_redirected
        if 'Identificación carpeta' in resp_logged_in_or_redirected.text:
            req_carpeta_link, req_carpeta_params = extract.build_req_params_from_form_html_patched(
                resp_logged_in_or_redirected.text,
                'LGN'
            )
            req_carpeta_params['carpeta'] = self.username_second
            req_carpeta_params['NOM_CARPETA'] = self.username_second

            resp_carpeta = s.post(
                urljoin(resp_logged_in_or_redirected.url, req_carpeta_link),
                data=req_carpeta_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

        s, resp_logged_in_final, reason = self._additional_login_reqs(s, resp_carpeta)

        s, resp_logged_in_w_weblogic = self._reopen_resp_with_weblogic_session_url(s, resp_logged_in_final)
        is_logged, is_credentials_error = self._is_logged_is_cred_errs(resp_logged_in_final)

        if WEB_LOGIC_SESSION not in resp_logged_in_w_weblogic.url:
            reason = ('Expected but not found WebLogicSession in resp.url'
                      '`is_logged` was {}'.format(is_logged))
            is_logged = False

        if not is_logged:
            reason = self._get_failed_login_reason(resp_logged_in_w_weblogic, reason)

        return s, resp_logged_in_w_weblogic, is_logged, is_credentials_error, is_redirected, reason

    def _get_failed_login_reason(
            self,
            resp_login: Response,
            reason: str) -> str:
        """Check the failed login reason when is_logged is False
        :return reason
        """

        if CAIXA_SIGN_APP_ACTIVATION_REQUIRED_MARKER in resp_login.text:
            self.logger.error('Detected "{}". Consider as "{}"'.format(
                CAIXA_SIGN_APP_ERR,
                DOUBLE_AUTH_REQUIRED_TYPE_COMMON
            ))
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON
        elif BLOCKED_USER_MARKER in resp_login.text:
            self.logger.error('Detected "{}". Consider as "{}"'.format(
                BLOCKED_USER_MARKER,
                BLOCKED_USER_TYPE_COMMON
            ))
            reason = BLOCKED_USER_TYPE_COMMON
        elif any(m in resp_login.text for m in EXPIRED_USER_MARKERS):
            self.logger.error('Detected "{}" into login response'.format(
                EXPIRED_USER_TYPE_COMMON
            ))
            reason = EXPIRED_USER_TYPE_COMMON

        return reason

    def _additional_login_reqs_for_jsp(self, resp_logged_in, s):
        # Deprecated request. Keep until 30/04/2023
        # resp_logged_in2 = s.get(
        #     resp_logged_in.url,
        #     headers=self.req_headers,
        #     proxies=self.req_proxies
        # )
        resp_logged_in2_url = parse_helpers.get_redirection_url(resp_logged_in.text),
        time.sleep(0.1)
        resp_logged_in2 = s.get(
            resp_logged_in2_url[0],
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        time.sleep(0.1)
        # Deprecated request. Keep until 30/04/2023
        # resp_logged_in4 = s.get(
        #     resp_logged_in3.url,
        #     headers=self.req_headers,
        #     proxies=self.req_proxies
        # )
        # time.sleep(1)
        return resp_logged_in2

    def _extract_companies(self, s: MySession,
                           resp_logged_in: Response) -> Tuple[List[Company], Response]:
        """
        It is possible to switch only one company from the list,
        then the urls will be changed and need to _extract_companies again
        """
        # from frame of 'Cambiar usuario' page
        req_companies_params = ('PN=LGU&PE=1&CLICK_ORIG=EIN_BPE_000&FLAG_PE=E'
                                '&FLAG_BORSA=false&BUFFER=&REMOVE_REFVAL=1')

        # resp_recent - always the same base after logged in
        resp_companies = s.get(
            # 'https://loc4.caixabank.es/GPeticiones
            # ;WebLogicSession=4DHVu-WDOBuCbN8z_gRLVwzt7UO8hdH5v80LTAFjLxM0gzKvDqDg!-268311288!1580284846
            splitquery(resp_logged_in.url)[0],
            params=req_companies_params,
            headers=self.basic_req_headers_updated({'Referer': resp_logged_in.url}),
            proxies=self.req_proxies
        )

        companies = (parse_helpers.get_companies(self.logger, resp_companies.text)
                     or parse_helpers.get_companies_new(self.logger, resp_companies.text))
        if not companies:
            # One contract
            company_title = parse_helpers.get_company_title(resp_logged_in.text)
            company = Company(title=company_title, request_params=[])
            if company_title:
                companies.append(company)
            else:
                self.logger.error("_extract_companies: can't extract company title to process. Abort.")
                return

        # Pagination
        resp_companies_i = resp_companies
        for page_ix in range(1, 11):
            if 'Siguientes' not in resp_companies_i.text:
                break

            self.logger.info('Get companies from page #{}'.format(page_ix + 1))

            req_link, req_params = parse_helpers.build_next_page_w_companies_req_params(resp_companies_i.text)

            if not req_params:
                self.basic_log_wrong_layout(resp_companies_i, "_extract_companies: can't get next page req_params")
                break

            resp_companies_i = s.post(
                urljoin(resp_companies_i.url, req_link),
                data=req_params,
                headers=self.basic_req_headers_updated({'Referer': resp_companies_i.url}),
                proxies=self.req_proxies
            )

            companies_i = (parse_helpers.get_companies(self.logger, resp_companies_i.text)
                           or parse_helpers.get_companies_new(self.logger, resp_companies_i.text))
            if list_funcs.is_sublist([c.title for c in companies], [c.title for c in companies_i]):
                self.logger.warning('_extract_companies: hanging pagination loop detected. Break the loop')
                break
            companies.extend(companies_i)

        return companies, resp_companies_i

    def process_subdomain(self,
                          s: MySession,
                          resp_logged_in: Response,
                          subdomain: str,
                          subdomain_ix: int) -> bool:
        with self.lock:
            if not self.companies_to_scrape_idxs:
                self.logger.info("{}: process_subdomain: no more companies to scrape. Exit".format(
                    subdomain
                ))
                return True

        # ix == 0 then it is the first and already logged in subdomain
        # first subdomain already extracted necessary info
        if subdomain_ix != 0:
            try:
                s, resp_logged_in, is_logged, is_credentials_error, is_redirected, reason = self.login(subdomain)
            except:
                self.logger.error(traceback.format_exc())
                return False
            if is_redirected:
                return False
            if not is_logged:
                self.logger.error("Can't log in subdomain {}. Skip".format(subdomain))
                return False
        self.process_access(s, resp_logged_in, subdomain)
        return True

    def process_access(self,
                       s: MySession,
                       resp_logged_in: Response,
                       subdomain: str) -> bool:

        # https://loc4.caixabank.es/GPeticiones
        # ;WebLogicSession=4DHVu-WDOBuCbN8z_gRLVwzt7UO8hdH5v80LTAFjLxM0gzKvDqDg!-268311288!1580284846
        # assert 'WebLogicSession' in resp_logged_in.url
        # to sync from different threads
        while True:
            with self.lock:
                if self.companies_to_scrape_idxs:
                    company_ix = self.companies_to_scrape_idxs.pop()
                else:
                    self.logger.info("{}: process_access: no more companies to scrape. Exit".format(
                        subdomain
                    ))
                    break
            # only serial processing
            self.process_company(s, resp_logged_in, company_ix, subdomain)
        return True

    def _extract_accounts_parsed(self,
                                 s: MySession,
                                 resp_company_home: Response,
                                 company_title: str) -> Tuple[MySession, List[AccountParsed]]:

        self.logger.info('{}: get accounts_parsed'.format(company_title))
        page_ix = 0

        # frame with accounts, 'Tesoreria' menu

        # 1st page with accounts
        req_accounts_params = OrderedDict([
            ('PN', 'GCT'),
            ('PE', '14'),
            ('CLICK_ORIG', 'MNU_EMP_EMP_0',),
            ('REMOVE_REFVAL', '1'),
            ('NUMERO_PESTANYA', '0')
        ])

        # # frame with accounts, 'Cuenta' menu
        # req_accounts_params_part = OrderedDict([
        #     ('PN', 'GCT'),
        #     ('PE', '14'),
        #     ('CLICK_ORIG', 'MNU_PAR_PAR_1',),
        #     ('REMOVE_REFVAL', '1'),
        #     ('NUMERO_PESTANYA', '0')
        # ])
        # req_main_frame_link = parse_helpers.get_main_frame_link_w_websession(resp_company_home.text)
        # req_wls_link = splitquery(req_main_frame_link)[0]  # WebLogicSession
        # req_accounts_url = urljoin(resp_company_home.url, req_wls_link)
        time.sleep(0.2)
        resp_accounts = s.post(
            splitquery(resp_company_home.url)[0],
            data=req_accounts_params,
            headers=self.basic_req_headers_updated({'Referer': resp_company_home.url}),
            proxies=self.req_proxies
        )

        # Works only of there are accounts,
        # wrong for -a 16556, FRANCISCO JAVIER MAURICIO FOCHE:
        #   no accounts found (with COMPANY_HAS_NO_ACCOUNTS_MARKER)
        is_private_view = 'Mis cuentas' in resp_accounts.text
        self.logger.info("{}: is 'Particulares' view: {}".format(
            company_title,
            is_private_view
        ))

        # -a 16556 FRANCISCO DE ASIS RIPOLL SOGAS:
        # accounts ES50 2100 8198 6102 0015 1457 CUENTA
        # ES19 2100 8198 6902 0019 2848 CUENTA
        # available in both: empresas (corporate) and particulatres (private) view
        # Empresas: dark gray header
        # Particulares: light blue header
        # (to switch between them manually click on top right username
        # and select the view from right slider)
        accounts_parsed = (
                parse_helpers.get_accounts_parsed(self.logger, resp_accounts.text, page_ix)
                or parse_helpers_particulares.get_accounts_parsed(self.logger, resp_accounts.text, page_ix)
        )
        if not accounts_parsed:
            if any(m in resp_accounts.text for m in COMPANY_HAS_NO_ACCOUNTS_MARKERS):
                self.logger.info(
                    '{}: no accounts found (with COMPANY_HAS_NO_ACCOUNTS_MARKERS)'.format(company_title)
                )
            else:
                self.logger.error(
                    '{}: suspicious results: no accounts found. '
                    'RESPONSE:\n{}'.format(company_title, resp_accounts.text)
                )

        # See 5_1st_page_manyaccs_resp_tesoreria.html,
        # avoid false positive detection for verSiguientes() from 5_resp_accs_202009
        if (('>Siguientes<' not in resp_accounts.text) and  # Particulares??/MicroBank (former Tesoreria view)
                ('Ver siguientes' not in resp_accounts.text)):  # Empresas (Cuentas view) -a 20312
            self.logger.info('{}: no more pages with accounts'.format(company_title))
            for acc in accounts_parsed:
                acc['financial_entity_account_id'] = self._get_fin_ent_account_id(acc)
            return s, accounts_parsed

        # Iterate over pages with accounts (-u 149727 -a 6033 VIA CELERE DESARROLLOS INMOBILIARIOS)

        self.logger.info('{}: get more accounts_parsed'.format(company_title))

        # Expect
        # PN	GCT
        # PE	111
        # NCTREL	020
        # CLAVE_CONTINUACION_CLCOTG	000
        # CLAVE_CONTINUACION_TOOFCU	000000000000000 000000000000000
        # CLAVE_CONTINUACION_TOGECU	00000000000 000000000000000
        # CLAVE_CONTINUACION_CLCOTG_SIG	020
        # CLAVE_CONTINUACION_TOOFCU_SIG	357100000000000 000000198388816
        # CLAVE_CONTINUACION_TOGECU_SIG	00000000000 000000198388816
        # SUMA_OFICINA_P	3.30091216E8
        # SUMA_TOTAL_P	3.30091216E8
        # SUMA_OFICINA_E	1983888.16
        # SUMA_TOTAL_E	1983888.16
        # REFVAL_SIMPLE_NUMERO_CUENTA
        # ORIGEN_INVOCACION
        # FLAG_PE	E
        # TORNA_PN_CCT	GCT
        # TORNA_PE_CCT	11
        # ALIAS_CUENTA
        # FLAG_MONEDA	0
        # NumFilasTabla	1
        # FLAG_KEEP_THE_CHANGE
        # MONEDA
        # MOSTRAR_TRASPASO_RAPIDO	N
        # CLICK_ORIG	''
        _, req_accs_next_params = extract.build_req_params_from_form_html_patched(
            resp_accounts.text,
            'formPrincipal',
            is_ordered=True
        )

        # Fill as js
        req_accs_next_params['CLICK_ORIG'] = 'PAG_GCT_11'
        req_accs_next_params['PE'] = '111'  # '11' causes hanging on 2nd page

        # Check for 'no next page' marker (Tesoreria '000', Cuentas '')
        while req_accs_next_params['CLAVE_CONTINUACION_CLCOTG_SIG'] not in ['000', '']:
            page_ix += 1
            if page_ix >= ACCS_PAGE_NUM_MAX_LIMIT:
                self.logger.error("{}: hanging loop detected while extracting accounts. "
                                  "Will scrape account only from the first page".format(company_title))
                # Drop all accs from additional pages
                # because most probably they are repeating accounts
                # with different refval_simple_numero_cuenta_param
                accounts_parsed = accounts_parsed[:20]
                break

            req_accs_next_params['CLAVE_CONTINUACION_CLCOTG'] = req_accs_next_params['CLAVE_CONTINUACION_CLCOTG_SIG']
            req_accs_next_params['CLAVE_CONTINUACION_TOOFCU'] = req_accs_next_params['CLAVE_CONTINUACION_TOOFCU_SIG']
            req_accs_next_params['CLAVE_CONTINUACION_TOGECU'] = req_accs_next_params['CLAVE_CONTINUACION_TOGECU_SIG']

            resp_accounts_i = s.post(
                splitquery(resp_company_home.url)[0],
                data=req_accs_next_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )
            accounts_parsed_i = parse_helpers.get_accounts_parsed(self.logger, resp_accounts_i.text, page_ix)
            self.logger.info("{}: got {} account(s) from page #{}".format(
                company_title,
                len(accounts_parsed_i),
                page_ix + 1
            ))
            accounts_parsed += accounts_parsed_i

            # patch for the main/prev req_accs_next_params
            req_accs_next_params_patch = parse_helpers.get_next_page_with_accs_params_patch(resp_accounts_i.text)
            if not req_accs_next_params_patch:
                self.logger.error("{}: expected req_accs_next_params_patch, got nothing. "
                                  "Check req params. Continue as is".format(company_title))
                break
            for k in ['CLAVE_CONTINUACION_CLCOTG_SIG', 'CLAVE_CONTINUACION_TOOFCU_SIG',
                      'CLAVE_CONTINUACION_TOGECU_SIG']:
                req_accs_next_params[k] = req_accs_next_params_patch[k]

            pass

        if page_ix == 0:
            self.logger.warning("{}: expected >1 pages with accounts, got 1. "
                                "Check req params. Continue as is".format(company_title))

        # Mutate accounts: set fin_ent_account_id explicitly,
        # necessary for children (Bankia)
        for acc in accounts_parsed:
            acc['financial_entity_account_id'] = self._get_fin_ent_account_id(acc)
        return s, accounts_parsed

    def _is_valid_company(
            self,
            company: Company,
            resp_company_home: Response) -> bool:
        """Check that switched to the target company with logs on failures
        :return is_valid
        """

        comp_title_lower = parse_helpers.lower_letters(company.title)
        company_titles_from_page = parse_helpers.get_available_company_titles(resp_company_home.text)

        for manual_action in MANDATORY_MANUAL_ACTION_MARKERS:
            if not any(company_titles_from_page) and manual_action in resp_company_home.text:
                self.logger.error(
                    '{}: {}: mandatory manual action required: "{}". Pls, inform the customer. '
                    'Skip the company (contract)'.format(
                        company.title,
                        ERR_CANT_SWITCH_TO_CONTRACT.description,
                        manual_action,
                    )
                )
                return False

        # To be sure that was switched correctly
        # handle case if company title is too long and was cut on the page (-u 242841 -a 12615)
        for company_title_from_page in company_titles_from_page:
            if not company_title_from_page:
                continue
            comp_title_from_page_lower = parse_helpers.lower_letters(company_title_from_page)
            max_ix = min(len(comp_title_lower), len(comp_title_from_page_lower)) - 1
            comp_title_lower_stripped = comp_title_lower[:max_ix]
            comp_title_from_page_lower_stripped = comp_title_from_page_lower[:max_ix]
            if (fuzzy_equal(comp_title_lower_stripped, comp_title_from_page_lower_stripped)
                    or fuzzy_equal(comp_title_from_page_lower_stripped, comp_title_lower_stripped)):
                return True

        self.logger.error(
            "Can't be sure that switched to correct company. "
            "Too different titles: expected '{}', got from resp: {}. "
            "Skip the company.".format(
                company.title,
                company_titles_from_page
            )
        )
        return False

    def _switch_to_company(
            self,
            s: MySession,
            resp_logged_in: Response,
            company_ix: int,
            subdomain: str) -> Tuple[bool, Optional[Company], Response]:
        # need to extract new Company due to changed urls for all except first company
        companies, resp_companies = self._extract_companies(s, resp_logged_in)
        self.logger.info("{}: got {} companies: {}".format(
            subdomain,
            len(companies),
            [c.title for c in companies]
        ))
        if len(companies) != self.n_companies:
            self.logger.error(
                "{}: can't extract correct list of companies: expected {}, got {}. Skip the company #{}. "
                "RESPONSE:\n\n{}".format(
                    subdomain,
                    self.n_companies,
                    len(companies),
                    company_ix,
                    resp_companies.text
                )
            )
            return False, None, Response()
        company = companies[company_ix]
        # Some companies (-a 21910, VIA CELERE GESTION DE PROYECTOS S.L.)
        # require extra reqs similar to _additional_login_reqs due to
        # enabled KYC actions
        resp_company_home_or_kyc = resp_logged_in

        self.logger.info("{}: company #{} named '{}'".format(subdomain, company_ix, company.title))
        # no req_company_home_params - one company added manually, no need to switch
        resp_switch_text_wo_tags = ''
        req_company_home_params = OrderedDict()  # type: Dict[str, str]
        if company.request_params:
            # switch to specific company
            for _ in range(3):
                req_switch_comp_params = parse_helpers.req_switch_comp_params(company)
                resp_switch_company = s.post(
                    splitquery(resp_logged_in.url)[0],
                    data=req_switch_comp_params,
                    headers=self.req_headers,
                    proxies=self.req_proxies
                )

                _, req_company_home_params = extract.build_req_params_from_form_html_patched(
                    resp_switch_company.text,
                    'LGN',
                    is_ordered=True
                )
                # success
                if req_company_home_params:
                    break

                if not req_company_home_params:
                    resp_switch_text_wo_tags = extract.text_wo_scripts_and_tags(resp_switch_company.text)
                    if 'Usted no puede acceder a este usuario porque ha caducado' in resp_switch_company.text:
                        self.logger.warning(
                            "Company {} is not accessible for the customer. Skip the company. "
                            "RESPONSE TEXT:\n\n{}".format(
                                company.title,
                                resp_switch_text_wo_tags
                            )
                        )
                        return False, None, Response()
                time.sleep(1 + random.random())
            else:
                self.logger.error(
                    "Can't switch to company {}. Unknown reason. Skip the company. "
                    "RESPONSE TEXT:\n\n{}".format(
                        company.title,
                        resp_switch_text_wo_tags
                    )
                )
                return False, None, Response()

            resp_company_home_or_kyc = s.post(
                splitquery(resp_logged_in.url)[0],
                data=req_company_home_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

        s, resp_company_home, _reason = self._additional_login_reqs(
            s,
            resp_company_home_or_kyc
        )

        ok = self._is_valid_company(
            company,
            resp_company_home
        )

        if not ok:
            self.basic_set_movements_scraping_finished_for_contract_accounts(
                company.title,
                ERR_CANT_SWITCH_TO_CONTRACT
            )
            return False, None, Response()  # already reported

        return True, company, resp_company_home

    def process_company(self,
                        s: MySession,
                        resp_logged_in: Response,
                        company_ix: int,
                        subdomain: str) -> bool:
        self.logger.info("{}: process company #{}".format(subdomain, company_ix))
        ok, company, resp_company_home = self._switch_to_company(s, resp_logged_in, company_ix, subdomain)
        if not ok:
            return False

        assert company  # for mypy

        company_title_from_homepage = parse_helpers.get_company_title(resp_company_home.text)

        if company_title_from_homepage != company.title:
            self.logger.info("{}: company #{}: title '{}' will be replaced by '{}' for accounts".format(
                subdomain,
                company_ix,
                company.title,
                company_title_from_homepage
            ))

        s, accounts_parsed = self._extract_accounts_parsed(s, resp_company_home, company.title)
        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                company_title_from_homepage,
                account_parsed,
            )
            for account_parsed in accounts_parsed
            # skip accounts with only account_alias - they are not current accounts
            if account_parsed['financial_entity_account_id']
        ]

        self.logger.info('{}: got {} accounts: {}'.format(
            company_title_from_homepage,
            len(accounts_parsed),
            accounts_parsed
        ))
        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent("GET ACCOUNTS")

        accounts_scraped_dict = self.basic_gen_accounts_scraped_dict(accounts_scraped)

        acc_nos = [a['account_no'] + a['account_alias'] for a in accounts_parsed]
        for acc_ix, _ in enumerate(accounts_parsed):
            is_success, should_renew_accounts_parsed = self.process_account(
                s,
                resp_company_home,
                company_title_from_homepage,
                accounts_parsed,
                accounts_scraped_dict,
                acc_ix,
                company.title
            )
            # renew if necessary for all accounts except the last one
            if should_renew_accounts_parsed and (acc_ix < len(accounts_parsed) - 1):
                ok, s, accounts_parsed_renewed = self._renew_accounts_parsed(
                    s,
                    resp_company_home,
                    company.title,
                    accounts_parsed,
                    accounts_parsed[acc_ix]
                )
                if ok:
                    accounts_parsed = accounts_parsed_renewed
                    self.logger.info("{}: Retry to process account with renewed accounts_parsed".format(
                        accounts_parsed[acc_ix]['account_alias']
                    ))
                    # process failed account after renew the accounts_parsed
                    is_success, should_renew_accounts_parsed = self.process_account(
                        s,
                        resp_company_home,
                        company_title_from_homepage,
                        accounts_parsed,
                        accounts_scraped_dict,
                        acc_ix,
                        company.title
                    )
                    if not is_success:
                        self.logger.error("{}: Failed retry to process account with renewed accounts_parsed".format(
                            accounts_parsed[acc_ix]['account_alias']
                        ))
                    continue
                else:
                    acc_renew_nos = [a['account_no'] + a['account_alias'] for a in accounts_parsed_renewed]
                    self.logger.error(
                        "Can't get correct accounts_parsed_renewed (total {}) != accounts_parsed (total {}).\n"
                        "accounts_parsed_renewed={}.\naccount_parsed={} (alias '{}').\n"
                        "Skip account processing after {}".format(
                            len(acc_renew_nos),
                            len(acc_nos),
                            acc_renew_nos,
                            acc_nos,
                            accounts_parsed[acc_ix]['account_no'],
                            accounts_parsed[acc_ix]['account_alias']
                        )
                    )
                    break

        # implemented in caixa_regular_receipts_scraper.py
        self.download_correspondence(s, resp_company_home, company.title)
        return True

    def _renew_accounts_parsed(
            self,
            s: MySession,
            resp_company_home: Response,
            company_title: str,
            accounts_parsed: List[AccountParsed],
            account_parsed: AccountParsed) -> Tuple[bool, MySession, List[AccountParsed]]:
        """Calls _extract_accounts_parsed to get new refvals and checks results"""
        account_scraped = account_parsed['account_no'] if account_parsed['account_no'] else account_parsed['account_alias']
        self.logger.info('Renew accounts_parsed (due to pagination or err) '
                         'on scraping for {}'.format(account_scraped))
        s, accounts_parsed_renewed = self._extract_accounts_parsed(s, resp_company_home, company_title)
        acc_nos = [a['account_no'] + a['account_alias'] for a in accounts_parsed]
        acc_renew_nos = [a['account_no'] + a['account_alias'] for a in accounts_parsed_renewed]
        if acc_renew_nos != acc_nos:
            return False, s, accounts_parsed_renewed
        self.logger.info('Successfully renewed accounts_parsed')
        return True, s, accounts_parsed_renewed

    def _is_validated_acc_at_page_w_movs(
            self,
            resp: Response,
            account_no: str,
            check_point: str,
            is_skip_on_err_msg=True) -> bool:
        """Checks that the fin_ent_account_id at the page is that we need
        to avoid movs of another account
        """
        account_no_from_page = parse_helpers.get_account_no_from_movs_page(
            resp.text
        ) or parse_helpers_particulares.get_account_no_from_movs_page(
            resp.text
        )
        # fin_ent_account_id can be shorter than from page (Bankia case)
        if account_no != account_no_from_page:
            msg = (
                "Can't open correct account page with {}. "
                "Expected for {}, got for {}. "
                "Check req params.".format(
                    check_point,
                    account_no,
                    account_no_from_page
                )
            )
            if is_skip_on_err_msg:
                msg += ' Skip movements scraping for {}'.format(account_no)
                self.logger.error(msg)
            else:
                self.logger.warning(msg)

            return False
        return True

    def _get_and_save_movs_by_dates_for_empresas(
            self,
            s: MySession,
            resp_company_home: Response,
            resp_recent_movs: Response,
            account_parsed: AccountParsed,
            account_scraped: AccountScraped) -> Tuple[bool, bool]:
        """:returns: (is_success, should_renew_next_account_parsed)"""

        should_renew_next_account_parsed = False  # always after pagination to get new refval
        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        account_no = account_scraped.AccountNo
        self.logger.info('{}: process empresas-like account view'.format(fin_ent_account_id))

        date_from_str = self.basic_get_date_from(
            fin_ent_account_id,
            rescraping_offset=SCRAP_MOVS_OFFSET__CUSTOM,
            max_offset=MOVS_MAX_OFFSET,
            max_autoincreasing_offset=MOVS_MAX_OFFSET
        )
        date_from = date_funcs.get_date_from_str(date_from_str)

        try:
            refval_numero_cuenta_for_req_filter_by_dates = parse_helpers.get_numero_cuenta_for_req_filter_by_dates(
                resp_recent_movs.text,
                account_parsed['account_page_ix']
            )
        except:
            self.logger.error(
                "{}: can't extract movements: HANDLED EXCEPTION: {}.\nSkip now.\n\nRESPONSE\n\n{}".format(
                    fin_ent_account_id,
                    traceback.format_exc(),
                    resp_recent_movs.text
                )
            )
            return False, True

        req_movs_filter_by_dates_params = parse_helpers.req_movs_filter_by_dates_params(
            date_from_str,
            self.date_to_str,
            refval_numero_cuenta_for_req_filter_by_dates
        )

        resp_movs_filtered = s.post(
            splitquery(resp_company_home.url)[0],
            data=req_movs_filter_by_dates_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if not self._is_validated_acc_at_page_w_movs(resp_movs_filtered, account_no, 'filtered movs'):
            return False, True

        mov_details_req_params = parse_helpers.get_movs_detail_req_params(
            resp_recent_movs.text
        )

        # desc
        movements_parsed = parse_helpers.get_movements_parsed(
            self.logger,
            fin_ent_account_id,
            resp_movs_filtered.text,
            mov_details_req_params
        )

        clave_continuation_oper_param = parse_helpers.get_clave_continuacion_oper_param(
            resp_movs_filtered.text
        )

        if not self.basic_should_scrape_extended_descriptions():
            self.logger.info("{}: doesn't require extended descriptions".format(fin_ent_account_id))
        else:
            movements_parsed = self.basic_get_movements_parsed_w_extra_details(
                s,
                movements_parsed,
                account_scraped,
                date_from_str,
                n_mov_details_workers=MOV_DETAILS_MAX_WORKERS,
                meta={
                    'resp_movs_filtered': resp_movs_filtered,
                    'page': 1,
                }
            )

        # Handle pagination
        if len(movements_parsed) >= MAX_MOVS_PER_PAGE:
            # Account has more movements -> do pagination
            resp_most_recent = resp_movs_filtered
            should_renew_next_account_parsed = True  # always after pagination
            for page_ix in range(MOVS_PAGE_NUM_MAX_LIMIT):
                refval_params = parse_helpers.get_refval_params_during_pagination(
                    resp_most_recent.text
                )

                req_movs_next_page_params = parse_helpers.req_movs_next_page_params(
                    refval_params=refval_params,
                    clave_continuation_oper_param=clave_continuation_oper_param,
                    loop_ix=page_ix,
                    date_from_str=date_from_str,
                    date_to_str=self.date_to_str,
                    max_movs_per_page=MAX_MOVS_PER_PAGE,
                )

                req_headers = self.basic_req_headers_updated({
                    'Referer': resp_most_recent.url
                })
                resp_movs_next_page = s.post(
                    splitquery(resp_company_home.url)[0],
                    data=req_movs_next_page_params,
                    headers=req_headers,
                    proxies=self.req_proxies
                )

                # replace 'REFVAL_SIMPLE_NUMERO_CUENTA', 'REFVAL_SIMPLE_CUENTA'
                mov_details_req_params.update(refval_params)
                movements_parsed_i = parse_helpers.get_movements_parsed(
                    self.logger,
                    fin_ent_account_id,
                    resp_movs_next_page.text,
                    mov_details_req_params
                )

                # detect hanged loop (may open 1st page after the last)
                if list_funcs.is_sublist(parse_helpers.movs_parsed_tuples(movements_parsed),
                                         parse_helpers.movs_parsed_tuples(movements_parsed_i)):
                    self.logger.info('{}: hanging loop detected: extracted already scraped movements. '
                                     'Abort pagination'.format(fin_ent_account_id))
                    break

                if self.basic_should_scrape_extended_descriptions():
                    meta = {
                        'resp_movs_filtered': resp_movs_filtered,
                        'page': page_ix + 1,
                    }
                    movements_parsed_i = self.basic_get_movements_parsed_w_extra_details(
                        s,
                        movements_parsed_i,
                        account_scraped,
                        date_from_str,
                        n_mov_details_workers=MOV_DETAILS_MAX_WORKERS,
                        meta=meta
                    )

                movements_parsed.extend(movements_parsed_i)
                if movements_parsed_i:
                    self.logger.info("{}: page {}: got movs since {} to {}".format(
                        fin_ent_account_id,
                        page_ix + 2,  # 2 - first page during pagination
                        movements_parsed_i[0]['operation_date'],
                        movements_parsed_i[-1]['operation_date']
                    ))

                # be sure that can process correct pagination
                if not refval_params.get('REFVAL_SIMPLE_NUMERO_CUENTA'):
                    self.logger.error(
                        "{}: can't extract movements due to can't process pagination: "
                        "expected REFVAL_SIMPLE_NUMERO_CUENTA param. "
                        "Skip now.\n\nRESPONSE:\n\n{}".format(
                            fin_ent_account_id,
                            resp_movs_next_page.text
                        )
                    )
                    return False, True

                clave_continuation_oper_param = parse_helpers.get_clave_continuacion_oper_param(
                    resp_movs_next_page.text
                )
                if len(movements_parsed_i) < MAX_MOVS_PER_PAGE:
                    self.logger.info("{}: no more movements to paginate".format(
                        fin_ent_account_id
                    ))
                    break

                # avoid pagination to too old dates (backend error)
                # break if already got too old mov
                date_oldest_str = movements_parsed_i[-1]['operation_date']  # '24/12/2018'
                date_oldest = date_funcs.get_date_from_str(date_oldest_str)
                if date_oldest < date_from:
                    self.logger.warning("{}: got too old movement {}. Break explicitly".format(
                        fin_ent_account_id,
                        date_oldest_str
                    ))
                    break
                resp_most_recent = resp_movs_next_page
                continue

        movements_parsed = parse_helpers.calculate_pending_amounts(
            self.logger,
            fin_ent_account_id,
            movements_parsed
        )

        movements_scraped, movements_parsed_corresponding = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            bankoffice_details_name='Oficina',
            payer_details_name='Remitente'
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        _, movements_scraped_w_receipts_info = self.download_receipts(
            s,
            resp_movs_filtered,
            account_scraped,
            movements_scraped,
            movements_parsed_corresponding
        )

        self.basic_set_movement_scraped_references(
            account_scraped,
            movements_scraped_w_receipts_info,
            parse_helpers.parse_reference_from_receipt
        )

        return True, should_renew_next_account_parsed

    def _get_and_save_movs_by_dates_for_particulares(
            self,
            s: MySession,
            resp_company_home: Response,
            resp_recent_movs: Response,
            account_parsed: AccountParsed,
            account_scraped: AccountScraped) -> Tuple[bool, bool]:
        """:returns: (is_success, should_renew_next_account_parsed)"""

        should_renew_next_account_parsed = False  # always after pagination to get new refval
        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        self.logger.info('{}: process new particulares-like account view'.format(fin_ent_account_id))

        date_from_str = self.basic_get_date_from(
            fin_ent_account_id,
            rescraping_offset=SCRAP_MOVS_OFFSET__CUSTOM,
            max_offset=MOVS_MAX_OFFSET,
            max_autoincreasing_offset=MOVS_MAX_OFFSET
        )
        refval_params = parse_helpers_particulares.get_refval_particulares_params(resp_recent_movs.text)

        req_movs_url = splitquery(resp_company_home.url)[0]
        req_movs_filter_by_dates_params = parse_helpers_particulares.req_movs_filter_by_dates_params(
            refval_params,
            date_from_str,
            self.date_to_str
        )

        resp_movs_filtered = s.post(
            req_movs_url,
            data=req_movs_filter_by_dates_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        movements_parsed = parse_helpers_particulares.get_movements_parsed(
            self.logger,
            fin_ent_account_id,
            resp_movs_filtered.text,
            refval_params
        )

        if not self.basic_should_scrape_extended_descriptions():
            self.logger.info("{}: doesn't require extended descriptions".format(fin_ent_account_id))
        else:
            movements_parsed = self.basic_get_movements_parsed_w_extra_details(
                s,
                movements_parsed,
                account_scraped,
                date_from_str,
                n_mov_details_workers=MOV_DETAILS_MAX_WORKERS,
                meta={
                    'resp_movs_filtered': resp_movs_filtered,
                    'page': 1,
                },
                callback=self.process_movement_new
            )

        resp_prev = resp_movs_filtered
        for page_ix in range(2, MOVS_PAGE_NUM_MAX_LIMIT):  # avoid inf loops
            has_next_page = bool(parse_helpers_particulares.get_movs_next_page_clave_continuacion_bus_param(
                resp_prev.text))
            if not has_next_page:
                break
            should_renew_next_account_parsed = True  # always after pagination
            oldest_mov_date = ''
            if movements_parsed:
                oldest_mov_date = movements_parsed[-1]['operation_date']
            self.logger.info('{}: open page #{} to get movs before {}'.format(
                fin_ent_account_id,
                page_ix,
                oldest_mov_date
            ))
            req_movs_params_i = parse_helpers_particulares.req_movs_next_page_params(
                resp_prev.text,
                refval_params,
                date_from_str,
                self.date_to_str
            )
            resp_movs_i = s.post(
                req_movs_url,
                data=req_movs_params_i,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            # Wrong default ValueDate, need to get from details
            movements_parsed_i = parse_helpers_particulares.get_movements_parsed(
                self.logger,
                fin_ent_account_id,
                resp_movs_i.text,
                refval_params
            )

            if self.basic_should_scrape_extended_descriptions():
                movements_parsed_i = self.basic_get_movements_parsed_w_extra_details(
                    s,
                    movements_parsed_i,
                    account_scraped,
                    date_from_str,
                    n_mov_details_workers=MOV_DETAILS_MAX_WORKERS,
                    meta={
                        'resp_movs_filtered': resp_movs_i,
                        'page': page_ix,
                    },
                    callback=self.process_movement_new
                )

            # detect hanged loop (may open 1st page after the last)
            if list_funcs.is_sublist(parse_helpers.movs_parsed_tuples(movements_parsed),
                                     parse_helpers.movs_parsed_tuples(movements_parsed_i)):
                self.logger.info('{}: hanging loop detected: extracted already scraped movements. '
                                 'Abort pagination'.format(fin_ent_account_id))
                break

            resp_prev = resp_movs_i
            movements_parsed.extend(movements_parsed_i)

        movements_scraped, movements_parsed_corresponding = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        _, movements_scraped_w_receipts_info = self.download_receipts(
            s,
            resp_movs_filtered,
            account_scraped,
            movements_scraped,
            movements_parsed_corresponding
        )

        self.basic_set_movement_scraped_references(
            account_scraped,
            movements_scraped_w_receipts_info,
            parse_helpers.parse_reference_from_receipt
        )

        return True, should_renew_next_account_parsed

    def _switch_to_oldview_empresas_movs(
            self,
            s: MySession,
            resp_recent_movs: Response) -> Tuple[MySession, Response]:
        """Since 2021-11"""
        req_oldview_recent_movs_params = OrderedDict([
            ('OPERACION_NUEVO_EXTRACTO', 'SALDO_Y_EXTRACTOS'),
            ('REFVAL_SIMPLE_NUMERO_CUENTA', extract.form_param(resp_recent_movs.text,
                                                               'REFVAL_SIMPLE_NUMERO_CUENTA')),
            ('PN', 'GCT'),
            ('PE', '100'),
            ('TIPO_CUENTAS', 'VIG'),
            ('OPERATIVA_ANTERIOR', 'S'),
            ('TORNA_PN', 'GCT'),
            ('TORNA_PE', '11'),
            ('FLUJO', 'GFI,7,"'),
        ])

        req_url = resp_recent_movs.url

        resp_oldview_recent_movs = s.post(
            req_url,
            data=req_oldview_recent_movs_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return s, resp_oldview_recent_movs

    def process_account(self,
                        s: MySession,
                        resp_company_home: Response,
                        company_title_for_account_scraped_creation: str,
                        accounts_parsed: List[AccountParsed],
                        accounts_scraped_dict: Dict[str, AccountScraped],
                        acc_ix: int,
                        company_title: str) -> Tuple[bool, bool]:
        """:returns: (is_success, should_renew_next_account_parsed)"""

        account_parsed = accounts_parsed[acc_ix]
        fin_ent_account_id = account_parsed['financial_entity_account_id']
        account_alias = account_parsed['account_alias']
        account_no = account_parsed['account_no']

        if not fin_ent_account_id:
            self.logger.info("Process_account: '{}': recent movs".format(account_alias))
        else:
            self.logger.info("Process_account: '{}': recent movs".format(fin_ent_account_id))

        # Handle account_alias
        account_scraped = accounts_scraped_dict.get(fin_ent_account_id)  # type: Optional[AccountScraped]
        should_renew_next_account_parsed = False  # always after pagination to get new refval

        # First, open most recent movs
        req_recent_movs_params = parse_helpers.req_recent_movs_params(account_parsed)
        if account_parsed['is_private_view']:
            # Particulares view
            req_recent_movs_params = parse_helpers_particulares.req_recent_movs_params(account_parsed)

        resp_recent_movs = s.post(
            splitquery(resp_company_home.url)[0],
            data=req_recent_movs_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # Check wrong request due to REFVAL_SIMPLE_NUMERO_CUENTA expiration
        if REQUEST_ERROR_MARKER in resp_recent_movs.text:
            self.logger.error("{}: can't get response due to ref expiration. Need to renew accounts_parsed".format(
                account_alias,
            ))
            return False, True
        # Only for account_alias (no account_no from list page) from or Cuentas view
        # create account_scraped here
        if not fin_ent_account_id:
            account_no_from_page = parse_helpers.get_account_no_from_movs_page(
                resp_recent_movs.text
            ) or parse_helpers_particulares.get_account_no_from_movs_page(
                resp_recent_movs.text
            )
            # Check for CUENTA IMAGC ... 0005 7936
            # then fill fin_ent_account_id and create account_scraped
            if account_no_from_page[-8:] == account_alias.replace(' ', '')[-8:]:
                # keep the original account_parsed (don't mutate it)
                # for further checkups (renew etc.)
                account_parsed_upd = account_parsed.copy()

                account_no = account_no_from_page  # IBAN
                account_parsed_upd['account_no'] = account_no
                fin_ent_account_id = self._get_fin_ent_account_id(account_parsed_upd)
                account_parsed_upd['financial_entity_account_id'] = fin_ent_account_id

                account_scraped = self.basic_account_scraped_from_account_parsed(
                    company_title_for_account_scraped_creation,
                    account_parsed_upd
                )
                self.basic_upload_accounts_scraped([account_scraped])
                self.logger.info('{}: got account_scraped from mov page: {}'.format(
                    account_alias,
                    account_scraped
                ))

        # Also for linter, handle Optional[..] above
        if not account_scraped:
            self.logger.error("{}: can't get account_scraped from mov page. Skip".format(
                account_alias,
            ))
            return False, True
        # / Only for account_alias form Cuentas view

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True, False

        self._update_related_account_info(account_scraped, account_parsed)

        date_from_str = self.basic_get_date_from(
            fin_ent_account_id,
            rescraping_offset=SCRAP_MOVS_OFFSET__CUSTOM,
            max_offset=MOVS_MAX_OFFSET,
            max_autoincreasing_offset=MOVS_MAX_OFFSET,
        )
        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        if not self._is_validated_acc_at_page_w_movs(resp_recent_movs, account_no, 'recent movs', False):
            # Try again
            should_renew_next_account_parsed = True
            ok, s, accounts_parsed_renewed = self._renew_accounts_parsed(
                s,
                resp_company_home,
                company_title,
                accounts_parsed,
                account_parsed
            )
            if not ok:
                self.logger.error("Can't get correctly renewed accounts. Skip {}".format(
                    account_no or account_alias
                ))
                return False, True
            account_parsed = accounts_parsed_renewed[acc_ix]
            req_recent_movs_params = parse_helpers.req_recent_movs_params(account_parsed)
            resp_recent_movs = s.post(
                splitquery(resp_company_home.url)[0],
                data=req_recent_movs_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )
            if not self._is_validated_acc_at_page_w_movs(resp_recent_movs, account_no, 'recent movs'):
                return False, True

        # Filter by dates

        # Was a temp solution, disabled since 6.0.0
        # try switching to 'old empresas view' to get earlier implemented extended descriptions
        # if 'versión anterior' in resp_recent_movs.text:
        #     # try to switch
        #     self.logger.info("{}: switch to 'old empresas view' with movements".format(fin_ent_account_id))
        #     s, resp_recent_movs = self._switch_to_oldview_empresas_movs(s, resp_recent_movs)

        # Parse by layout (see below -a 6923, STIN SA)
        if 'TablaBean02' not in resp_recent_movs.text:
            # 'Particulares' type subaccess
            return self._get_and_save_movs_by_dates_for_particulares(
                s,
                resp_company_home,
                resp_recent_movs,
                account_parsed,
                account_scraped
            )

        # 'Empresas' type subaccess
        # Special case: layout for one-acc-Family contract movements is the same as for Empresas
        # -a 6923, STIN SA (ES9321008663100200023523)
        return self._get_and_save_movs_by_dates_for_empresas(
            s,
            resp_company_home,
            resp_recent_movs,
            account_parsed,
            account_scraped
        )

    def process_movement_new(
            self,
            s: MySession,
            movement_parsed: MovementParsed,
            fin_ent_account_id: str,
            meta: Optional[dict]) -> MovementParsed:
        assert meta

        mov_str = self.basic_mov_parsed_str(movement_parsed)
        page_ix = meta['page']
        self.logger.info("{}: page #{}: process (new impl) {}".format(
            fin_ent_account_id,
            page_ix,
            mov_str
        ))

        mov_details_req_params = movement_parsed['mov_details_req_params']
        if not mov_details_req_params:
            return movement_parsed

        resp_movs_filtered = meta['resp_movs_filtered']  # type: Response

        resp_mov_details = s.post(
            resp_movs_filtered.url,
            data=mov_details_req_params,
            headers=self.basic_req_headers_updated({'Referer': resp_movs_filtered.url}),
            proxies=self.req_proxies
        )

        description_extended = parse_helpers_particulares.get_description_extended(
            self.logger,
            fin_ent_account_id,
            resp_mov_details.text,
            movement_parsed
        )

        receipt_params = parse_helpers_particulares.get_movs_receipts_req_params(
            mov_details_req_params
        )

        movement_parsed_extra_details = movement_parsed.copy()
        movement_parsed_extra_details['description_extended'] = description_extended
        movement_parsed_extra_details['receipt_params'] = receipt_params

        return movement_parsed_extra_details

    def process_movement(self,
                         s: MySession,
                         movement_parsed: MovementParsed,
                         fin_ent_account_id: str,
                         meta: Optional[dict]) -> MovementParsed:

        """Extracts extra details for particular movement
        Important optimization:
        - if the scraper is not a receipts_scraper and the movement already saved,
          then it will not process movement (i.e. not open using additional HTTP req).
        In other cases (movement not saved or receipts_scraper even for saved movement),
          then it will process the movement to extract extra details
          (extended description and pdf req params)
        """
        assert meta

        mov_str = self.basic_mov_parsed_str(movement_parsed)
        self.logger.info("{}: process {}".format(
            fin_ent_account_id,
            mov_str
        ))

        req_params = movement_parsed['mov_details_req_params']
        if not req_params:
            return movement_parsed

        resp_movs_filtered = meta['resp_movs_filtered']  # type: Response

        resp_mov_details = s.post(
            resp_movs_filtered.url,
            data=req_params,
            headers=self.basic_req_headers_updated({'Referer': resp_movs_filtered.url}),
            proxies=self.req_proxies
        )

        if 'PANTALLA_DE_ERROR' in resp_mov_details.text:
            # If there are very many movements (up to 100 pages)
            # then the backend may abort (?) the session
            # -u 290483 -a 16807, ES0821003450222200076885
            self.logger.warning(
                "{}: {}: can't get correct details: RESPONSE:\n{}".format(
                    fin_ent_account_id,
                    movement_parsed['id'],
                    resp_mov_details.text
                )
            )

        resp_mov_more_details = Response()
        if '<tr' not in resp_mov_details.text:
            # Handle case if the movement has receipt: in this case need one more step
            # (website loads and displays the receipt at prev step,
            # -u 290483 -a 16807, ES2121008660660200055884)

            req_params_if_has_receipt = OrderedDict([
                ('PN', req_params.get('PN')),
                ('PE', req_params.get('PE')),
                ('CLICK_ORIG', req_params.get('CLICK_ORIG')),
                ('NUMERO_MOVIMIENTO', req_params.get('NUMERO_MOVIMIENTO')),
                ('FECHA_CONTABLE', req_params.get('FECHA_CONTABLE')),
                ('REFVAL_SIMPLE_NUMERO_CUENTA', req_params.get('REFVAL_SIMPLE_NUMERO_CUENTA')),
                ('POSICION_TR_ABIERTO', req_params.get('POSICION_TR_ABIERTO')),
                ('INDICADOR_CANCELADA', req_params.get('INDICADOR_CANCELADA')),
                ('FLAG_TITULO', req_params.get('FLAG_TITULO', 'U')),
                ('NUMERO_SUBMOVIMIENTO', req_params.get('NUMERO_SUBMOVIMIENTO')),
                ('TIPO_CUENTAS', req_params.get('TIPO_CUENTAS'))
            ])

            resp_mov_more_details = s.post(
                resp_movs_filtered.url,
                data=req_params_if_has_receipt,
                headers=self.basic_req_headers_updated({'Referer': resp_movs_filtered.url}),
                proxies=self.req_proxies
            )

        # prefer resp_mov_more_details if provided
        description_extended = parse_helpers.get_description_extended(
            self.logger,
            fin_ent_account_id,
            resp_mov_more_details.text or resp_mov_details.text,
            movement_parsed
        )

        receipt_params = parse_helpers.get_movs_receipts_req_params(resp_mov_details.text)

        if not receipt_params:
            receipt_params = parse_helpers.get_movs_receipts_req_params_from_first_comm(resp_mov_details.text)
            if receipt_params:
                self.logger.info('{}: {}: receipt params got from the '
                                 'first movement communication.'.format(fin_ent_account_id, mov_str))

        movement_parsed_extra_details = movement_parsed.copy()
        movement_parsed_extra_details['description_extended'] = description_extended
        movement_parsed_extra_details['receipt_params'] = receipt_params

        return movement_parsed_extra_details

    def login_to_subdomain(self) -> Tuple[MySession, Response, bool, bool, str, List[str]]:
        """:returns (session, resp_logged_in, is_logged, is_cred_err, reason, list_of_allowed_subdomains)"""

        random.seed(date_funcs.now_ts())
        # assignments to suppress 'reference before assignment'
        # false positive err notifications from mypy
        s = self.basic_new_session()
        resp_logged_in = Response()
        is_logged = False
        is_credentials_error = False

        # reorder to obtain random ordering
        # as most close to web browser behavior
        subdomains = SUBDOMAINS.copy()  # type: List[str]
        random.shuffle(subdomains)
        subdomains_not_available = []  # type: List[str]
        # special case if forced login after redirection
        subdomain_allowed = ''
        reason = ''  # not_logged_in_reason

        environ_cookies = ENVIRON_COOKIES.get(self.db_financial_entity_access_id)

        if environ_cookies is None:
            self.logger.warning('No cookie found at environ cookies')
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COOKIE
            return s, resp_logged_in, is_logged, is_credentials_error, reason, []

        # Try each subdomain
        # stop when receive correct session - that means no subdomain error
        # OR use get_allowed_subdomain if all subdomains were failed or redirected
        for ix, subdomain in enumerate(subdomains):
            try:
                s, resp_logged_in, is_logged, is_credentials_error, is_redirected, reason = self.login(subdomain)
            except:
                self.logger.error("SUBDOMAIN '{} 'LOGIN EXC:\n{}. Skip subdomain.".format(
                    subdomain,
                    traceback.format_exc()
                ))
                subdomains_not_available.append(subdomain)
                continue
            # don't work with the subdomain which redirects to another
            if is_redirected:
                subdomains_not_available.append(subdomain)
                continue
            # all fine
            break
        else:
            self.logger.info('No more subdomains to use. '
                             'Try to log in any subdomain with allow_redirection')
            subdomain_allowed = SUBDOMAINS[0]
            s, resp_logged_in, is_logged, is_credentials_error, is_redirected, reason = self.login(
                subdomain_allowed,
                allow_redirection=True
            )
            if is_redirected:
                # Was redirected again - that means subdomain_allowed was changed again
                subdomain_allowed = parse_helpers.get_subdomain_of_url(resp_logged_in.url)
                self.logger.info("Got subdomain after JS-based redirection: {}".format(subdomain_allowed))

        if not is_logged or is_credentials_error:
            return s, resp_logged_in, is_logged, is_credentials_error, reason, []

        if subdomain_allowed:
            # Special case - forced login after all redirections,
            # in this case only this subdomain is allowed
            subdomains = [subdomain_allowed]
        else:
            # Remove already failed subdomains if
            # was logged in during the loop over subdomains
            for subd_na in subdomains_not_available:
                try:
                    subdomains.pop(subdomains.index(subd_na))
                except Exception as e:
                    self.logger.error('HANDLED EXCEPTION: {}. CHECK THE CODE. '
                                      'Subdomains={}, subd_na={}'.format(e, subdomains, subd_na))

        self.logger.info('Allowed subdomains: {}'.format(subdomains))

        # Set the list of indexes of companies to scrape and the number of companies.
        # It is necessary to scrape from different subdomains
        companies, _ = self._extract_companies(s, resp_logged_in) or [0]
        self.companies_to_scrape_idxs = [ix for ix in range(len(companies))]
        self.n_companies = len(companies)
        return s, resp_logged_in, is_logged, is_credentials_error, reason, subdomains

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, reason, subdomains = self.login_to_subdomain()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        if not project_settings.IS_CONCURRENT_SCRAPING:
            for ix, subdomain in enumerate(subdomains):
                self.process_subdomain(s, resp_logged_in, subdomain, ix)
        else:
            # n_workers = min(len(subdomains), self.n_companies)
            n_workers = 1  # these days (2019-10), try to scape using only 1 worker
            with futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
                futures_dict = {
                    executor.submit(self.process_subdomain, s, resp_logged_in, subdomain, ix): subdomain
                    for ix, subdomain in enumerate(subdomains)
                }
                self.logger.log_futures_exc('process_subdomain', futures_dict)

        self.basic_log_time_spent("GET MOVEMENTS")
        return self.basic_result_success()
