import random
import time
from collections import OrderedDict
from typing import Tuple
from urllib.parse import urljoin

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    ACCOUNT_NO_TYPE_UNKNOWN, AccountScraped,
    MOVEMENTS_ORDERING_TYPE_ASC, ScraperParamsCommon, MainResult,
    DOUBLE_AUTH_REQUIRED_TYPE_COMMON
)
from scrapers.santander_brasil_scraper import parse_helpers
from scrapers.santander_brasil_scraper import parse_helpers_novo
from scrapers.santander_brasil_scraper.santander_brasil_loginer import SantanderBrasilLoginer

__version__ = '1.9.0'

__changelog__ = """
1.9.0
use account-level result_codes
1.8.0
call basic_upload_movements_scraped with date_from_str
1.7.3
aligned double auth msg
1.7.2
upd type hints
get_movements_parsed: handle gracefully if can't parse movs
1.7.1
removed unused
1.7.0
new layout ("Consultar novo" for movs)
1.6.0
login: resp_logoff_from_old
process_company: fixed basic_log_wrong_layout args
1.5.0
login: 'Probably, SMS AUTH required' detector
use basic_log_wrong_layout
1.4.0
process_account: use basic_get_date_from
1.3.0
login: return the reason from if failed, detect 'sms auth required' 
1.2.0
improved login method (several attempts if got RETRY_MARKER)
logout method
parse_helpers_novo: get_account_parsed: handle err resp to avoid exc
1.1.0
process_account: 
    extract cuenta_form_geral_id_param and 
    recent_movs_form_geral_id_param from pages (were consts)
1.0.0
init
"""

CREDENTIALS_ERROR_MARKER = 'Dados informados inválidos'
LOGGED_IN_MARKER = '<span class="space">Olá,</span>'
# msg: Please wait for completion of the operation.Do not update your browser
RETRY_MARKER = 'Por favor, aguarde a finalização da operação'


class SantanderBrasilNovoScraper(SantanderBrasilLoginer):
    """SantanderBrasilDefaultScraper provides scraping for
    'Pessoa Jurídica (Novo)' access type (new).

    Implemented features:
    - the scraper supports 1 account per access
    (there is a way to switch accounts via "TROCAR CONTA" link in the list
    of movements, but due to there is only one access for this fin entity
    and another account doesn't have any movements at all, then several
    accounts per access are not supported for now)
    - balance displayed at home page totally different to temp_balance of
    the most recent movement, because balance at the total page also includes
    balances of some investment tools, just to note.
    """

    scraper_name = 'SantanderBrasilNovoScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies, self.scraper_name)

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s, resp_logged_in_pre_form, ok = self.common_login()
        if not ok:
            return s, resp_logged_in_pre_form, False, False, ''

        # common place to occure credentials error marker
        if CREDENTIALS_ERROR_MARKER in resp_logged_in_pre_form.text:
            is_credentials_error = True
            return s, resp_logged_in_pre_form, False, is_credentials_error, ''

        # necessary to continue in Novo
        resp_logoff_from_old = s.post(
            'https://www.santandernetibe.com.br/Logoff.asp',
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        if resp_logoff_from_old.status_code != 200:
            self.logger.error(
                "Can't perform correct req to /Logoff.asp (to logout from old UI). "
                "Continue as is"
            )

        req_ibweb_action_url, req_ibweb_params = extract.build_req_params_from_form_html_patched(
            resp_logged_in_pre_form.text,
            'frm'
        )
        if not (req_ibweb_action_url and req_ibweb_params):
            return s, resp_logged_in_pre_form, False, False, "Can't parse req_ibweb_params"

        req_url = urljoin(resp_logged_in_pre_form.url, req_ibweb_action_url)

        resp_ibweb = s.post(
            req_url,
            data=req_ibweb_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_pre_home_ticket_param = parse_helpers_novo.get_ticket_param(resp_ibweb.text)
        if not req_pre_home_ticket_param:
            return s, resp_ibweb, False, False, "Can't parse req_pre_home_ticket_param"

        req_pre_home_params = {'Ticket': req_pre_home_ticket_param}

        time.sleep(0.5 + random.random())
        req_home_url = 'https://pj.santandernetibe.com.br/ibeweb/'
        resp_pre_home_novo = s.post(
            req_home_url,
            data=req_pre_home_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # continue
        resp_home_novo = Response()
        is_logged = False
        is_credentials_error = False
        for i in range(3):
            resp_home_novo = s.get(
                'https://pj.santandernetibe.com.br/ibeweb/pages/home/homeNovo.xhtml',
                headers=self.req_headers,
                proxies=self.req_proxies
            )
            is_credentials_error = CREDENTIALS_ERROR_MARKER in resp_home_novo.text
            is_logged = LOGGED_IN_MARKER in resp_home_novo.text

            if ('Existem pedidos de autorização do número de celular para habilitação do serviço QRCode por SMS.'
                    in resp_home_novo.text):
                self.logger.warning('Probably, {}'.format(DOUBLE_AUTH_REQUIRED_TYPE_COMMON))
                # return s, resp_home_novo, False, False, "SMS AUTH required"

            if is_logged or is_credentials_error:
                break

            # unknown reason: not logged in, not a credentials err, no 'wait for completetion' msg
            if RETRY_MARKER not in resp_home_novo.text:
                break

            # retry attempt
            self.logger.info('Received msg: "wait for completion of the operation". '
                             'Wait and retry #{}'.format(i + 1))
            time.sleep(5 + random.random())

        return s, resp_home_novo, is_logged, is_credentials_error, ''

    def process_company(self, s: MySession, resp_home_novo: Response) -> bool:
        # only one account per access

        fin_ent_account_id = self._get_fin_ent_account_id()
        account_parsed = parse_helpers_novo.get_account_parsed(resp_home_novo.text,
                                                               fin_ent_account_id)

        if not account_parsed:
            self.basic_log_wrong_layout(resp_home_novo, "Can't extract account_parsed. Abort")
            return False

        self.logger.info('Got account {}'.format(account_parsed))

        account_scraped = self.basic_account_scraped_from_account_parsed(
            self.db_customer_name,
            account_parsed,
            country_code='BRA',
            account_no_format=ACCOUNT_NO_TYPE_UNKNOWN,
            is_default_organization=True
        )
        self.basic_upload_accounts_scraped([account_scraped])
        self.basic_log_time_spent('GET ACCOUNTS')

        self.process_account(s, account_scraped)
        return True

    def process_account(self, s: MySession, account_scraped: AccountScraped) -> bool:
        # Pagination is not necessary.
        # At least if fetched less than 100 movs (current case)

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        # '9jf/CEzquwwX5IYIOZfFfZ6sdox8f62c202dyECX7hvHRt3A'
        req_menu_novo_url = 'https://pj.santandernetibe.com.br/ibeweb/pages/menu/menuNovo.xhtml'
        resp_cuenta_init = s.get(
            req_menu_novo_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        view_state_param = parse_helpers_novo.get_view_state_param(resp_cuenta_init.text)
        # expect j_id_62 or j_id_5z
        cuenta_form_geral_id_param = parse_helpers_novo.get_cuenta_page_form_geral_id_param(resp_cuenta_init.text)
        if not (view_state_param and cuenta_form_geral_id_param):
            self.basic_log_wrong_layout(
                resp_cuenta_init,
                "Can't parse view_state_param/cuenta_form_geral_id_param. Abort"
            )
            return False

        fgrl = 'formGeral:{}'.format(cuenta_form_geral_id_param)
        req_cuenta_page_params = OrderedDict([
            ('javax.faces.partial.ajax', 'true'),
            ('javax.faces.source', fgrl),
            ('javax.faces.partial.execute', '@all'),
            ('javax.faces.partial.render', 'formGeral:idFormGeral'),
            (fgrl, fgrl),
            ('idItemMenu', '4001'),
            ('formGeral:{}_menuid'.format(cuenta_form_geral_id_param), '0'),
            ('formGeral:drunningMode', 'prod4'),  # prod1
            ('formGeral:segmento', '228'),
            ('formGeral:autenticacao', ''),
            ('formGeral:oferta', ''),
            ('formGeral_SUBMIT', '1'),
            ('javax.faces.ViewState', view_state_param)
        ])

        # expect
        # <partial-response>
        # <redirect url="/ibeweb/pages/menu/menuNovo.xhtml"/>
        # </partial-response>
        resp_cuenta_menu = s.post(
            req_menu_novo_url,
            data=req_cuenta_page_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if '<redirect url="/ibeweb/pages/menu/menuNovo.xhtml">' not in resp_cuenta_menu.text:
            self.basic_log_wrong_layout(resp_cuenta_menu, "Can't get correct resp_cuenta_menu. Abort")
            return False

        resp_cuenta = s.get(
            req_menu_novo_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if 'Consultar' not in resp_cuenta.text:
            self.basic_log_wrong_layout(
                resp_cuenta,
                "Can't get correct resp_cuenta. Expected to find text 'Consultar'. Abort"
            )
            return False

        # expect from formGeral:j_id_7x:1:j_id_82
        recent_movs_form_geral_id_param = parse_helpers_novo.get_recent_movs_form_geral_id_param(resp_cuenta.text)
        if not recent_movs_form_geral_id_param:
            self.basic_log_wrong_layout(
                resp_cuenta,
                "Can't parse recent_movs_form_geral_id_param. Abort"
            )
            return False

        req_recent_movs_params = OrderedDict([
            ('formGeral:drunningMode', 'prod1'),
            ('formGeral:segmento', '228'),
            ('formGeral:autenticacao', ''),
            ('formGeral:trocaConta', 'false'),
            ('formGeral_SUBMIT', '1'),
            ('javax.faces.ViewState', view_state_param),
            ('redirectPage', 'goConsultarContaCorrenteExtratos'),
            ('descricaoMenuPai', 'Conta Corrente'),
            ('descricaoMenu', 'Consultar'),  # was 'Consultar+Extrato'
            ('idItemMenu', '4928'),
            ('idItemMenuPai', '4026'),
            ('redirectPageIBPJClassico', 'NOVOIBPJ'),
            ('fluxoCapAssinatura', ''),
            ('formGeral:_idcl', 'formGeral:{}'.format(recent_movs_form_geral_id_param)),
        ])
        # ok
        # necessary to open req_recent_movs_own_page
        resp_recent_movs = s.post(
            req_menu_novo_url,
            data=req_recent_movs_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        view_state_movs_own_page_param = parse_helpers_novo.get_view_state_param(
            resp_recent_movs.text
        )

        if not view_state_movs_own_page_param:
            self.logger.error("Can't parse view_state_movs_own_page_param. Abort. RESPONSE:\n{}".format(
                resp_recent_movs.text
            ))
            return False
        # ok
        req_movs_own_page_url = ('https://pj.santandernetibe.com.br/ibeweb/pages/contaCorrente/'
                                 'extratos/contaCorrenteConsultarExtratos.xhtml')

        req_movs_filtered_params = OrderedDict([
            ('javax.faces.partial.ajax', 'true'),
            ('javax.faces.source', 'formGeral:consultarExtratoDatePicker'),
            ('javax.faces.partial.execute', '@all'),
            ('javax.faces.partial.render', 'formGeral:geral'),
            ('formGeral:consultarExtratoDatePicker', 'formGeral:consultarExtratoDatePicker'),
            ('formGeral:dataInicial', date_from_str),  # '01/01/2019'
            ('formGeral:dataFinal', self.date_to_str),  # '23/01/2019'
            ('formGeral:porPeriodo', ''),
            ('formGeral:selTipoBandeira', 'Todos'),
            ('formGeral:htmlToPrintHidden', ''),
            ('formGeral:htmlToPdfHidden', ''),  # ...<BASE64 HTML>... in real req
            ('formGeral:drunningMode', 'prod1'),  # was prod4 before 1.7.0
            ('formGeral:segmento', '228'),
            ('formGeral:autenticacao', ''),
            # ('formGeral:oferta', ''), commented since 1.7.0
            ('formGeral:trocaConta', 'false'),
            ('formGeral_SUBMIT', '1'),
            ('javax.faces.ViewState', view_state_movs_own_page_param),
        ])

        # TODO check headers
        # expecting x-dtpc: 80$219127217_815h5vIDKSEDRKIOJLIEJGOOIIMHAQLAKMATIB
        resp_movs_filtered = s.post(
            req_movs_own_page_url,
            data=req_movs_filtered_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        ok, movements_parsed = parse_helpers.get_movements_parsed(resp_movs_filtered.text)
        if not ok:
            self.basic_log_wrong_layout(resp_movs_filtered, "{}: can't extract SALDO ANTERIOR. Skip".format(
                fin_ent_account_id
            ))
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
            return False

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
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

    def logout(self, s: MySession) -> bool:
        """Prevent case when can't log in due temp restriction.
        Msg:
            Aguarde 20 minutos para realizar novo acesso.
            Lembre-se: ao finalizar o uso do Internet Banking,
            encerre o acesso através do botão “Sair”.
        """
        self.logger.info('= Logout =')

        resp_home_novo = s.get(
            'https://pj.santandernetibe.com.br/ibeweb/pages/home/homeNovo.xhtml',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        view_state_param = parse_helpers_novo.get_view_state_param(resp_home_novo.text)

        # if it changes
        # can get j_id for 'Sair' using regexp for
        # <a id="formPainelNotificacoes:j_id_23" href="#"
        # class="ui-commandlink ui-widget sair" aria-label="Sair"
        # onclick="PrimeFaces.ab({source:'formPainelNotificacoes:j_id_23',partialSubmit:true});return false;"
        # title="Sair">Sair</a>

        req_logout_step1_params = OrderedDict([
            ('javax.faces.partial.ajax', 'true'),
            ('javax.faces.source', 'formPainelNotificacoes:j_id_23'),
            ('javax.faces.partial.execute', '@all'),
            ('formPainelNotificacoes:j_id_23', 'formPainelNotificacoes:j_id_23'),
            ('formPainelNotificacoes:acSimple_input', ''),
            ('formPainelNotificacoes:acSimple_hinput', ''),
            ('formPainelNotificacoes_SUBMIT', '1'),
            ('javax.faces.ViewState', view_state_param)
        ])

        resp_logout_step1 = s.post(
            resp_home_novo.url,
            data=req_logout_step1_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if 'Deseja sair do Internet Banking Empresarial?' not in resp_logout_step1.text:
            self.logger.error("Can't logout correctly.\nRESPONSE:\n{}".format(resp_logout_step1.text))
            return False

        req_logout_step2_params = OrderedDict([
            ('javax.faces.partial.ajax', 'true'),
            ('javax.faces.source', 'closeMessageLogoutSim'),
            ('javax.faces.partial.execute', '@all'),
            ('closeMessageLogoutSim', 'closeMessageLogoutSim'),
            ('formPainelNotificacoes:acSimple_input', ''),
            ('formPainelNotificacoes:acSimple_hinput', ''),
            ('formPainelNotificacoes_SUBMIT', '1'),
            ('javax.faces.ViewState', view_state_param)
        ])

        resp_logout_step2 = s.post(
            resp_home_novo.url,
            data=req_logout_step2_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # the most important
        req_logout_step3_params = OrderedDict([
            ('javax.faces.partial.ajax', 'true'),
            ('javax.faces.source', 'formGeral:j_id_5t'),
            ('javax.faces.partial.execute', '@all'),
            ('formGeral:j_id_5t', 'formGeral:j_id_5t'),
            ('formGeral:drunningMode', 'prod4'),
            ('formGeral:segmento', '228'),
            ('formGeral:autenticacao', ''),
            ('formGeral:oferta', ''),
            ('formGeral_SUBMIT', '1'),
            ('javax.faces.ViewState', view_state_param)
        ])

        resp_logout_step3 = s.post(
            resp_home_novo.url,
            data=req_logout_step3_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()
        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                extract.text_wo_scripts_and_tags(resp_logged_in.text),
                reason
            )

        try:
            self.process_company(s, resp_logged_in)
        except Exception as e:
            raise e  # just bubble up
        finally:
            self.logout(s)  # mandatory logout

        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
