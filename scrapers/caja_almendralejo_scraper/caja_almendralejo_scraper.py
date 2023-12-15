from typing import Tuple

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import AccountScraped, ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.caja_almendralejo_scraper import parse_helpers

__version__ = '1.3.0'
__changelog__ = """
1.3.0
call basic_upload_movements_scraped with date_from_str
1.2.0
parse_helpers: get_movements_parsed: handle new layout
1.1.0
use basic_new_session
upd type hints
1.0.0
init
"""


class CajaAlmendralejoScraper(BasicScraper):
    scraper_name = 'CajaAlmendralejoScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

    def login(self) -> Tuple[MySession, Response, bool, bool]:
        s = self.basic_new_session()

        # Get initial cookies
        resp_init = s.get(
            'https://www.cajalnet.es/GetLoginAction.do',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_login_params = {
            'j_username': self.username,
            'j_password': self.userpass,
            'campoOculto': '',
        }

        resp_logged_in = s.post(
            'https://www.cajalnet.es/SetLoginAction.do',
            data=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = 'Salir de la Banca' in resp_logged_in.text  # 'Contrato Nº'
        is_credentials_error = 'Usuario y/o password incorrectos' in resp_logged_in.text

        return s, resp_logged_in, is_logged, is_credentials_error

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:

        # Menu (top) Cuentas -> (side) Extrato -> Saldos cuentas
        resp_accounts = s.get(
            'https://www.cajalnet.es/GetConsultaSaldos.do?OID_MENU=117',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_parsed = parse_helpers.get_accounts_parsed(resp_accounts.text)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                acc_parsed['organization_title'],
                acc_parsed,
            )
            for acc_parsed in accounts_parsed
        ]

        self.logger.info('Got {} accounts: {}'.format(
            len(accounts_scraped),
            accounts_scraped
        ))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET ACCOUNTS')

        for account_scraped in accounts_scraped:
            self.process_account(s, account_scraped)

        return True

    def process_account(self, s: MySession, account_scraped: AccountScraped) -> bool:

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        req_accounts_dropdown_params = {
            'cod': 'TCUM',
            'searchService': 'es.indra.cra.bancavirtual.comun.service.BancaVirtualService',
            'searchMethod': 'findAllCuentasExtracto',
            'proviene': 'select',
            'valor': 'numCuenta',
            'nombre': 'numTipoCuenta'
        }

        resp_accounts_dropdown = s.get(
            'https://www.cajalnet.es/GetConsultaDatos.do',
            params=req_accounts_dropdown_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        combo_param = parse_helpers.get_req_movs_combo_param(resp_accounts_dropdown.text,
                                                             fin_ent_account_id)

        # Date filter is not working. Get ALL movs
        # (200 movs, 6 years...)
        req_movs_params = {
            'urlEntrada': '/GetUltimosMovimientos',
            'tipoOperacion': 'Todos',
            'comboCuentas': combo_param,  # 'ES36 3001 0053 0553 1075 0924 | CUENTA CORRIENTE',
            'idTransaccion': 'TCUM',
            'fechaActual': '',
            'numCuenta': account_scraped.AccountNo[4:],  # '30010053055310750924',
            'comboOperaciones': '0',
            'fechaInicio': '',  # can use 14/09/2019 format, but it doesn't take effect
            'fechaFin': '',
            'importeMin': '0',
            'importeMax': '999999999999.99',
            'method': 'Aceptar'
        }

        resp_movs = s.post(
            'https://www.cajalnet.es/SetBuscarExtractos.do',
            data=req_movs_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        movements_parsed_desc = parse_helpers.get_movements_parsed(resp_movs.text)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_desc,
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
        s, resp_logged_in, is_logged, is_credentials_error = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url, resp_logged_in.text)

        self.process_access(s, resp_logged_in)
        self.basic_log_time_spent('GET MOVEMENTS')

        return self.basic_result_success()
