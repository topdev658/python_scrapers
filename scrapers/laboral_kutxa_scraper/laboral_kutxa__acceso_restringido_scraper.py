import threading
from typing import Dict, List, Tuple

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (AccountScraped, AccountParsed, ScraperParamsCommon, MainResult)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from .custom_types import Contract

__version__ = '1.1.0'

__changelog__ = """
1.1.0
process_contract: check org_cif when there is switch contract
_get_organization_params: returns org_cif to check it
1.0.0
init
"""

lock = threading.Lock()

# Error del Servicio (Cod. 65059) - website down
# Error del Servicio (Cod. 5) - the company is turned off by the customed
RESP_ERR_SIGNS = [
    'Error del Servicio (Cod. 65059)',
    'No hay conexiones disponibles con el host',
]
IS_COMPANY_TURNED_OFF_SIGN = 'Error del Servicio (Cod. 5)'

WRONG_CREDENTIALS_MARKERS = [
    'meta name="CodError" content="50002"',  # wrong username
    'meta name="CodError" content="50014"',  # wrong password
    'El usuario o pin introducido es err'
]


class LaboralKutxaAccesoRestringidoScraper(BasicScraper):
    scraper_name = 'LaboralKutxaAccesoRestringidoScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.update_inactive_accounts = False
        self.is_success = True  # some children use it (N43)

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()
        reason = ''
        is_credential_error = False

        resp_set_cookie = s.get(
            'https://lknet.laboralkutxa.com/reducida'
        )

        user_data = {
            "usuario": self.username,
            "CODREDUCIDA": self.username_second,
            "clave": self.userpass,
            "submit1": "Aceptar"
        }

        resp_logged_in = s.post(
            'https://lknet.laboralkutxa.com/reducida/checklogon.asp',
            data=user_data,
            proxies=self.req_proxies,
        )

        is_logged = 'Caja Laboral Net - Acceso al servicio' \
                    in resp_logged_in.text

        return s, resp_logged_in, is_logged, is_credential_error, reason

    def _get_organization_params(
            self,
            s: MySession,
            lkid_param: str) -> Tuple[bool, str]:
        """:returns (ok, org_title, org_cif)"""
        resp_user = s.get(
            'https://lkweb.laboralkutxa.com/srv/api/usuario',
            headers=self.basic_req_headers_updated({
                'Accept': 'application/json, text/plain, */*',
                'origen': 'web',
                'lkid': lkid_param
            }),
            proxies=self.req_proxies
        )

        ok, resp_user_json = self.basic_get_resp_json(
            resp_user,
            "Can't get resp_user_json. Abort"
        )
        if not ok:
            return False, ''  # already reported

        org_title = resp_user_json['usuario']['razonSocial']
        org_cif = resp_user_json['usuario']['nif']
        return True, org_title, org_cif

    def _upload_accounts_scraped(self, accounts_scraped: List[AccountScraped]) -> None:
        """Can override in children"""
        self.basic_upload_accounts_scraped(accounts_scraped)

    def _switch_to_contract(
            self,
            s: MySession,
            contract: Contract,
            ix: int,
            lkid_param: str,
            csrf_token: str) -> Tuple[bool, bool, str, str]:
        """:returns (ok, is_available, lkid_param, csrf_token)"""
        self.logger.info('Switch to {}'.format(contract))
        if ix == 0:
            return True, True, lkid_param, csrf_token

        req_params = {
            'tokenAdministrador': csrf_token,
            'idUsuarioAdministrado': contract.id
        }
        resp_contract = s.post(
            'https://lkweb.laboralkutxa.com/srv/api/login-administrador',
            json=req_params,
            headers=self.basic_req_headers_updated({
                "lkid": lkid_param,
                "origen": "web",
            }),
            proxies=self.req_proxies
        )

        ok, resp_contract_json = self.basic_get_resp_json(
            resp_contract,
            "Can't get resp_contract_json. Abort"
        )
        if not ok:
            return False, False, '', ''

        # -a 4041
        # disabled contract Contract(org_title='AUTOMOVILES Y CAMIONES,S.A.', id='AU00011905', cif='A48024434')
        # {"solicitarSCA":false,"mensaje":"51 TARJETA USUARIO C.L.NET , INEXISTENTE","resultado":65101}
        if resp_contract_json['resultado'] != 0:
            self.logger.info('{}: disabled contract detected. Skip. RESPONSE: {}'.format(
                contract.org_title,
                resp_contract.text
            ))
            return True, False, lkid_param, csrf_token

        lkid_param_upd = resp_contract_json['lkId']
        return True, True, lkid_param_upd, csrf_token

    def process_access(self, s: MySession, lkid_param: str) -> bool:
        resp_user = s.get(
            'https://lkweb.laboralkutxa.com/srv/api/usuario',
            headers=self.basic_req_headers_updated({
                'origen': 'web',
                'lkid': lkid_param
            }),
            proxies=self.req_proxies,
        )
        ok, resp_user_json = self.basic_get_resp_json(
            resp_user,
            "Can't get resp_user_json. Abort"
        )
        if not ok:
            return False  # already reported

        csrf_token = resp_user_json['usuario'].get('administrador', {}).get('token', '')
        contracts = parse_helpers.get_contracts_newweb(resp_user_json)
        for ix, contract in enumerate(contracts):
            ok, is_available, lkid_param, csrf_token = self._switch_to_contract(
                s,
                contract=contract,
                ix=ix,
                lkid_param=lkid_param,
                csrf_token=csrf_token
            )
            if not ok:
                self.is_success = False
                return False

            if not is_available:
                continue  # already reported
            ok = self.process_contract(s, contract, lkid_param)
            if not ok:
                # don't interrupt regular scraping
                # but it'll be important for some children (so they can interrupt, see N43 scraper)
                self.is_success = False
        return True

    def process_contract(self, s: MySession, contract: Contract, lkid_param: str) -> bool:
        ok, org_title, org_cif = self._get_organization_params(s, lkid_param)
        # Check successfully switch contract with org title and cif because
        # it is possible that the title is too long and does not appear complete (no match)
        if (org_title != contract.org_title) and (org_cif != contract.cif):
            self.logger.error("{}: couldn't switch to the contract. Got wrong org_title='{}'. Skip".format(
                contract.org_title,
                org_title
            ))
            return False

        self.logger.info('{}: process contract'.format(org_title))
        resp_accs = s.get(
            # 'https://lkweb.laboralkutxa.com/srv/api/mis-productos',
            'https://lkweb.laboralkutxa.com/srv/api/cuentas',
            headers=self.basic_req_headers_updated({
                'origen': 'web',
                'lkid': lkid_param
            }),
            proxies=self.req_proxies,
        )
        ok, resp_accs_json = self.basic_get_resp_json(
            resp_accs,
            "Can't get resp_accs_json. Abort"
        )
        if not ok:
            return False  # already reported

        ok, accounts_parsed = parse_helpers.get_accounts_parsed_newweb(resp_accs_json)
        if not ok:
            self.logger.error("{}: can't get accounts_parsed. RESPONSE: {}".format(
                org_title,
                resp_accs
            ))
            return False

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                organization_title=org_title,
                account_parsed=acc,
            ) for acc in accounts_parsed
        ]

        self._upload_accounts_scraped(accounts_scraped)
        self.logger.info('{}: got {} accounts: {}'.format(
            org_title,
            len(accounts_scraped),
            accounts_scraped
        ))
        self.basic_log_time_spent('GET BALANCES')

        accounts_scraped_dict = self.basic_gen_accounts_scraped_dict(accounts_scraped)

        # Serial processing
        for account_parsed in accounts_parsed:
            self.process_account(s, lkid_param, accounts_scraped_dict, account_parsed)

        self.download_correspondence(s, contract, lkid_param)

        return True

    def process_account(
            self,
            s: MySession,
            lkid_param: str,
            accounts_scraped_dict: Dict[str, AccountScraped],
            account_parsed: AccountParsed) -> bool:
        fin_ent_account_id = account_parsed['financial_entity_account_id']
        account_scraped = accounts_scraped_dict[fin_ent_account_id]

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return False

        date_from, date_from_str = self.basic_get_date_from_dt(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        req_movs_url = 'https://lkweb.laboralkutxa.com/srv/api/cuentas/{}/movimientos/buscar'.format(
            account_parsed['position_id_param']
        )
        req_movs_params = {
            'fechaDesde': date_from.strftime('%Y-%m-%d'),  # 2020-10-01,
            'fechaHasta': self.date_to.strftime('%Y-%m-%d'),  # 2020-12-16
        }
        resp_movs = s.get(
            req_movs_url,
            params=req_movs_params,
            headers=self.basic_req_headers_updated({
                'origen': 'web',
                'lkid': lkid_param,
            }),
            proxies=self.req_proxies
        )
        ok, resp_movs_json = self.basic_get_resp_json(
            resp_movs,
            "Can't get resp_movs_json. Skip"
        )
        if not ok:
            return False  # already reported

        # No examples to impl pagination
        movs_parsed_desc = parse_helpers.get_movements_parsed_newweb(resp_movs_json)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movs_parsed_desc,
            date_from_str
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        return True

    def main(self) -> MainResult:

        s, resp_logged_in, is_logged, is_credentials_error, lkid_param, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        self.process_access(s, lkid_param)

        self.basic_log_time_spent('GET MOVEMENTS')

        return self.basic_result_success()
