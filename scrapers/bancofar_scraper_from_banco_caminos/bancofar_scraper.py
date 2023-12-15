from typing import Dict, Tuple
from urllib.parse import urljoin

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    ScraperParamsCommon
)
from scrapers.banco_caminos_scraper.banco_caminos_scraper import BancoCaminosScraper
from . import parse_helpers
from .environs import Env, ENVS

__version__ = '1.3.0'

__changelog__ = """
1.3.0
use envs()
1.2.0
login_to_sso: call updated _select_contract
1.1.0
login_to_sso
1.0.0
from BancoCaminosScraper
"""


class BancofarScraper(BancoCaminosScraper):
    scraper_name = 'BancofarScraper'
    # For login()
    _login_company_id = 'BF'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    def envs(self) -> Dict[int, Env]:
        return ENVS

    def login_to_sso(self, contract_ix: int = 0) -> Tuple[MySession, Response, bool, bool, str]:
        """These actions allows to open Ruralvia-based user portal.
        Meanwhile BancoCaminos-based portal API is working too,
        so, let's just use BancoCaminos-based when it's enough and use this for specific cases (N43)
        """
        s, resp_logged_in, is_logged, is_credentials_error, reason = super().login()
        if not is_logged:
            return s, resp_logged_in, is_logged, is_credentials_error, reason

        contracts = self._get_contracts(s)
        contract = contracts[contract_ix]

        _resp_contract_selected_json = self._select_contract(s, contract.id)

        # Get user info
        resp_sso = s.get(
            'https://api.grupocaminos.es/products/sso/rsi',
            headers=self.basic_req_headers_updated({
                'Content-Type': 'application/json',
                'uuid': self._uuid
            }),
            proxies=self.req_proxies
        )
        resp_sso_json = self._decrypt_json(resp_sso.text)

        req_login_ruralvia_params = {
            'loginType': 'accesoSSO',
            'ISUM_Portal': '115',
            'forceNewSession': 'true',
            'acceso_idioma': 'es_ES'
        }
        req_login_ruralvia_data = {
            'usuarioBE': resp_sso_json['coreEBUserId'],  # '4C016079',
            'tokenSSO': resp_sso_json['tokenSSO']  # '32df5121-9425-4a39-8e03-0179a9cb80d8'
        }

        # dev/resp_login_form_ruralvia.html
        resp_login_form_ruralvia = s.post(
            "https://banca.bancofaronline.es/isum/Main?ISUM_SCR=login",
            params=req_login_ruralvia_params,
            data=req_login_ruralvia_data,
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=False
        )

        req_login_ruralvia_step2_link, req_login_ruralvia_step2_params = \
            extract.build_req_params_from_form_html_patched(
                resp_login_form_ruralvia.text,
                'form1'
            )

        # Some params weren't extracted, doing it here,
        # should get vals for 'Usuario' and 'Token'
        req_login_ruralvia_step2_params_extra = parse_helpers.get_form_inputs(
            resp_login_form_ruralvia.text,
            'form1'
        )

        req_login_ruralvia_step2_params.update(req_login_ruralvia_step2_params_extra)

        req_ruralvia_step2_url = urljoin(resp_login_form_ruralvia.url, req_login_ruralvia_step2_link.strip())

        resp_ruralvia_step2 = s.post(
            req_ruralvia_step2_url,
            data=req_login_ruralvia_step2_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=False
        )

        req_ruralvia_step3_link, req_ruralvia_step3_params = extract.build_req_params_from_form_html_patched(
            resp_ruralvia_step2.text,
            'FORM_RVIA_0'
        )

        req_ruralvia_step3_url = urljoin(resp_ruralvia_step2.url, req_ruralvia_step3_link.strip())

        # <script language="javascript">
        #     window.location.href = \'/isum/\';
        # </script>
        resp_login_step3 = s.post(
            req_ruralvia_step3_url,
            data=req_ruralvia_step3_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=False
        )

        resp_ruralvia_step4 = s.get(
            urljoin(resp_login_step3.url, '/isum/'),
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=False
        )
        is_logged = 'Contrato' in resp_ruralvia_step4.text

        # To process Ruralvia-based portal
        return s, resp_ruralvia_step4, is_logged, is_credentials_error, reason
