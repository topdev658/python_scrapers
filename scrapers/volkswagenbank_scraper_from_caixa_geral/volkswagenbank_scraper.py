import urllib.parse
from typing import List, Tuple

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import AccountParsed, MovementParsed, ScraperParamsCommon
from scrapers.caixa_geral.caixa_geral_scraper import CaixaGeralScraper
from scrapers.volkswagenbank_scraper_from_caixa_geral import parse_helpers as vw_parse_helpers

__version__ = '1.5.1'

__changelog__ = """
1.5.1
upd type hints
fmt
1.5.0
_get_selected_account_id
parse_helpers: more strict get_selected_account_id
1.4.0
_check_selected_account
parse_helpers: get_selected_account_id
1.3.0
parse_helpers: get_movements_parsed: check selected account
1.2.0
impl _after_login_hook to click 'continue' on a notification
parse_helpers: upd log msgs
1.1.0
parse_helpers:
  get_movements_parsed: 
    temp_balance_calc to fix possible errors in received temp_balance
    TEMP_BALANCE_MAX_ERRORS to limit number of allowed temp_balance errors 
fmt
type hints
1.0.0
Inherits many from CaixaGeralScraper
"""


class VolkswagenBankScraper(CaixaGeralScraper):

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='VolkswagenScraper',
                 website='https://www.volkswagenbank.es',
                 camino_param='1480',
                 caja_param='1480') -> None:
        super().__init__(scraper_params_common,
                         proxies,
                         scraper_name,
                         website,
                         camino_param,
                         caja_param)

    def _get_accounts_parsed(self, resp_accs: Response) -> List[AccountParsed]:
        return vw_parse_helpers.get_accounts_parsed(resp_accs.text, self.logger)

    def _get_movements_parsed(self, resp_mov: Response,
                              fin_ent_account_id: str) -> List[MovementParsed]:
        return vw_parse_helpers.get_movements_parsed(resp_mov.text, fin_ent_account_id, self.logger)

    def _get_selected_account_id(self, resp_movs_text: str) -> str:
        return vw_parse_helpers.get_selected_account_id(resp_movs_text)

    def _authreq_post_params(self, pin: str, sello_param: str) -> dict:
        # CAMINO=1480&CAJA=1480&OPERACION=0002&SELLO=2018.03.21.16.20.09&IDIOMA=01&PIN
        # =8a143cc5afb65a6a764ac706242ed80e&PINV3=si&INDSELLO=1&IDEN=CL&BROKER=SI&PAN=22721149&NAVEGADOR=&VERSION=&MENU=
        return {
            'CAMINO': self.camino_param,
            'CAJA': self.caja_param,
            'OPERACION': '0002',
            'SELLO': sello_param,
            'IDIOMA': '01',
            'PIN': pin,
            'PINV3': 'si',
            'INDSELLO': '1',
            'IDEN': 'CL',
            'BROKER': 'SI',
            'PAN': str(self.username).upper(),
            'NAVEGADOR': '',
            'VERSION': '',
            'MENU': ''
        }

    def _movreq_post_params(self, basic_params: dict, date_from_str: str) -> dict:
        # OPERAC=5838?
        return {
            'CLIENTE': basic_params['CLIENTE'],
            'IDIOMA': basic_params['IDIOMA'],
            'CAJA': basic_params['CAJA'],
            'OPERAC': basic_params['OPERAC'],
            'CTASEL': '',
            'CTAFOR': '',
            'CAMINO': basic_params['CAMINO'],
            'GCUENTA': basic_params['GCUENTA'],
            'FECHADESDE': date_from_str,
            'FECHAHASTA': self.date_to_str,
            'IMPORTEDESDE': '',
            'IMPORTEHASTA': '',
            'BSQAVANZADA': 'yes'
        }

    def _after_login_hook(
            self,
            s: MySession,
            resp_logged_in: Response) -> Tuple[MySession, Response, bool, str]:
        """:returns (session, resp, is_logged, reason)"""

        if 'campaignAjax' not in resp_logged_in.text:
            # no action required
            return s, resp_logged_in, True, ''

        self.logger.info('_after_login_hook: click "continue" on a notification page')

        campaign_link = extract.re_first_or_blank(r'var\s+campaignAjax="(.*?)"', resp_logged_in.text)
        resp_notice = s.get(
            urllib.parse.urljoin(resp_logged_in.url, campaign_link),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # click 'continue'
        if 'form id="frmContinuar"' not in resp_notice.text:
            return s, resp_notice, False, "Expected, but couldn't find 'frmContinuar' during _after_login_hook"

        req_continue_link, req_continue_params = extract.build_req_params_from_form_html_patched(
            resp_notice.text,
            'frmContinuar'
        )
        resp_continue = s.post(
            urllib.parse.urljoin(resp_notice.url, req_continue_link),
            data=req_continue_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        return s, resp_continue, True, ''
