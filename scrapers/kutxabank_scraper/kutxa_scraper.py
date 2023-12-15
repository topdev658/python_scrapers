import os
import random
import re
import subprocess
import time
import urllib.parse
from collections import OrderedDict
from concurrent import futures
from typing import List, Tuple

from custom_libs import extract
from custom_libs.log import log
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (AccountScraped, MOVEMENTS_ORDERING_TYPE_ASC,
                                  ScraperParamsCommon, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_COMMON)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.kutxabank_scraper import login_helpers
from scrapers.kutxabank_scraper import meta
from scrapers.kutxabank_scraper import parse_helpers
from scrapers.kutxabank_scraper.custom_types import ReqAttrs

__version__ = '11.19.0'

__changelog__ = """
11.19.0
added DOUBLE_AUTH_MARKERS
11.18.0
more WRONG_CREDENTIALS_MARKERS
11.17.0
use account-level result_codes
11.16.1
upd log msg
11.16.0
call basic_upload_movements_scraped with date_from_str
11.15.0
_get_ice_session_id
11.14.1
parse_helpers: fixed typing
11.14.0
upd self.login_init_url
11.13.0
renamed to download_correspondence()
11.12.0
download company documents (correspondence)
11.11.0
skip inactive accounts
11.10.0
process_account: several attempts to log in, extra delays
MAX_WORKERS_PROCESS_ACCOUNT = 4
11.9.0
login() with reason
11.8.0
more 'wrong credentials' markers
11.7.0
use basic_new_session
upd type hints
fmt
custom type ReqAttrs for better typing
11.6.0
use basic_get_date_from
11.5.0
switch_to_consultas_tab: extract consultas_tab_idcl and consultas_tab_id params from the resp
less verbose logging (moved under debug())
11.4.0
switch_to_consultas_tab: upd req params due to changed layout
11.3.0
_select_additional_login_options: use extract.build_req_params_from_form_html 
  as more generic approach (need for cajasur -u 294116 -a 17004 
  where 'activador' param != self.login_activador_param)
11.2.1
upd msgs
strict import
11.2.0
reduced MAX_WORKERS_PROCESS_ACCOUNT (was 12, now 8)
login:
    more informative err msgs if can't log in due to incorrect responses
    increased interval between requests
11.1.0
Limit the number of workers for process_accounts from len(accounts) to MAX_WORKERS_PROCESS_ACCOUNT 
to avoid 'NO MORE PROXIES' error
11.0.1
err log msgs instead of assertions
11.0.0
use ordered dicts as params in login process
parse_helpers: use extract.build_req_params_from_form_html_patched intead of custom impl
meta: removed unused
parse_helpers: build_req_data_from_form_params:     
    FIX 'idioma' param (should be upper case even if lower case at the page) 
    it necessary to correct call 'Selección de empresa' page
10.1.0
parse_helpers: currencies: added more markers to detect EUR and USD
10.0.0
support new encrypted DATA_LOGON_PORTAL param
9.1.0
basic_movements_scraped_from_movements_parsed: new format of the result 
9.0.0
login_helpers to pass through pinpad
_get_encrypted
"""

DEBUG = False

# Was 8, led to login errs:
# 9094 - En este momento no podemos atender su petición. Inténtelo más tarde.
# 99001 - En este momento no podemos atender su petición. Inténtelo más tarde.
# for accs 4040, 19602, 11504
MAX_WORKERS_PROCESS_ACCOUNT = 4


def debug(text: str):
    if DEBUG:
        log(text)


CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'kutxa_encrypter.js'
))

WRONG_CREDENTIALS_MARKERS = [
    'El número de usuario o la clave de acceso introducida es errónea',
    'La identificación de usuario y/o la clave de acceso no son correctas',
    'Alguno de los datos introducidos no es correcto',
]

DOUBLE_AUTH_MARKERS = [
    'enviaremos a su móvil la clave que debe introducir'
]


class KutxaScraper(BasicScraper):
    scraper_name = 'KutxaScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        # to redefine in child (caja_rural_del_sur)
        self.base_url = 'https://www.kutxabank.es/'
        self.login_init_url = 'https://portal.kutxabank.es/cs/Satellite/kb/es/empresas'
        # self.login_step1_url = 'https://portal.kutxabank.es/cs/jsp/internet/login/realizarLogin.jsp'
        self.login_step1_url = ('https://www.kutxabank.es/NASApp/BesaideNet2/Gestor'
                                '?PORTAL_CON_DCT=SI&PRESTACION=login'
                                '&FUNCION=directoportal&ACCION=control&destino=')
        self.pinpad_url = ('https://www.kutxabank.es/NASApp/BesaideNet2/Gestor'
                           '?PRESTACION=login&FUNCION=login&ACCION=directoportalImage&idioma=ES&i=11')
        self.login_activador_param = 'CAS'

        self.req_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0',
            'Upgrade-Insecure-Requests': '1'
        }
        self.update_inactive_accounts = False

    def _get_pass_encrypted(self, s: MySession, resp: Response, userpass: str) -> Tuple[bool, str]:
        """
        Download digits from positions
        Then compare with saved to get map number: position
        Then reproduce password
        """
        digit_to_position = {}
        resp_pinpad_gif = Response()
        for i in range(1, 4):
            self.logger.info('Get pinpad: attempt #{}'.format(i))
            try:
                resp_pinpad_gif = s.get(
                    self.pinpad_url,
                    headers=self.req_headers,
                    proxies=self.req_proxies,
                    timeout=30
                )
                break
            except Exception as e:
                self.logger.warning('Get pinpad: HANDLED EXCEPTION: {}'.format(e))
                time.sleep(0.5 + random.random())
        else:
            return False, ''

        digits_from_pinpad = login_helpers.get_pinpad_digits(resp_pinpad_gif.content)
        for digit_pos, digit_val in enumerate(digits_from_pinpad):
            assert digit_val != -1  # will raise exception if recognition error occur
            digit_to_position[str(digit_val)] = str(digit_pos)

        userpass_encrypted = ''
        for digit_userpass in str(userpass):
            userpass_encrypted += digit_to_position[digit_userpass]

        return True, userpass_encrypted

    def _get_data_logon_encrypted(self, pass_encrypted: str) -> str:
        cmd = '{} "{}" "{}" "{}"'.format(CALL_JS_ENCRYPT_LIB, self.username, pass_encrypted, 'false')
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def _url(self, suffix: str) -> str:
        return urllib.parse.urljoin(self.base_url, suffix)

    def _get_ice_session_id(self, resp: Response) -> str:
        ice_session_id = extract.rex_first_or_blank(
            meta.Logged.Rex.ice_session_id,
            resp.text
        )
        return ice_session_id

    def _send_receive_updates(self, s: MySession, ice_session_id: str,
                              optional_data: dict) -> Response:

        debug('send_receive_updates {}:{}'.format(ice_session_id, optional_data))

        req_url = self._url('/NASApp/BesaideNet2/block/send-receive-updates')

        req_data = {
            'ice.event.type': 'onclick',
            'ice.event.alt': 'false',
            'ice.event.ctrl': 'false',
            'ice.event.shift': 'false',
            'ice.event.meta': 'false',
            'ice.event.x': str(170 + random.randint(1, 100)),
            'ice.event.y': str(275 + random.randint(1, 200)),
            'ice.event.left': 'true',
            'ice.event.right': 'false',
            'icefacesCssUpdates': '',
            'javax.faces.ViewState': '1',
            'javax.faces.RenderKitId': '',
            'ice.session': ice_session_id,
            'ice.view': '1',
            'rand': str(random.random())
        }

        req_data.update(optional_data)
        resp = s.post(req_url,
                      data=req_data,
                      headers=self.req_headers,
                      proxies=self.req_proxies)
        return resp

    def _dispose_views(self, s: MySession, ice_session_id: str) -> Response:

        req_url = self._url('/NASApp/BesaideNet2/block/dispose-views')
        req_data = {ice_session_id: '1', 'rand': str(random.random())}
        resp = s.post(req_url,
                      data=req_data,
                      headers=self.req_headers,
                      proxies=self.req_proxies)
        return resp

    def _open_page(self, s: MySession, url: str) -> Response:
        resp = s.get(url, headers=self.req_headers, proxies=self.req_proxies)
        return resp

    def is_logged(self, resp: Response) -> Tuple[bool, bool]:
        # + url=/NASApp/BesaideNet2/pages/login/entradaBanca.iface?destino=resumen.home">
        reason = ''
        is_logged = meta.LOGGED_URL_SIGN in resp.url
        is_credentials_error = any(m in resp.text for m in WRONG_CREDENTIALS_MARKERS)
        # enviaremos a su móvil la clave que debe introducir
        if any(m in resp.text for m in DOUBLE_AUTH_MARKERS):
            is_logged = False
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON
        return is_logged, is_credentials_error, reason

    def _select_additional_login_options(self, s: MySession,
                                         resp: Response) -> Response:
        """Select "_Todo el grupo de empresas_" (All companies)"""

        self.logger.info('Select all companies login step')

        # expect
        # req_params = OrderedDict([
        #     ('PRESTACION', 'login'),
        #     ('FUNCION', 'login'),
        #     ('ACCION', 'comprobacioncambiofirma'),
        #     ('IDIOMA', 'ES'),
        #     ('destino', ''),
        #     ('activador', 'CAS'),
        #     ('tiposeleccion', ''),
        #     ('listaEmpresas', '')
        # ])
        # NOTE: we expect, that the 'activador' param may be different
        # for different accesses, but for now it was 'CAS for all cases
        action_url, req_params = extract.build_req_params_from_form_html_patched(resp.text, 'frmPrincipal',
                                                                                 is_ordered=True)
        # all companies selection
        req_params['tiposeleccion'] = 'T'
        req_params['listaEmpresas'] = '#'

        req_url = urllib.parse.urljoin(resp.url, action_url)
        resp_option_selected = s.post(
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return resp_option_selected

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:

        s = self.basic_new_session()

        resp_init = s.get(
            self.login_init_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        id_segmento = extract.rex_first_or_blank(
            meta.Login.Rex.resp_init_idSegmento,
            resp_init.text
        )

        if not id_segmento:
            return s, resp_init, False, False, "Can't log in: can't get correct id_segmento (empty is invalid)."

        ok, pass_encrypted = self._get_pass_encrypted(s, resp_init, self.userpass)
        if not ok:
            return s, resp_init, False, False, "Can't get pass_encrypted"
        data_logon_encrypted = self._get_data_logon_encrypted(pass_encrypted)

        req_data_step1 = OrderedDict([
            ('idioma', 'es'),
            ('password', pass_encrypted),
            ('tecladoVirtual', 'SI'),  # with encrypted userpass
            ('usuarioInsertado', self.username),
            ('usuarioSinFormatear', self.username),
            ('activador', self.login_activador_param),
            ('sitioWeb', ''),
            ('destino', ''),
            ('tipoacceso', ''),
            ('idSegmento', id_segmento),
            ('DATA_LOGON_PORTAL', data_logon_encrypted)
        ])

        req_data_step1['activador'] = 'MP'  # reset for all accesses..

        req_vals = ReqAttrs(
            url=self.login_step1_url,
            req_data=req_data_step1,
            method='post'
        )
        resp = resp_init  # type: Response

        step = 0
        while True:
            step += 1
            if not req_vals.url:
                reason = ("Can't log in: can't get correct req_params at step {}: {} "
                          "(invalid req_params['url']) ".format(step, req_vals))
                return s, resp, False, False, reason

            self.logger.info('Login step {}'.format(step))
            debug('Step params: {}'.format(req_vals))

            if req_vals.method.lower() == 'post':
                resp = s.post(req_vals.url,
                              data=req_vals.req_data,
                              headers=self.req_headers,
                              proxies=self.req_proxies)
            else:
                resp = s.get(req_vals.url,
                             headers=self.req_headers,
                             proxies=self.req_proxies)

            if meta.LOGIN_ADDITIONAL_QUESTIONS_URL_SIGN in resp.url:
                resp = self._select_additional_login_options(s, resp)

            is_logged, is_credentials_error, reason = self.is_logged(resp)
            if is_logged or is_credentials_error or reason:
                self.logger.info('Finished login requests')
                break

            req_vals = parse_helpers.build_req_data_from_form_params(
                resp.url,
                resp.text
            )
            if not req_vals.url:
                req_vals = parse_helpers.build_req_data_from_refresh_url(
                    resp.url,
                    resp.text
                )

            time.sleep(0.2 + random.random() * 0.2)
        return s, resp, is_logged, is_credentials_error, reason

    def get_accounts_scraped(self, resp: Response) -> List[AccountScraped]:

        accounts_form = extract.rex_first_or_blank(
            meta.UserAccountPositionTab.Rex.accounts_form,
            resp.text
        )

        accounts_parsed = parse_helpers.get_accounts_parsed(accounts_form)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                self.db_customer_name,
                account_parsed,
                is_default_organization=True
            )
            for account_parsed in accounts_parsed
        ]

        return accounts_scraped

    def switch_to_consultas_tab(self, s: MySession, resp: Response) -> Tuple[Response, str]:
        # Referer = https://www.kutxabank.es/NASApp/BesaideNet2/
        #           pages/resumen/resumen_posiciones.iface

        self.logger.info(
            'SELECT CONSULTAS TAB: {}'.format(
                self.username
            )
        )
        ice_session_id = extract.rex_first_or_blank(
            meta.Logged.Rex.ice_session_id,
            resp.text
        )

        req1_url = self._url('/NASApp/BesaideNet2/block/send-receive-updates')
        # formMenuPasivo:j_id128:1:j_id130 and formMenuPasivo:j_id128:1:j_id131
        consultas_tab_idcl, consultas_tab_id = parse_helpers.get_consultas_tab_idcl_and_id(resp.text)
        if not (consultas_tab_idcl and consultas_tab_id):
            self.logger.error("Can't switch to consultas tab: "
                              "can't parse consultas_tab_idcl and consultas_tab_id. "
                              "Check the layout:"
                              "\nRESPONSE:\n{}".format(resp.text))
            return resp, ice_session_id

        req1_data = {
            'ice.submit.partial': 'false',
            # hist: j_id147:1:j_id150, j_id143:1:j_id146, j_id126:1:j_id129, j_id128:1:j_id131
            'ice.event.target': consultas_tab_id,
            # hist: j_id147:1:j_id149, j_id143:1:j_id145, j_id126:1:j_id128, j_id128:1:j_id130
            'ice.event.captured': consultas_tab_idcl,
            'formMenuPasivo': 'formMenuPasivo',
            'icefacesCssUpdates': '',
            'javax.faces.ViewState': '1',
            'javax.faces.RenderKitId': 'ICEfacesRenderKit',
            'formMenuPasivo:_idcl': consultas_tab_idcl,
            'ice.session': ice_session_id,
            'ice.view': '1',
            'ice.focus': consultas_tab_idcl,
            'rand': str(random.random())
        }

        resp1 = s.post(req1_url,
                       data=req1_data,
                       headers=self.req_headers,
                       proxies=self.req_proxies)
        debug(resp1.text)

        resp2 = self._dispose_views(s, ice_session_id)
        debug(resp2.text)

        resp3 = self._open_page(
            s,
            self._url('/NASApp/BesaideNet2/pages/comun/pantalla_blanco.iface')
        )
        debug(resp3.text)
        self.logger.info('SELECT CONSULTAS TAB: {}: DONE'.format(self.username))

        return resp3, ice_session_id

    def open_page_with_acc_at_consultas_tab(
            self,
            s: MySession,
            resp: Response,
            ice_session_id: str,
            fin_ent_account_id: str) -> Tuple[MySession, Response]:
        """Need to open exact page at consultas tab where target account displayed
        or movements processing will fail
        """
        if fin_ent_account_id in resp.text:
            return s, resp

        # limited range of pages 2-9 to avoid possible infinite search on err resp
        # it will process 99 accounts
        resp1 = Response()  # for linter
        for page in range(2, 10):
            self.logger.info('Open page {} with accounts'.format(page))

            form_id = 'formMenuOpciones:PanelSeries:0:MenuContratosPagina{}'.format(page)
            optional_data = {
                'ice.submit.partial': False,
                'ice.event.target': form_id,
                'ice.event.captured': form_id,
                'formMenuOpciones': '',
                'formMenuOpciones:PanelSeries:0:MenuContratosCajaBusqueda': 'parte de su nº de contrato o alias',
                'formMenuOpciones:_idcl': form_id,
                'ice.focus': form_id
            }
            resp1 = self._send_receive_updates(s, ice_session_id, optional_data)
            debug(resp1.text)

            if fin_ent_account_id in resp1.text:
                break

            page += 1
            time.sleep(0.2)
        else:
            self.logger.error("Can't open page with account at consultas tab")

        return s, resp1

    def process_account(self, account_scraped: AccountScraped) -> bool:

        account_no = account_scraped.AccountNo
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account("{} (of {})".format(account_no, fin_ent_account_id), date_from_str)

        # Handle temp errs
        # when many workers are trying to log in
        s = MySession()
        resp_logged_in = Response()
        is_logged = False
        is_credentials_error = False
        for i in range(2, 4):
            # To avoid login errs for many concurrent login attempts
            time.sleep(random.random() * i)
            s, resp_logged_in, is_logged, is_credentials_error, _reason = self.login()
            if is_logged or is_credentials_error:
                break

        # stop processing without set fin ent inactive because
        # general checkup from 'main' method
        if is_credentials_error:
            self.logger.error(
                'Not logged in while ACCOUNT PROCESSING. Wrong credentials. The fin ent access '
                'still active due to was successfully logged in at initial step.'
            )
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_CANT_LOGIN_CONCURRENTLY)
            return False

        if not is_logged:
            self.logger.error(
                'Not logged in due to unknown reason (not credentials error) '
                'while ACCOUNT PROCESSING.  Try later. Finishing now.'
                '\nRESPONSE:\n{}\n{}'.format(
                    resp_logged_in.url, resp_logged_in.text
                )
            )
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_CANT_LOGIN_CONCURRENTLY)
            return False

        resp1, ice_session_id = self.switch_to_consultas_tab(s, resp_logged_in)
        s, resp11 = self.open_page_with_acc_at_consultas_tab(s, resp1, ice_session_id, fin_ent_account_id)

        resp2 = self.select_movements(s, ice_session_id, account_scraped.FinancialEntityAccountId)

        resp3 = self.select_movements_between_dates(
            s,
            resp2,
            ice_session_id,
            account_scraped.FinancialEntityAccountId
        )

        resp4 = self.select_mov_btw_dates_submit_dates(
            s,
            resp3,
            ice_session_id,
            account_scraped.FinancialEntityAccountId,
            date_from_str
        )

        time.sleep(0.1)

        resp_excel = self.extract_excel(s, ice_session_id, fin_ent_account_id)
        movements_parsed = parse_helpers.get_movements_parsed_from_excel(resp_excel.content)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )
        self.basic_log_process_account(account_no, date_from_str, movements_scraped)
        return True

    def select_movements(self, s: MySession, ice_session_id: str,
                         financial_entity_account_id: str) -> Response:

        self.logger.info(
            'SELECT MOVEMENTS: {}: {}'.format(
                ice_session_id,
                financial_entity_account_id
            )
        )

        # first account form id, but we can pass any with financial_entity_account_id
        form_id = 'formMenuOpciones:PanelSeries:0:j_id77:_0'

        optional_data = {
            'ice.submit.partial': True,
            'ice.event.target': form_id,
            'ice.event.captured': form_id,
            'formMenuOpciones': 'formMenuOpciones',
            # search box
            'formMenuOpciones:PanelSeries:0:MenuContratosCajaBusqueda': 'parte de su nº de contrato o alias',
            'formMenuOpciones:PanelSeries:0:SelectRadioMenuContratos': financial_entity_account_id,
            'formMenuOpciones:_idcl': '',
            'ice.focus': form_id,
            'formMenuOpciones:PanelSeries:0:j_id77': 'PAS0001',
        }
        resp1 = self._send_receive_updates(s, ice_session_id, optional_data)
        debug(resp1.text)

        resp2 = self._dispose_views(s, ice_session_id)
        debug(resp2.text)

        req_url = self._url('/NASApp/BesaideNet2/pages/pasivo/pasivo_movimientos_seleccion.iface')
        resp3 = self._open_page(s, req_url)
        debug(resp3.text)

        self.logger.info(
            'SELECT MOVEMENTS: {}: {}: DONE'.format(
                ice_session_id,
                financial_entity_account_id
            )
        )

        return resp3

    def select_movements_between_dates(
            self,
            s: MySession,
            resp: Response,
            ice_session_id: str,
            financial_entity_account_id: str) -> Response:
        """
        Can be used only after Select movements
        """
        self.logger.info(
            "SELECT BETWEEN DATES: {}: {}".format(
                ice_session_id,
                financial_entity_account_id
            )
        )

        # formCriterios:criteriosMovimientos:_5
        form_id = extract.re_first_or_blank(
            meta.Logged.Re.acc_option_form_id_pattern.format('Entre fechas'),
            resp.text
        )

        optional_data = {
            'ice.submit.partial': True,
            'ice.event.target': form_id,
            'ice.event.captured': form_id,
            'formCriterios': 'formCriterios',
            'formCriterios: _idcl': form_id,
            'javax.faces.RenderKitId': 'ICEfacesRenderKit',
            'formCriterios:seleccionTipoMov': 'T',
            'formCriterios:criteriosMovimientos': 'desdehasta',
            'ice.focus': form_id,
        }
        resp = self._send_receive_updates(s, ice_session_id, optional_data)
        debug(resp.text)

        self.logger.info(
            'SELECT BETWEEN DATES: {}: {}: DONE'.format(
                ice_session_id,
                financial_entity_account_id
            )
        )
        return resp

    def select_mov_btw_dates_submit_dates(
            self,
            s: MySession,
            resp: Response,
            ice_session_id: str,
            financial_entity_account_id: str,
            date_from_str: str) -> Response:
        """
        Can be used only after Select movements
        """

        self.logger.info(
            'SELECT BETWEEN DATES: SUBMIT DATES: {}: {}'.format(
                ice_session_id,
                financial_entity_account_id
            )
        )
        form_id = 'formCriterios:mostrar'

        # '01/11/2016' -> ['01', '11', '2016']
        from_date_list = date_from_str.split('/')
        to_date_list = self.date_to_str.split('/')

        optional_data = {
            'ice.submit.partial': True,
            'ice.event.target': form_id,
            'ice.event.captured': '',
            'formCriterios:seleccionTipoMov': 'T',
            'formCriterios:criteriosMovimientos': 'desdehasta',
            'formCriterios:calendarioDesde': date_from_str,
            'formCriterios:calendarioDesde_cmb_dias': from_date_list[0],
            'formCriterios:calendarioDesde_cmb_mes': from_date_list[1],
            'formCriterios:calendarioDesde_cmb_anyo': from_date_list[2],
            'formCriterios:calendarioDesde_hdn_locale': 'es_ES_CAS',
            'formCriterios:calendarioHasta': self.date_to_str,
            'formCriterios:calendarioHasta_cmb_dias': to_date_list[0],
            'formCriterios:calendarioHasta_cmb_mes': to_date_list[1],
            'formCriterios:calendarioHasta_cmb_anyo': to_date_list[2],
            'formCriterios:calendarioHasta_hdn_locale': 'es_ES_CAS',
            'formCriterios:j_idformCriterios:calendarioHastasp': '',
            'formCriterios:j_idformCriterios:calendarioDesdesp': '',
            'formCriterios': '',
            'formCriterios:_idcl': form_id,
            'ice.focus': form_id,  # after open
        }

        resp = self._send_receive_updates(s, ice_session_id, optional_data)
        debug(resp.text)
        available_movements = re.findall(
            r'id="formListado:dataContent:\d+:concepto">(.*?)</span>',
            resp.text)
        self.logger.info('Available movements:\n{}'.format(available_movements))
        self.logger.info(
            'SELECT BETWEEN DATES: SUBMIT DATES: {}: {}: DONE'.format(
                ice_session_id,
                financial_entity_account_id
            )
        )
        return resp

    def extract_excel(self, s: MySession, ice_session_id: str,
                      fin_ent_account_id: str) -> Response:

        self.logger.info('GET MOVEMENTS: {}: {}'.format(ice_session_id, fin_ent_account_id))

        optional_data = {
            'ice.submit.partial': False,
            'ice.event.target': 'formListado:resourceExcel',
            'formListado:_idcl': 'formListado:resourceExcel',
            'ice.event.captured': '',
            'javax.faces.RenderKitId': 'ICEfacesRenderKit',
            'formListado': 'formListado',
            'ice.focus': 'formListado:resourceExcel',
        }

        resp1 = self._send_receive_updates(s, ice_session_id, optional_data)
        resp2 = self._dispose_views(s, ice_session_id)
        resp_excel = s.post(
            self._url('/NASApp/BesaideNet2/pages/comun/descargar.jsp'),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return resp_excel

    def main(self) -> MainResult:

        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp_logged_in.url, resp_logged_in.text, reason)

        accounts_scraped = self.get_accounts_scraped(resp_logged_in)
        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=MAX_WORKERS_PROCESS_ACCOUNT) as executor:
                futures_dict = {
                    executor.submit(self.process_account, account_scraped):
                        account_scraped.AccountNo
                    for account_scraped in accounts_scraped
                }
                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_scraped in accounts_scraped:
                self.process_account(account_scraped)

        self.basic_log_time_spent('GET MOVEMENTS')

        self.download_correspondence(s, resp_logged_in)

        return self.basic_result_success()
