import datetime
import json
import os
import random
import subprocess
import time
import traceback
from collections import OrderedDict
from typing import List, Optional, Tuple, Dict

from custom_libs import list_funcs
from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (AccountScraped, MovementParsed, ScraperParamsCommon,
                                  MainResult, DOUBLE_AUTH_REQUIRED_TYPE_COMMON)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.bankia_scraper import parse_helpers
from .custom_types import Company

__version__ = '6.24.0'

__changelog__ = """
6.24.0
use renamed list_funcs
6.23.0
custom_types: Company.codigo_usuario_param required for proper switching
switch_company: use company.codigo_usuario_param instead of self.api_username
6.22.0
more DOUBLE_AUTH_MARKERS
6.21.0
call basic_upload_movements_scraped with date_from_str
6.20.1
upd var names
6.20.0
re-log in after failed attempt to switch to a company (contact)
6.19.0
login: increased timeouts
6.18.1
parse_helpers: fixed typing
6.18.0
renamed to download_correspondence()
6.17.0
skip inactive accounts
6.16.0
2FA detector
more markers for wrong credentuals detector
6.15.0
switch_company: more delays
strict Company type
fixed type annotations
correct event_number for document processing
get_organization_title: more try/except
6.14.0
use basic_new_session
6.13.0
login: check intermediate resps 
6.12.0
upd type hints
MySession with logger
6.11.0
use basic_get_resp_json
removed _json_loads_orddict
6.10.0
process_account: limit the number of pages (150)
handle the case when backend returns movs of the 1st page after the last one
6.9.0
login: exc -> err with reason on 'UNSUPPORTED access type'
6.8.0
process_account: use new contains.uniq_tail
6.7.0
changes to fix floating errs: broken pagination, err with 'wrong contract ID' msg, inconsistent movements
  process_account: 
    movements_parsed_to_merge: dynamic uniq_seq_len param for contains.uniq_tail to handle short lists
    get event_number_param now from resp (was calculated)
  changed _get_movements_parsed_from_first_page_filtered_by_dates (url, params, headers)
  changed _get_movements_parsed_from_next_page_filtered_by_dates (headers) 
6.6.0
use basic_get_date_from
6.5.0
login: adjusted headers
6.4.0
parse_helpers: now uses extract.remove_extra_spaces instead of _remove_extra_spaces 
6.3.3
parse_helpers: get_document_text_info: fixed bug caused that some correspondence documents 
 of Received Transfer type not be associated with its corresponding movement
6.3.2
DAF: parse_helpers.get_document_text_info fixed to match the movement_id for all the company document types
parse_helpers._get_date_to_str
6.3.1
DAF:
process_company: calls download_company_documents instead download_documents
6.3.0
pagination for movements
'no accounts' marker
6.2.0
support changed API for movements (no pagination for movements impl)
6.1.1
fmt
6.1.0
DAF:
download_documents: called at the end of process_company to download 
the correspondence documents from the company mailbox.
parse_helpers new functions:
get_documents_parsed
get_receipt_text_faster_fitz
get_checksum
6.0.0
changed scrapers's structure: process_access, process_company
process_account: don't do req_movs_filtered_by_dates if there are no movements_recent 
    (handle case if there are no movs during last 2 years) 
parse_helpers: get_movements_parsed: exc handler with err msg
process_access: increasing event_number through all companies and accounts
_json_loads_orddict for all resp_movs
warnings in _check_wrong_resp
better type hints
more informative err msgs
5.3.1
parse_helpers: fixed type hints
5.3.0
handle case when pagination returns already extracted movements: contains.uniq_tail
removed the redundant date filters of movements_parsed 
5.2.0
get_list_of_companies: handle wrong resp: send notification and skip with common scraping error 
5.1.0
parse_helpers: description_extended
5.0.0
receipts downloading support moved to BasicReceiptsScraper and BasicScraper 
4.4.0
parse_helpers: extended descriptions
4.3.0
receipt name from KeyValue
4.2.0
basic_movements_scraped_from_movements_parsed: new format of the result
4.1.0
db_connector.should_download_receipts
4.0.0
impl receipts downloading 
"""

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'bankia_encrypter.js'
))

USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0"

INT_DATE_FMT = '%Y-%m-%d'  # the website date fmt
REQUEST_RETRY_ATTEMPTS = 5

WRONG_CREDETIALS_MARKERS = [
    'Identificacion no posible',
    'Identificador o clave incorrecta',
    'Usuario no existe',
    'Usuario bloqueado',  # -a  16919
]

DOUBLE_AUTH_MARKERS = [
    # Redirects to:
    # BankiaSu usuario no tiene teléfono móvil informado
    # Por motivos de seguridad, para acceder a Bankia Online Empresas
    # es necesario que informe su teléfono móvil en el que recibirá un Código SMS de seguridad.
    # Puede hacerlo en cualquier Oficina Bankia.
    # Consider as 2FA
    # -a 8813
    '"j_gid_response_cod_error":"CM00010E"',
]


class BankiaScraper(BasicScraper):
    """Only serial processing allowed"""

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BankiaScraper') -> None:

        self.scraper_name = scraper_name

        super().__init__(scraper_params_common, proxies)
        self.api_username = '0001'
        self.req_proxies = proxies
        self.req_headers = {
            'User-Agent': USER_AGENT,
            'Content-Type': 'application/json;charset=utf-8',
            'x-j_gid_cod_app': 'o2',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        self.update_inactive_accounts = False

    def _json_loads_orddict(self, text: str) -> OrderedDict:
        return json.JSONDecoder(object_pairs_hook=OrderedDict).decode(text)

    def _get_encrypted(self, clave: str) -> str:
        cmd = '{} "{}" "{}"'.format(CALL_JS_ENCRYPT_LIB, clave, self.userpass)
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def _req_json_post_with_retry(self,
                                  session: MySession,
                                  url: str,
                                  json_data: dict,
                                  headers: Dict[str, str],
                                  proxies: List[Dict[str, str]]) -> Response:
        resp = Response()  # suppress linter warnings
        for i in range(REQUEST_RETRY_ATTEMPTS):
            resp = session.post(url, json=json_data, headers=headers, proxies=proxies)
            if 'OPERATIVA TEMPORALMENTE NO DISPONIBLE' in resp.text:
                time.sleep(random.random())
                self.logger.info('Repeat on err resp #{}'.format(i + 1))
                continue
            break
        return resp

    def _req_json_get_with_retry(self,
                                 session: MySession,
                                 url: str,
                                 headers: Dict[str, str],
                                 proxies: List[Dict[str, str]]) -> Response:
        resp = Response()  # suppress linter warnings
        for i in range(REQUEST_RETRY_ATTEMPTS):
            resp = session.get(url, headers=headers, proxies=proxies)
            if 'OPERATIVA TEMPORALMENTE NO DISPONIBLE' in resp.text:
                time.sleep(random.random())
                self.logger.info('Repeat on err resp #{}'.format(i + 1))
                continue
            break
        return resp

    def _check_wrong_resp(self, resp: Response, account_scraped: AccountScraped) -> bool:
        if ('Identifier of contract not found' in resp.text
                or 'OPERATIVA TEMPORALMENTE NO DISPONIBLE' in resp.text):
            self.logger.warning(
                '{}: got unwanted response\n'
                'RESPONSE TEXT:\n{}\n'
                'May cause further parsing errors.'.format(
                    account_scraped.FinancialEntityAccountId,
                    extract.text_wo_scripts_and_tags(resp.text)
                )
            )
            return False
        return True

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:

        s = self.basic_new_session()
        s.resp_codes_bad_for_proxies = [500, 502, 504, None]  # 403, 503 - valuable

        _resp_init = s.get(
            'https://oficinaempresas.bankia.es/es/login.html',
            headers={'User-Agent': USER_AGENT},
            proxies=self.req_proxies,
            timeout=60,
        )

        # status_code 403 is expected, the resp will contain useful info
        resp_key = s.get(
            'https://oficinaempresas.bankia.es/api/1.0/login/key',
            headers={
                'User-Agent': USER_AGENT,
                'Referer': 'https://oficinaempresas.bankia.es/es/login.html',
                'x-j_gid_cod_app': 'o2'
            },
            proxies=self.req_proxies,
            timeout=60,
        )

        if 'j_gid_response_rsa' not in resp_key.text:
            return s, resp_key, False, False, 'Unexpected response (no "j_gid_response_rsa" in resp_key)'

        j_gid_response_rsa = resp_key.json()['j_gid_response_rsa']

        password_encrypted = self._get_encrypted(j_gid_response_rsa)  # .replace('+', ' ')

        if self.access_type == 'Contrato':
            # login by contract with specific username
            self.api_username = self.username  # important (set to 1001 or same)
            req_login_params = {
                'j_gid_action': 'login',
                'j_gid_cod_app': 'o2',
                'j_gid_num_usuario': self.username,  # 1001
                'j_gid_password': password_encrypted,
            }
            # for mypy
            if self.username_second:
                req_login_params['j_gid_num_contrato'] = self.username_second  # 2340032050600

        # Acceso clientes for BMN scraper if DB entry wasn't updated
        elif self.access_type in ['Seudónimo', 'Acceso clientes']:
            # login by contract or pseudonim (with default username 0001)
            req_login_params = {
                'j_gid_action': 'login',
                'j_gid_cod_app': 'o2',
                'j_gid_num_usuario': '0001',
                'j_gid_password': password_encrypted,
            }
            # for mypy
            if self.username:
                req_login_params['j_gid_pseudonimo'] = self.username
            if self.username_second:
                req_login_params['j_gid_num_contrato'] = self.username_second
        else:
            return s, Response(), False, False, 'UNSUPPORTED access type: {}. Abort'.format(self.access_type)

        req_login_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://oficinaempresas.bankia.es/es/login.html',
            'x-j_gid_cod_app': 'o2',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'User-Agent': USER_AGENT
        }

        resp_login = s.post(
            'https://oficinaempresas.bankia.es/api/1.0/escenariocliente/personalizacion/login',
            data=req_login_params,
            headers=req_login_headers,
            proxies=self.req_proxies,
            timeout=60,
        )

        is_logged = (resp_login.status_code in [200, 201]) and (
                'j_gid_response_contrato' in resp_login.text)  # 503 user not exists/blocked, 200 wrong passw
        is_credentials_error = any(m in resp_login.text for m in WRONG_CREDETIALS_MARKERS)

        reason = ''
        if not (is_logged or is_credentials_error) and (
                resp_login.status_code == 428  # -a 17722
                or any(m in resp_login.text for m in DOUBLE_AUTH_MARKERS)):
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        return s, resp_login, is_logged, is_credentials_error, reason

    def get_list_of_companies(self, s: MySession) -> Tuple[bool, List[Company]]:
        """
        {"contratosAsociados": [
            {"codigoUsuario": "0001", "identificadorContrato": "2340000619300", "alias": "",
             "parentesco": "P", "estado": "",
             "fechaAlta": {"valor": "1900-01-01-00.00.00.000000"},
             "fechaEstado": {"valor": "1900-01-01-00.00.00.000000"}},

            {"codigoUsuario": "0001", "identificadorContrato": "2340011799200",
             "alias": "TUNELAN OBRAS SUBTERRANEAS SL-", "parentesco": "H", "estado": "A",
             "fechaAlta": {"valor": "2015-06-18-00.00.00.000000"},
             "fechaEstado": {"valor": "2015-06-18-00.00.00.000000"}}]}

        :returns (is_success, [list of companies])
        """
        exn = Exception()
        resp = Response()
        for i in range(3):
            try:
                time.sleep(0.5 + 0.5 * random.random())
                resp = s.get(
                    'https://oficinaempresas.bankia.es/api/1.0/sap/contratosmultiacceso',
                    headers=self.req_headers,
                    proxies=self.req_proxies
                )
                resp_json = resp.json()
                companies = [
                    Company(
                        codigo_usuario_param=c['codigoUsuario'],
                        contract_id=c['identificadorContrato'],
                    )
                    for c in resp_json['contratosAsociados']
                ]

                return True, companies
            except Exception as e:
                exn = e  # memo last
                self.logger.warning("Can't get companies (contracts). Retry."
                                    "\nHANDLED EXCEPTION: {}".format(e))
        self.logger.error("Can't extract companies. Abort."
                          "\nHANDLED EXCEPTION: {}.\nRESPONSE {}".format(exn, resp.text))
        return False, []

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        ok, companies = self.get_list_of_companies(s)
        if not ok:
            return False

        self.logger.info('Access has {} companies: {}'.format(
            len(companies),
            companies
        ))

        event_number = 1
        for ix, company in enumerate(companies):
            ok, company_param = self.switch_company(s, company) if ix else (True, None)
            # company was blocked by user
            if not ok:
                self.logger.info('Re-log in after failed attempt to switch to {}'.format(
                    company))  # Need to re-login after failed attempt
                s, _resp_logged_in, is_logged, _is_credentials_error, _reason = self.login()
                event_number = 1
                if not is_logged:
                    self.logger.error("Couldn't log in after failed attempt to switch to {}. Abort".format(
                        company
                    ))
                    break
                # Next company (contract)
                continue

            # NOTE: if we skip processing of first company, the scraping of all first accounts
            # of all companies (contracts) will fail - important for parallel processing development
            event_number = self.process_company(s, resp_logged_in, event_number, company_param)
            time.sleep(0.5 + 0.5 * random.random())
        return True

    def switch_company(self, s: MySession, company: Company) -> Tuple[bool, Optional[str]]:
        """:returns (ok, company_param)"""

        req1_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'x-j_gid_cod_app': 'o2',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'User-Agent': USER_AGENT
        }

        j_gid_indice = self.api_username + company.contract_id

        req1_params_od = OrderedDict([
            ('j_gid_num_usuario_asociado', company.codigo_usuario_param),
            ('j_gid_num_contrato_asociado', company.contract_id),
            ('j_gid_indice', j_gid_indice)
        ])

        resp = s.post(
            'https://oficinaempresas.bankia.es/api/1.0/escenariocliente/loginAsociado',
            data=req1_params_od,
            headers=req1_headers,
            proxies=self.req_proxies
        )

        # company can be blocked at fin entity level
        if resp.status_code != 201:
            self.logger.warning(
                'Wrong resp code != 201 while switching to {} : resp: {}. '
                'Possible reason: the company is blocked by user. '
                'Skip company processing'.format(company, resp.text))
            return False, None

        return True, j_gid_indice

    def get_organization_title(self,
                               s: MySession,
                               company_param: Optional[str] = None) -> Tuple[bool, str]:
        """:return (is_success, organization_title)"""

        req_headers = self.req_headers.copy()
        organization_title = ''
        if company_param:
            req_headers['j_gid_indice'] = company_param

        resp = s.get(
            'https://oficinaempresas.bankia.es/api/1.0/escenariocliente/personalizacion',
            headers=req_headers,
            proxies=self.req_proxies
        )

        ok, resp_org_data = self.basic_get_resp_json(
            resp,
            "Can't get organization_title. "
            "Skip company with company_param {}".format(company_param)
        )
        if not ok:
            return False, ''

        try:
            organization_title = resp_org_data['data']['datosBasicosCliente']['nombreRazonSocial']
        except:
            self.logger.error(
                "Can't extract organization_title. "
                "Skip company with company_param {}."
                "\nRESPONSE:\n{}".format(company_param, resp_org_data)
            )
            return False, ''
        return True, organization_title

    def process_company(self,
                        s: MySession,
                        resp_logged_in: Response,
                        event_number: int,
                        company_param: Optional[str] = None) -> int:

        ok, organization_title = self.get_organization_title(s, company_param)
        if not ok:
            # already logged other useful info
            self.logger.warning('Failed to process company {}'.format(company_param))
            return event_number

        self.logger.info('Process company {}'.format(organization_title))

        req_pos_global_url = 'https://oficinaempresas.bankia.es/api/1.0/posicionglobal/productos'
        req_pos_global_data = {'idVista': '1'}

        req_headers = self.req_headers.copy()
        if company_param:
            req_headers['j_gid_indice'] = company_param

        resp_pos_global = self._req_json_post_with_retry(
            s,
            req_pos_global_url,
            req_pos_global_data,
            req_headers,
            self.req_proxies
        )
        # broken balances for credit accounts
        # data_global = resp_pos_global.json()

        req_cuentas_url = 'https://oficinaempresas.bankia.es/api/1.0/cuentas/posiciontotal'
        resp_cuentas = self._req_json_get_with_retry(
            s,
            req_cuentas_url,
            req_headers,
            self.req_proxies
        )

        ok, resp_data = self.basic_get_resp_json(
            resp_cuentas,
            "Can't get json from resp_cuentas. Skip company {}".format(organization_title)
        )
        if not ok:
            return event_number

        if 'NoHayCuentasPosicionTotalCuentasSPR' in resp_cuentas.text:
            self.logger.info("Company {} has NO accounts".format(organization_title))
            return event_number

        try:
            accounts_parsed = parse_helpers.get_accounts_parsed(resp_data)
        except:
            self.logger.error(
                "Company '{}': get_accounts_scraped:\n"
                "HANDLED EXCEPTION {}\n\n"
                "RESPONSE DATA\n{}.\n"
                "Skip.".format(
                    organization_title,
                    traceback.format_exc(),
                    resp_data
                )
            )
            return event_number

        self.logger.info('Company {} has {} accounts: {}'.format(
            organization_title,
            len(accounts_parsed),
            accounts_parsed
        ))

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                organization_title,
                account_parsed
            )
            for account_parsed in accounts_parsed
        ]

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('{}: GET ACCOUNTS'.format(organization_title))

        for account_ix, account_scraped in enumerate(accounts_scraped):
            self.process_account(
                s,
                resp_logged_in.text,
                event_number,
                account_scraped,
                organization_title,
                account_ix,
                company_param
            )
            event_number += 1

        self.download_correspondence(s, event_number, organization_title, company_param)
        # event_number += 1
        return event_number

    def _get_movements_parsed_from_first_page_filtered_by_dates(
            self,
            s: MySession,
            date_from: datetime.datetime,
            date_from_str: str,
            account_scraped: AccountScraped,
            account_ix: int,
            company_param=None) -> Tuple[List[MovementParsed], dict]:

        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        # filter by dates if necessary
        # s1 - page1, s2 - page2
        req_url = ('https://oficinaempresas.bankia.es/api/1.0/servicios/'
                   'cuentas.movimientos/3.0/cuentas/movimientos')

        req_params = OrderedDict([
            ("criteriosBusquedaCuenta", OrderedDict([
                ("fechaOperacionDesde", date_from.strftime(INT_DATE_FMT)),
                ("fechaOperacionHasta", self.date_to.strftime(INT_DATE_FMT))
            ])),
            ("identificadorCuenta", OrderedDict([
                ("digitosDeControl", account_scraped.AccountNo[2:4]),
                ("identificador", account_scraped.AccountNo[4:]),
                ("pais", account_scraped.AccountNo[:2]),
            ])),
        ])

        # it is necessary to set j_gid_indice only if acc idx > 0
        req_headers = self.req_headers.copy()
        if company_param:
            req_headers['j_gid_indice'] = company_param

        req_headers['x-j_gid_cod_app'] = 'o2'

        resp_movs_filtered_first_page = self._req_json_post_with_retry(
            s,
            req_url,
            req_params,
            req_headers,
            self.req_proxies
        )

        self._check_wrong_resp(resp_movs_filtered_first_page, account_scraped)

        ok, resp_json = self.basic_get_resp_json(
            resp_movs_filtered_first_page,
            err_msg="{}: can't get json from resp_movs_filtered_first_page. Skip".format(
                fin_ent_account_id
            ),
            is_ordered=True
        )
        if not ok:
            return [], resp_json

        if 'data' not in resp_json:
            self.logger.error(
                "{}: _get_movements_parsed_from_first_page_filtered_by_dates: "
                "no 'data' field in resp_movs_filtered_first_page. RESPONSE:\n{}".format(
                    fin_ent_account_id,
                    resp_movs_filtered_first_page.text
                ))
            return [], resp_json

        ok, movements_parsed = parse_helpers.get_movements_parsed(
            resp_json,
            self.logger,
            account_scraped,
            date_from_str,
            self.date_to_str
        )

        return movements_parsed, resp_json

    def _get_movements_parsed_from_next_page_filtered_by_dates(
            self, s: MySession,
            event_number_param: int,
            date_from_str: str,
            page_num: int,
            account_scraped: AccountScraped,
            account_ix: int,
            company_param=None) -> Tuple[List[MovementParsed], dict]:

        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        # ! event_number should be == 1 for the 1st acc of the 1st company
        req_url = ('https://oficinaempresas.bankia.es/api/1.0/servicios/'
                   'cuentas.movimientos/3.0/cuentas/'
                   'movimientos?_eventId=obtenerMovimientosCuenta&'
                   'execution=e{}s{}').format(event_number_param, page_num)
        req_params = OrderedDict([
            ("identificadorCuenta", OrderedDict([
                ("pais", account_scraped.AccountNo[:2]),
                ("digitosDeControl", account_scraped.AccountNo[2:4]),
                ("identificador", account_scraped.AccountNo[4:])
            ])),
            ("indicadorTipoBusqueda", 1),
            ("criteriosBusqueda", {})
        ])

        # it is necessary to set j_gid_indice only if acc idx > 0
        req_headers = self.req_headers.copy()
        if company_param:
            req_headers['j_gid_indice'] = company_param

        req_headers['x-j_gid_cod_app'] = 'o2'

        resp_movs_filtered_next_page = self._req_json_post_with_retry(
            s,
            req_url,
            req_params,
            req_headers,
            self.req_proxies
        )

        self._check_wrong_resp(resp_movs_filtered_next_page, account_scraped)
        ok, resp_json = self.basic_get_resp_json(
            resp_movs_filtered_next_page,
            err_msg="{}: can't get json from resp_movs_filtered_next_page. Skip".format(
                fin_ent_account_id
            ),
            is_ordered=True
        )
        if not ok:
            return [], resp_json

        if 'data' not in resp_json:
            self.logger.error(
                "{}: _get_movements_parsed_from_next_page_filtered_by_dates: "
                "no 'data' field in resp_movs_filtered_next_page. "
                "Most probable reason: wrong event_number={}. Skip movements. RESPONSE:\n{}".format(
                    fin_ent_account_id,
                    event_number_param,
                    resp_movs_filtered_next_page.text
                ))
            return [], resp_json

        ok, movements_parsed = parse_helpers.get_movements_parsed(
            resp_json,
            self.logger,
            account_scraped,
            date_from_str,
            self.date_to_str,
        )

        return movements_parsed, resp_json

    def process_account(self,
                        s: MySession,
                        resp_logged_in: str,
                        event_number_param: int,
                        account_scraped: AccountScraped,
                        organization_title,
                        account_ix,
                        company_param=None) -> bool:

        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        date_from = datetime.datetime.strptime(date_from_str, project_settings.SCRAPER_DATE_FMT)

        self.basic_log_process_account(
            '{}: {}'.format(organization_title, fin_ent_account_id),
            date_from_str
        )

        # event_number += 1  # breaks more movs for API 3.0
        movements_parsed_all = []  # type: List[MovementParsed]

        movements_parsed_from_page, resp_json = \
            self._get_movements_parsed_from_first_page_filtered_by_dates(
                s,
                date_from,
                date_from_str,
                account_scraped,
                account_ix,
                company_param,
            )

        movements_parsed_all.extend(movements_parsed_from_page)

        # from ...=e1s1
        event_number_param_str = extract.re_first_or_blank(r'&execution=e(\d+)s\d+', json.dumps(resp_json))
        if event_number_param_str:
            event_number_param = int(event_number_param_str)
        else:
            self.logger.warning(
                '{}: expected event number in resp, but got nothing. Use calculated. RESPONSE:\n{}'.format(
                    fin_ent_account_id,
                    json.dumps(resp_json)
                )
            )

        #  more movements
        page_num = 0
        for i in range(150):  # limit the number of pages, 150 * 40 = 6000 movs
            page_num += 1  # 1st "more" page_num == 1

            resp_data = resp_json.get('data', {})
            if not resp_data:
                # already logged/reported
                break
            is_more_movements = resp_data.get('indicadorMasRegistros') or resp_data.get('indicadorPaginacion')
            if not is_more_movements:
                break

            self.logger.info("{}: parse more movements from page #{}".format(
                fin_ent_account_id, page_num
            ))

            time.sleep(0.1)
            movements_parsed_from_page, resp_json_i = \
                self._get_movements_parsed_from_next_page_filtered_by_dates(
                    s,
                    event_number_param,
                    date_from_str,
                    page_num,
                    account_scraped,
                    account_ix,
                    company_param,
                )

            movements_parsed_to_merge = list_funcs.uniq_tail(movements_parsed_all,
                                                             movements_parsed_from_page)

            # avoid inf loops even if is_more_movements == True
            if not movements_parsed_to_merge:
                self.logger.info('{}: no movements to merge. '
                                 'Break the loop'.format(fin_ent_account_id))
                break

            # avoid inf loops when backend returns movements of the 1st page after the last page
            if list_funcs.is_sublist(movements_parsed_all, movements_parsed_to_merge):
                self.logger.info(
                    '{}: fetched repeating movements (already in movements_parsed_all). '
                    'movements_parsed_all.index(movements_parsed_to_merge[0]) is {}. '
                    'Break the loop'.format(
                        fin_ent_account_id,
                        movements_parsed_all.index(movements_parsed_to_merge[0]),
                    )
                )
                break

            movements_parsed_all.extend(movements_parsed_to_merge)

            if (date_funcs.get_date_from_str(movements_parsed_from_page[-1]['operation_date'], '%Y-%m-%d')
                    < date_from):
                self.logger.info('{}: got movements with date < date_from. '
                                 'Break the loop'.format(fin_ent_account_id))
                break

            resp_json = resp_json_i

        movements_scraped, movements_parsed_filtered = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_all,
            date_from_str
        )

        self.basic_log_process_account(
            '{}: {}'.format(organization_title, fin_ent_account_id),
            date_from_str,
            movements_scraped
        )

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        self.download_receipts(s, account_scraped, movements_scraped, movements_parsed_filtered)
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

        self.logger.info('Logged in: {}'.format(date_funcs.now()))

        ok = self.process_access(s, resp_logged_in)
        if not ok:
            return self.basic_result_common_scraping_error()

        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
