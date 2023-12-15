import datetime
import json
import random
import re
import time
import urllib.parse
from typing import Dict, List
from typing import Optional, Tuple

from custom_libs import list_funcs
from custom_libs import extract
from custom_libs import requests_helpers
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    AccountParsed, AccountScraped, MovementParsed
)
from project.custom_types import MOVEMENTS_ORDERING_TYPE_ASC, ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from . import parse_helpers_filiales

__version__ = '2.9.0'

__changelog__ = """
2.9.0
use renamed list_funcs
2.8.0
use basic_is_in_process_only_accounts
2.7.0
more CREDENTIALS_ERROR_MARKERS
2.6.0
more LOGGED_IN_URLS (with 'nwe_v1' auth method)
2.5.0
use account-level result_codes
upd log msgs
2.4.0
call basic_upload_movements_scraped with date_from_str
2.3.0
use set_date_to_for_future_movs
2.2.0
login(self):
  added detection login error from response url for:
    CREDENTIALS_ERROR_MARKERS_URL
2.1.0
login: now returns reason (aligned with SantanderEmpresasNuevoScraper)
2.0.0
combined with SantanderOrgWFilialesScraper
1.27.0
skip inactive accounts
1.26.0
process_contract: use NO_ACCOUNTS_RESPS to avoid false-positive 'wrong layout' detections
1.25.1
more 'wrong credentials' markers
1.25.0
process_account: use parse_helpers.reorder_and_calc_temp_balances to get today's movements
1.24.0
process_account: skip movements w/o temp_balance 
  they are future movs and there is no reliable way to calculate their balances
1.23.0
process_account: response code checker for resp_movs to detect restricted permissions 
1.22.1
use basic_new_session
1.22.0
_get_movements_resp: return explicit 'ok' flag for better typing
1.21.0
MySession with self.logger
1.20.1
more type hints
1.20.0
s.resp_codes_bad_for_proxies w/o 403 - it's in usage by the website
1.19.1
USUARIO REVOCADO as a 'credentials error' marker
1.19.0
suppose wrong layout if can't extract accounts
1.18.0
_get_accounts_parsed to be able to redefine in in children
1.17.1
renamed vars, added todo
1.17.0
_get_movements_resp: several attempts to get resp_movs, handle exc
1.16.0
parse_helpers: reorder_movements_of_current_date: use is_desc_ordering() to detect unknown ordering
1.15.0
DAF: include download_checks in process_account
1.14.0
use basic_get_date_from
1.13.0
parse_helpers: _get_extended_description: use val with 'Concepto' tag instead of descr_short
call basic_movements_scraped_from_movements_parsed with bankoffice_details_name, payer_details_name
1.12.0
parse_helpers: _get_extended_description
1.11.0
process_account: download_receipts
_get_movements_resp: use url that returns movements with receipts info
parse_helpers: get_movements_parsed: added has_receipt flag 
1.10.1
log 'Company has accounts'
1.10.0
more LOGGED_IN_URLS
1.9.0
more CREDENTIALS_ERROR_MARKERS (special for Empresas (nuevo) access)
1.8.0
resp_init: req_headers, req_proxies
parse_helpers: get_accounts_parsed: get currency from saldoDispContr if not provided in saldoDisp
1.7.1
improved log msgs
1.7.0
more markers to detect 'is_logged_in'
1.6.0
basic_movements_scraped_from_movements_parsed: new format of the result 
1.5.0
more CREDENTIALS_ERROR_MARKERS
1.4.0
calc self.date_to from basic date_to to handle received date_to arg
1.3.1
correct accounts_scraped_suffixes
1.3.0
accounts_scraped_suffixes to interact with SantanderSraperFiliales
1.2.0
added more IS_CREDENTIAL_ERROR_SIGNS
1.1.0
login: added upper() for username and password
1.0.0
replaced the santander_api_scraper to process temp_balances and huge movements
"""

# Found different behavior basing on user agent
# Use modern user agent to get correct behavior
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0'
DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS = 10  # offset to scrape future movements (08/01 from 05/01)

CREDENTIALS_ERROR_MARKERS = [
    'SU CLAVE DE ACCESO HA SIDO REVOCADA POR SEGURIDAD',
    'LA CLAVE DE ACCESO ES INCORRECTA',
    'LOS DATOS INTRODUCIDOS SON INCORRECTOS. INTÉNTALO DE NUEVO',
    'Las credenciales proporcionadas no corresponden a ningún cliente',
    'USUARIO REVOCADO. CONTACTE CON SU SUCURSAL PARA LA REACTIVACION',
    'Datos de acceso incorrectos',
    'Alias/Password incorrectos',  # nwe_v1
]

CREDENTIALS_ERROR_MARKERS_URL = [
    'ERROR_DATOS_INCORRECTOS',
    'ERROR_REVOCADO',
]

LOGGED_IN_URLS = [
    'https://empresas3.gruposantander.es/www-empresas/',
    'https://empresas3.gruposantander.es/empresas/',
    'https://empresas3.gruposantander.es/paas/loginnwe/',  # nuevo muticontract
    'https://empresas3.gruposantander.es/paas/api/v2/nwe-login-api/public/v1/login'  # nwe_v1
]

# Markers to avoid false-positive 'wrong layout' detections
# in process_access
NO_ACCOUNTS_RESPS = [
    '{"elements":[],"tokenRepos":null,"endList":true,'
    '"urlTransfer":"/lr/group/santander-empresas/iframe2?url=/TRANS1_PHOENIX/public/"}',
    '{"elements":[],"tokenRepos":null,"endList":true,"urlTransfer":""}'
]


class SantanderEmpresasScraper(BasicScraper):
    """
    Don't change IP while logged in
    Only one logged in session allowed
    """

    scraper_name = 'SantanderEmpresasScraper'
    FUTURE_MOVEMENTS_OFFSET = 0  # already set by DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        # IMPORTANT
        # set +N days to filter movements to be sure
        # that all future movements will be extracted
        # to calculate correct temp_balance for future movements
        # (acc balance is with the future movs)
        self.date_to = self.date_to + datetime.timedelta(days=DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS)
        self.date_to_str = self.date_to.strftime(project_settings.SCRAPER_DATE_FMT)  # '30/01/2017'
        self.req_headers = {'User-Agent': USER_AGENT}
        # to interact with SantanderScraperFiliales, suffix = [-10:] of fin_ent_account_id
        self.accounts_scraped_suffixes = []  # type: List[str]
        self.update_inactive_accounts = False
        self.set_date_to_for_future_movs()

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        self.logger.info('Regular web site: log in: start')
        s = self.basic_new_session()
        # remove 403
        s.resp_codes_bad_for_proxies = [500, 502, 503, 504, None]

        resp_init = s.get(
            'https://empresas3.gruposantander.es/Estatico/BEComponentesGeneralesAccesoSEI/Html/webempresas.htm',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_url = ('https://empresas3.gruposantander.es/SEI_PARTENON_ENS/'
                   'BEComponentesGeneralesAccesoSEI/'
                   'OPAccesoEmpresasABE/s.bto?dse_contextRoot=true')

        req_params = {
            'entradaDesde': 'AVISO_SEG_FIRMA',
            'mensajeXML': '',
            'hojaEstilos': '../../Estatico/ComunesSEI/Styles/estilo_e.css&imagenes.flecha=flecha_e.gif',
            'imagenes.boton': 'boton_e.gif',
            'dse_operationName': 'OPAccesoEmpresasABE',
            'dse_parentContextName': '',
            'dse_processorState': 'initial',
            'dse_nextEventName': 'start',
            'dse_errorPage': 'ComunesSEI\\OPComunesSEI_V1\\errorJspAccesoEmpresas.jsp',
            'cod_entrada': 'S',
            'DatosCliente.ENTRADA_POR': '',
            'usuario': self.username_second.upper(),
            'passwd': self.userpass.upper(),
            'DocumentoEntrada.Documento': self.username.upper(),
            'DocumentoEntrada.TipoDocumento': 'S',
            'timestamp': '',
            'datoAgent': 'es-ES : {}'.format(USER_AGENT)
        }

        resp_step1 = s.post(
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        resp_logged_in = resp_step1

        is_credentials_error = any(marker in resp_step1.text for marker in CREDENTIALS_ERROR_MARKERS)

        if not is_credentials_error:
            is_credentials_error = any(marker in resp_step1.url for marker in CREDENTIALS_ERROR_MARKERS_URL)

        is_logged = False

        if not is_credentials_error:

            cookies_domain = '.gruposantander.es'
            cookies = {}
            new_universal_cookie_val = parse_helpers.get_new_universal_cookie(resp_step1.text)
            cookies['NewUniversalCookie'] = new_universal_cookie_val
            s = requests_helpers.update_mass_cookies(s, cookies, cookies_domain)

            # if custom USER_AGENT
            action2_url, req_step2_params = extract.build_req_params_from_form_html(
                resp_step1.text,
                'acceso_portal'
            )

            # if DEFAULT_USER_AGENT....
            if not action2_url:
                action2_url, req_step2_params = extract.build_req_params_from_form_html(
                    resp_step1.text,
                    'enlazaWebAntigua'
                )

            req_step2_url = urllib.parse.urljoin(resp_step1.url, action2_url)

            resp_step2 = s.post(
                req_step2_url,
                data=req_step2_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            resp_logged_in = resp_step2
            is_logged = any(resp_step2.url == u for u in LOGGED_IN_URLS)

        reason = ''
        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def _open_accounts(self, s: MySession, token_repos_param='') -> Tuple[Response, dict, bool]:
        """
        :return: (resp, resp_json, is_success)
                 is_success is False only if can't get resp_json
        """
        req_headers = self.req_headers.copy()
        req_url = 'https://empresas3.gruposantander.es/CUENT2_PHOENIX/public/filteraccount/findByAlias'

        req_data = {
            'alias': '',
            'idRepos': '',
            'tokenRepos': token_repos_param,
            'filiales': 'C',
            'active': 'findByAlias'
        }

        resp = s.post(
            req_url,
            json=req_data,
            headers=req_headers,
            proxies=self.req_proxies
        )

        try:
            resp_json = resp.json()
        except Exception as exc:
            self.logger.error("process_contract: can't extract json from resp:\nexc: {}\nresp: {}".format(
                exc,
                resp.text
            ))
            return resp, {}, False
        return resp, resp_json, True

    def _get_accounts_parsed(self, resp_json: dict) -> List[AccountParsed]:
        """Can override in a child"""
        return parse_helpers.get_accounts_parsed(resp_json)

    def process_contract(self, s, resp_logged_in) -> bool:

        resp_accounts, reps_accounts_initial_json, is_success = self._open_accounts(s)
        if not is_success:
            return False

        accounts_parsed_initial = self._get_accounts_parsed(reps_accounts_initial_json)
        if not accounts_parsed_initial and not any(m == resp_accounts.text for m in NO_ACCOUNTS_RESPS):
            self.basic_log_wrong_layout(resp_accounts, "Expected, but couldn't extract accounts")

        accounts_parsed_more = []  # type: List[AccountParsed]
        # iterate till there are more accounts
        is_end_list_of_accounts = reps_accounts_initial_json.get('endList', True)
        token_repos_param = reps_accounts_initial_json.get('tokenRepos')
        while (not is_end_list_of_accounts) and token_repos_param:
            self.logger.info('get more accounts')

            resp, resp_accounts_more_json, is_success = self._open_accounts(s, token_repos_param)
            if not is_success:
                return False

            accounts_parsed_more_from_resp = parse_helpers.get_accounts_parsed(resp_accounts_more_json)
            accounts_parsed_more += accounts_parsed_more_from_resp

            is_end_list_of_accounts = resp_accounts_more_json.get('endList', True)
            token_repos_param = resp_accounts_more_json.get('tokenRepos')
            time.sleep(random.random())

        accounts_parsed = accounts_parsed_initial + accounts_parsed_more

        company_title = ''
        if accounts_parsed:
            company_title = accounts_parsed[0]['company']

        self.logger.info("Company {} has {} accounts: {}".format(
            company_title,
            len(accounts_parsed),
            accounts_parsed
        ))

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                account_parsed['company'],
                account_parsed
            ) for account_parsed in accounts_parsed
        ]

        # to interact with SantanderScraperFiliales
        self.accounts_scraped_suffixes = [
            acc_scraped.FinancialEntityAccountId[-10:]
            for acc_scraped in accounts_scraped
        ]

        self.logger.info('Updated accounts_scraped_suffixes = {}'.format(
            self.accounts_scraped_suffixes
        ))

        accounts_scraped_dict = self.basic_gen_accounts_scraped_dict(accounts_scraped)

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        # Only serial mode is allowed
        accounts_processed_is_success = []
        for account_parsed in accounts_parsed:
            is_success = self.process_account(s, account_parsed, accounts_scraped_dict)
            accounts_processed_is_success.append(is_success)

        return all(accounts_processed_is_success)

    def _open_movements(self,
                        s: MySession,
                        account_parsed: AccountParsed,
                        date_from_str: str,
                        token_repos_param='') -> Tuple[bool, Response, dict]:
        """
        :param date_from_str: in usual '30/01/2018' format
        :return: Tuple[is_success, resp, resp_json_if_success]
        """

        def fmt_date(date_str):
            """
            :param date_str: '30/01/2017' format (usual scraper date format)
            :return date_str_fmt: '2017-01-30' format
            """
            return datetime.datetime.strptime(
                date_str,
                project_settings.SCRAPER_DATE_FMT
            ).strftime('%Y-%m-%d')

        # common accesses, no receipt info
        # req_url = 'https://empresas3.gruposantander.es/CUENT2_PHOENIX/public/appointments/byOperationDate'

        # with PDF receipt status
        fin_ent_account_id = account_parsed['financial_entity_account_id']

        req_url = ('https://empresas3.gruposantander.es/paas/'
                   'api/nwe-cuentas-phoenix/public/appointments/byOperationDate')

        req_data = {
            "iban": {
                "ibanCountry": account_parsed['iban_data']['countryIban'],
                "ibanDc": account_parsed['iban_data']['dcIban'],
                "entity": account_parsed['iban_data']['entity'],
                "office": account_parsed['iban_data']['office'],
                "dc": account_parsed['iban_data']['dc'],
                "account": account_parsed['iban_data']['accountNumber'],
            },

            "filterAppointmentsGroupingDatesCommand": {
                "groupDate": "byDates",
                "dateIni": fmt_date(date_from_str),  # "2017-12-01"
                "dateEnd": fmt_date(self.date_to_str)  # "2018-01-21"
            },

            "movementType": "all",
            "typeQuery": "M",
            "type": "M",
            "operationCode": None,

            "tokenRepos": token_repos_param,
            "currencyAccount": account_parsed['currency'],

        }

        resp_movs = Response()
        req_exc = None  # type: Optional[Exception]

        # Several attempts to get resp_movs
        for i in range(2):
            try:
                resp_movs = s.post(
                    req_url,
                    json=req_data,
                    headers=self.req_headers,
                    proxies=self.req_proxies,
                    timeout=30
                )
                break
            except Exception as exc:
                req_exc = exc
        else:
            self.logger.error("{}: _get_movements_resp: can't get resp:\nexc: {}".format(
                fin_ent_account_id,
                req_exc,
            ))
            return False, resp_movs, {}

        try:
            resp_movs_json = resp_movs.json()
        except Exception as exc:
            self.logger.error("{}: _get_movements_resp: can't extract json from resp:\nexc: {}\nresp: {}".format(
                fin_ent_account_id,
                exc,
                resp_movs.text,
            ))
            return False, resp_movs, {}
        return True, resp_movs, resp_movs_json

    def process_account(self,
                        s: MySession,
                        account_parsed: AccountParsed,
                        accounts_scraped_dict: Dict[str, AccountScraped]) -> bool:
        """
        :return: is_success state (False on resp http code errors)
        """
        account_no = account_parsed['account_no']
        fin_ent_account_id = account_parsed['financial_entity_account_id']

        if not self.basic_is_in_process_only_accounts(account_no):
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.SKIPPED_EXPLICITLY)
            return True  # already reported

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        ok, resp_movs, resp_movs_initial_json = self._open_movements(s, account_parsed, date_from_str)
        if not ok:
            return False

        if resp_movs.status_code >= 400:
            self.logger.warning("{}: can't get correct response with movements. "
                                "Probably, restricted permissions for the account. "
                                "Pls, check the website manually to get the reason. "
                                "Abort now.\nRESPONSE:\n{}".format(fin_ent_account_id, resp_movs.text))
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_DISABLED_ACCOUNT)
            return False

        movs_parsed_initial = parse_helpers.get_movements_parsed(resp_movs_initial_json)

        movs_parsed_more = []  # type: List[MovementParsed]
        # interate until there are more accounts
        is_end_list_of_movs = resp_movs_initial_json.get('endList', True)
        token_repos_param = resp_movs_initial_json.get('tokenRepos')
        while (not is_end_list_of_movs) and token_repos_param:  # todo use 'for' loop
            movs_for_logs = movs_parsed_more if movs_parsed_more else movs_parsed_initial
            if movs_for_logs:
                self.logger.info('{}: open more movements (the latest was {}, looking from {} to {})'.format(
                    fin_ent_account_id,
                    movs_for_logs[-1]['operation_date'],
                    date_from_str,
                    self.date_to_str
                ))
            else:
                self.logger.warning('{}: an attempt to open more movements, but there are no previous'.format(
                    fin_ent_account_id,
                ))

            ok, resp_movs_more, resp_movs_more_json = self._open_movements(
                s,
                account_parsed,
                date_from_str,
                token_repos_param
            )
            if not ok:
                self.basic_log_wrong_layout(
                    resp_movs_more,
                    '{}: process_account: dates from {} to {}: error in reps_mov_more'.format(
                        fin_ent_account_id,
                        date_from_str,
                        self.date_to_str
                    )
                )
                self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
                return False

            movs_parsed_more_from_resp = parse_helpers.get_movements_parsed(resp_movs_more_json)
            movs_parsed_more += movs_parsed_more_from_resp

            is_end_list_of_movs = resp_movs_more_json.get('endList', True)
            token_repos_param = resp_movs_more_json.get('tokenRepos')
            time.sleep(random.random())

        movements_parsed = movs_parsed_initial + movs_parsed_more
        movements_parsed_asc = parse_helpers.reorder_and_calc_temp_balances(movements_parsed)

        movements_scraped, movements_parsed_corresponding = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_asc,
            date_from_str,
            bankoffice_details_name='Oficina',
            payer_details_name='Concepto',
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        account_scraped = accounts_scraped_dict[fin_ent_account_id]

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        self.download_receipts(
            s,
            account_scraped,
            account_parsed,
            movements_scraped,
            movements_parsed_corresponding
        )

        self.download_checks(
            account_scraped,
            movements_scraped,
        )

        return True

    def _get_secreto(self, s: MySession) -> Tuple[MySession, str]:
        req_url = 'https://empresas3.gruposantander.es/www-empresas/s/cookie/secreto'
        resp = s.get(
            req_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # from {"cod_operacion":"cs","resultado":"OK","data":{"obj":{"name":"cs","value":"-----BEGIN DAT-----
        # bJZrwgqwnC1R884hBwjxZjQaAzkDB4JJ2K5Uq9Bkeki6uDNmXxJO0utYXnA64jpx
        # K7azWACjSmqiP/WIKu/7ttqIn3lzPfu1JlYgxgkpT5LPlx7iBXStgo3Bi3fxJde6
        # Mhps2JD+8OxCs9eKBUd4sFOajaIE9OlAdrX8rXo0Fh4= -----END DAT-----","underConstruction":false}}}

        secreto = resp.json().get('data', {}).get('obj', {}).get('value')
        return s, secreto

    def _open_pos_global_step1(self,
                               s: MySession,
                               resp_prev: Response) -> Tuple[MySession, Response]:
        # -- open pos global step 1
        s, secreto = self._get_secreto(s)

        req_url_pos_global_step1 = 'https://empresas3.gruposantander.es/SEI_PARTENON_ENS' \
                                   '/BEComponentesGeneralesAccesoSEI/OPAccesoEmpresasPortal/s.bto?dse_contextRoot=true'

        req_params_pos_global_step1 = {
            'dse_operationName': 'OPAccesoEmpresasPortal',
            'dse_processorState': 'initial',
            'dse_nextEventName': 'startl',
            'secreto': secreto,
            'menuID': 'POSICION_GLOBAL;'
        }

        resp_pos_global_step1 = s.post(
            req_url_pos_global_step1,
            data=req_params_pos_global_step1,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return s, resp_pos_global_step1

        # resp_pos_global_step1 contains
        # top.codigoPersona_E = "000940573";    // <--- use for  DatosEntrada.persona.Codigo
        # top.nombrePersona_E = "VIA CELERE DESARROLLOS INMOBIL"; // <--- for DatosEntrada.titular

    def _open_pos_global_step2(self,
                               s: MySession,
                               resp_pos_global_step1: Response) -> Tuple[MySession, Response]:
        # resp_pos_global_step1 contains
        # top.codigoPersona_E = "000940573";    // <--- use for  DatosEntrada.persona.Codigo
        # top.nombrePersona_E = "VIA CELERE DESARROLLOS INMOBIL"; // <--- for DatosEntrada.titular

        codigo_param = extract.re_first_or_blank(
            r'top\.codigoPersona_E\s*[=]\s*"([^"]*?)"',
            resp_pos_global_step1.text
        )

        titular_param = extract.re_first_or_blank(
            r'top\.nombrePersona_E\s*[=]\s*"([^"]*?)"',
            resp_pos_global_step1.text
        )

        # -- open position global step2
        req_url_pos_global_step2 = 'https://empresas3.gruposantander.es/SEI_PARTENON_ENS' \
                                   '/BEComponentesGeneralesAccesoSEI/OPAccesoEmpresasPortal/s.bto?dse_contextRoot' \
                                   '=true&dse_operationName=OPPosicionGlobalConsGP&dse_parentContextName' \
                                   '=&dse_errorPage=Globales/Jsp/errorJspEmpresas.jsp&dse_processorState=initial' \
                                   '&dse_nextEventName=start'

        req_params_pos_global_step2 = {
            'DatosEntrada.persona.Tipo': 'J',
            'DatosEntrada.persona.Codigo': codigo_param,
            'DatosEntrada.titular': titular_param,
            'DatosEntrada.persona.TIPO_DE_PERSONA': '',
            'DatosEntrada.persona.CODIGO_DE_PERSONA': ''
        }

        resp_pos_global_step2 = s.post(
            req_url_pos_global_step2,
            data=req_params_pos_global_step2,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return s, resp_pos_global_step2

    def _open_filiales_page(
            self,
            s: MySession,
            resp_pos_global_step2: Response) -> Tuple[MySession, Response, bool]:
        """:returns (session, resp_filiales, has_filiales)"""

        # resp_pos_global_step2 contains
        #
        # <form name="filiales" action="s.bto" method="post">
        # <input type="hidden" name="dse_sessionId" value="kgT4M8CT_W6RqCDiczKWwU8">
        # <input type="hidden" name="dse_operationName" value="OPPosicionGlobalConsGP">
        # <input type="hidden" name="dse_applicationName" value="GestionProductosSEI">
        # <input type="hidden" name="dse_threadId" value="defaultExecutionThreadIdentifier">
        # <input type="hidden" name="dse_pageId" value="0">
        # <input type="hidden" name="dse_processorState" value="ListaFamiliasGP">
        # <input type="hidden" name="dse_processorId" value="AC16BCA38551EDDDE556C498">
        # <input type="hidden" name="dse_cmd" value="continue">
        # <input type="hidden" name="dse_errorPage"
        # value="../../ComunesSEI/OPComunesSEI_V1/errorJspEmpresas.jsp"/>
        # <input type="hidden" name="dse_nextEventName" value="Filiales"/>
        # <input type="hidden" name="DatosEntrada.tipoAcceso" value="F"/>
        # <input type="hidden" name="DatosFilial.Titular" value=""/>
        # <input type="hidden" name="primeraVez" value="N"/>
        # </form>

        has_filiales = False

        req_url_filiales = 'https://empresas3.gruposantander.es/SEI_PARTENON_ENS/BEComponentesGeneralesAccesoSEI' \
                           '/OPAccesoEmpresasPortal/s.bto?dse_contextRoot=true'

        _, req_params_filiales = extract.build_req_params_from_form_html(
            resp_pos_global_step2.text,
            'filiales'
        )

        # NO FILIALES
        if not req_params_filiales:
            return s, Response(), has_filiales

        has_filiales = True

        resp_filiales = s.post(
            req_url_filiales,
            data=req_params_filiales,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return s, resp_filiales, has_filiales

    def process_filiales(self, s: MySession, resp_logged_in: Response) -> bool:

        # open filial account page
        # open movements page to get all digits to build iban
        # create account parsed using the data
        # get movements using _get_movements_resp and parse_helper

        s, resp_pos_global_step1 = self._open_pos_global_step1(s, resp_logged_in)
        s, resp_pos_global_step2 = self._open_pos_global_step2(s, resp_pos_global_step1)
        # need to re-open after each filial processing
        s, resp_filiales, has_filiales = self._open_filiales_page(s, resp_pos_global_step2)

        if not has_filiales:
            self.logger.info('No filiales found')
            return True

        # get number of filiales
        filiales_markers = re.findall('tdrescent', resp_filiales.text)

        # process each filial in serial mode
        for i, _ in enumerate(filiales_markers):
            self.process_filial(s, resp_pos_global_step2, i)

        return True

    def _open_filial_details_page(self,
                                  s: MySession,
                                  resp_filiales: Response,
                                  filial_idx: int) -> Tuple[MySession, Response, str]:
        # expcecting action_url = 's.bto'
        _, req_params_filial_details = extract.build_req_params_from_form_html(
            resp_filiales.text,
            'aceptar'
        )

        req_url_filial_details = ('https://empresas3.gruposantander.es/SEI_PARTENON_ENS/'
                                  'BEComponentesGeneralesAccesoSEI/OPAccesoEmpresasPortal/'
                                  's.bto?dse_contextRoot=true')

        # open list of filiales if i > 0 (or getting wrong resp)
        req_params_filial_details['indice'] = str(filial_idx)
        resp_filial_details = s.post(
            req_url_filial_details,
            data=req_params_filial_details,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return s, resp_filial_details, req_url_filial_details

    def _open_filial_cuentas_page(self,
                                  s: MySession,
                                  resp_filial_details: Response,
                                  req_url_filial_details: str) -> Tuple[MySession, Response]:

        # there is the form
        # <form name="detalle" id="detalle" action="s.bto" method="post">
        # <input type="hidden" name="dse_sessionId" value="wX-dgPp4VOL0U6RQWiyQcKP">
        # <input type="hidden" name="dse_operationName" value="OPPosicionGlobalConsGP">
        # <input type="hidden" name="dse_applicationName" value="GestionProductosSEI">
        # <input type="hidden" name="dse_threadId" value="defaultExecutionThreadIdentifier">
        # <input type="hidden" name="dse_pageId" value="0">
        # <input type="hidden" name="dse_processorState" value="ListaFamiliasGP">
        # <input type="hidden" name="dse_processorId" value="AC16BCA28C4DC819E8BF2346">
        # <input type="hidden" name="dse_cmd" value="continue">
        # <input type="hidden" name="dse_errorPage" value="../../ComunesSEI/OPComunesSEI_V1/errorJspEmpresas.jsp"/>
        # <input type="hidden" name="dse_nextEventName" value="Detalle"/>
        # <input type="hidden" name="primeraVez" value="S"/>
        # <input type="hidden" name="indiceFamilias"/>
        # </form>

        _, req_params_filial_cuentas = extract.build_req_params_from_form_html(
            resp_filial_details.text,
            'detalle'
        )

        # can be different for different fililaes
        # from
        # <td class="tdrescent"><input type="radio" name="Seleccion" value="2"/></td>
        # <td class="tdresizq">&nbsp;CUENTAS CORRIENTES                                </td>
        cuentas_form_param_str = extract.re_first_or_blank(
            r'(?si)name="Seleccion"\s*value="(\d+)"[^<]*</td>\s*<td\s*class="tdresizq">&nbsp;CUENTAS\s+CORRIENTES',
            resp_filial_details.text
        )

        try:
            cuentas_form_param_int = int(cuentas_form_param_str)
        except Exception:
            self.basic_log_wrong_layout(resp_filial_details, "Can't parse cuentas_form_param_str. Skip filial")
            return s, Response()

        req_params_filial_cuentas['indiceFamilias'] = str(cuentas_form_param_int)  # 0/1/2 = cuentas

        req_url_filial_cuentas = req_url_filial_details

        resp_filial_cuentas = s.post(
            req_url_filial_cuentas,
            data=req_params_filial_cuentas,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return s, resp_filial_cuentas

    def process_filial(self,
                       s: MySession,
                       resp_pos_global_step2: Response,
                       filial_idx: int) -> bool:

        s, resp_filiales, _ = self._open_filiales_page(s, resp_pos_global_step2)
        s, resp_filial_details, req_url_filial_details = self._open_filial_details_page(s, resp_filiales, filial_idx)

        if 'CUENTAS CORRIENTES' not in resp_filial_details.text:
            self.logger.info('Filial #{}: no cuentas. Skip'.format(filial_idx))
            return True

        # default selected value will be Cuentas if exists in filial
        s, resp_filial_cuentas = self._open_filial_cuentas_page(s, resp_filial_details, req_url_filial_details)

        if 'NO HAY DATOS' in resp_filial_cuentas.text:
            self.logger.info('Filial #{}: no cuentas. Skip'.format(filial_idx))
            return True

        if not resp_filial_cuentas.text:
            self.basic_log_wrong_layout(
                resp_filial_details,
                "Can't open resp_filial_cuentas of filial #{}".format(filial_idx)
            )
            return False

        # these nos don't contain all digits to build iban
        # only movements page contains all digits of an account of filial
        # '004918372  010464504', '0049183729  10464512' not presented in the main list

        # var tablaCuentas = ["00491555  2810203346","00491837  2010464407","00491837  2010464504","00491837
        # 2910464512"]
        # var tablaSaldos = ["62.698,85 EUR","44.937,55 EUR","23.921,45 EUR","71.908,40 EUR"]
        table_accounts_str = extract.re_first_or_blank(r'var\s*tablaCuentas\s*\=\s*(\[.*?\])', resp_filial_cuentas.text)
        table_saldos_str = extract.re_first_or_blank(r'var\s*tablaSaldos\s*\=\s*(\[.*?\])', resp_filial_cuentas.text)

        if table_accounts_str and table_saldos_str:
            table_accounts = json.loads(table_accounts_str)
            table_saldos = json.loads(table_saldos_str)
        else:
            self.basic_log_wrong_layout(
                resp_filial_cuentas,
                "Can't parse accounts from filial #{}".format(filial_idx)
            )
            return False

        accounts_to_saldos = {
            acc_id: table_saldos[i]
            for i, acc_id in enumerate(table_accounts)
        }

        # accounts, available only from filiales UI
        account_to_saldos_fililales_only = {
            k: v
            for k, v in accounts_to_saldos.items()
            if k[-10:] not in self.accounts_scraped_suffixes
        }

        self.logger.info("Filial #{} has accounts {}. And new filial-only accounts will be processed: {}".format(
            filial_idx,
            accounts_to_saldos,
            account_to_saldos_fililales_only
        ))

        # -- process each account to get movements in serial mode
        for acc_id, balance_str in account_to_saldos_fililales_only.items():
            self.process_filial_account(s, resp_filial_cuentas, acc_id, balance_str)
        return True

    def _open_filial_acc_movs_page(
            self,
            s: MySession,
            resp_filial_cuentas: Response,
            account_id_from_filial_page: str,
            date_from_str='') -> Tuple[MySession, Response]:

        mov_secreto_param = extract.re_first_or_blank(
            r'top\.secreto\="([^"]*?)";',
            resp_filial_cuentas.text
        ).strip()

        d_to, m_to, y_to = self.date_to_str.split('/')

        if not date_from_str:
            d_from, m_from, y_from = d_to, m_to, y_to
        else:
            d_from, m_from, y_from = date_from_str.split('/')

        req_url_mov_acc_filial = 'https://empresas3.gruposantander.es/cgi-bin/' \
                                 'sei/cuentas_bk/cue_movimientos_detallados'
        req_params_mov_acc_filial = {
            'secreto': mov_secreto_param,
            'anoinicio': y_from,
            'mesinicio': m_from,
            'diainicio': d_from,
            'anofin': y_to,
            'mesfin': m_to,
            'diafin': d_to,
            'tipo_movimientos': '3',
            'de_donde': 'PosGloWas',
            'tipo_entrada': 'C',
            # '00491837  2110463401' # 2 spaces!
            'cuenta': account_id_from_filial_page,
            'saldo': ''  # ''1.537.220,45 EUR'
        }

        resp_mov_acc_filial = s.post(
            req_url_mov_acc_filial,
            data=req_params_mov_acc_filial,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        return s, resp_mov_acc_filial

    def _open_more_movs_page(
            self,
            s: MySession,
            resp_prev: Response) -> Tuple[bool, MySession, Response]:
        """:return (is_success, session, response)"""

        fields = ['secreto', 'cuentasMovs', 'descripcion', 'moneda', 'anoinicio', 'anofin',
                  'mesinicio', 'mesfin', 'diainicio', 'diafin', 'importe_desde', 'importe_hasta',
                  'tipo_movimientos', 'operacion', 'cuenta', 'datos_repaginacion', 'tipo_entrada',
                  'saldo', 'grupo', 'alias', 'cliente', 'fecha_contable', 'de_donde', 'empresa',
                  'tip_persona', 'cod_persona', 'criterio', 'fecha', 'des_familia', 'cod_familia',
                  'titular1', 'titular2', 'titular3', 'tipo_consulta', 'numero_bloque',
                  'numCuentasSeleccionadas', 'cuentaSeleccionada']

        # will extract unused fields, need to filter them then
        _, req_params_next_movs_page_from_form = extract.build_req_params_from_form_html(resp_prev.text, 'masdatos')
        secreto_param = extract.re_first_or_blank(r'top.secreto\s*=\s*"(.*?)"', resp_prev.text)
        req_params_next_movs_page_from_form['secreto'] = secreto_param

        req_params_next_movs_page = {
            k: v
            for k, v in req_params_next_movs_page_from_form.items()
            if k in fields
        }

        # Fix cumulative error of the 'title' param (mutating title with unprintable chars)
        # provided by the bank's backend during the pagination
        # that leads to hanging backend, spoiled responses and further memory leak in underlying libs...:
        # 'UST GLOBAL ESPAÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂA S.A.U' -> ''
        req_params_next_movs_page['titular1'] = ''

        if not req_params_next_movs_page:
            return False, s, Response()

        resp_more_movs = s.post(
            'https://empresas3.gruposantander.es/cgi-bin/sei/cuentas_bk/cue_movimientos_detallados',
            data=req_params_next_movs_page,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        return True, s, resp_more_movs

    def process_filial_account(self,
                               s: MySession,
                               resp_filial_cuentas: Response,
                               acc_id: str,
                               balance_str: str) -> bool:
        """
        Filial account IBAN can be extracted only from movements page

        Can't extract movements same way as in SantanerScraper,
        thus, need to extract filial account movements using specific way

        Retrieves account_scraped and movements_scraped
        """
        self.logger.info('Process_filial_account: {}'.format(acc_id))

        # -- Retrieve account
        s, resp_mov_acc_filial_most_recent = self._open_filial_acc_movs_page(s, resp_filial_cuentas, acc_id)

        account_parsed = parse_helpers_filiales.get_filial_account_parsed(
            resp_mov_acc_filial_most_recent.text,
            balance_str,
            self.logger
        )

        if not account_parsed:
            self.basic_log_wrong_layout(
                resp_mov_acc_filial_most_recent,
                "{}: no account_parsed. Skip the account".format(acc_id)
            )
            return False

        account_scraped = self.basic_account_scraped_from_account_parsed(
            account_parsed['company'],
            account_parsed
        )

        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        self.basic_upload_accounts_scraped([account_scraped])
        self.basic_log_time_spent('GET BALANCE of filial account: {}'.format(fin_ent_account_id))

        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        # necessary for future movements balance calculation
        last_known_temp_balance = None  # type: Optional[float]

        # -- Retrieve all movements
        # open movs of specific dates interval
        s, resp_mov_acc_filial = self._open_filial_acc_movs_page(s, resp_filial_cuentas, acc_id, date_from_str)
        movements_parsed_asc, last_known_temp_balance = parse_helpers_filiales.get_filial_movements_parsed(
            resp_mov_acc_filial.text,
            last_known_temp_balance
        )

        resp_mov_acc_filial_i = resp_mov_acc_filial

        # 'M&aacute;s movimientos' or 'Más movimientos'
        while 's movimientos' in resp_mov_acc_filial_i.text:  # todo use 'for' loop
            if movements_parsed_asc:
                self.logger.info('{}: open more movements (the latest was {}, looking from {} to {})'.format(
                    fin_ent_account_id,
                    movements_parsed_asc[-1]['operation_date'],
                    date_from_str,
                    self.date_to_str
                ))
            resp_mov_acc_filial_prev = resp_mov_acc_filial_i
            ok, s, resp_mov_acc_filial_i = self._open_more_movs_page(s, resp_mov_acc_filial_prev)
            if not ok:
                self.basic_log_wrong_layout(
                    resp_mov_acc_filial_prev,
                    "{}: can't parse req_params_next_movs_page".format(fin_ent_account_id)
                )
                break

            movements_parsed_i, last_known_temp_balance = parse_helpers_filiales.get_filial_movements_parsed(
                resp_mov_acc_filial_i.text,
                last_known_temp_balance
            )
            movements_parsed_new = list_funcs.uniq_tail(movements_parsed_asc, movements_parsed_i)
            movements_parsed_asc += movements_parsed_new
            if not movements_parsed_new:
                break

        movements_scraped, movements_parsed_corresponding = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_asc,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        # VB: fix earlier unprocessed accounts
        self.download_receipts(
            s,
            account_scraped,
            account_parsed,
            movements_scraped,
            movements_parsed_corresponding
        )

        self.download_checks(
            account_scraped,
            movements_scraped,
        )

        return True

    def main(self) -> MainResult:

        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp_logged_in.url, resp_logged_in.text, reason)

        is_success = self.process_contract(s, resp_logged_in)
        self.process_filiales(s, resp_logged_in)

        self.basic_log_time_spent('GET MOVEMENTS')

        if not is_success:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        return self.basic_result_success()
