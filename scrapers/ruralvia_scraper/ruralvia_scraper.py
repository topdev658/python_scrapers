import calendar
import random
import re
import threading
import time
from concurrent import futures
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional, Union
from urllib.parse import urljoin

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import list_funcs
from custom_libs.check_resp import is_error_msg_in_resp
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    MOVEMENTS_ORDERING_TYPE_ASC, MovementParsed,
    ScraperParamsCommon, AccountParsed, MainResult,
    DOUBLE_AUTH_REQUIRED_TYPE_COMMON, DOUBLE_AUTH_REQUIRED_TYPE_OTP,
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.ruralvia_scraper import parse_helpers

__version__ = '6.46.0'

__changelog__ = """
6.46.0 2023.11.16
more DOUBLE_AUTH_MARKERS
6.45.0 2023.06.14
process_account: added call to download_receipts for pichincha
6.44.0
N_COMPANY_PROCESSING_WORKERS set to 1 to avoid concurrent contracts processing
_open_company_inicio_page:  reduced time.sleep between attempts
process_company: process account with 1 max_workers (it was 16)
6.43.0
__init__: changed init url to https://www.cajaruraldenavarra.com/es/empresas-negocios from  'https://www.grupocajarural.es/'
6.42.0
process_account: 
    min/max of op_date and val_date for date_from/date_to during iteration over dates
    _cur_day_or_next_after_wkend to handle backend inconsistency
6.41.0
use renamed list_funcs
6.40.0
__init__: changed init url to 'https://www.grupocajarural.es/' from 'https://eurocajarural.es/'
6.39.0
use basic_is_in_process_only_accounts
6.38.0
paginate by 'next page' and by chaging date filter to scrape as many movs as possible 
for dates with >= 210 movs (-a 3441 ES6130080152611751331420 16/09/2021)
6.37.0
use account-level result_codes
6.36.0
CUSTOM_OFFSET  
6.35.0
more DOUBLE_AUTH_MARKERS
6.34.0
call basic_upload_movements_scraped with date_from_str
6.33.0
more ERR_RESP_MARKERS
step1_select_company_if_several_companies: extra param validationToken (for Pichincha)
6.32.0
self.ssl_cert = True for auto verification (instead of prev custom cert)
6.31.0
DESC pagination
6.30.0
_get_companies_parsed
_open_company_inicio_page
fmt
6.29.0
select_company: upd req params
6.28.0
ssl_cert_init
6.27.0
strict _rstrip_aux
6.26.0
custom ssl_cert
6.25.0
renamed to download_correspondence()
6.24.0
strict 'wrong credentials' markers
process_account: use post req_movs_params instead of get
6.23.0
impl logout: now only Bankoa use it
6.22.0
N_COMPANY_PROCESSING_WORKERS
6.21.0
download_company_documents
6.20.0
skip inactive accounts
6.19.0
company processing: several attempts to log in
manual exceptions -> is_success flags
ERR_RESP_SIGN (one) -> ERR_RESP_MARKERS (many)
6.18.0
login: several attempts to open login_form
6.17.0
redundant_accounts support (to handle ambiguous duplicated accounts with and without reversed movements)
process_access: 
  better ordering detection for movements_parsed (can be asc or desc)
  support for custom _create_mov_req_params (used by eurocaja)
  can_paginate flag for custom pagination (used by eurocaja)
6.16.0
process_account: use MAX_OFFSET_FOR_MOVEMENTS as max_autonicreasing_offset arg
6.15.1
aligned double auth msg
6.15.0
parse_helpers: movements_parsed_order_asc
process_account: movements_parsed_all_ensure_asc
6.14.0
use basic_new_session
upd type hints
fmt
6.13.0
MAX_OFFSET_FOR_MOVEMENTS=80
_upd_acc_from_movfilter_page
6.12.0
MAX_OFFSET_FOR_MOVEMENTS
process_account: 
  use max_offset
  check 2FA while extract movements
use urllib.parse than urllib.request for better IDE introspection
6.11.0
login: check for wrong layout
6.10.0
process_account: use new contains.uniq_tail 
6.9.0
detect sms auth reason, changed login() signature
6.8.0
process_account:
  use basic_get_date_from
  MAX_MOVEMENTS = 210 (was 250)
  fixed date_from_str if iterative filter of dates was working: use date_from_str_i 
6.7.0
new self.domain property (useful for arquia red)
all requests: use urljoin with self.domain
select_company: additional request if no action4_url (useful for arquia red)
6.6.0
new default self.login_init_url, self.toga_param
6.5.0
more customizations for login method
6.4.0
select_company: use resp4_company or resp_cuentas_overview as resp w/ accounts
  (covers arquia red case)
6.3.0
process_account: ascending ordering in resp_movs,
  iterative movements filtering to extract more than 250 movements
6.2.1
fixed type hints
6.2.0
basic_movements_scraped_from_movements_parsed: new format of the result 
6.1.1
log info upd
6.1.0
parse_helpers: handle USD currnecy
6.0.1
process_account: dates in err msgs
6.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
"""

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:51.0) Gecko/20100101 Firefox/51.0'

# TODO set as self.req_headers and use self.basic_req_headers_updated
# to be used as REQ_HEADERS.copy() to update Referer, which is necessary for this scraper
REQ_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'User-Agent': USER_AGENT,
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.5'
}

# temporary title while real title not parsed
DEFAULT_COMPANY_TITLE = 'DEFAULT COMPANY'

# # 03/2019 max 250 movs for all (!) pages (can get as 1 page):
# La consulta realizada tiene más de 250 movimientos.
# Si desea que se genere un fichero con la totalidad de sus
# movimientos, pulse 'Aceptar' y en 1 hora aproximadamente
# podrá consultarlos desde la opción Ficheros Solicitados
# de la pantalla Movimientos.
# There is no possibility to get more than 250 at all
# example -u 97716 -a 3441 account ES6130080152611751331420 for 15 days
# Solution: ascending ordering, change date_from if got len(movs) == MAX_MOVEMENTS
# 210 since 6.8.0
MAX_MOVEMENTS = 210
lock = threading.Lock()

MAX_OFFSET_FOR_MOVEMENTS = 80  # days; 90 max

ERR_RESP_MARKERS = [
    'Código de error interno',
    'Tiempo de conexión excedido',
    'La sesión ha caducado'
]

# 'Error de acceso' is too wide
CREDENTIALS_ERROR_MARKERS = [
    'forma incorrecta alguno de los datos',  # .. de acceso / .. para el usuario indicado
    'Tu usuario ha sido bloqueado',
]

DOUBLE_AUTH_MARKERS = [
    'Te hemos enviado un código a tu teléfono para verificar tu identidad',
    'necesitamos enviarte un código mediante SMS a tu móvil',
    'le estamos solicitando una clave de seguridad que enviamos a su teléfono móvil'
]

LOGIN_ATTEMPTS = 3

CUSTOM_OFFSET = {
    'ES6130080152611751331420': 2,  # days
}

DATE_FMT = '%d/%m/%Y'


class RuralviaScraper(BasicScraper):
    N_COMPANY_PROCESSING_WORKERS = 1  # can redefine in children (Bankoa)

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='RuralviaScraper') -> None:

        self.scraper_name = scraper_name
        super().__init__(scraper_params_common, proxies)
        # SSL cert for 'portal' zone,
        # need to set it manually if for some reason
        # `requests` can't resolve it automatically
        self.ssl_cert = True  # type: Union[str, bool]
        # SSL cert for 'init' zone (initial req)
        # if None, then self.ssl_cert will be used
        # (for now, set in Pichincha)
        self.ssl_cert_init = None  # type: Union[Optional[str], bool]

        # use scraper_name from params because
        # it is possible that this scraper will be used for
        # different financial entities
        self.req_headers = REQ_HEADERS.copy()

        # for concurrent scraping. will be used to decide need to log in more or use initial session
        self.companies_len = 0
        # will be used to set delay to log in bcs in other case will be blocked
        self.company_future_num = 0

        # for customization (different fin entities)
        # now defaults for most of them
        self.login_init_url = 'https://www.cajaruraldenavarra.com/es/empresas-negocios'
        self.domain = 'https://www.ruralvia.com'
        self.toga_param = self.username[:2]
        # VB:
        # Special list with accounts that should be skipped.
        # There are accounts (found at Ruralvia) with exact IBAN
        # in different sub-contracts (companies)
        # but the movements are not identical:
        # for example, -a 20739 ES4830810239453199389614:
        # one of the accounts contains extra 'mutual eliminating' movements
        # (movements+reversed movements?, imgs dev/valuable...movs.png)
        # and one of them not. 'Valuable' movements are in both.
        # This may lead to balance integrity errors during the insertions
        # and movement overriding. Solution: skip explicit redundant accounts
        # Form: [(company_title, account_iban)]
        self.redundant_accounts = []  # type: List[Tuple[str, str]]

        self.update_inactive_accounts = False

    def _rstrip_aux(self, text: str) -> str:
        """Strict rstrip to avoid cases like
        'SYMfauVeoURtXTu_aux'.rstrip('_aux') -> 'SYMfauVeoURtXT' (no trailing 'u')
        Used in children
        """
        return re.sub('_aux$', '', text)

    def increase_company_future_num(self) -> None:
        with lock:
            self.company_future_num += 1

    def _req_get(self, s: MySession, url: str) -> Response:
        resp = s.get(url, headers=self.req_headers, proxies=self.req_proxies)
        return resp

    def _req_post(self, s: MySession, url: str, params: dict) -> Response:
        resp = s.post(url, params=params, headers=self.req_headers, proxies=self.req_proxies)
        return resp

    def _cur_day_or_next_after_wkend(self, dt: datetime) -> datetime:
        """
        Returns current day or next Mon after weekend
        It is neccessary to handle bad filtering from ruralvia backend:
        it doesn't include weekend dates if date_to belongs to weekend,
        so it should be Monday-Friday
        :return:
        """
        weekday = calendar.weekday(dt.year, dt.month, dt.day)
        weekend_day = max(0, weekday - 4)  # 0 for Mon-Fri, 1 - Sut, 2 - Sun
        dt_upd = dt + timedelta(days=(3 - weekend_day)) if weekend_day else dt
        return dt_upd

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        """
        Need to set Referer or will be blocked
        """
        s = MySession()
        resp3_login_form = Response()
        reason = ''

        for att in range(1, LOGIN_ATTEMPTS + 1):
            s = self.basic_new_session()
            s.verify = self.ssl_cert_init or self.ssl_cert  # 'init' zone

            resp1_init = s.get(
                self.login_init_url,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            s.verify = self.ssl_cert  # 'portal' zone

            isum_portal = extract.re_first_or_blank(r'ISUM_Portal=(\d+)', resp1_init.text)

            req_login_form_url = urljoin(
                self.domain,
                '/isum/Main?ISUM_SCR=login&loginType=accesoSeguro&ISUM_Portal={}&acceso_idioma=es_ES'.format(
                    isum_portal)
            )

            req_login_form_pre_url = urljoin(
                self.domain,
                '/isum/services/redirect_acceso.jsp?url={}'.format(req_login_form_url)
            )

            resp2_login_form_pre = s.get(
                req_login_form_pre_url,
                headers=self.basic_req_headers_updated({'Referer': resp1_init.url}),
                proxies=self.req_proxies
            )

            resp3_login_form = s.post(
                req_login_form_url,
                params={'accesoIphone': 'si'},
                headers=self.basic_req_headers_updated({'Referer': resp2_login_form_pre.url}),
                proxies=self.req_proxies
            )

            # Get login params

            login_form_url = extract.re_first_or_blank(
                '(?si)<form id="form1" action="(.*?)"',
                resp3_login_form.text
            ).strip()
            username_first_field_name = extract.re_first_or_blank(
                '<label for="(.*?)">Usuario</label>',
                resp3_login_form.text
            )
            username_second_field_name = extract.re_first_or_blank(
                '<label for="(.*?)">NIF / NIE</label>',
                resp3_login_form.text
            )
            password_field_name = extract.re_first_or_blank(
                '<label for="(.*?)">Contraseña</label>',
                resp3_login_form.text
            )

            if not (login_form_url and
                    username_first_field_name and
                    username_second_field_name and
                    password_field_name):
                reason = "WRONG LAYOUT. Can't parse login_form_url/..._field_name"
                if att < LOGIN_ATTEMPTS:
                    self.logger.warning('{}. Retry #{}'.format(reason, att))
                    time.sleep(5 + random.random())
                continue
            # No wrong layout
            break
        else:
            # Failed to open resp3_login_form
            return s, resp3_login_form, False, False, reason

        initial_access_page_param = ('BDP_RVIA05_POS_GLOBAL|'
                                     'BDP_RVIA05_ORDEN_INICIO_POSICION_GLOBAL_PAR;'
                                     'PARTICULAR|BDP_RVIA05_ORDEN_INICIO_POSICION_GLOBAL_EMP;'
                                     'EMPRESA')

        req_params = {
            username_first_field_name: self.username,
            username_second_field_name: self.username_second,
            password_field_name: self.userpass,
            'context': initial_access_page_param,
            'botoncico': 'Entrar',
            'TOGA': self.toga_param
        }

        time.sleep(0.2)

        resp4_logged_in = s.post(
            login_form_url,
            params=req_params,
            headers=self.basic_req_headers_updated({'Referer': resp3_login_form.url}),
            proxies=self.req_proxies
        )

        is_logged_in = ('Salir' in resp4_logged_in.text or  # several companies
                        'USUARIO_RACF' in resp4_logged_in.text)  # one company

        reason = ''
        if any(m in resp4_logged_in.text for m in DOUBLE_AUTH_MARKERS):
            is_logged_in = False
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        is_credentials_error = any(m in resp4_logged_in.text for m in CREDENTIALS_ERROR_MARKERS)

        # SAME STEPS AS FOR 'SELECT COMPANY'
        return s, resp4_logged_in, is_logged_in, is_credentials_error, reason

    def logout(self, s: MySession, resp_company: Response, org_title: str) -> bool:
        self.logger.info('{}: logout'.format(org_title))

        salir_link = extract.re_first_or_blank(
            '<a href="(.*?)"[^>]+id="botonSalir" >',
            resp_company.text
        )

        is_logged_out = False
        if salir_link:
            resp_salir = s.get(
                urljoin(resp_company.url, salir_link),
                headers=self.req_headers,
                proxies=self.req_proxies
            )
            is_logged_out = 'desconexion' in resp_salir.url

        if not is_logged_out:
            self.basic_log_wrong_layout(resp_company, "{}: can't log out".format(org_title))

        return is_logged_out

    def _get_companies_parsed(self, resp_logged_in: Response) -> List[dict]:
        # try to parse several companies from companies list
        companies_parsed = parse_helpers.get_several_companies_parsed(resp_logged_in.text)
        if not companies_parsed:
            # one company, get company title from Inicio page title
            companies_parsed = [{'title': DEFAULT_COMPANY_TITLE}]
        self.logger.info('Got {} companies: {}'.format(
            len(companies_parsed),
            [c['title'] for c in companies_parsed]
        ))
        # to create new sessions if more than 1 company
        self.companies_len = len(companies_parsed)
        return companies_parsed

    def process_user_account(self, s: MySession, resp_logged_in: Response) -> bool:
        self.logger.info('Process user account')

        companies_parsed = self._get_companies_parsed(resp_logged_in)

        # can process companies (get accounts_scraped) using one session
        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=self.N_COMPANY_PROCESSING_WORKERS) as executor:
                futures_dict = {
                    executor.submit(self.process_company, s, resp_logged_in, company_dict):
                        company_dict['title'] for company_dict in companies_parsed}
                self.logger.log_futures_exc('process_company', futures_dict)
        else:
            for company_parsed in companies_parsed:
                self.process_company(s, resp_logged_in, company_parsed)

        return True

    def _create_select_company_req_params(self, company_req_params_list: List[str]) -> Dict[str, str]:

        req_params = {
            'SELCON': company_req_params_list[0],
            'NOMUSUPRAL': company_req_params_list[1],
            'NIFUSUPRAL': company_req_params_list[2],
            'NIPUSUPRAL': company_req_params_list[3],
            'USUPRAL': company_req_params_list[4],
            'PERCON': company_req_params_list[5],
            'PERUSU': company_req_params_list[5],
            'PRITAR': company_req_params_list[6],
            'TRANSAC': company_req_params_list[7],
            'NOMENT': company_req_params_list[8],
            'TOGAIRIS': company_req_params_list[9],
            'ENTID': company_req_params_list[10],
            'CODOFI': company_req_params_list[11],
            'TIPO_PERFIL': company_req_params_list[12],
            'target': "_parent",
        }

        return req_params

    def step1_select_company_if_several_companies(
            self,
            s: MySession,
            resp_logged_in: Response,
            company_parsed) -> Tuple[bool, Response, Dict[str, str]]:

        def extract_form_param(param_name):
            return extract.form_param(resp_logged_in.text, param_name)

        req_headers = REQ_HEADERS.copy()

        # click the link. step1
        company_req_params_list = company_parsed['req_params_list']
        req1_params = self._create_select_company_req_params(company_req_params_list)
        req1_params['ISUM_OLD_METHOD'] = extract_form_param('ISUM_OLD_METHOD')
        req1_params['ISUM_ISFORM'] = extract_form_param('ISUM_ISFORM')
        req1_params['clavePagina'] = extract_form_param('clavePagina')
        req1_params['NUMCON'] = extract_form_param('NUMCON')
        req1_params['ESTUSR'] = extract_form_param('ESTUSR')
        req1_params['VENGO_DE_CAMBIO_PASS'] = extract_form_param('VENGO_DE_CAMBIO_PASS')
        req1_params['encriptado'] = extract_form_param('encriptado')
        req1_params['ALERTASCONTRATOS'] = extract_form_param('ALERTASCONTRATOS')
        req1_params['INDICADOR_AD'] = extract_form_param('INDICADOR_AD')
        # Pichincha only
        validation_token = extract_form_param('validationToken')
        if validation_token:
            req1_params['validationToken'] = validation_token

        action1_url = extract.re_first_or_blank(
            '<FORM name="FORM_RVIA_0" method="post" action="(.*?)"',
            resp_logged_in.text
        )

        if not action1_url:
            self.logger.error('No select_company_url {}'.format(company_parsed))
            return False, Response(), {}

        req1_url = urljoin(self.domain, action1_url)
        req_headers['Referer'] = resp_logged_in.url

        resp1_company = s.post(
            req1_url,
            params=req1_params,
            headers=req_headers,
            proxies=self.req_proxies
        )

        has_errors = is_error_msg_in_resp(
            ERR_RESP_MARKERS,
            resp1_company,
            self.logger,
            'step1_select_company_if_several_companies: resp1_company'
        )

        if has_errors or resp1_company.status_code != 200:
            self.logger.error('Error opening company {}'.format(company_parsed))
            return False, Response(), {}

        return True, resp1_company, req_headers

    def select_company(self,
                       s: MySession,
                       resp1_company: Response,
                       req_headers: Dict[str, str]) -> Tuple[MySession, Response, str, Dict[str, str]]:

        # step 2
        action2_url, req2_params = extract.build_req_params_from_form_html(
            resp1_company.text,
            'FORM_RVIA_0',
            is_ordered=True
        )

        req2_url = urljoin(resp1_company.url, action2_url)
        req_headers['Referer'] = resp1_company.url

        resp2_company = s.post(
            req2_url,
            data=req2_params,
            headers=req_headers,
            proxies=self.req_proxies
        )

        is_error_msg_in_resp(
            ERR_RESP_MARKERS,
            resp2_company,
            self.logger,
            'select_company: resp2_company'
        )

        # step 3 -- get company initial page
        action3_url = extract.re_first_or_blank(
            """window.location.href = ['"](.*?)['"]""",
            resp2_company.text
        )

        req3_url = urljoin(resp2_company.url, action3_url)
        req_headers['Referer'] = resp2_company.url

        resp3_company = s.get(
            req3_url,
            headers=req_headers,
            proxies=self.req_proxies
        )

        is_error_msg_in_resp(
            ERR_RESP_MARKERS,
            resp3_company,
            self.logger,
            'select_company: resp3_company'
        )

        # step 3.1 -- get url of Cuentas tab
        action_url_cuentas_tab = extract.re_first_or_blank(
            'href="(.*?)">Cuentas</a>',
            resp3_company.text
        )
        req_url_cuentas_tab = urljoin(resp3_company.url, action_url_cuentas_tab)

        # step 4 -- get accounts overview

        action4_url = extract.re_first_or_blank(
            '<a href="(.*?)" id="url1"',
            resp3_company.text
        )

        req4_params = {
            'ISUM_OLD_METHOD': 'POST',
            'ISUM_ISFORM': "true"
        }

        if not action4_url:
            # additional request needed if no action4_url (arquia red)
            resp35_company = s.post(
                resp3_company.url,
                data=req4_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            action4_url = extract.re_first_or_blank(
                '<a href="(.*?)" id="url1"',
                resp35_company.text
            )

        req4_url = urljoin(resp3_company.url, action4_url)
        req_headers['Referer'] = resp3_company.url

        resp4_company = s.post(
            req4_url,
            data=req4_params,
            headers=req_headers,
            proxies=self.req_proxies
        )

        is_error_msg_in_resp(
            ERR_RESP_MARKERS,
            resp4_company,
            self.logger,
            'select_company: resp4_company'
        )

        # open explicitly page with cuentas without banner
        resp_cuentas_overview = s.get(urljoin(
            resp4_company.url,
            '/isum/srv.BDP_RVIA05_ORDEN_INICIO_POSICION_GLOBAL'
            '_MULTI_EMP.BDP_RVIA05_CARRUSEL_POS_GLOBAL_MULTI'
        ))

        # handle case if resp_cuentas_overview doesn't
        # provide necessary data but resp4_company does
        # Arquia Red case
        if 'Saldo' in resp4_company.text and ('Saldo' not in resp_cuentas_overview.text):
            return s, resp4_company, req_url_cuentas_tab, req_headers

        return s, resp_cuentas_overview, req_url_cuentas_tab, req_headers

    def _open_company_inicio_page(
            self,
            s: MySession,
            resp_logged_in: Response,
            company_parsed: dict) -> Tuple[bool, MySession, Response, str, Dict[str, str]]:
        """
        :return: (ok, sess, resp_comp_inicio, req_url_cuentas_tab, req_headers)
        """
        company_title = company_parsed['title']
        # create new session if several companies per user account for concurrent scraping
        if self.companies_len > 1:  # project_settings.IS_CONCURRENT_SCRAPING and
            self.increase_company_future_num()
            is_logged_in = False
            reason = ''
            for i in range(1, 3):
                time.sleep(1 + random.random())  # to log in with some delays
                # log in
                s, resp_logged_in, is_logged_in, is_credentials_error, reason = self.login()
                if is_logged_in or is_credentials_error or ('DOUBLE AUTH' in reason):
                    break
                self.logger.warning("Can't log in for company processing: {}. Wait and retry #{}".format(
                    company_title,
                    i
                ))

            if not is_logged_in:
                self.logger.error(
                    "Can't log in for company processing: {}. Reason: {}. "
                    'Skip the company. '
                    'The access will not be marked as wrong credentials'.format(company_title, reason)
                )
                return False, s, Response(), '', {}

            # select necessary company
            ok, resp_select_company_step1, req_headers = self.step1_select_company_if_several_companies(
                s,
                resp_logged_in,
                company_parsed
            )
            if not ok:
                return False, s, Response(), '', {}  # already reported

            s, resp_company, req_url_cuentas_tab, req_headers = self.select_company(
                s, resp_select_company_step1, req_headers
            )
        # one company
        else:
            req_headers = REQ_HEADERS.copy()
            s, resp_company, req_url_cuentas_tab, req_headers = self.select_company(
                s, resp_logged_in, req_headers
            )
        self.logger.info('{}: opened Inicio page'.format(company_title))
        return True, s, resp_company, req_url_cuentas_tab, req_headers

    def process_company(self,
                        s: MySession,
                        resp_logged_in: Response,
                        company_parsed: dict) -> bool:
        """
        :param company_parsed: dict {req_params_list: List[str], title: str}
        get accounts and upload them
        then for each account run 'process account' to get movements
        """

        company_title = company_parsed['title']
        self.logger.info('Process company: {}'.format(company_title))

        ok, s, resp_company, req_url_cuentas_tab, req_headers = self._open_company_inicio_page(
            s,
            resp_logged_in,
            company_parsed
        )
        if not ok:
            return False  # already reported

        # extract company title from Inicio page
        # it is necessary only if one company per user account
        # or company title was extracted from list of companies
        if company_parsed['title'] == DEFAULT_COMPANY_TITLE:
            company_parsed['title'] = parse_helpers.get_company_title_from_inicio_page(
                self.db_customer_name,
                resp_company.text
            )

        accounts_parsed_raw = parse_helpers.parse_accounts_overview(resp_company.text)
        # Drop redundant accounts to avoid balance integrity errors
        # due to ambiguous reversed movements in duplicated accounts
        accounts_parsed = [
            acc_parsed for acc_parsed in accounts_parsed_raw
            if (company_parsed['title'], acc_parsed['account_no']) not in self.redundant_accounts
        ]

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(company_parsed['title'], acc_parsed)
            for acc_parsed in accounts_parsed
        ]

        self.logger.info('Company {} has {} accounts {}'.format(
            company_title,
            len(accounts_parsed),
            accounts_parsed
        ))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        # switch to Cuentas tab and process each account from this place
        req_headers['Referer'] = resp_company.url
        resp_accounts_mov_filter = s.get(
            req_url_cuentas_tab,
            headers=req_headers,
            proxies=self.req_proxies
        )

        is_error_msg_in_resp(
            ERR_RESP_MARKERS,
            resp_accounts_mov_filter,
            self.logger,
            'process_company: resp_accounts_mov_filter'
        )

        # should use individual session for each account to get movements
        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=1) as executor:

                futures_dict = {
                    executor.submit(
                        self.process_account, s, company_parsed,
                        account_parsed, resp_accounts_mov_filter): account_parsed['account_no']
                    for account_parsed in accounts_parsed
                }

                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_parsed in accounts_parsed:
                self.process_account(s, company_parsed, account_parsed, resp_accounts_mov_filter)

        self.download_correspondence(s, resp_company, company_parsed['title'])
        return True

    def _upd_acc_from_movfilter_page(
            self,
            company_parsed: dict,
            account_parsed: AccountParsed,
            resp_accounts_mov_filter: Response) -> AccountParsed:
        """Update balance from this page
        before starting fixing movements
        It's useful if no movements extracted due to
        date range restriction (max 90 days)
        And the balance at 'Inicio' page id not correct.

        Updated the db.
        Helps to avoid balance integrity error msg "Scraped less than saved. Can't fix"
        """
        fin_ent_account_id = account_parsed['account_no']
        if self.date_to == date_funcs.today():
            ok, account_balance_from_movfilter_page = parse_helpers.get_acc_balance_from_movfiter_page(
                self.logger,
                fin_ent_account_id,
                resp_accounts_mov_filter.text
            )
            if ok and (account_balance_from_movfilter_page != account_parsed['balance']):
                self.logger.info(
                    '{}: found more reliable place to get the balance. '
                    'Use {} instead of {}'.format(
                        fin_ent_account_id,
                        account_balance_from_movfilter_page,
                        account_parsed['balance']
                    )
                )
                account_parsed['balance'] = account_balance_from_movfilter_page
                account_scraped = self.basic_account_scraped_from_account_parsed(
                    company_parsed['title'],
                    account_parsed
                )
                self.basic_upload_accounts_scraped([account_scraped])
        return account_parsed

    def _create_mov_req_params(
            self,
            resp_prev: Response,
            account_parsed: AccountParsed,
            date_from_str: str,
            date_to_str: str,
            page_ix=0) -> Tuple[bool, str, Dict[str, str]]:

        """
        {'primeraVez': '1', 'mov_primeraVez': '', 'NumClave': '', 'anyoRemesa': '', 'indicador':
        'MV', 'cuenta': '', 'dondeEfecto': 'MV', 'DESCRIPCIONCANAL': '', 'ENTIDAD_I': '',
        'tamanioPagina': '50', 'FECHAMOVDESDE': '', 'indicadorEfecto': '', 'ACUERDO_I': '',
        'IND_SEPA': '', 'fechaComparacion': '0', 'mov_campoPaginacion': '', 'codDocumento': 'EC',
        'campoPaginacion': 'lista', 'clavePagina': '', 'ISUM_ISFORM': 'true', 'tipoBusqueda':
        '2', 'clavePaginaVolver': 'MENUP_PAS_MOV_CUENTAS', 'FECHASTA': '', 'FECHA_CREA': '',
        'fechaValor': '', 'ordenBusqueda': 'A', 'nMovs': '1', 'paginaActual': '0',
        'descripcionCuenta': '', 'FECHA_VALOR': '', 'ISUM_OLD_METHOD': 'post', 'Entidad': '',
        'CUENTA': '', 'OFICINA_I': '', 'IMPORTMAX': '', 'DESCUENTA': '', 'FECDESDE': '',
        'numRemesa': '', 'diasAnteriores': '', 'FECHAMOVHASTA': '', 'mov_paginaActual': '',
        'indic': '', 'NORHOST': '', 'CUENTA_SELEC': '', 'origenApunte': '', 'numClave': '',
        'clavePaginaSiguiente': 'PAS_MOV_CUENTAS', 'CUENTA_DESC': '', 'ESSEPA': '',
        'mov_tamanioPagina': ''}

        'can_paginate' is used to explicitly interrupt the pagination (eurocaja rural can detect it)

        :returns (can_paginate, req_url, req_params)

        """

        action_url, req_params = extract.build_req_params_from_form_html(
            resp_prev.text,
            form_name='FORM_RVIA_0',
            is_ordered=True
        )

        req_url = urljoin(resp_prev.url, action_url)

        selcta_option = parse_helpers.get_selcta_option_from_mov_filter_form(resp_prev, account_parsed)

        # https://www.ruralvia.com/isum/Main?ISUM_ID=portlets_area&ISUM_SCR=linkServiceScr&ISUM_CIPH=tdGzJQkSnxO7YhRI8BM8W16%2Bw8GOt%2B0qxwdttk%2Bkz5dwtTMU2ifxiVYn25PjkSP8w6gRexE8H0b77bUdi6cks0ZWUSy8bCRcQMc17gfMFVVjCVgyeZqXzbJa8z5DM%2FSISr%2F3jAuElGnc%2FhK%2B4syu54tnf2ahPxaR26vR43QEN8TwuvIcC0qXwS%2FLBiZk2eKXr44xxVoovFdv16Y411w8hUoa757Z%2BaLqHLER3taS33m2OQYvXiBdo2dcnPMLvof7
        # paginaActual: 2
        # pagXpag: 5

        req_params['nMovs'] = ''  # 1 -> ''
        req_params['tipoBusqueda'] = '1'  # 2 -> 1
        req_params['FECHAMOVDESDE'] = date_from_str
        req_params['FECHAMOVHASTA'] = date_to_str
        req_params['IMPORTMIN'] = ''  # not presented
        req_params['tipoMovimiento'] = ''  # not presented
        # "ordenBusqueda": "D",
        req_params['ordenBusqueda'] = 'A'  # (A)scending / (D)escending , 03/2019 - A to scrape > 250 movs
        req_params['clavePagina'] = 'PAS_MOV_CUENTAS'  # '' -> val      OK
        req_params['cuenta'] = account_parsed['req_params_raw']['cuenta']  # not presented -> val
        # not presented -> val
        req_params['DIVISA_COD'] = account_parsed['req_params_raw']['DIVISA_COD']
        req_params['DIVISA_NAME'] = account_parsed['currency_raw']  # not presented -> val
        req_params['DIVISA_DESC'] = ''  # not presented -> val
        # not presented -> val
        req_params['descripcionCuenta'] = account_parsed['req_params_raw']['descripcionCuenta']
        req_params['SALDO_CONTABLE'] = ''  # not presented -> val
        req_params['cuentaSel'] = selcta_option or ''  # not presented -> val
        req_params['FechaDesde'] = date_from_str  # not presented -> val
        req_params['FechaHasta'] = date_to_str  # not presented -> val
        req_params['importeDesde'] = ''  # not presented -> val
        req_params['importeHasta'] = ''  # not presented -> val
        req_params['botonVolver'] = 'MM'  # not presented -> val
        req_params['busquedaAvanzada'] = ''  # not presented -> val
        req_params['numMovs'] = '0'  # not presented -> val
        req_params['mostrarAlert250'] = '1'  # not presented -> val    OK
        req_params['columnaOrden'] = '0'  # not presented -> val       OK
        req_params['tipoOrden'] = '0'  # not presented -> val          OK
        req_params['ultimoOrden'] = '0'  # not presented -> val
        req_params['saldoVisible'] = ''  # not presented -> val
        req_params['fechaOperacion'] = ''  # not presented -> val
        req_params['fechaComparacion'] = date_to_str  # '0' -> val
        req_params['CERO'] = '0'  # not presented -> val
        # !! movements per page, to get max available from one page
        req_params['tamanioPagina'] = str(MAX_MOVEMENTS)
        req_params['paginaActual'] = str(page_ix)

        # if dropdown with several accounts only
        if selcta_option:
            req_params['SELCTA'] = selcta_option  # not presented -> val        OK

        if not selcta_option:  # one account per company sign?
            req_params['primeraVez'] = '1'

        can_paginate = True
        return can_paginate, req_url, req_params

    def process_account(
            self,
            s: MySession,
            company_parsed: dict,
            account_parsed: AccountParsed,
            resp_accounts_mov_filter: Response) -> bool:
        """
        log in again to process each account in different session
        get movements and upload them
        """

        account_no = account_parsed['account_no']
        # = account_no for ruralvia
        fin_ent_account_id = account_parsed['account_no']

        if not self.basic_is_in_process_only_accounts(fin_ent_account_id):
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.SKIPPED_EXPLICITLY)
            return True  # already reported

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        rescraping_offset = CUSTOM_OFFSET.get(fin_ent_account_id)
        date_from_str = self.basic_get_date_from(
            fin_ent_account_id,
            rescraping_offset=rescraping_offset,
            max_offset=MAX_OFFSET_FOR_MOVEMENTS,
            max_autoincreasing_offset=MAX_OFFSET_FOR_MOVEMENTS
        )
        self.basic_log_process_account(account_no, date_from_str)
        movements_parsed_all = []  # type: List[MovementParsed]

        # Can't extract from excel (failed earlier)

        # Iterative filtering by dates to get more than 250 (210) movs (max limit for all pages):
        # if got 250 (210) movs from the resp,
        # then change date_from to the date of the last mov and get more movements
        date_from_str_i = date_from_str
        date_to_str_i = self.date_to_str
        resp_movs = Response()
        resp_prev = resp_accounts_mov_filter
        # Limit to avoid inf loops * (30 movs DESC / 210 movs ASC pre page)
        # HTML returns max 250 movs per filter request
        page_ix = 0
        for filter_ix in range(1, 50):
            # The trick is to change date_from to scrape all possible movements
            # BUT, if there are too many movements per date, we need to set next
            # page ix
            can_paginate, req_movs_url, req_movs_params = self._create_mov_req_params(
                resp_prev,
                account_parsed,
                date_from_str_i.replace('/', '-'),  # 01-02-2017 format
                date_to_str_i.replace('/', '-'),
                page_ix
            )
            if not can_paginate:
                break

            resp_movs = s.post(
                req_movs_url,
                data=req_movs_params,
                headers=self.basic_req_headers_updated({
                    'Referer': resp_prev.url
                }),
                proxies=self.req_proxies
            )

            if 'Introduzca las posiciones solicitadas de su clave de firma.' in resp_movs.text:
                self.logger.error(
                    '{}: {} to get movements. '
                    'Dates from {} to {}. '
                    'Try to use younger date_from. Skip the account'.format(
                        fin_ent_account_id,
                        DOUBLE_AUTH_REQUIRED_TYPE_OTP,
                        date_from_str_i,
                        self.date_to_str
                    )
                )
                self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_ACCOUNT_DOUBLE_AUTH)
                return False

            is_error_msg_in_resp(
                ERR_RESP_MARKERS,
                resp_movs,
                self.logger,
                'process_account: resp_movs: {}: dates from {} to {}'.format(
                    fin_ent_account_id,
                    date_from_str,
                    self.date_to_str
                )
            )

            if resp_movs.status_code != 200:
                self.logger.error(
                    "{}: dates from {} to {}: error while opening movements of account. Skip account.".format(
                        fin_ent_account_id,
                        date_from_str,
                        self.date_to_str
                    )
                )

                self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
                return False

            # Can be ordered ASC or DESC
            # (CajaRuralZamoraScraper: -u 482348 -a 29825: ES1430850095612380524625: DESC ordering detected)
            movements_parsed_i = parse_helpers.parse_movements_from_html(resp_movs.text)

            # In some cases the movements are DESC and already were scraped.
            # Need to check for unhandled inf loop
            if all(m in movements_parsed_all for m in movements_parsed_i):
                break

            # Backend repeats some movements on the next page.
            movements_parsed_uniq_i = list_funcs.uniq_tail(
                movements_parsed_all,
                movements_parsed_i
            )

            self.logger.info(
                "{}: got {} unique movs (1st {}, last {}) of extracted from {} to {} on page #{}".format(
                    fin_ent_account_id,
                    len(movements_parsed_uniq_i),
                    movements_parsed_uniq_i[0]['operation_date'] if movements_parsed_uniq_i else 'None',
                    movements_parsed_uniq_i[-1]['operation_date'] if movements_parsed_uniq_i else 'None',
                    movements_parsed_i[0]['operation_date'] if movements_parsed_i else 'None',
                    movements_parsed_i[-1]['operation_date'] if movements_parsed_i else 'None',
                    page_ix
                )
            )

            movements_parsed_all += movements_parsed_uniq_i

            # old checkup. stay it as is
            if len(movements_parsed_i) > MAX_MOVEMENTS:
                self.logger.error(
                    '{}: dates from {} to {}: error: unexpectedly too many movements per page. '
                    'Skip account processing. Check the req parameters. RESPONSE:\n{}'.format(
                        fin_ent_account_id,
                        date_from_str,
                        self.date_to_str,
                        resp_movs,
                    )
                )
                self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
                return False

            # Detect many movements, pagination required
            if (len(movements_parsed_i) == MAX_MOVEMENTS
                    or (movements_parsed_uniq_i
                        and any(m in resp_movs.text for m in ['Siguientes', 'Página']))):  # 'more pages' marker
                # The approach with a pagination based on changing date_from (date_to)
                # Next iteration: scrape movements from (to) the last date
                # BUT if there are too many movements per date, then change the page with keeping the date
                if parse_helpers.is_asc_ordering(movements_parsed_uniq_i):
                    # Will work only with ASC ordering: change date_from
                    # NEXT date_from with tricks (see TRICKS for date_to below)
                    #  but no need to avoid date_from belonging to weekend - it works correct
                    date_from_str_i_next = min(
                        datetime.strptime(movements_parsed_uniq_i[-1]['operation_date'], DATE_FMT),
                        datetime.strptime(movements_parsed_uniq_i[-1]['value_date'], DATE_FMT)
                    ).strftime(DATE_FMT)
                    # Too many movements, date changing won't work, need to get next page
                    if date_from_str_i_next == date_from_str_i:
                        page_ix += 1
                    else:
                        date_from_str_i = date_from_str_i_next
                        page_ix = 0
                    self.logger.info(
                        "{}: ASC order detected. Filter by changing date_from={}, page_ix={}".format(
                            fin_ent_account_id,
                            date_from_str_i,
                            page_ix
                        )
                    )

                else:
                    # Will work only with DESC ordering: change date_to
                    # TRICKS
                    # 1. if date_to belongs to weekend, it must be changed to next Mon
                    #   (see ES4630850071312385767823, date_to 14/08/2022-08-14 and 15/08/2022)
                    # 2. if date_to by op_date != date_to by val_date
                    #   then applied mov filter will omit dates where val_date > op_date
                    #   (see ES4630850071312385767823, date_to 04/08/2022, and 05/08/2022),
                    #   so max(by op_date, by val_date) must be used
                    date_to_dt_i_next_raw = max(
                        datetime.strptime(movements_parsed_uniq_i[-1]['operation_date'], DATE_FMT),
                        datetime.strptime(movements_parsed_uniq_i[-1]['value_date'], DATE_FMT),
                    )
                    date_to_str_i_next = self._cur_day_or_next_after_wkend(date_to_dt_i_next_raw).strftime(DATE_FMT)
                    # / TRICKS
                    # Too many movements, date changing won't work, need to get next page
                    if date_to_str_i_next == date_to_str_i:
                        page_ix += 1
                    else:
                        date_to_str_i = date_to_str_i_next
                        page_ix = 0
                    self.logger.info(
                        "{}: DESC order detected. Filter by changing date_to={}{}, page_ix={}".format(
                            fin_ent_account_id,
                            date_to_str_i,
                            ' (next after weekend)' if date_to_str_i_next != date_to_str_i_next else '',
                            page_ix,
                        )
                    )

                self.logger.info(
                    '{}: date filter ix #{}: page ix #{}: extracted {} movements ({} uniq). Need to get more from {} to {}'.format(
                        fin_ent_account_id,
                        filter_ix,
                        page_ix,  # fix: already changed to next
                        len(movements_parsed_i),
                        len(movements_parsed_uniq_i),
                        date_from_str,
                        self.date_to_str
                    )
                )
                resp_prev = resp_movs
                continue

            break

        movements_parsed_all_ensure_asc = parse_helpers.movements_parsed_order_asc(
            movements_parsed_all
        )

        if movements_parsed_all and (movements_parsed_all != movements_parsed_all_ensure_asc):
            self.logger.info("{}: reordered movements to ASC".format(fin_ent_account_id))

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_all_ensure_asc,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )
        self.basic_log_process_account(account_no, date_from_str, movements_scraped)

        if not movements_scraped:
            # Try to avoid balance integrity error msg 'scraped less than saved'
            account_parsed = self._upd_acc_from_movfilter_page(
                company_parsed,
                account_parsed,
                resp_movs
            )

        account_scraped = self.basic_account_scraped_from_account_parsed(company_parsed['title'], account_parsed)
        ok = self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        if ok:
            self.download_receipts(
                s,
                account_scraped,
                movements_scraped,
                movements_parsed_all_ensure_asc
            )

        return True

    def main(self) -> MainResult:

        self.logger.info('main: started')

        session, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()
        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp_logged_in.url, resp_logged_in.text,
                                                              reason)

        self.process_user_account(session, resp_logged_in)
        self.basic_log_time_spent('GET ALL BALANCES AND MOVEMENTS')

        return self.basic_result_success()
