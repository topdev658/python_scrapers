import random
import time
from concurrent import futures
from typing import Dict, Tuple
from urllib.parse import urljoin

from custom_libs import extract
from custom_libs.check_resp import is_error_msg_in_resp
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, DOUBLE_AUTH_REQUIRED_TYPE_COOKIE
from scrapers.ruralvia_scraper import parse_helpers
from scrapers.ruralvia_scraper.ruralvia_scraper import (
    DEFAULT_COMPANY_TITLE, ERR_RESP_MARKERS, REQ_HEADERS,
    RuralviaScraper, LOGIN_ATTEMPTS
)

__version__ = '1.13.0'

__changelog__ = """
1.14.0
fix the new window with the changes
Add the logg if the scraper not found accounts in the bank
1.13.0
use strict _rstrip_aux
1.12.1
upd type hints
1.12.0
login: more delays
1.11.0
logout
1.10.0
login: upd req params
1.9.0
login: several confirmation for 'wrong credentials'
N_COMPANY_PROCESSING_WORKERS = 1
1.8.0
process_company: several attempts to log in
login: more delays, more checks
manual exceptions -> is_success flags
upd wrong credentials marker
upd self.domain
double auth detector
1.7.1
login: delete req param with a linter-friendly approach
1.7.0
use basic_new_session
upd type hints
1.6.0
disabled is_credentials_error (always False)
1.5.0
login: changed signature
1.4.0
loop and additional checks for more stable authorization
1.3.1
urljoin for action_url (to be sure), longer delays
1.3.0
login: adjusted delays and headers for more stable authorization, more log msgs
1.2.1
fixed typo in comments
1.2.0
upd login method (new req params)
1.1.0
new login method (different to common Ruralvia's method)
1.0.0
init
"""

WRONG_CREDENTIALS_MARKERS = [
    # 'Error de acceso' covers too wide range of cases, use more explicit
    'Has introducido de forma incorrecta alguno de los datos para el usuario indicado',
    'Tu usuario ha sido bloqueado'
]


class BankoaScraper(RuralviaScraper):
    """
    Basic functions from RuralviaScraper
    """
    N_COMPANY_PROCESSING_WORKERS = 1  # gentle processing

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BankoaScraper') -> None:

        super().__init__(scraper_params_common, proxies, scraper_name)
        self.logger.info('Scraper started')
        self.domain = 'https://bankoa.bankoaonline.com/'

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        """Need to set Referer or will be blocked"""

        init_url = 'https://bankoa.bankoaonline.com/'
        resp_login_form_page = Response()
        reason = ''
        # For linter
        s = MySession()
        action_link = ''
        username_field_name = ''
        password_field_name = ''
        req_params = {}  # type: Dict[str, str]
        # several cofirmations for wrong credetials,
        # bcs Bankoa often returns false-positive markers 1 time
        n_credentals_error_remain = 2

        for att in range(LOGIN_ATTEMPTS):
            s = self.basic_new_session()
            reason = ''  # reset on each attempt

            # Expect to be redirected to
            # https://bankoa.bankoaonline.com/isum/Main?ISUM_SCR=login
            # &loginType=accesoSeguroUsuario&ISUM_Portal=107&acceso_idioma=es_ES&forceNewSession=true
            resp_login_form_page = s.get(
                init_url,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            time.sleep(1 + att * random.random())

            if 'forceNewSession' not in resp_login_form_page.url:
                reason = 'Unexpected login URL: {}'.format(resp_login_form_page.url)
            else:
                action_link, req_params = extract.build_req_params_from_form_html_patched(
                    resp_login_form_page.text,
                    form_id='form1',
                    is_ordered=True
                )

                username_field_name = extract.re_first_or_blank(
                    r"""(?si)<label for=["']([^'"]+)['"]>\s*Usuario</label>""",
                    resp_login_form_page.text
                )

                password_field_name = extract.re_first_or_blank(
                    r"""<(?si)label for=["']([^'"]+)["']>\s*Contraseña</label>""",
                    resp_login_form_page.text
                )

                if not (action_link and
                        username_field_name and
                        'aux' in username_field_name and
                        password_field_name and
                        'aux' in password_field_name):
                    reason = "WRONG LAYOUT. Can't parse login_form_url/..._field_name"
            if reason and att < LOGIN_ATTEMPTS:
                self.logger.warning('{}. Retry #{}'.format(reason, att))
                time.sleep(5 + random.random())
                continue

            # Next login steps

            open_pos_global_context_param = (
                'BDP_RVIA05_POS_GLOBAL|'
                'BDP_RVIA05_ORDEN_INICIO_POSICION_GLOBAL_PAR;'
                'PARTICULAR|BDP_RVIA05_ORDEN_INICIO_POSICION_GLOBAL_EMP;'
                'EMPRESA'
            )

            # Expect like
            # OrderedDict([('field_tmp', '-'),
            #              ('field_tmp2', '-'),
            #              ('lttkMozkFCXFkne_aux', ''),
            #              ('lttkMozkFCXFkne', '340...18H'),
            #              ('jHhDnTkHQxFBTYP_aux', ''),
            #              ('jHhDnTkHQxFBTYP', 'iako...711'),
            #              ('ibXqHZsIJemfWDU', '-0138'),
            #              ('context',
            #               'BDP_RVIA05_POS_GLOBAL|BDP_RVIA05_ORDEN_INICIO_POSICION_GLOBAL_PAR;PARTICULAR
            #               |BDP_RVIA05_ORDEN_INICIO_POSICION_GLOBAL_EMP;EMPRESA'),
            #              ('TOGA', '34')])

            # req_params[username_field_name.rstrip('_aux')] = self.username + entidad_param
            req_params[self._rstrip_aux(username_field_name)] = self.username
            req_params[self._rstrip_aux(password_field_name)] = self.userpass
            req_params[username_field_name] = self.username
            req_params[password_field_name] = '*' * len(self.userpass)
            req_params['context'] = open_pos_global_context_param
            req_params['TOGA'] = self.username[:2]

            # Delete from req, linter-friendly approach
            if 'botoncico' in req_params:
                del req_params['botoncico']

            time.sleep(5 + random.random())

            resp_logged_in = s.post(
                urljoin(init_url, action_link.strip()),
                data=req_params,
                headers=self.basic_req_headers_updated({
                    'Referer': resp_login_form_page.url,
                    'Upgrade-Insecure-Requests': '1'
                }),
                proxies=self.req_proxies
            )

            is_logged_in = ('Salir' in resp_logged_in.text or  # several companies
                            'USUARIO_RACF' in resp_logged_in.text)  # one company

            # Always False was a temp solution
            # to avoid false positive for 11902 bankoa avia,
            # when marker was 'forma incorrecta alguno de los datos para el usuario indicado'
            # is_credentials_error = False
            is_credentials_error = any(m in resp_logged_in.text for m in WRONG_CREDENTIALS_MARKERS)

            # Several attempts (2) to confirm wrong credentials
            if is_credentials_error:
                n_credentals_error_remain -= 1

            if is_credentials_error and n_credentals_error_remain > 0 and att < LOGIN_ATTEMPTS:
                self.logger.warning("Possible false-positive 'wrong credentials'. "
                                    "Wait 1 minute (!) and retry")
                time.sleep(60 + 5 * random.random())
                continue

            if is_credentials_error and ('forceNewSession' not in resp_login_form_page.url):
                self.logger.error("Failed authorization (with credentials error).\n"
                                  "Most probably it is a false positive detection "
                                  "due to unexpected initial redirection to {}.\n"
                                  "COULDN'T LOG IN CORRECTLY FROM THIS URL.\n"
                                  "Check and adjust login method.".format(resp_login_form_page.url))

            reason = (DOUBLE_AUTH_REQUIRED_TYPE_COOKIE
                      if 'Si no has recibido el código SMS llamanos al servicio Att' in resp_logged_in.text
                      else '')

            # SAME STEPS AS FOR 'SELECT COMPANY'
            # Success / wrong credentials / 2FA
            return s, resp_logged_in, is_logged_in, is_credentials_error, reason

        # Won't log in, not a credentials error
        return s, resp_login_form_page, False, False, reason

    def select_company(
            self,
            s: MySession,
            resp1_company: Response,
            req_headers: Dict[str, str]) -> Tuple[MySession, Response, str, Dict[str, str]]:

        # Step 2
        req2_link, req2_params = parse_helpers.build_req_params_from_form_html(
            resp1_company.text,
            'FORM_RVIA_0'
        )

        req2_url = urljoin(resp1_company.url, req2_link)
        req_headers['Referer'] = resp1_company.url

        resp2_company = s.post(
            req2_url,
            params=req2_params,
            headers=req_headers,
            proxies=self.req_proxies
        )

        is_error_msg_in_resp(
            ERR_RESP_MARKERS,
            resp2_company,
            self.logger,
            'select_company: resp2_company'
        )

        # Step 3 -- get company initial page
        req3_link = extract.re_first_or_blank(
            """window.location.href = ['"](.*?)['"]""",
            resp2_company.text
        )

        req3_url = urljoin(resp2_company.url, req3_link)
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

        # Step 4 -- get accounts overview

        req4_link = extract.re_first_or_blank(
            '<a href="(.*?)" id="url1"',
            resp3_company.text
        )

        req4_url = urljoin(resp3_company.url, req4_link)
        req_headers['Referer'] = resp3_company.url

        req4_params = {
            'ISUM_OLD_METHOD': 'POST',
            'ISUM_ISFORM': "true"
        }

        resp4_company = s.post(
            req4_url,
            req4_params,
            headers=req_headers,
            proxies=self.req_proxies
        )

        is_error_msg_in_resp(
            ERR_RESP_MARKERS,
            resp4_company,
            self.logger,
            'select_company: resp4_company'
        )

        # specific for bankoa scraper
        action_url_cuentas_tab = extract.re_first_or_blank(
            'href="(.*?)">Cuentas</a>',
            resp4_company.text
        )
        req_url_cuentas_tab = urljoin(resp4_company.url, action_url_cuentas_tab)
        # for quit the pop up is necessary go to another option of menu and return to "iniciar"
        # that is my option for fix the scraper and no change so much the scraper.After to 15/11/2021 more or less
        # delete this fix when BANKOA remove the pop up.
        action_transfer_tab = extract.re_first_or_blank(
            'href="(.*?)">Transferencias</a>',
            resp4_company.text
        )
        req_url_transfer = urljoin(resp4_company.url, action_transfer_tab)
        pass_transfer = s.get(
            req_url_transfer,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        # Comeback to "inicio"
        action_inicio_tab = extract.re_first_or_blank(
            'href="(.*?)">Inicio</a>',
            pass_transfer.text
        )
        req_url_inicio = urljoin(resp4_company.url, action_inicio_tab)
        resp_inicio = s.get(
            req_url_inicio,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        req_inicio_link = extract.re_first_or_blank(
            'href="(.*?)" id="url1" ></a>',
            resp_inicio.text
        )
        req_url2 = urljoin(resp4_company.url, req_inicio_link)
        resp4_company = s.post(
            req_url2,
            req4_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        # delete to here
        return s, resp4_company, req_url_cuentas_tab, req_headers
        # / specific for bankoa scraper

    def process_company(self,
                        s: MySession,
                        resp_logged_in: Response,
                        company_parsed: dict) -> bool:
        """
        :param company_parsed: {req_params_list, title}

        Get accounts and upload them
        then for each account run 'process account' to get movements
        """

        company_title = company_parsed['title']
        self.logger.info('Process company: {}'.format(company_title))

        # create new session if several companies per user account for concurrent scraping
        if self.companies_len > 1:  # project_settings.IS_CONCURRENT_SCRAPING and
            self.increase_company_future_num()
            is_logged_in = False
            reason = ''
            for i in range(1, 3):
                time.sleep(self.company_future_num * (1 + random.random()))  # to log in with some delays
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
                return False

            # select necessary company
            ok, resp_select_company_step1, req_headers = self.step1_select_company_if_several_companies(
                s,
                resp_logged_in,
                company_parsed
            )
            if not ok:
                return False  # already reported

            s, resp_company, req_url_cuentas_tab, req_headers = self.select_company(
                s, resp_select_company_step1, req_headers
            )
        # One company
        else:
            req_headers = REQ_HEADERS.copy()
            s, resp_company, req_url_cuentas_tab, req_headers = self.select_company(
                s, resp_logged_in, req_headers
            )

        # Extract company title from Inicio page
        # it is necessary only if one company per user account
        # or company title was extracted from list of companies
        if company_parsed['title'] == DEFAULT_COMPANY_TITLE:
            company_parsed['title'] = parse_helpers.get_company_title_from_inicio_page(
                self.db_customer_name,
                resp_company.text
            )

        accounts_parsed = parse_helpers.parse_accounts_overview(resp_company.text)
        # logg if the scraper not found accounts in the bank
        if not accounts_parsed:
            self.logger.error("The bank no has accounts or not found")
            return True

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(company_parsed['title'], acc_parsed)
            for acc_parsed in accounts_parsed
        ]

        self.logger.info('Company {} has accounts {}'.format(company_title, accounts_parsed))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        # Switch to Cuentas tab and process each account from this place
        # specific for bankoa scraper
        req_headers['Referer'] = resp_company.url
        resp_cuentas_tab = s.get(
            req_url_cuentas_tab,
            headers=req_headers,
            proxies=self.req_proxies
        )
        action_url_movimientos_filter = extract.re_first_or_blank(
            r'href="([^"]*)"\s*>Movimientos</a>',
            resp_cuentas_tab.text
        )
        req_url_mov_filter = urljoin(resp_cuentas_tab.url, action_url_movimientos_filter)
        req_headers['Referer'] = resp_cuentas_tab.url
        resp_accounts_mov_filter = s.get(
            req_url_mov_filter,
            headers=req_headers,
            proxies=self.req_proxies
        )
        # / specific for bankoa scraper

        is_error_msg_in_resp(
            ERR_RESP_MARKERS,
            resp_accounts_mov_filter,
            self.logger,
            'process_company: resp_accounts_mov_filter'
        )

        # Should use individual session for each account to get movements
        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=16) as executor:

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

        self.logout(s, resp_company, company_title)

        return True
