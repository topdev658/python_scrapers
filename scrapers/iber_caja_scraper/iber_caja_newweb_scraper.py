import datetime
import random
import time
from collections import OrderedDict
from typing import Tuple, Dict, List

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    ScraperParamsCommon, MainResult, AccountScraped, MovementParsed,
    DOUBLE_AUTH_REQUIRED_TYPE_COMMON
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers_newweb as parse_helpers
from .custom_types import Contract

__version__ = '2.0.0'
__changelog__ = """
2.0.0 2023.09.09
login: 
  changed partial url from 'bancadigitalweb' to 'banca-digital-spa'
  changed partial url from 'bancadigitalweb' to 'banca-digital-apigw
  deleted call to 'antiforgery' and don't XSRF-TOKEN cookie
  Moved getting tokenSesion (value for'x-ibercaja-st' header) after get user info because new tokenSesion is returned in login request 
process_contract, process_account:
  changed partial url from 'bancadigitalweb' to 'banca-digital-apigw 
1.9.0
process contract according to login_type
1.8.0
now let the correct log of DOUBLE_AUTH
1.7.0
call basic_upload_movements_scraped with date_from_str
1.6.0
login: check for access_token availability to avoid exc
1.5.1
upd log msgs
1.5.0
login: get contacts for early detection of unexpectedly expired sessions
1.4.1
upd log msgs
1.4.0
small delay between contracts
1.3.0
download_correspondence
1.2.0
process_access: expired session detector
1.1.0
parse_helpers_newweb: get_movements_parsed: use textoLinea1 and textoLinea2 (instead of concepto) 
  to build descr with more details 
1.0.0
init
"""

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:51.0) Gecko/20100101 Firefox/51.0'

MOVEMENTS_PER_PAGE = 50  # 50 by default
# From prev scraper
#   offset to scrape future movements (08/01 from 05/01)
DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS = 10

DOUBLE_AUTH_MARKERS = [
    'Porfavor introduce la clave SMS que hemos enviado a tu móvil para verificar que eres tú.',
    'Esta verificación se realizará periódicamente al acceder a tus cuentas, en base a criterios de seguridad.'
]

LOGIN_TYPE_NEGOCIO_MARKER = 'nego'


class IberCajaScraper(BasicScraper):
    scraper_name = 'IberCajaScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.login_type = None
        self.date_to = self.date_to + datetime.timedelta(days=DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS)
        self.date_to_str = self.date_to.strftime(project_settings.SCRAPER_DATE_FMT)  # '30/01/2017'
        self.req_headers = {'User-Agent': USER_AGENT}
        self.update_inactive_accounts = False

    def _now_millis(self):
        return int(time.time() * 1000)

    def set_req_headers(self, hdr_dict: Dict[str, str]) -> None:
        """Upadtes self.req_headers
        Invoke it in the end of login()
        """
        self.req_headers = self.basic_req_headers_updated(hdr_dict)

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        reason = ''
        s = self.basic_new_session()

        _resp_init = s.get(
            'https://banca.ibercaja.es/',
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=True,
        )

        req_auth_params = OrderedDict([
            ('client_id', 'bancadigital-spa'),
            ('redirect_uri',
             'https://banca.ibercaja.es/omnicanalidad/canales/banca-digital-spa/v1/signin-oidc'),
            ('response_type', 'code'),
            ('scope',
             'openid profile api.corebanking alfabetico identidad iberfabric.omnicanalidad.canales.'
             'bancadigitalweb.apigateway offline_access iberfabric.soporte.plataforma.identidad.api.self'
             ' telefono iberfabric.omnicanalidad.canales.conversaciones'),
            # var n = "N" + Math.random() + Date.now();
            ('nonce', 'N{}{}'.format(random.random(), self._now_millis())),
            # Date.now() + "" + Math.random() + Math.random()
            ('state', '{}{}{}'.format(self._now_millis(), random.random(), random.random())),
            # Any sha256-generated
            #  used by front-end
            # ('code_challenge', 'ch5UTMg4COX1EbcoOkVaPtKAsdBp_EjQxon6Wf3BzuU'),
            ('code_challenge', 'e2p9VwCpfXesVPt11JUdvURrMjP23SJ7rgBA5dSj81I'),
            ('code_challenge_method', 'S256'),
            ('login_timestamp', str(int(time.time())))
        ])

        # Expecting to be redirected to
        #  https://identidad.ibercaja.es/soporte/plataforma/identidad/api/v1/Account/Login?ReturnUrl=...'
        resp_login_form = s.get(
            'https://identidad.ibercaja.es/soporte/plataforma/identidad/api/v1/connect/authorize',
            params=req_auth_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # With fields:
        #   __RequestVerificationToken
        #   Data
        _, req_login_data = extract.build_req_params_from_form_html_patched(
            resp_login_form.text,
            form_id='login'
        )

        if not req_login_data['Data']:
            data_param = extract.re_first_or_blank(
                '<input type="hidden" value="([^"]+)"[^>]id="Data"',
                resp_login_form.text
            )
            req_login_data['Data'] = data_param

        req_login_data['Username'] = self.username
        req_login_data['Password'] = self.userpass
        req_login_data['button'] = 'login'

        # After redirection expecting
        #  https://banca.ibercaja.es/omnicanalidad/canales/bancadigitalweb/v1/signin-oidc
        #  ?code=212E16294CF9BE875561C4C77525335DBB94ED58581CF246736BB917FB5DBBF9
        #  &scope=openid%20profile%20api.corebanking%20alfabetico%20identidad%20iberfabric.omnicanalidad.canales.bancadigitalweb.apigateway%20offline_access%20iberfabric.soporte.plataforma.identidad.api.self%20telefono%20iberfabric.omnicanalidad.canales.conversaciones
        #  &state=16218816629770.398923947531277130.9851533487727189
        #  &session_state=0b686odx5rIte-qpnaWposjDfHJc3Lxjb80pFu3AbnY.8FFF7EF64B9D72BAB4419E88A0B3C6E6
        #  also see resp_logged_in.html
        resp_logged_in = s.post(
            resp_login_form.url,
            data=req_login_data,
            headers=self.basic_req_headers_updated({
                'Referer': resp_login_form.url
            })
        )

        is_logged = '/omnicanalidad/canales/banca-digital-spa/v1/' in resp_logged_in.text
        is_credentials_error = 'Datos incorrectos. Vuelva a intentarlo' in resp_logged_in.text
        # 2FA
        if any(m in resp_logged_in.text for m in DOUBLE_AUTH_MARKERS):
            is_logged = False
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        if not is_logged:
            return s, resp_logged_in, is_logged, is_credentials_error, reason

        code_param = extract.req_params_as_ord_dict(resp_logged_in.url)['code']

        req_token_params = OrderedDict([
            ('grant_type', 'authorization_code'),
            ('client_id', 'bancadigital-spa'),
            ('code_verifier',
             # for code_challenge from req_auth_params
             'C0.39176530194021786162188235797116218823579710.8893222823594056'),
            ('code', code_param),
            ('redirect_uri',
             'https://banca.ibercaja.es/omnicanalidad/canales/banca-digital-spa/v1/signin-oidc')
        ])

        resp_token = s.post(
            'https://identidad.ibercaja.es/soporte/plataforma/identidad/api/v1/connect/token',
            data=req_token_params,
            headers=self.basic_req_headers_updated({
                'Referer': 'https://banca.ibercaja.es/'
            }),
            proxies=self.req_proxies
        )

        resp_token_json = resp_token.json()
        # 06241B8184EC0D6B1D9653F47ED6EA2A6AC931E5023234AE45F5372544DA5386
        access_token = resp_token_json.get('access_token')
        if access_token is None:
            return s, resp_token, False, is_credentials_error, "Can't get access_token"

        access_token_type = resp_token_json['token_type']  # Bearer
        self.set_req_headers({'Authorization': '{} {}'.format(access_token_type, access_token)})

        # Get userinfo to process the contracts according to the login_type
        resp_userinfo = s.get(
            'https://identidad.ibercaja.es/soporte/plataforma/identidad/api/v1/connect/userinfo',
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        self.login_type = parse_helpers.get_login_type(resp_userinfo.text)

        # Get contracts here to be sure that successfully logged in
        # bcs some accesses lose the session (-a 6062)
        if is_logged:

            # Get tokenSesion to set value for x-ibercaja-st header
            resp_login2 = s.get(
                'https://banca.ibercaja.es/omnicanalidad/canales/banca-digital-apigw/v1/api/login',
                headers=self.req_headers,
                proxies=self.req_proxies,
                verify=False,
            )

            self.set_req_headers({'x-ibercaja-st': resp_login2.json()['tokenSesion']})

            resp_contracts = s.get(
                'https://banca.ibercaja.es/omnicanalidad/canales/banca-digital-apigw/v1/api/perfil/perfil-contratos',
                headers=self.basic_req_headers_updated({
                    'EsNegocio': 'false',
                    'IdContrato': '',
                    'NIPTitular': '',
                    'Orden': '0',
                    'PlaybackMode': 'Real',
                }),
                proxies=self.req_proxies,
                verify=False
            )

            # Unauthorized
            if resp_contracts.status_code == 401:
                is_logged = False
                reason = 'Expired session. Pls, check the access manually'
                return s, resp_contracts, is_logged, is_credentials_error, reason
            # Success
            resp_logged_in = resp_contracts

        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def get_contracts_by_login_type(self, contracts: List[Contract]) -> List[Contract]:
        """ Contract download control according to the login_type ('nego' or other like 'part') """
        contracts_by_login_type = []  # type: List[Contract]
        for contract_by_login_type in contracts:
            append_contract = False
            # When login_type is 'nego', only process contracts with 'negocio == True'
            # 'EsNegocio' request header doesn't work. This fix avoid customer -u 523512 to see 'Particulares'
            # accounts from 'negocio' access (-a 37208)
            if LOGIN_TYPE_NEGOCIO_MARKER in self.login_type and contract_by_login_type.negocio_param == 'true':
                append_contract = True

            # When login_type is different from 'nego', all contracts with 'negocio == False' are processed
            if LOGIN_TYPE_NEGOCIO_MARKER not in self.login_type and contract_by_login_type.negocio_param == 'false':
                append_contract = True

            if append_contract:
                contracts_by_login_type.append(contract_by_login_type)
            else:
                self.logger.info('Contract type \'{}\' doesn\'t match access {}: {}'.format(
                    'negocio' if contract_by_login_type.negocio_param == 'true' else 'not negocio',
                    self.login_type,
                    "{} ({})".format(contract_by_login_type.org_title, contract_by_login_type.id)
                ))
        return contracts_by_login_type

    def process_access(self, s: MySession, resp_contracts: Response) -> bool:
        contracts = parse_helpers.get_contracts(resp_contracts.json())
        self.logger.info('Got {} contracts: {}'.format(
            len(contracts),
            ["{} ({})".format(c.org_title, c.id) for c in contracts]
        ))
        contracts_by_login_type = self.get_contracts_by_login_type(contracts)
        self.logger.info('Got {} contracts by {}: {}'.format(
            len(contracts_by_login_type),
            self.login_type,
            ["{} ({})".format(c.org_title, c.id) for c in contracts_by_login_type]
        ))
        for contract in contracts_by_login_type:
            time.sleep(1 + random.random())
            self.process_contract(s, contract)

        self.basic_log_time_spent('GET MOVEMENTS')

        return True

    def process_contract(self, s: MySession, contract: Contract) -> bool:
        org_title = contract.org_title
        self.logger.info('Process contract {}'.format(org_title))

        self.set_req_headers({
            'EsNegocio': contract.negocio_param,
            'IdContrato': contract.id,
            'NIPTitular': contract.title,
            'Orden': contract.orden_param,
            'PlaybackMode': 'Real',
        })

        resp_accounts = s.get(
            'https://banca.ibercaja.es/omnicanalidad/canales/banca-digital-apigw/v1/api/posicion-global'
            '/cuentas-tarjetas-comercios/cuentas',
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=False
        )
        accounts_parsed = parse_helpers.get_accounts_parsed(resp_accounts.json())

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                contract.org_title,
                account_parsed,
            )
            for account_parsed in accounts_parsed
        ]

        self.logger.info('{}: got {} accounts: {}'.format(
            contract.org_title,
            len(accounts_scraped),
            accounts_scraped
        ))
        self.basic_log_time_spent('GET ACCOUNTS')
        self.basic_upload_accounts_scraped(accounts_scraped)

        for account_scraped in accounts_scraped:
            self.process_account(s, contract, account_scraped)

        self.download_correspondence(s, contract)

        return True

    def process_account(
            self,
            s: MySession,
            contract: Contract,
            account_scraped: AccountScraped) -> bool:
        # Drop ESXX prefix
        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        # We calc it on the fly due to backward comp
        #  with fin_ent_account_id provided by previous web (and scraper)
        fin_ent_account_id_for_reqs = fin_ent_account_id[4:]

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        req_movs_params = {
            "CuentaId": fin_ent_account_id_for_reqs,  # "20859727130330348449",
            "FechaInicio": date_from_str,  # "01/05/2021"
            "FechaFin": self.date_to_str,  # "26/05/2021"
            "ImporteMin": None,
            "ImporteMax": None,
            "ConceptoId": None,
            "TipoMovimiento": None,
            "NumeroContrato": contract.id,
            "EsContratoNegocio": contract.negocio_param,
            "TraerFinanciacion": False,
            "Pagina": 0,
            "ElementosPagina": MOVEMENTS_PER_PAGE,
            "DatosFinanciacion": {
                "ConceptoFinanciable": None,
                "CuentaCCC": fin_ent_account_id_for_reqs,
                "FechaDesde": date_from_str,
                "FechaHasta": self.date_to_str,
                "ImporteDesde": None,
                "ImporteHasta": None,
                "NumeroMaximoMovimientos": MOVEMENTS_PER_PAGE,
                "TipoMovimiento": "Todos"
            }
        }

        movements_parsed = []  # type: List[MovementParsed]
        for page_ix in range(100):
            req_movs_params['Pagina'] = page_ix
            self.logger.info('{}: get movements from page #{}'.format(fin_ent_account_id, page_ix + 1))

            resp_movs_i = s.post(
                'https://banca.ibercaja.es/omnicanalidad/canales/banca-digital-apigw/v1/'
                'api/Cuentas/Movimientos/busqueda',
                json=req_movs_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
                verify=False
            )

            movements_parsed_i = parse_helpers.get_movements_parsed(resp_movs_i.json())
            movements_parsed.extend(movements_parsed_i)
            if len(movements_parsed_i) < MOVEMENTS_PER_PAGE:
                self.logger.info('{}: no more pages with movements'.format(fin_ent_account_id))
                break

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
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

        return self.basic_result_success()
