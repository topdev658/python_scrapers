import time
from collections import OrderedDict
from typing import Tuple, Dict, List

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import MOVEMENTS_ORDERING_TYPE_ASC, ScraperParamsCommon, MainResult, \
    DOUBLE_AUTH_REQUIRED_TYPE_COMMON
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.santander_totta_scraper import parse_helpers

__version__ = '1.10.0'
__changelog__ = """
1.10.0 2023.10.03
login: upd DOUBLE_AUTH_MARKERS
1.9.0 2023.04.13
process_access: 
    get accounts params from response to process accounts from different contracts
parse_helpers.get_accounts_params: new parse_helpers method to get right account params (clientNumber and accountNumber)
1.8.0
login: DOUBLE_AUTH_MARKERS after request to secondFactorAuthSMS
1.7.0
login: get request to secondFactorAuthSMS
1.6.0
call basic_upload_movements_scraped with date_from_str
1.5.0
login: get OGC_TOKEN, reason
1.4.0
_get_csrf_token_header
1.3.0
manual ssl cert support
1.2.0
use basic_new_session
upd type hints
fmt
1.1.0
support Portugal lang in login() and in parse_helpers.get_account_parsed() 
1.0.0
init
"""

CREDENTIALS_ERROR_MARKER = 'O nome de utilizador ou os caracteres do código de acesso estão incorretos'

LOGGED_IN_MARKERS = [
    'Saldos y Movimientos',  # ES
    'Saldos e Movimentos'  # PT
]

DOUBLE_AUTH_MARKERS = [
    'Autenticación refuerzo', # ES
    'Ingrese el código que recibió en su teléfono móvil', # ES
    'Le hemos enviado un SMS al número de teléfono móvil', # ES
    'Enviamos-lhe um SMS para o número de telemóvel' # PT
]


class SantanderTottaScraper(BasicScraper):
    scraper_name = 'SantanderTottaScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.ssl_cert = 'www-empresas-santander-pt-chain.pem'

    def _get_csrf_token_header(self, s: MySession) -> Tuple[bool, Dict[str, str]]:
        resp_token = s.post(
            'https://www.empresas.santander.pt/canalempresas/actions/finance/nbe_csrf_guard',
            data={},
            headers=self.basic_req_headers_updated({
                'FETCH-CSRF-TOKEN': '1',
            }),
            proxies=self.req_proxies
        )
        if 'OGC_TOKEN' not in resp_token.text:
            self.basic_log_wrong_layout(resp_token, "Can't get resp_token")
            return False, {}
        # Parses 'OGC_TOKEN:TA8Y-UCYQ-XK1J-21KK-86QT-6QDB-F18C-ASXF'
        token = resp_token.text.split(':')[1].strip()
        return True, {'OGC_TOKEN': token}

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()

        resp_init = s.get(
            'https://www.empresas.santander.pt/canalempresas/finance/login.jsp',
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=self.ssl_cert
        )

        resp_ogc_token = s.post(
            'https://www.empresas.santander.pt/canalempresas/actions/finance/nbe_csrf_guard',
            data='',
            headers=self.basic_req_headers_updated({
                'FETCH-CSRF-TOKEN': '1',
                'Referer': resp_init.url
            }),
            proxies=self.req_proxies,
            verify=self.ssl_cert
        )
        # OGC_TOKEN:PMIY-011B-A7JK-W4K3-KZ0E-4GS0-2C4T-DDTH
        if 'OGC_TOKEN' not in resp_ogc_token.text:
            return s, resp_ogc_token, False, False, "Can't get OGC_TOKEN"
        ogc_token = resp_ogc_token.text.split(':')[1]

        req_login_params = OrderedDict([
            ('username', self.username),
            ('password', self.userpass),
            ('g-recaptcha-response', ''),
            ('login-action', ''),
            #('sessiontoken', ''),  # c15bc79b5754553d0f1a87edb018f501
            #('P2hoCyPjpg', ''),    # 'language:es-ES,colorDepth:24,...,audio:35.73833402246237'
            ('OGC_TOKEN', ogc_token)
        ])

        req_login_url = ('https://www.empresas.santander.pt/canalempresas/actions/'
                         'finance/login/login_one_step/loginmulti/doLogin')
        resp_logged_in_step1 = s.post(
            req_login_url,
            data=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=self.ssl_cert,
        )

        is_credentials_error = CREDENTIALS_ERROR_MARKER in resp_logged_in_step1.text
        if is_credentials_error:
            return s, resp_logged_in_step1, False, is_credentials_error, ''

        req_login_url_auth = ('https://www.empresas.santander.pt/canalempresas/actions/'
                              'finance/login/login_one_step/loginmulti/secondFactorAuthSMS')
        resp_logged_in_step2 = s.get(
            req_login_url_auth,
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=self.ssl_cert,
        )
        if any(m in resp_logged_in_step2.text for m in DOUBLE_AUTH_MARKERS):
            is_logged = False
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON
            return s, resp_logged_in_step2, is_logged, is_credentials_error, reason

        req_home_url = ('https://www.empresas.santander.pt/canalempresas/actions/'
                        'finance/patrimonio/saldos_movimentos/saldo/controller/consultasaldo')

        # Handle case if additional user action is required
        # - skip it if possible and open home page explicitly
        if resp_logged_in_step1.url == req_home_url:
            resp_logged_in = resp_logged_in_step1
        else:
            resp_logged_in = s.get(
                req_home_url,
                headers=self.req_headers,
                proxies=self.req_proxies,
                verify=self.ssl_cert
            )

        is_logged = any(m in resp_logged_in.text for m in LOGGED_IN_MARKERS)

        return s, resp_logged_in, is_logged, is_credentials_error, ''

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        # Get accounts params from response to process accounts from different contracts
        accounts_params = parse_helpers.get_accounts_params(resp_logged_in.text)

        # Can extract account iban only after additional requests,
        # so, we'll extract it from movs pages
        for account_params in accounts_params:
            self.process_account(s, account_params)

        return True

    def process_account(self, s: MySession, account_params: List[str]) -> bool:
        account_number = account_params['accountNumber']
        self.logger.info('Process account {}'.format(account_number))

        req_recent_movs_url = ('https://www.empresas.santander.pt/canalempresas/actions/'
                               'finance/patrimonio/saldos_movimentos/contado/controller/'
                               'contadomulti/initConsult')

        # Already got the right parameters in the get_accounts_params method call
        req_recent_movs_params = account_params

        resp_recent_movs = s.get(
            req_recent_movs_url,
            params=req_recent_movs_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=self.ssl_cert
        )

        organization_title = parse_helpers.get_organization_title(resp_recent_movs.text)

        account_parsed = parse_helpers.get_account_parsed(resp_recent_movs.text, account_number)
        if not account_parsed:
            self.logger.error("Can't get correct account_parsed. Skip.\nRESPONSE:\n{}".format(
                resp_recent_movs.text
            ))
            return False

        account_scraped = self.basic_account_scraped_from_account_parsed(
            organization_title,  # no available at the page, only user name != org title
            account_parsed,
            country_code='PRT',  # Portugal
        )

        self.logger.info('Got account: {}'.format(account_parsed))
        self.basic_upload_accounts_scraped([account_scraped])
        self.basic_log_time_spent('GET ACCOUNT')

        # filter movements

        # necessary to open it first
        resp_movs_form = s.get(
            'https://www.empresas.santander.pt/canalempresas/actions/finance/patrimonio/'
            'movimentos/movimentosmulti/changeAccount',
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=self.ssl_cert
        )

        # Filter by dates

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        # HTML: perform filter by dates
        req_filter_movs_url = ('https://www.empresas.santander.pt/canalempresas/actions/finance/'
                               'patrimonio/movimentos/movimentosform')

        req_filter_movs_params = OrderedDict([
            ('startDate', date_from_str.replace('/', '-')),  # '01-07-2018'
            ('endDate', self.date_to_str.replace('/', '-')),  # '17-02-2019'
            ('movTypeFilterValue', ''),
            ('clickedTimePeriod', 'Intervalo personalizado'),
            ('filterAmountDate', 'true'),
            ('oldFilterAmountDate', 'false'),
            ('filter-type', 'DDOP'),  # DDVAL
            ('movTypeFilter', ''),
            ('amountFilterValue', ''),
            ('type', '1'),
            ('beginVal', ''),
            ('endVal', ''),
            ('moreVal', ''),
            ('lessVal', ''),
            ('searchtxt', '')
        ])

        resp_movs_filtered_html = s.get(
            req_filter_movs_url,
            params=req_filter_movs_params,
            headers=self.basic_req_headers_updated({'Referer': resp_recent_movs.url}),
            proxies=self.req_proxies,
            verify=self.ssl_cert,
        )

        ok, token_header = self._get_csrf_token_header(s)
        if not ok:
            return False  # already reported

        # Ajax: get all movements
        req_movs_filtered_ajax_url = ('https://www.empresas.santander.pt/canalempresas/actions/'
                                      'finance/patrimonio/movimentos/movimentosmulti/getAllMovements')

        req_movs_filtered_ajax_params = OrderedDict([
            ('ajaxRequest', 'true'),
            ('_', str(int(time.time() * 1000))),
        ])
        req_headers_movs_filtered_ajax = self.basic_req_headers_updated({
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest, XMLHttpRequest',
            'Referer': resp_movs_filtered_html.url
        })
        req_headers_movs_filtered_ajax.update(token_header)
        resp_movs_filtered_ajax = s.get(
            req_movs_filtered_ajax_url,
            params=req_movs_filtered_ajax_params,
            headers=req_headers_movs_filtered_ajax,
            proxies=self.req_proxies,
            verify=self.ssl_cert,
        )

        try:
            movements_parsed_asc = parse_helpers.get_movements_parsed(resp_movs_filtered_ajax.json())
        except:
            self.basic_log_wrong_layout(resp_movs_filtered_ajax, "Can't get movements_parsed")
            return False

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
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

        self.process_access(s, resp_logged_in)
        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
