from typing import Tuple, Dict

from custom_libs.myrequests import Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, AccountParsed
from scrapers.ruralvia_scraper.ruralvia_scraper import RuralviaScraper

__version__ = '1.3.0'

__changelog__ = """
1.3.0
_create_mov_req_params: align params with super()
1.2.0
custom _create_mov_req_params for 'Siguientes'-based pagination and get ASC movs
redundant_accounts
1.1.1
fmt
1.1.0
toga from username (similar to bankoa)
fmt
1.0.0
init
"""

PAGINATION_MARKER = 'Siguientes'  # special marker that explicitly requires pagination


class EurocajaRuralScraper(RuralviaScraper):
    """
    All functions from RuralviaScraper with specific scraper's name
    and login customization (init url, req params)
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='EurocajaRuralScraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)
        self.login_init_url = 'https://eurocajarural.es/'
        self.toga_param = self.username[:2]
        self.redundant_accounts = [
            ('ALIMENTOS EL BERCIAL, SC', 'ES4830810239453199389614'),  # -a 20739
            ('VICENTE DE CASTRO PECCI', 'ES6830810239423134815822'),  # -a 20754
            ('VICENTE DE CASTRO PECCI', 'ES1930810180622588826723'),  # -a 20754
            ('MARIA TERESA SANCHEZ GUDIEL', 'ES2730810008042631644412')  # -a 20776
        ]
        self.logger.info('Scraper started')

    def _create_mov_req_params(
            self,
            resp_prev: Response,
            account_parsed: AccountParsed,
            date_from_str: str,
            date_to_str: str,
            page_ix=0) -> Tuple[bool, str, Dict[str, str]]:
        """Implements pagination for -a 20776, acc ...4412 and similar cases with
        'Siguientes'-based pagination with descending movements
        instead of needed 'Pagina'-based with ascending movements
        """
        _, req_url, req_params = super()._create_mov_req_params(
            resp_prev,
            account_parsed,
            date_from_str,
            date_to_str,
            page_ix=page_ix
        )
        _req_params_orig = req_params.copy()
        can_paginate = True
        fin_ent_account_id = account_parsed['account_no']

        # Some accounts allows only this:
        # Use appropriate way for 'Siguientes'-based pagination

        if PAGINATION_MARKER in resp_prev.text:
            self.logger.info('{}: {}-based pagination'.format(fin_ent_account_id, PAGINATION_MARKER))

            if req_params['saldoArrastreLast'] == '0':  # after all movs the first one is suggested.
                can_paginate = False

            req_params['paginar'] = 's'
            req_params['NumSecuencia'] = req_params['numeroSecuencialApunteLast']
            req_params['numeroSecuencialApunteFirst'] = req_params['numeroSecuencialApunteLast']
            req_params['saldoArrastre'] = req_params['saldoArrastreLast']
            req_params['saldoArrastreFirst'] = req_params['saldoArrastreLast']
            req_params['codigoMoneda'] = req_params['codigoMonedaLast']
            req_params['codigoMonedaFirst'] = req_params['codigoMonedaLast']

        return can_paginate, req_url, req_params
