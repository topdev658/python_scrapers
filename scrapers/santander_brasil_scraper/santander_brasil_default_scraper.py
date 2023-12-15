from collections import OrderedDict
from typing import Tuple

from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    ACCOUNT_NO_TYPE_UNKNOWN, ACCOUNT_TYPE_CREDIT, AccountParsed,
    MOVEMENTS_ORDERING_TYPE_ASC, ScraperParamsCommon, MainResult
)
from scrapers.santander_brasil_scraper import parse_helpers
from scrapers.santander_brasil_scraper.santander_brasil_loginer import SantanderBrasilLoginer

__version__ = '2.5.0'

__changelog__ = """
2.5.0
use account-level result_codes
2.4.0
call basic_upload_movements_scraped with date_from_str
2.3.0
upd type hint
get_movements_parsed: handle gracefully if can't parse movs
fmt
2.2.0
process_account: use basic_get_date_from
2.1.0
login: return the reason from if failed, detect 'need to change access type' 
process_contract: detect 'need to change access type'
2.0.0
moved from santander_brasil_scraper to obtain a support for santander_brasil_novo 
inherits SantanderBrasilLoginer
"""


class SantanderBrasilDefaultScraper(SantanderBrasilLoginer):
    """SantanderBrasilDefaultScraper provides scraping for
    'Pessoa Jurídica' access type (default).
    Only one account per access
    """

    scraper_name = 'SantanderBrasilDefaultScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies, self.scraper_name)

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:

        s, resp_logged_in, ok = self.common_login()
        if not ok:
            return s, resp_logged_in, False, False, ''

        is_logged = resp_logged_in.status_code == 200 and 'PMData' in resp_logged_in.cookies.keys()
        is_credentials_error = 'Dados informados inválidos' in resp_logged_in.text
        reason = ''
        if 'Internet Banking - Novo IBPJ' in resp_logged_in.text:
            is_logged = False
            reason = "NEED TO SWITCH TO 'Pessoa Juridica (Novo)' ACCESS TYPE"

        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def process_contract(self, s: MySession) -> bool:
        req_balances_url = 'https://www.santandernetibe.com.br/NIB_Saldo.asp'
        resp_balances = s.get(
            req_balances_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if ('sua conexão foi encerrada após alguns minutos de inatividade ou pelo '
            'fechamento incorreto da sessão do Internet Banking' in resp_balances.text):
            self.logger.error(
                "Can't continue. The session was interrupted. Most probable reason: "
                "NEED TO SWITCH TO 'Pessoa Juridica (Novo)' ACCESS TYPE. Abort now"
            )
            return False
        # only one account per access
        account_parsed = parse_helpers.get_account_parsed(resp_balances.text,
                                                          self._get_fin_ent_account_id())
        self.logger.info('Got account {}'.format(account_parsed))
        self.process_account(s, account_parsed)
        return True

    def process_account(self, s: MySession, account_parsed: AccountParsed) -> bool:
        fin_ent_account_id = account_parsed['account_no']
        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        req_mov_url = 'https://www.santandernetibe.com.br/Paginas/contacorrente/Extrato_Detalhe.asp'
        req_mov_params = OrderedDict([
            ('DataIni', date_from_str),
            ('DataFin', self.date_to_str)
        ])

        # No pagination for movements implemented - website returns all movs at once
        resp_mov = s.get(
            req_mov_url,
            params=req_mov_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        ok, movements_parsed = parse_helpers.get_movements_parsed(resp_mov.text)
        if not ok:
            self.basic_log_wrong_layout(resp_mov, "{}: can't extract SALDO ANTERIOR. Skip".format(
                fin_ent_account_id
            ))
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
            return False

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        # Update account_parsed after movements parsed
        # and set account_scraped
        if any(m.TempBalance < 0 for m in movements_scraped):
            account_parsed['account_type'] = ACCOUNT_TYPE_CREDIT

        account_scraped = self.basic_account_scraped_from_account_parsed(
            self.db_customer_name,
            account_parsed,
            country_code='BRA',
            account_no_format=ACCOUNT_NO_TYPE_UNKNOWN,
            is_default_organization=True
        )
        self.basic_upload_accounts_scraped([account_scraped])
        self.basic_log_time_spent('GET ACCOUNTS')

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

        self.process_contract(s)
        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
