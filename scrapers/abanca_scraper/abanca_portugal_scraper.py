import datetime
import re
import threading
import time
import urllib.parse
from collections import OrderedDict
from concurrent import futures
from typing import Dict, List, Optional, Set, Tuple

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, MOVEMENTS_ORDERING_TYPE_ASC, DOUBLE_AUTH_REQUIRED_TYPE_COMMON,
    MovementParsed, ScraperParamsCommon, MainResult, BLOCKED_USER_TYPE_COMMON
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.abanca_scraper import parse_helpers
from scrapers.abanca_scraper.custom_types import AccountByCompany, Company

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'

__version__ = '1.1.0'

__changelog__ = """
1.1.0 2023.10.20
refactored 'country' to 'iban_country_code'
1.0.0 2023.10.18
init
refactored from AbancaBeAbancaScraper to AbancaPortugalScraper
"""

WRONG_CREDENTIALS_MARKERS = [
    'Error ao validar credenciaIS',  # wrong password
    'Os dados de entrada n&#227;o est&#227;o corretos',  # wrong username
    'seu dispositivo Token',  # hardware token access
]

DOUBLE_AUTH_MARKERS = [
    'recebidas em seu celular',
    'devemos verificar sua identidade',
]

NEW_PIN_REQUIRED_MARKER = ('deve modificar seu PIN')

BLOCKED_USER_MARKERS = [
    'bloqueado inserindo o Pin',  # user blocked after many attempts
]


class AbancaPortugalScraper(BasicScraper):
    scraper_name = 'AbancaPortugalScraper'
    iban_country_code = 'PT'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.req_headers = {'User-Agent': USER_AGENT}
        self.__uniq_accounts = set()  # type: Set[str]
        self.__lock = threading.Lock()
        self.update_inactive_accounts = False
        self.must_use_username_second = False
        self.is_success = True
        # Special dict to get these flags from different pages,
        # True if 'no accounts' marker has been detected
        # from 'Contas a ordem' top menu page
        self._no_accounts_flags = {}  # type: Dict[str, bool]

    def _default_company(self) -> Company:
        """It's used for one-company accesses"""
        # Note idx == -1
        return Company(title=self.db_customer_name, idx=-1, idcl_param='')

    def _is_uniq_account(self, fin_ent_account_id: str) -> bool:
        """Allows to avoid double scraping for accounts attached several times
        to different contracts (-u 318793 -a 20114).
        In this case, the duplicated account will be processed only one time.
        Finally, it reduces the number of open sessions for serial and parallel scraping
        and makes it more stable.

        :returns true if a new one (unique), false if duplicated
        """
        with self.__lock:
            if fin_ent_account_id not in self.__uniq_accounts:
                # the new one
                self.__uniq_accounts.add(fin_ent_account_id)
                return True
        # duplicated
        return False

    def _get_date_from(self, fin_ent_account_id) -> str:
        """Since 09/2019 there is a limitation: max offset is 90 days"""
        date_from_str_by_db = self.basic_get_date_from(fin_ent_account_id)
        date_from = max(
            date_funcs.get_date_from_str(date_from_str_by_db),
            self.date_to - datetime.timedelta(days=89)
        )
        date_from_str = date_funcs.convert_dt_to_scraper_date_type1(date_from)
        if date_from_str != date_from_str_by_db:
            self.logger.info("{}: redefined date_from due to max 90 days offset")
        return date_from_str

    def _set_has_no_accounts(self, company_title: str, has_no_accounts_flag: bool) -> bool:
        with self.__lock:
            self._no_accounts_flags[company_title] = has_no_accounts_flag
        return True

    def _get_has_no_accounts(self, company_title: str) -> Optional[bool]:
        with self.__lock:
            val = self._no_accounts_flags.get(company_title)
        return val

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        self.logger.info('login: start')

        s = self.basic_new_session()
        # set to False as insecure temporary fix
        # if [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
        s.verify = True
        self.logger.info('login: open home page: start')
        resp_init = s.get('https://be.abanca.pt', headers=self.req_headers, proxies=self.req_proxies)
        self.logger.info('login: open home page: success')

        view_state_param = parse_helpers.get_view_state_param(resp_init.text)
        # username_second is for CaixaGeral accesses
        username = self.username_second if self.must_use_username_second else self.username
        self.logger.info('Log in with username "{}..."'.format(username[:5]))

        req_params = OrderedDict([
            ('loginForm:infoCompatibilidadOpenedState', ''),
            ('loginForm:param', '2080'),
            ('loginForm:j_token_id', username),
            ('loginForm:j_pin', self.userpass),
            ('loginForm:btnAceptar', 'Entrar'),
            ('loginForm_SUBMIT', '1'),
            ('loginForm:_idcl', ''),
            ('javax.faces.ViewState', view_state_param),
        ])

        req_login_url = 'https://be.abanca.pt/BEPRJ001/jsp/SECURE_login_pt_step1.faces'

        self.logger.info('login: auth req: start')
        resp_logged_in = s.post(
            req_login_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        self.logger.info('login: auth req: success')

        is_logged = 'Sair' in resp_logged_in.text

        is_credentials_error = any(m in resp_logged_in.text for m in WRONG_CREDENTIALS_MARKERS)
        reason = ''
        if any(m in resp_logged_in.text for m in DOUBLE_AUTH_MARKERS):
            is_logged = False
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        if NEW_PIN_REQUIRED_MARKER in resp_logged_in.text:
            self.logger.error('Detected: "NEW PIN required. Pls, inform the customer". '
                              'Consider as wrong credentials')
            is_logged = False
            is_credentials_error = True

        if any(m in resp_logged_in.text for m in BLOCKED_USER_MARKERS):
            self.logger.error('Bank blocked user')
            reason = BLOCKED_USER_TYPE_COMMON
        self.logger.info('login: finished')
        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def _load_position_global_page_details(
            self,
            s: MySession,
            company_title: str,
            page_source: str) -> Tuple[MySession, Response]:
        """Ajax resp to load all necessary data on position global page.
        It can be loaded partially, so need to check and reload if necessary
        """
        req_url = ('https://be.abanca.pt/BEPRJ001/jsp/'
                   'BEPR_PosicionGlobalInicio.faces?javax.portlet.faces.DirectLink=true')
        view_state_param = parse_helpers.get_view_state_param(page_source)
        # self.logger.info('view_state_param: {}'.format(view_state_param))

        req_params = OrderedDict([
            ('AJAXREQUEST', '_viewRoot'),
            ('formulario:idcc', parse_helpers.get_idcc_param(page_source)),
            ('formulario:CAT_CTAS_PT:0:operacionCuentas', ''),
            ('formulario:CAT_CTAS_PT__hiddenSelected', ''),
            ('formulario:CAT_CTAS_PT__hiddenDeselected', ''),
            ('formulario:CAT_CTAS_PT_tablaSeleccion', ''),
            ('formulario:CAT_CREDITO_PT:0:operacionCreditos', ''),
            ('formulario:CAT_CREDITO_PT__hiddenSelected', ''),
            ('formulario:CAT_CREDITO_PT__hiddenDeselected', ''),
            ('formulario:CAT_CREDITO_PT_tablaSeleccion', ''),
            ('formulario_SUBMIT', '1'),
            ('formulario:_link_hidden_', ''),
            ('formulario:_idcl', ''),
            ('javax.faces.ViewState', view_state_param),
            ('formulario:btnCargarPosicionGlobal', 'formulario:btnCargarPosicionGlobal')
        ])

        resp_pos_global = Response()
        for att in range(1, 16):

            self.logger.info('{}: _load_position_global_page_details: att #{}: start'.format(
                company_title,
                att
            ))
            resp_pos_global = s.post(
                req_url,
                data=req_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
            )

            # links loaded?
            if not re.search(r'(?si)<td class="pglobal-column-1">\s*(<script.*?</script>\s*)?<a.*?</td>',
                             resp_pos_global.text):
                self.logger.info(
                    '{}: _load_position_global_page_details: att #{}: '
                    'partial content detected: retry'.format(
                        company_title,
                        att
                    )
                )
                time.sleep(1.0 * att)
                continue

            try:
                parse_helpers.get_accounts_parsed(resp_pos_global.text, self.iban_country_code)
            except ValueError as exc:
                # can't convert to float - no balance returned, need to retry
                if 'could not convert string to float' in str(exc):
                    time.sleep(1.0)
                    continue
                else:
                    raise exc
            self.logger.info('{}: _load_position_global_page_details: att #{}: success'.format(
                company_title,
                att
            ))
            break
        else:
            # It's possible that there are no active accounts.
            # Check it from 'Contas' page
            resp_accounts = s.get(
                'https://be.abanca.pt/BEPRJ001/jsp/app.faces?_flowId=BEPR_posicionCuentas-flow',
                headers=self.req_headers,
                proxies=self.req_proxies
            )
            ok, has_no_accounts = parse_helpers.check_no_accounts_pt(resp_accounts.text)
            if ok and has_no_accounts:
                self.logger.info("{}: 'no accounts' flag detected".format(company_title))
                self._set_has_no_accounts(company_title, has_no_accounts)
                return s, resp_pos_global

            if not ok:
                self.basic_log_wrong_layout(
                    resp_accounts,
                    "Can't get 'has_no_accounts' flag"
                )

            self.logger.error('{}: _load_position_global_page_details: failed. RESPONSE:\n{}'.format(
                company_title,
                resp_pos_global.text
            ))
            self.is_success = False

        return s, resp_pos_global

    def get_accounts_scraped(self,
                             s: MySession,
                             resp_prev: Response,
                             company: Company,
                             is_default_organization=False) -> List[AccountScraped]:
        ok, accounts_parsed = parse_helpers.get_accounts_parsed(resp_prev.text, self.iban_country_code)
        if not ok and (self._get_has_no_accounts(company.title) is not True):
            self.basic_log_wrong_layout(resp_prev, 'No accounts_parsed')
            self.is_success = False
        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                company.title,
                account_parsed,
                is_default_organization=is_default_organization,
                country_code='PRT'
            )
            for account_parsed in accounts_parsed
        ]

        return accounts_scraped


    def _open_recent_movements(
            self,
            s: MySession,
            flow_execution_key: str,
            idcl_param: str,
            idcc_param: str,
            view_state_param: str) -> Tuple[MySession, Response]:
        """This page contains filter form to get movements for specific account"""

        req_url = ('https://be.abanca.pt/BEPRJ001/jsp/'
                   'BEPR_PosicionGlobalInicio.faces?javax.portlet.faces.DirectLink=true')
        req_headers = self.req_headers.copy()
        # resp company selected (not loaded)
        req_headers['Referer'] = ('https://be.abanca.pt/BEPRJ001/jsp/BEPR_SeleccionContrato.faces'
                                  '?_flowExecutionKey={}'.format(flow_execution_key))
        req_headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'

        req_params = OrderedDict([
            ('formulario:idcc', idcc_param),
            ('formulario:CAT_CTAS_PT:0:operacionCuentas', ''),
            ('formulario:CAT_CTAS_PT__hiddenSelected', ''),
            ('formulario:CAT_CTAS_PT__hiddenDeselected', ''),
            ('formulario:CAT_CTAS_PT_tablaSeleccion', ''),
            ('formulario:CAT_CREDITO_PT:0:operacionCreditos', ''),
            ('formulario:CAT_CREDITO_PT__hiddenSelected', ''),
            ('formulario:CAT_CREDITO_PT__hiddenDeselected', ''),
            ('formulario:CAT_CREDITO_PT_tablaSeleccion', ''),
            ('formulario:CAT_PRESTAMO_PT:0:operacionPrestamosEspana', ''),
            ('formulario:CAT_PRESTAMO_PT__hiddenSelected', ''),
            ('formulario:CAT_PRESTAMO_PT__hiddenDeselected', ''),
            ('formulario:CAT_PRESTAMO_PT_tablaSeleccion', ''),
            ('formulario_SUBMIT', '1'),
            ('formulario:_link_hidden_', ''),
            ('formulario:_idcl', idcl_param),
            ('javax.faces.ViewState', view_state_param),
        ])

        resp_recent_mov = s.post(
            req_url,
            data=req_params,
            headers=req_headers,
            proxies=self.req_proxies
        )

        return s, resp_recent_mov

    def _open_date_filter(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            date_from_str: str,
            view_state_param: str,
            date_separator: str) -> Tuple[MySession, Response]:

        account_no_param = account_scraped.AccountNo

        req_url = 'https://be.abanca.pt/BEPRJ001/jsp/BEPR_movimientos_LST.faces?javax.portlet.faces.DirectLink=true'

        req_params = OrderedDict([
            ('AJAXREQUEST', '_viewRoot'),
            ('formulario:panelAyudaOpenedState', ''),
            ('formulario:panelModalSaldosOpenedState', ''),
            ('formulario:idCuenta', account_no_param),
            ('formulario:radioSeleccion', 'F'),
            ('formulario:fInicioInputDate', date_from_str.replace('/', date_separator)),
            ('formulario:fInicioInputCurrentDate', date_from_str[-7:]),
            ('formulario:tipoOrdenacion', ['1', '1']),
            ('formulario:fFinInputDate', self.date_to_str.replace('/', date_separator)),
            ('formulario:fFinInputCurrentDate', self.date_to_str[-7:]),
            ('formulario:importeD', ''),
            ('formulario:importeH', ''),
            ('formulario:concepto', ''),
            ('formulario:tipo', ''),
            ('formulario:dataMovimientos__hiddenSelected', ''),
            ('formulario:dataMovimientos__hiddenDeselected', ''),
            ('formulario:dataMovimientos_tablaSeleccion', ''),
            ('formulario_SUBMIT', '1'),
            ('formulario:_link_hidden_', ''),
            ('formulario:_idcl', ''),
            ('javax.faces.ViewState', view_state_param),
            ('formulario:supporttipoOrdenacion', 'formulario:supporttipoOrdenacion',)
        ])

        resp_date_filter = s.post(
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        return s, resp_date_filter

    def _open_movs_filtered(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            date_from_str: str,
            view_state_param: str,
            date_separator: str) -> Tuple[MySession, Response]:

        account_no_param = account_scraped.AccountNo

        date_from_param = date_from_str.replace('/', date_separator)
        date_to_param = self.date_to_str.replace('/', date_separator)
        date_from_current_date_param = date_from_str[-7:]
        date_to_current_date_param = self.date_to_str[-7:]

        req_movs_params = OrderedDict([
            ('formulario:panelAyudaOpenedState', ''),
            ('formulario:panelModalSaldosOpenedState', ''),
            ('formulario:idCuenta', account_no_param),
            ('formulario:radioSeleccion', 'F'),
            ('formulario:fInicioInputDate', date_from_param),
            ('formulario:fInicioInputCurrentDate', date_from_current_date_param),
            ('formulario:tipoOrdenacion', '1'),
            ('formulario:fFinInputDate', date_to_param),
            ('formulario:fFinInputCurrentDate', date_to_current_date_param),
            ('formulario:importeD', ''),
            ('formulario:importeH', ''),
            ('formulario:concepto', ''),
            ('formulario:tipo', ''),
            ('formulario:btnFiltrar', 'Consultar'),
            ('formulario:dataMovimientos__hiddenSelected', ''),
            ('formulario:dataMovimientos__hiddenDeselected', ''),
            ('formulario:dataMovimientos_tablaSeleccion', ''),
            ('formulario_SUBMIT', '1'),
            ('formulario:_link_hidden_', ''),
            ('formulario:_idcl', ''),
            ('javax.faces.ViewState', view_state_param)
        ])

        resp_mov_filtered_html = s.post(
            'https://be.abanca.pt/BEPRJ001/jsp/BEPR_movimientos_LST.faces',
            data=req_movs_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return s, resp_mov_filtered_html

    def _open_movs_excel(
            self,
            s: MySession,
            resp_movs_html: Response,
            account_scraped: AccountScraped,
            date_from_str: str,
            view_state_param: str,
            flow_execution_key: str,
            date_separator: str) -> Tuple[bool, MySession, Response]:
        """:returns (is_success, session, resp_excel_or_any_if_failed)"""

        account_no_param = account_scraped.AccountNo

        excel_param = parse_helpers.get_excel_param(resp_movs_html.text)
        if not excel_param:
            self.logger.error("{} (company {}): can't get correct excel_param. Skip _open_mov_excel".format(
                account_scraped.FinancialEntityAccountId,
                account_scraped.OrganizationName
            ))
            return False, s, resp_movs_html  # resp_movs_filtered_html is useless for further extraction

        date_from_param = date_from_str.replace('/', date_separator)
        date_to_param = self.date_to_str.replace('/', date_separator)
        date_from_current_date_param = date_from_str[-7:]
        date_to_current_date_param = self.date_to_str[-7:]

        req_preexcel_params = OrderedDict([
            ('AJAXREQUEST', '_viewRoot'),
            ('formulario:panelAyudaOpenedState', ''),
            ('formulario:panelModalSaldosOpenedState', ''),
            ('formulario:idCuenta', account_no_param),  # '20801208213040001027'
            ('formulario:ultimosmeses', ''),
            ('formulario:radioSeleccion', 'F'),
            ('formulario:fInicioInputDate', date_from_param),  # '15/10/2018' or '15-10-2018'
            ('formulario:fInicioInputCurrentDate', date_from_current_date_param),  # '10/2018'
            ('formulario:tipoOrdenacion', '1'),
            ('formulario:fFinInputDate', date_to_param),  # '07/11/2018' or '07-11-2018'
            ('formulario:fFinInputCurrentDate', date_from_current_date_param),  # '11/2018'
            ('formulario:importeD', ''),
            ('formulario:importeH', ''),
            ('formulario:concepto', ''),
            ('formulario:tipo', ''),
            ('formulario_SUBMIT', '1'),
            ('formulario:_link_hidden_', ''),
            ('formulario:_idcl', ''),
            ('javax.faces.ViewState', view_state_param),
            # ('formulario:_idJsp398', 'formulario:_idJsp398'), # old val
            # ('formulario:_idJsp400', 'formulario:_idJsp400'), # old val
            # ('formulario:_idJsp401', 'formulario:_idJsp401'), # replaced with excel_param
            (excel_param, excel_param),
        ])

        req_preexcel_headers = self.basic_req_headers_updated({
            'Referer': resp_movs_html.url,
            'Accept': '*/*'
        })

        _resp_preexcel = s.post(
            'https://be.abanca.pt/BEPRJ001/jsp/BEPR_movimientos_LST.faces?javax.portlet.faces.DirectLink=true',
            data=req_preexcel_params,
            headers=req_preexcel_headers,
            proxies=self.req_proxies
        )

        req_excel_params = OrderedDict([
            ('formulario:btnExportToExcel', 'Submit Query'),
            ('formulario:panelAyudaOpenedState', ''),
            ('formulario:panelModalSaldosOpenedState', ''),
            ('formulario:idCuenta', account_no_param),  # '20801208213040001027'
            ('formulario:radioSeleccion', 'F'),
            ('formulario:fInicioInputDate', date_from_param),  # '15/10/2018'
            ('formulario:fInicioInputCurrentDate', date_from_current_date_param),  # '10/2018'
            ('formulario:tipoOrdenacion', '1'),
            ('formulario:fFinInputDate', date_to_param),  # '07/11/2018'
            ('formulario:fFinInputCurrentDate', date_to_current_date_param),  # '11/2018'
            ('formulario:importeD', ''),
            ('formulario:importeH', ''),
            ('formulario:concepto', ''),
            ('formulario:tipo', ''),
            ('formulario_SUBMIT', '1'),
            ('formulario:_link_hidden_', ''),
            ('formulario:_idcl', ''),
            ('javax.faces.ViewState', view_state_param),
        ])

        req_excel_headers = self.basic_req_headers_updated({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1'
        })

        resp_movs_excel = s.post(
            'https://be.abanca.pt/BEPRJ001/jsp/BEPR_movimientos_LST.faces',
            data=req_excel_params,
            headers=req_excel_headers,
            proxies=self.req_proxies,
            stream=True
        )

        return True, s, resp_movs_excel

    # to test file downloading from abanca - working but not used
    def _open_movs_pdf(
            self,
            s: MySession,
            view_state_param: str,
            flow_execution_key) -> Tuple[MySession, Response]:

        req_url = 'https://be.abanca.pt/BEPRJ001/jsp/BEPR_movimientos_LST.faces'

        req_params = OrderedDict([
            ('formAux_SUBMIT', '1'),
            ('formAux:_idcl', 'formAux:idPdf2'),
            # ('formAux:_idcl', 'formAux:idExcel1'),
            ('formAux:_link_hidden_', ''),
            ('javax.faces.ViewState', view_state_param)
        ])

        req_headers = self.req_headers.copy()
        req_headers['Referer'] = ('https://be.abanca.pt/BEPRJ001/jsp/BEPR_movimientos_LST.faces'
                                  '?_flowExecutionKey={}'.format(flow_execution_key))
        req_headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'

        resp_mov_pdf = s.post(
            req_url,
            data=req_params,
            headers=req_headers,
            proxies=self.req_proxies,
            stream=True
        )

        return s, resp_mov_pdf

    def _get_companies(self, resp_logged_in: Response) -> Tuple[List[Company], Dict[str, str], str]:

        action_url_raw, req_params_raw = extract.build_req_params_from_form_html(
            resp_logged_in.text,
            'formSeleccion'
        )
        # delete unused params
        req_select_company_params = {k: v for k, v in req_params_raw.items()
                                     if ('Cabecera' not in k and 'Panel' not in k)}

        req_select_company_url = urllib.parse.urljoin(resp_logged_in.url, action_url_raw)
        companies = parse_helpers.get_companies(resp_logged_in.text)  # type: List[Company]
        return companies, req_select_company_params, req_select_company_url

    def _open_resp_company_selected(
            self,
            company: Company,
            is_multicontract=True) -> Tuple[bool, MySession, Response, Company, Response]:
        """:returns (is_success, s, resp_company_selected_loaded, company, resp_company_selected)"""

        # empty company for false results
        default_company = self._default_company()

        # log in for each company processing
        # and redefine company processing params
        company_title = company.title
        self.logger.info('{}: _open_resp_company_selected: login: start'.format(company_title))

        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()
        self.logger.info('{}: _open_resp_company_selected: login: success'.format(company_title))

        if not is_logged:
            self.logger.error('{}: not logged in while processing. Reason: {}'.format(
                company_title,
                reason or '<unknown>'
            ))
            self.is_success = False
            return False, s, Response(), default_company, Response()

        if is_multicontract:
            companies, req_params, req_url = self._get_companies(resp_logged_in)

            if company != self._default_company():
                for c in companies:
                    if company.title == c.title and company.idx == c.idx:
                        company = c  # change idcl_param
                        break
                else:
                    self.logger.error('Company with title {} not found in {}'.format(company.title, companies))
                    self.is_success = False
                    return False, s, Response(), default_company, Response()
            else:
                self.logger.error('company {} is not correct for multi-contract'.format(company))
                self.is_success = False
                return False, s, Response(), default_company, Response()

            company_req_params = req_params.copy()
            company_req_params['formSeleccion:_idcl'] = company.idcl_param

            resp_company_selected = s.post(
                req_url,
                data=company_req_params,
                headers=self.basic_req_headers_updated({'Referer': resp_logged_in.url}),
                proxies=self.req_proxies
            )
        else:
            # default company
            company = self._default_company()
            resp_company_selected = resp_logged_in

        if 'Nenhum contrato dispon' in resp_company_selected.text:
            time.sleep(5)
            self.basic_log_wrong_layout(resp_company_selected, 'Contract not selected. Abort.')
            self.is_success = False
            return False, s, Response(), default_company, Response()

        s, resp_company_selected_loaded = self._load_position_global_page_details(
            s,
            company.title,
            resp_company_selected.text
        )
        return True, s, resp_company_selected_loaded, company, resp_company_selected

    def process_company_to_get_balances(
            self,
            company: Company,
            s: MySession,
            resp_logged_in: Response,
            is_multicontract=True) -> List[AccountByCompany]:

        if is_multicontract:
            ok, s, resp_company_selected, company, _ = self._open_resp_company_selected(company)
            # not logged in - return empty list of accounts
            # then they will be marked as scraped by state resetter
            if not ok:
                return []
            accounts_scraped = self.get_accounts_scraped(s, resp_company_selected, company)
        else:
            accounts_scraped = self.get_accounts_scraped(
                s,
                resp_logged_in,
                company,
                is_default_organization=True
            )
        self.logger.info('{}: got {} accounts: {}'.format(
            company.title,
            len(accounts_scraped),
            accounts_scraped
        ))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        accounts_by_company = [
            AccountByCompany(account_scraped=account_scraped, company=company)
            for account_scraped
            in accounts_scraped
        ]

        return accounts_by_company

    def process_companies_to_get_balances(
            self,
            s: MySession,
            resp_logged_in: Response) -> Tuple[List[AccountByCompany], bool]:

        accounts_by_companies = []  # type: List[AccountByCompany]
        companies, req_params, req_url = self._get_companies(resp_logged_in)
        self.logger.info('Got {} companies (contracts): {}'.format(
            len(companies),
            companies
        ))
        is_multicontract = False

        # several contracts
        if companies:
            is_multicontract = True
            self.logger.info('Is multicontract: {}'.format(is_multicontract))
            # iterate over len of companies, each company param could be redefined
            # when logged in again
            for company in companies:
                accounts_by_company = self.process_company_to_get_balances(company, s, resp_logged_in)
                accounts_by_companies.extend(accounts_by_company)
        # one contract
        else:
            self.logger.info('Is multicontract: {}'.format(is_multicontract))
            company = self._default_company()
            s, resp_company_selected_loaded = self._load_position_global_page_details(
                s,
                company.title,
                resp_logged_in.text
            )
            accounts_by_company = self.process_company_to_get_balances(
                company,
                s,
                resp_company_selected_loaded,
                is_multicontract=False
            )
            accounts_by_companies.extend(accounts_by_company)

        return accounts_by_companies, is_multicontract

    def process_accounts(self, accounts_by_companies: List[AccountByCompany], is_multicontract: bool) -> bool:
        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=max(len(accounts_by_companies), 1)) as executor:
                futures_dict = {
                    executor.submit(self.process_account,
                                    account_by_company,
                                    is_multicontract): account_by_company
                    for account_by_company in accounts_by_companies
                }
                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_by_company in accounts_by_companies:
                self.process_account(account_by_company, is_multicontract)

        self.basic_log_time_spent('GET MOVEMENTS')

        return True

    def process_account(self, account_by_company: AccountByCompany, is_multicontract: bool) -> bool:

        company = account_by_company.company
        account_scraped = account_by_company.account_scraped

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        if not self._is_uniq_account(fin_ent_account_id):
            self.logger.info("{}: has been processed already. Skip".format(
                fin_ent_account_id
            ))
            return True

        account_no = account_scraped.AccountNo

        date_from_str = self._get_date_from(fin_ent_account_id)

        self.logger.info('Process account {}: {}'.format(account_no, company))

        ok, s, resp_comp_selected_loaded, company, resp_comp_selected = self._open_resp_company_selected(
            company,
            is_multicontract=is_multicontract
        )

        if not ok:
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_CANT_SWITCH_TO_CONTRACT)
            return False

        flow_execution_key1 = parse_helpers.get_flow_execution_key(resp_comp_selected.url)
        idcc_param1 = parse_helpers.get_idcc_param(resp_comp_selected.text)
        view_state_param1 = parse_helpers.get_view_state_param(resp_comp_selected.text)
        ok, idcl_param = parse_helpers.get_account_idcl_param(resp_comp_selected_loaded.text, account_no)
        if not ok:
            self.basic_log_wrong_layout(
                resp_comp_selected_loaded,
                "{}: can't find idcl_param for the account".format(account_no)
            )
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
            return False

        exception = None  # type: Optional[Exception]
        resp_for_err_report = Response()
        movements_parsed_excel = []  # type: List[MovementParsed]
        reason = ''
        for i in range(3):
            s, resp_mov_recent = self._open_recent_movements(
                s,
                flow_execution_key1,
                idcl_param,
                idcc_param1,
                view_state_param1
            )

            # '-' or '/' for different accesses (!)
            date_separator = parse_helpers.get_date_separator(resp_mov_recent.text)
            if not date_separator:
                self.logger.warning("{}: can't extract date_separator. Retry".format(
                    fin_ent_account_id,
                ))
                resp_for_err_report = resp_mov_recent
                continue

            view_state_param2 = parse_helpers.get_view_state_param(resp_mov_recent.text)
            s, resp_date_filter = self._open_date_filter(
                s,
                account_scraped,
                date_from_str,
                view_state_param2,
                date_separator
            )

            view_state_param3 = parse_helpers.get_view_state_param(resp_date_filter.text)
            s, resp_movs_filtered = self._open_movs_filtered(
                s,
                account_scraped,
                date_from_str,
                view_state_param3,
                date_separator
            )

            if 'o tem movimentos na conta para a pesquisa indicada' in resp_movs_filtered.text:
                self.logger.info('{}: no movements found during period from {} to {}. Skip'.format(
                    fin_ent_account_id,
                    date_from_str,
                    self.date_to_str
                ))
                break

            # Only 2nd attempt filters by D.Valor!
            # 1st attempt filtered by D.Contavel
            s, resp_movs_filtered2 = self._open_movs_filtered(
                s,
                account_scraped,
                date_from_str,
                view_state_param=parse_helpers.get_view_state_param(resp_movs_filtered.text),
                date_separator=date_separator
            )

            view_state_param4 = parse_helpers.get_view_state_param(resp_movs_filtered2.text)
            ok, s, resp_mov_excel = self._open_movs_excel(
                s,
                resp_movs_filtered,
                account_scraped,
                date_from_str,
                view_state_param4,
                flow_execution_key1,
                date_separator
            )

            if not ok:
                resp_for_err_report = resp_mov_excel
                continue
            # s, resp_mov_pdf = self._open_mov_pdf(s, view_state_param4, flow_execution_key1)

            try:
                movements_parsed_excel, reason = parse_helpers.get_movements_parsed_from_excel(
                    resp_mov_excel,
                    account_no
                )
                if reason:
                    self.logger.warning('{}: {}. RETRY'.format(
                        fin_ent_account_id,
                        reason
                    ))
                    exception = None
                    resp_for_err_report = resp_mov_excel
                    time.sleep(0.5)
                    continue

                # commented since excel movs repaired at 2018-11-07
                # can't parse all movements if pagination occurred
                # movements_parsed_all = parse_helpers.get_movements_parsed(resp_mov_filtered.text)
                break
            except Exception as exc:
                self.logger.warning(
                    "Can't parse movs from resp for {}: dates from {} to {}: {}. RETRY".format(
                        account_by_company,
                        date_from_str,
                        self.date_to_str,
                        exc
                    )
                )
                reason = ''
                resp_for_err_report = resp_mov_excel
                time.sleep(0.5)
                exception = exc
        else:
            if reason:
                self.logger.error(
                    "Can't parse movements from {}: dates from {} to {}:\n"
                    "REASON:\n{}\n\nRESPONSE:\n{}".format(
                        account_by_company,
                        date_from_str,
                        self.date_to_str,
                        reason,
                        resp_for_err_report.text,
                    )
                )
            else:
                self.logger.error(
                    "Can't parse movements from {}: dates from {} to {}:\n"
                    "EXCEPTION:\n{}\n\nRESPONSE:\n{}".format(
                        account_by_company,
                        date_from_str,
                        self.date_to_str,
                        exception,
                        resp_for_err_report.text,
                    )
                )

            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
            self.is_success = False
            return False

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_excel,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.logger.info(
            'Process_account {}: from company {}: dates from {} to {}: {} movements: {}'.format(
                account_no,
                company.title,
                date_from_str,
                self.date_to_str,
                len(movements_scraped),
                movements_scraped
            )
        )

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

        accounts_by_companies, is_multicontract = self.process_companies_to_get_balances(s, resp_logged_in)
        if not self.is_success:
            return self.basic_result_common_scraping_error()

        self.process_accounts(accounts_by_companies, is_multicontract)
        self.download_correspondence()

        return self.basic_result_success()

        if not self.access_type_scraper:
            return self.basic_result_common_scraping_error()

        return self.access_type_scraper.main()