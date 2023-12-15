import urllib.parse
from collections import OrderedDict
from concurrent import futures
from typing import List, Optional, Tuple

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import AccountParsed, MOVEMENTS_ORDERING_TYPE_ASC, ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.banca_march_scraper import parse_helpers
from .custom_types import AccountsDropdownPageData

__version__ = '6.6.0'

__changelog__ = """
6.6.0
call basic_upload_movements_scraped with date_from_str
6.5.0
renamed to download_correspondence()
6.4.0
skip inactive accounts
6.3.0
download_company_documents
6.2.0
process_access, _get_accounts_parsed_from_acc_details: handle new layout 
6.1.0
use basic_new_session
6.0.1
upd type hints
6.0.0
use Empresas view to extract accounts
use basic_log_wrong_layout
parse_helpers: more type hints
5.2.0
_get_accounts_parsed_from_acc_details: use only Consulta saldo disponible link for credit EUR accs
 to avoid access-level restrictions (Información de contrato may be blocked with err for the access)
5.1.0
process_account: correct implementation for non-EUR accounts (other requests)
parse_helpers: get_movements_parsed: handle null val in a date (skip - not a movement) 
5.0.0
removed 'resumen' page support (disabled for some accesses)
try to extract balance from 'contrato info' pages, or, if these pages are disabled, 
  then from 'saldo disponible' pages.
send err notification with suggestions if got foreign currency accounts from 'saldo disponible' pages
use basic_get_date_from
4.6.0
upd login method, use OWASP-CSRFTOKEN for all requests
4.5.0
basic_movements_scraped_from_movements_parsed: new format of the result
4.4.0
parse_helpers: upd selector
4.3.0
extract debit and credit accounts if there is no 'Resumen' page
4.2.0
extract accounts if there is no 'Resumen' page
4.1.0
Check for 'Resumen' page
4.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
"""


# TODO use Movements page to extract ccs param and IBAN
#  then get the acc details after movements is filtered
#  This allows to extact movs of closed accs and doesn't lean on
#  'Contrato' or 'Saldo' pagesself.update_inactive_accounts = False
class BancaMarchScraper(BasicScraper):
    scraper_name = 'BancaMarchScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.update_inactive_accounts = False

    def _fetch_csrf_token(self, s: MySession) -> str:
        resp_csrf_token = s.post(
            'https://telemarch.bancamarch.es/htmlVersion/JavaScriptServlet',
            headers=self.basic_req_headers_updated({
                'FETCH-CSRF-TOKEN': '1',
            }),
            proxies=self.req_proxies
        )

        # 'OWASP-CSRFTOKEN:OAEL-BSXN-B3LV-GS7W-NU0O-V9ZJ-VCPA-THCO'
        # -> 'OAEL-BSXN-B3LV-GS7W-NU0O-V9ZJ-VCPA-THCO'
        csrf_token = resp_csrf_token.text.split(':')[1]
        return csrf_token

    def _req_params_w_csrf_token(self, s: MySession, req_params: dict = None) -> dict:
        """Adds OWASP-CSRFTOKEN to all req_params"""
        token = self._fetch_csrf_token(s)
        req_params = req_params or {}
        req_params.update({'OWASP-CSRFTOKEN': token})
        return req_params

    def login(self) -> Tuple[MySession, Response, bool, bool]:

        s = self.basic_new_session()

        req_init_url = 'https://telemarch.bancamarch.es/htmlVersion/index.jsp?idioma=es'
        # get initial cookie
        resp_init = s.get(
            req_init_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        owasp_token = self._fetch_csrf_token(s)

        req_login_url = 'https://telemarch.bancamarch.es/htmlVersion/Login'

        req_login_params = OrderedDict([
            ('tr', 'login1'),
            ('acc', 'login'),
            ('testnw', 'H'),
            ('idioma', '0'),
            ('id', 'H'),
            ('app', 'bd'),
            ('script', '0'),
            ('lanzar', ''),
            ('param1', ''),
            ('param2', ''),
            ('param3', ''),
            ('param4', ''),
            ('param5', ''),
            ('param6', ''),
            ('showOp', ''),
            ('menu', ''),
            ('usuario', self.username),
            ('entorno', 'empresa'),
            ('tipoAutenticacion', 'clave'),
            ('clave', self.userpass),
            ('btnOk', 'Acceder'),
            ('OWASP-CSRFTOKEN', owasp_token)
        ])

        resp_logged_in = s.post(
            req_login_url,
            data=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = 'Desconectar' in resp_logged_in.text
        is_credentials_error = 'Identificación errónea' in resp_logged_in.text

        resp_empresas = None  # type: Optional[Response]
        if is_logged:
            # Switch to 'Empresas' view to be able to extract all accounts
            resp_empresas = s.get(
                'https://telemarch.bancamarch.es/htmlVersion/XTransManager'
                '?tr=ENTORNO&num=03080&idioma=&entorno=particular',
                params=self._req_params_w_csrf_token(s),
                headers=self.req_headers,
                proxies=self.req_proxies
            )

        return s, resp_empresas or resp_logged_in, is_logged, is_credentials_error

    def _get_accounts_parsed_of_specific_type(
            self,
            s: MySession,
            req_accounts_of_type_list_url: str) -> Tuple[MySession, List[AccountParsed]]:

        accounts_parsed_from_page = []  # type: List[AccountParsed]

        resp_page_w_accs_dropdown_list = s.get(
            req_accounts_of_type_list_url,
            params=self._req_params_w_csrf_token(s),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_link, req_params = extract.build_req_params_from_form_html_patched(
            resp_page_w_accs_dropdown_list.text,
            form_name='frm',
            is_ordered=True
        )

        accounts_ccs_params = parse_helpers.get_accounts_details_urls_params(
            resp_page_w_accs_dropdown_list.text
        )

        # expect 'https://telemarch.bancamarch.es/htmlVersion/XTransManager'
        req_acc_details_url = urllib.parse.urljoin(resp_page_w_accs_dropdown_list.url, req_link)
        for acc_ccs_param in accounts_ccs_params:
            # contract information
            # https://telemarch.bancamarch.es/htmlVersion/XTransManager?tr=OP&num=03252
            # &accion=infocontratoMenu&testnw=H&ccs=01001003930110000221
            # &btnAccept=Aceptar&OWASP-CSRFTOKEN=JMD8-NODE-HQ4G-V6RO-H8TX-M7MA-106S-K932
            #
            # consulta saldo
            # https://telemarch.bancamarch.es/htmlVersion/XTransManager?tr=OP&num=03001
            # &ccs=01001003930110000221&btnAccept=Aceptar
            # &OWASP-CSRFTOKEN=JMD8-NODE-HQ4G-V6RO-H8TX-M7MA-106S-K932

            req_params['ccs'] = acc_ccs_param
            req_acc_details_param = self._req_params_w_csrf_token(s, req_params)
            resp_acc_details = s.get(
                req_acc_details_url,
                params=req_acc_details_param,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            if 'SISTEMA NO DISPONIBLE TEMPORALMENTE' in resp_acc_details.text:
                self.basic_log_wrong_layout(
                    resp_acc_details,
                    "{}: can't get account_parsed. Err page. Skip".format(acc_ccs_param))
            else:
                try:
                    account_parsed = parse_helpers.get_account_parsed_from_details(
                        resp_acc_details.text,
                        acc_ccs_param
                    )
                    accounts_parsed_from_page.append(account_parsed)
                except Exception as exc:
                    self.basic_log_wrong_layout(
                        resp_acc_details,
                        "{}: can't get account_parsed. Got an EXCEPTION: {}. Skip".format(acc_ccs_param, exc)
                    )
        return s, accounts_parsed_from_page

    def _get_accounts_parsed_from_acc_details(
            self,
            s: MySession,
            resp_logged_in: Response) -> List[AccountParsed]:

        self.logger.info('Get accounts_parsed from account details pages')

        accounts_parsed = []  # type: List[AccountParsed]

        # Note: only 'contrato info' pages provides balances in foreign currency, so,
        # if there is no possibility to get 'contrato info' for foreign curr accounts,
        # the scraper will send err notification with suggestions what to do in this case.

        accs_dropdown_pages = [
            # Empresas view

            # EUR debit and credit
            # Cuentas -> Cuentas
            # With credit accs: -u 189397 -a 9314, -u 264489 -a 14517
            # -u 226491 -a 11121 (doesn't have 'Información de contrato')
            # Keep even after new layout sincw 22/05/2020
            AccountsDropdownPageData(
                is_foreign_currency=False,
                # NOT EXISTING opid_XXXYYY TO USE saldo_link_class,
                # suitable for any acc
                # where Información de contrato was failing for -u 264489 -a 14517 (access restriction)
                contrato_li_class='opid_XXXYYY',  # DISABLED due to -a 14517
                contrato_link_text='Información de contrato',
                saldo_link_class='opid_166',
                saldo_link_text='Consulta saldo disponible'
            ),
            # New layout since 22/05/2020
            AccountsDropdownPageData(
                is_foreign_currency=False,
                contrato_li_class='opid_XXXYYY',
                contrato_link_text='Información de contrato',
                saldo_link_class='opid_165',  # changed in New
                saldo_link_text='Consulta saldo disponible'
            ),

            # Foreign currency debit and credit
            # Cuentas -> Cuentas divisa/Internacional
            # -u 318793 -a 20115
            # Keep even after new layout after 22/05/2020
            AccountsDropdownPageData(
                is_foreign_currency=True,
                contrato_li_class='opid_155',
                contrato_link_text='Información de contrato',
                saldo_link_class='opid_120',
                saldo_link_text='Consulta saldo disponible',
            ),
            # New layout since 22/05/2020
            AccountsDropdownPageData(
                is_foreign_currency=True,
                contrato_li_class='opid_154',  # Changed in New
                contrato_link_text='Información de contrato',
                saldo_link_class='opid_XXXYYY',  # Disabled in New, no examples
                saldo_link_text='Consulta saldo disponible',
            ),

            # Particulares view: disabled
        ]

        for acc_dropdown_page_data in accs_dropdown_pages:
            req_accounts_of_type_list_url = parse_helpers.get_accounts_list_url(
                self.logger,
                resp_logged_in.text,
                resp_logged_in.url,
                acc_dropdown_page_data,
            )
            if req_accounts_of_type_list_url:
                s, accounts_parsed_i = self._get_accounts_parsed_of_specific_type(
                    s,
                    req_accounts_of_type_list_url
                )
                if accounts_parsed_i:
                    accounts_parsed += accounts_parsed_i
        return accounts_parsed

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:

        if not any(m in resp_logged_in.text for m in ['saldo disponible', 'Descargar App >']):
            self.basic_log_wrong_layout(resp_logged_in, "Can't extract accounts: no 'saldo disponible' found. Abort")
            return False

        accounts_parsed = self._get_accounts_parsed_from_acc_details(s, resp_logged_in)
        if not accounts_parsed:
            self.basic_log_wrong_layout(resp_logged_in, "No accounts_parsed extracted. Abort")
            return False

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                self.db_customer_name,
                account_parsed,
                is_default_organization=True
            )
            for account_parsed in accounts_parsed
        ]

        self.logger.info('Got {} accounts: {}'.format(len(accounts_scraped), accounts_scraped))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=len(accounts_scraped)) as executor:
                futures_dict = {
                    executor.submit(self.process_account, s, account_parsed): account_parsed['account_no']
                    for account_parsed in accounts_parsed
                }
                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_parsed in accounts_parsed:
                self.process_account(s, account_parsed)

        self.download_correspondence(s, organization_title=self.db_customer_name)
        return True

    def process_account(self, s: MySession, account_parsed: AccountParsed) -> bool:

        fin_ent_account_id = account_parsed['account_no']

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        acc_currency = account_parsed['currency']
        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        if acc_currency == 'EUR':
            req_mov_url = (
                'https://telemarch.bancamarch.es/htmlVersion/XTransManager?'
                'tr=OP'
                '&num=03002'
                '&paso=0'
                '&c01623={}'
                '&TIPO_EXTRACTO=periodo'
                '&c01575={}'
                '&c01770={}'
                '&TIPO_NATURALEZA=0'
                '&conceptosCsb=0'
                '&importeD='
                '&importeH='
                '&salida=txt'.format(
                    account_parsed['ccs_param'],
                    date_from_str,
                    self.date_to_str
                )
            )
        else:
            # To get correct bb param
            resp_mov_filter = s.get(
                'https://telemarch.bancamarch.es/htmlVersion/XTransManager?'
                'tr=OP'
                '&num=03026_Cuentas',
                params=self._req_params_w_csrf_token(s),
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            req_mov_url = (
                'https://telemarch.bancamarch.es/htmlVersion/XTransManager?'
                'tr=OP'
                '&num=03026_Cuentas'
                '&accion=consulta'
                '&bb={}'
                '&ccs={}'
                '&tipopeticion=fecha'
                '&fecha={}'
                '&formatosalida=txt'
                '&btnAccept=Aceptar'.format(
                    extract.form_param(resp_mov_filter.text, 'bb'),
                    account_parsed['ccs_param'],
                    date_from_str,  # '01/08/2019'
                )
            )

        resp_mov = s.get(
            req_mov_url,
            params=self._req_params_w_csrf_token(s),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        movements_parsed = parse_helpers.get_movements_parsed(resp_mov.text)
        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            self.basic_account_scraped_from_account_parsed(
                self.db_customer_name,
                account_parsed,
                is_default_organization=True
            ),
            movements_scraped,
            date_from_str=date_from_str
        )

        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url, resp_logged_in.text)

        self.process_access(s, resp_logged_in)
        self.basic_log_time_spent('GET MOVEMENTS')

        return self.basic_result_success()
