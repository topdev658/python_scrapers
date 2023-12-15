from typing import Dict, Tuple

from custom_libs import extract
from custom_libs.myrequests import Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, AccountParsed
from scrapers.ruralvia_scraper.ruralvia_scraper import RuralviaScraper

__version__ = '2.4.0'

__changelog__ = """
2.4.0
_create_mov_req_params: align params with super()
2.3.0
now works self.ssl_cert = True 
2.2.0
ssl_cert
ssl_cert_init
2.1.0
custom login_init_url, domain (were default)
custom _create_mov_req_params: added validationToken param to Ruralvia's
2.0.0
new project structure
1.1.0
comment custom select_company
1.0.1
reformatted
"""


class PichinchaScraper(RuralviaScraper):
    """
    all functions from RuralviaScraper with specific scraper's name
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='PichinchaScraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)
        self.login_init_url = 'https://www.bancopichincha.es/'
        self.domain = 'https://clientes.bancopichincha.es/'
        self.ssl_cert_init = False  # 'bancopichincha-es-chain.pem' brings err [X509] PEM lib (_ssl.c:3053)
        self.ssl_cert = True  # 'clientes-bancopichincha-es-chain.pem' brings err
        self.logger.info('Scraper started')

    def _create_mov_req_params(
            self,
            resp_prev: Response,
            account_parsed: AccountParsed,
            date_from_str: str,
            date_to_str: str,
            page_ix: int = 0) -> Tuple[bool, str, Dict[str, str]]:

        can_paginate, req_movs_url, req_movs_params = super()._create_mov_req_params(
            resp_prev,
            account_parsed,
            date_from_str,
            date_to_str,
            page_ix=page_ix
        )

        validation_token_param = extract.re_first_or_blank(
            '<div data-token="([^"]+)" id="tokenValid">',
            resp_prev.text
        )
        req_movs_params['validationToken'] = validation_token_param
        return can_paginate, req_movs_url, req_movs_params
