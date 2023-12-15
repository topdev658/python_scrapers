import re
import random
import time
from typing import Tuple
from urllib.parse import urljoin

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, DOUBLE_AUTH_REQUIRED_TYPE_COMMON
from scrapers.ruralvia_scraper.ruralvia_scraper import RuralviaScraper

__version__ = '2.10.0'
__changelog__ = """
2.10.0
use strict _rstrip_aux
2.9.0
1 login attempt, wrong credentials -> 'probably, false-positive wrong credentials'
upd login req params
more log msgs
2.8.0
login: more delays
reduce N_COMPANY_PROCESSING_WORKERS
2.7.1
aligned double auth msg
2.7.0
2FA required detector
2.6.0
use basic_new_session
2.5.1
upd type hints
2.5.0
LOGIN_ATTEMPTS
2.4.0
CREDENTIALS_ERROR_MARKERS
login: WRONG LAYOUT checks to prevent false-positive credentials error detection
2.3.0
login: changed signature
2.2.0
self.domain to process multi-contract accesses
2.1.0
use as userpass: username_second if provided (arquia red) or userpass (arquia nuevo support)
2.0.0
inherits ruralvia, custom login method
1.1.1
comments upd
1.1.0
basic_movements_scraped_from_movements_parsed: new format of the result
1.0.0
moved from ArquiaBancaScraper
"""

CREDENTIALS_ERROR_MARKERS = [
    'Has introducido de forma incorrecta alguno de los datos para el usuario indicado',
    'Has introducido de forma incorrecta alguno de los datos de acceso'
]

LOGIN_ATTEMPTS = 1


class ArquiaBancaRedScraper(RuralviaScraper):
    """
    Basic functions from RuralviaScraper
    """
    N_COMPANY_PROCESSING_WORKERS = 1  # gentle processing

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='ArquiaBancaRedScraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)
        self.domain = 'https://www.arquiaonline.com'

    # Similar to Bankoa's login method
    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        """
        Need to set Referer or will be blocked
        """

        s = self.basic_new_session()
        resp_logged_in = Response()
        is_logged_in = False
        is_credentials_error = False
        reason = ''

        # 2 attempts to reduce false-positive credentials errors
        for attempt in range(LOGIN_ATTEMPTS):
            s = self.basic_new_session()  # reset cookies

            resp_init = s.get(
                'https://www.arquia.com/es-es/',
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            time.sleep(1 + random.random())

            req_login_form_url = extract.re_first_or_blank(
                """value="Entrar"[^>]+'(https://www.arquiaonline.com[^']+)""",
                resp_init.text
            )

            if not req_login_form_url:
                reason = "WRONG LAYOUT. Can't parse req_login_form_url"
                return s, resp_init, False, False, reason

            resp_login_form_page = s.get(
                req_login_form_url,
                headers=self.basic_req_headers_updated({'Referer': resp_init.url}),
                proxies=self.req_proxies
            )

            req_link, req_params = extract.build_req_params_from_form_html_patched(
                resp_login_form_page.text,
                form_id='form1',
                is_ordered=True
            )

            username_field_name = extract.re_first_or_blank(
                r"""(?si)<label for=["']([^'"]+)['"]>\s*NIF / NIE</label>""",
                resp_login_form_page.text
            )

            password_field_name = extract.re_first_or_blank(
                r"""<(?si)label for=["']([^'"]+)["']>\s*Contraseña</label>""",
                resp_login_form_page.text
            )

            # open_pos_global_context_param = (
            #     'BDP_RVIA05_POS_GLOBAL|BDP_RVIA05_ORDEN_INICIO_POSICION_GLOBAL_PAR;'
            #     'PARTICULAR|BDP_RVIA05_ORDEN_INICIO_POSICION_GLOBAL_EMP;EMPRESA'
            # )

            if not (req_link and
                    username_field_name and
                    'aux' in username_field_name and
                    password_field_name and
                    'aux' in password_field_name):
                reason = "WRONG LAYOUT. Can't parse action_url/username_field_name/password_field_name"
                return s, resp_login_form_page, False, False, reason

            # expect like
            # field_tmp=-
            # vIVfKcZRdXIRkri_aux=username
            # vIVfKcZRdXIRkri=username
            # dmgPNkyPJoJVnEz_aux=********
            # dmgPNkyPJoJVnEz=passwd_8_chars
            # KHnpFLpsmwkWYgT=-3183
            # pVzRJjlXoVDRNGI=es_ES
            # TOGA=50

            req_params[username_field_name] = self.username
            req_params[self._rstrip_aux(username_field_name)] = self.username
            # ! earlier username_second if provided (Arquia Red) or userpass (Arquia nuevo)
            # brought wrong credentials bcs Arquia nuevo also has unused username_second
            req_params[password_field_name] = '*' * len(self.userpass)
            req_params[self._rstrip_aux(password_field_name)] = self.userpass
            # req_params['context'] = open_pos_global_context_param
            req_params['TOGA'] = self.username[:2]

            if 'botoncico' in req_params:
                del req_params['botoncico']

            assert req_params[self._rstrip_aux(password_field_name)]

            time.sleep(1 + random.random())

            resp_codes_bad_for_proxies_bak = s.resp_codes_bad_for_proxies.copy()
            s.resp_codes_bad_for_proxies = [403, None]  # no 50x
            resp_logged_in = s.post(
                urljoin(resp_login_form_page.url, req_link.strip()),
                data=req_params,
                headers=self.basic_req_headers_updated({'Referer': resp_login_form_page.url}),
                proxies=self.req_proxies
            )
            s.resp_codes_bad_for_proxies = resp_codes_bad_for_proxies_bak

            is_logged_in = ('Salir' in resp_logged_in.text or  # several companies
                            'USUARIO_RACF' in resp_logged_in.text)  # one company

            is_credentials_error = any(m in resp_logged_in.text for m in CREDENTIALS_ERROR_MARKERS)
            if is_credentials_error:
                reason = ('Probably, false-positive wrong credentials. Pls, check it manually.'
                          " The scraper keeps the access as 'active'")
                # Reset detected wrong credentials to keep the access as 'active'
                is_credentials_error = False
                self.basic_log_wrong_layout(
                    resp_login_form_page,
                    'Login form page led to false-positive wrong credentials'
                )

            if 'Introduce el código' in resp_logged_in.text:
                reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON
                return s, resp_logged_in, is_logged_in, is_credentials_error, reason

            if is_logged_in:
                return s, resp_logged_in, is_logged_in, is_credentials_error, reason

            # Next attempt if got credentials error (probably, false-positive)
            # Don't wait after the last attempt
            if is_credentials_error and attempt < LOGIN_ATTEMPTS - 1:
                self.logger.warning("Possible false-positive 'wrong credentials'. "
                                    "Wait 1 minute (!) and retry")
                time.sleep(60 + 5 * random.random())

        return s, resp_logged_in, is_logged_in, is_credentials_error, reason
