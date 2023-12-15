import random
import time
from collections import OrderedDict
from typing import Optional, Tuple, List

from custom_libs import list_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, AccountScraped, MovementParsed, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.bpi_scraper import parse_helpers

__version__ = '2.8.0'

__changelog__ = """
2.8.0
use renamed list_funcs
2.7.0
process_account: handle different pagination cases:
  page contains all previous + own movements OR contains only its own movements
2.6.0
call basic_upload_movements_scraped with date_from_str
2.5.0
parse_helpers: resp_text_clean (handles js escapes)
2.4.0
req_movs_params: 
  use parse_helpers.get_eventtarget_param.., parse_helpers.get_ajax_param.. 
  instead of const params
2.3.1
added todos
2.3.0
upd req params (-a 21147)
2.2.0
_select_account (-a 20311)
2.1.0
upd req params
more 'next page' markers
2.0.0
process_account, parse_helpers: upd reqs and parsers (new web)
1.3.0
skip inactive accounts
1.2.0
use basic_new_session
upd type hints
1.1.0
new basic url
1.0.1
more log msgs
1.0.0
init
"""

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0'


class BPIScraper(BasicScraper):
    """For now, only serial scraping implemented and tested
    (it's enough for the current usage)
    """
    scraper_name = 'BPIScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.req_headers = {'User-Agent': USER_AGENT}
        self.update_inactive_accounts = False

    def login(self) -> Tuple[MySession, Response, bool, bool]:
        s = self.basic_new_session()

        # to get user session cookies
        resp_start = s.get(
            'https://www.bpinetempresas.pt/signon/signon.asp',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        time.sleep(0.2 + random.random())

        req_login_params = (
            "<dadosformulario>"
            "<campo nome='__submited'>sim</campo>"
            "<campo nome='__accao'></campo>"
            "<campo nome='ScreenHeight'>768</campo>"
            "<campo nome='ScreenWidth'>1366</campo>"
            "<campo nome='CustomerCode'>{}</campo>"
            "<campo nome='Password'>{}</campo>"
            "</dadosformulario>".format(self.username, self.userpass)
        )

        req_login_headers = self.basic_req_headers_updated({
            'X-Requested-With': 'XMLHttpRequest',
            'PedidoXML': 'sim',
            'Referer': resp_start.url
        })

        resp_logged_in = s.post(
            'https://bpinetempresas.bancobpi.pt/signon/signonRender.asp',
            data=req_login_params,
            headers=req_login_headers,
            proxies=self.req_proxies
        )

        # <resultado sucesso="sim">
        #   <accao>
        #     document.location.href = 'https://bpinetempresas.bancobpi.pt/NetEmp/SignOn.aspx';
        #   </accao>
        # </resultado>
        is_logged = '<resultado sucesso="sim">' in resp_logged_in.text
        is_credentials_error = '<resultado sucesso="nao"><mensagem>Acesso inv' in resp_logged_in.text
        resp_inicio = None  # type: Optional[Response]
        if is_logged:
            # to get authenticated session cookies
            reps_signon = s.get(
                'https://bpinetempresas.bancobpi.pt/NetEmp/SignOn.aspx',
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            resp_inicio = s.get(
                'https://bpinetempresas.bancobpi.pt/NetEmp/Inicio.aspx',
                headers=self.req_headers,
                proxies=self.req_proxies
            )

        return s, resp_inicio or resp_logged_in, is_logged, is_credentials_error

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:

        resp_accounts = s.get(
            'https://bpinetempresas.bancobpi.pt/operacoes/consultas/posicaointegrada/posicaointegrada.asp',
            headers=self.basic_req_headers_updated({
                'Referer': resp_logged_in.url
            }),
            proxies=self.req_proxies
        )

        org_title = parse_helpers.get_organization_title(resp_accounts.text)
        if not org_title:
            self.basic_log_wrong_layout(resp_accounts, "Can't parse org_title. Use blank")

        accounts_parsed = parse_helpers.get_accounts_parsed(resp_accounts.text)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                org_title,
                acc_parsed,
                country_code=acc_parsed['country_code']
            )
            for acc_parsed in accounts_parsed
        ]

        self.logger.info('Got {} accounts: {}'.format(
            len(accounts_scraped),
            accounts_scraped
        ))
        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET ACCOUNTS')

        for acc_ix, acc_scraped in enumerate(accounts_scraped):
            self.process_account(s, org_title, acc_scraped, acc_ix)

        return True

    def _select_account(self,
                        s: MySession,
                        resp_prev: Response,
                        account_scraped: AccountScraped) -> Tuple[bool, Response]:
        """Need to explicitly select another account to get valid movements"""

        self.logger.info('{}: select account'.format(account_scraped.FinancialEntityAccountId))

        req_movs_url = 'https://bpinetempresas.bancobpi.pt/NetEmp_Contas_DO/Movimentos.aspx'
        org_param = parse_helpers.get_org_param_for_movs(resp_prev.text)
        # Filter by title to handle different order of accounts
        # from different views
        acc_for_movs = [
            a for a in parse_helpers.get_accounts_for_movs(resp_prev.text)
            if account_scraped.AccountNo in a.title
        ][0]

        date_to_param = self.date_to_str.replace('/', '-')

        req_select_acc_params = OrderedDict([
            # TODO try re with CW_NETEmp_Comum_wtEmpresasContas
            ('__EVENTTARGET',
             'LT_BPINetEmpresas_wt37$block$wtContext$CW_NETEmp_Comum_wtEmpresasContas$block$'
             'LT_BPI_Patterns_wt3$block$wtAccountValue$wtcbListaContas'),
            ('__EVENTARGUMENT', ''),
            ('__OSVSTATE', parse_helpers.get_osvstate_param(resp_prev.text)),
            ('__VIEWSTATE', ''),
            ('__VIEWSTATEGENERATOR', parse_helpers.get_viewstategenerator_param(resp_prev.text)),
            ('LT_BPINetEmpresas_wt37$block$wtContext$CW_NETEmp_Comum_wtEmpresasContas$block'
             '$LT_BPI_Patterns_wt9$block$wtAccountValue$wtcbListaEmpresas',
             org_param),
            ('LT_BPINetEmpresas_wt37$block$wtContext$CW_NETEmp_Comum_wtEmpresasContas$block'
             '$LT_BPI_Patterns_wt3$block$wtAccountValue$wtcbListaContas',
             acc_for_movs.req_param),  # '286972080'
            ('LT_BPINetEmpresas_wt37_block_wtMainContent_CW_Contas_Empresas_wtMovimentos_block$1103974314',
             'Todos'),
            ('LT_BPINetEmpresas_wt37$block$wtMainContent$CW_Contas_Empresas_wtMovimentos$block$WebPatterns_wt125$block'
             '$wtContent$LT_BPI_Patterns_wtFormFiltroPattern$block$wtForm$LT_BPI_Patterns_wt111$block'
             '$wtRow$LT_BPI_Patterns_wt92$block$wtInput$wttxtMontanteInf',
             ''),
            ('LT_BPINetEmpresas_wt37$block$wtMainContent$CW_Contas_Empresas_wtMovimentos$block$WebPatterns_wt125$block'
             '$wtContent$LT_BPI_Patterns_wtFormFiltroPattern$block$wtForm$LT_BPI_Patterns_wt111$block'
             '$wtRow$LT_BPI_Patterns_wt92$block$wtInput$wttxtMontanteSup',
             ''),
            ('LT_BPINetEmpresas_wt37$block$wtMainContent$CW_Contas_Empresas_wtMovimentos$block$WebPatterns_wt125$block'
             '$wtContent$LT_BPI_Patterns_wtFormFiltroPattern$block$wtForm$LT_BPI_Patterns_wt103$block'
             '$wtRow$LT_BPI_Patterns_wt73$block$wtInput$wttxtDataInicio',
             date_to_param),
            ('LT_BPINetEmpresas_wt37$block$wtMainContent$CW_Contas_Empresas_wtMovimentos$block$WebPatterns_wt125$block'
             '$wtContent$LT_BPI_Patterns_wtFormFiltroPattern$block$wtForm$LT_BPI_Patterns_wt103$block'
             '$wtRow$LT_BPI_Patterns_wt73$block$wtInput$wttxtDataFim',
             date_to_param),
            ('LT_BPINetEmpresas_wt37$block$wtMainContent$CW_Contas_Empresas_wtMovimentos$block$WebPatterns_wt125$block'
             '$wtContent$LT_BPI_Patterns_wtFormFiltroPattern$block$wtForm$LT_BPI_Patterns_wt66$block'
             '$wtRow$LT_BPI_Patterns_wt55$block$wtInput$wt98',
             'todos'),
            ('__AJAX',
             '1259,845,LT_BPINetEmpresas_wt37_block_wtContext_CW_NETEmp_Comum_wtEmpresasContas_block'
             '_LT_BPI_Patterns_wt3_block_wtAccountValue_wtcbListaContas,150,285,0,0,0,0,'),
            ('__AJAXEVENT', 'Change')  # !!!
        ])

        resp_selected_acc = s.post(
            '{}?_ts={}'.format(req_movs_url, int(time.time() * 1000)),
            data=req_select_acc_params,
            headers=self.basic_req_headers_updated({
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://bpinetempresas.bancobpi.pt/NetEmp_Contas_DO/Movimentos.aspx'
            }),
            proxies=self.req_proxies,
            timeout=60
        )

        # account_selected_req_param = parse_helpers.get_selected_account_req_param(resp_changed_acc.text)
        if 'LT_BPINetEmpresas_wt37_block_wtMainContent_wtNoMovements' not in resp_selected_acc.text:
            self.basic_log_wrong_layout(
                resp_selected_acc,
                "Can't select account {}. Skip".format(acc_for_movs)
            )
            return False, resp_selected_acc

        return True, resp_selected_acc

    def process_account(self,
                        s: MySession,
                        org_title: str,
                        account_scraped: AccountScraped,
                        acc_ix: int) -> bool:
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        req_movs_url = 'https://bpinetempresas.bancobpi.pt/NetEmp_Contas_DO/Movimentos.aspx'
        resp_movs_w_filter = s.get(
            req_movs_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        org_param = parse_helpers.get_org_param_for_movs(resp_movs_w_filter.text)
        # Filter by title to handle different order of accounts
        # from different views
        acc_for_movs = [
            a for a in parse_helpers.get_accounts_for_movs(resp_movs_w_filter.text)
            if account_scraped.AccountNo in a.title
        ][0]

        req_movs_params = OrderedDict([
            ('__EVENTTARGET', ''),  # dyn
            ('__EVENTARGUMENT', ''),
            ('__OSVSTATE', ''),  # dyn
            ('__VIEWSTATE', ''),
            ('__VIEWSTATEGENERATOR', parse_helpers.get_viewstategenerator_param(resp_movs_w_filter.text)),  # '8BD0E57F'
            ('LT_BPINetEmpresas_wt37$block$wtContext$CW_NETEmp_Comum_wtEmpresasContas$block'
             '$LT_BPI_Patterns_wt9$block$wtAccountValue$wtcbListaEmpresas',
             org_param),  # '164903206'
            ('LT_BPINetEmpresas_wt37$block$wtContext$CW_NETEmp_Comum_wtEmpresasContas$block'
             '$LT_BPI_Patterns_wt3$block$wtAccountValue$wtcbListaContas',
             acc_for_movs.req_param),  # '286972080'
            ('LT_BPINetEmpresas_wt37_block_wtMainContent_CW_Contas_Empresas_wtMovimentos_block$1103974314',
             'Todos'),
            ('LT_BPINetEmpresas_wt37$block$wtMainContent$CW_Contas_Empresas_wtMovimentos$block'
             '$WebPatterns_wt125$block$wtContent$LT_BPI_Patterns_wtFormFiltroPattern$block$wtForm'
             '$LT_BPI_Patterns_wt111$block$wtRow$LT_BPI_Patterns_wt92$block$wtInput$wttxtMontanteInf',
             ''),
            ('LT_BPINetEmpresas_wt37$block$wtMainContent$CW_Contas_Empresas_wtMovimentos$block'
             '$WebPatterns_wt125$block$wtContent$LT_BPI_Patterns_wtFormFiltroPattern$block$wtForm'
             '$LT_BPI_Patterns_wt111$block$wtRow$LT_BPI_Patterns_wt92$block$wtInput$wttxtMontanteSup',
             ''),
            ('LT_BPINetEmpresas_wt37$block$wtMainContent$CW_Contas_Empresas_wtMovimentos$block'
             '$WebPatterns_wt125$block$wtContent$LT_BPI_Patterns_wtFormFiltroPattern$block$wtForm'
             '$LT_BPI_Patterns_wt103$block$wtRow$LT_BPI_Patterns_wt73$block$wtInput$wttxtDataInicio',
             date_from_str.replace('/', '-')),  # '01-04-2021'
            ('LT_BPINetEmpresas_wt37$block$wtMainContent$CW_Contas_Empresas_wtMovimentos$block'
             '$WebPatterns_wt125$block$wtContent$LT_BPI_Patterns_wtFormFiltroPattern$block$wtForm'
             '$LT_BPI_Patterns_wt103$block$wtRow$LT_BPI_Patterns_wt73$block$wtInput$wttxtDataFim',
             self.date_to_str.replace('/', '-')),  # '01-05-2021'
            ('LT_BPINetEmpresas_wt37$block$wtMainContent$CW_Contas_Empresas_wtMovimentos$block'
             '$WebPatterns_wt125$block$wtContent$LT_BPI_Patterns_wtFormFiltroPattern$block'
             '$wtForm$LT_BPI_Patterns_wt66$block$wtRow$LT_BPI_Patterns_wt55$block$wtInput$wt98',
             'todos'),
            ('__AJAX', '')  # dyn
        ])

        movements_parsed_desc = []  # type: List[MovementParsed]
        resp_movs_prev = resp_movs_w_filter

        if acc_ix > 0:
            ok, resp_movs_prev = self._select_account(s, resp_movs_w_filter, account_scraped)
            if not ok:
                return False

        # Avoid inf loop
        for page_ix in range(1, 101):
            self.logger.info("{}: {}: get page #{} with movements".format(
                org_title,
                fin_ent_account_id,
                page_ix
            ))

            osvstate_param = (
                # 1st acc 1st page
                    parse_helpers.get_osvstate_param(resp_movs_prev.text) or
                    # other accs 1st pages
                    parse_helpers.get_osvstate_param_selected_account(resp_movs_prev.text) or
                    # any acc pagination
                    parse_helpers.get_osvstate_param_pagination(resp_movs_prev.text)
            )

            req_movs_params['__OSVSTATE'] = osvstate_param

            eventtarget_param = (
                parse_helpers.get_eventtarget_param__filter(resp_movs_prev.text)
                if page_ix == 1
                else parse_helpers.get_eventtarget_param__seemore(resp_movs_prev.text)
            )

            if not eventtarget_param:
                self.basic_log_wrong_layout(
                    resp_movs_prev,
                    "{}: can't extract eventtarget_param. Abort".format(fin_ent_account_id)
                )
                return False

            req_movs_params['__EVENTTARGET'] = eventtarget_param

            ajax_param_raw = (
                parse_helpers.get_ajax_param__filter(resp_movs_prev.text)
                if page_ix == 1
                else parse_helpers.get_ajax_param__seemore(resp_movs_prev.text)
            )

            if not ajax_param_raw:
                self.basic_log_wrong_layout(
                    resp_movs_prev,
                    "{}: can't extract ajax_param_raw. Abort".format(fin_ent_account_id)
                )
                return False

            ajax_param = '1323,1186,{},509,719,285,0,739,523,'.format(ajax_param_raw)
            req_movs_params['__AJAX'] = ajax_param

            resp_movs_i = s.post(
                '{}?_ts={}'.format(req_movs_url, int(time.time() * 1000)),
                data=req_movs_params,
                headers=self.basic_req_headers_updated({
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': 'https://bpinetempresas.bancobpi.pt/NetEmp_Contas_DO/Movimentos.aspx'
                }),
                proxies=self.req_proxies,
                timeout=60
            )

            movements_parsed_i = parse_helpers.get_movements_parsed(resp_movs_i.text)
            # Handle both cases:
            # 1. if each page contains all previous movements
            # 2. if each page contains only its own movements
            movements_parsed_i_uniq = list_funcs.uniq_tail(movements_parsed_desc, movements_parsed_i)
            movements_parsed_desc.extend(movements_parsed_i_uniq)

            if ('Ver Mais' not in resp_movs_i.text) and ('See More' not in resp_movs_i.text):
                self.logger.info('{}: no more pages with movements'.format(fin_ent_account_id))
                break

            if (('Ver Mais' in resp_movs_i.text) or ('See More' in resp_movs_i.text)) and not movements_parsed_i:
                self.basic_log_wrong_layout(resp_movs_i, "{}: page# {}: can't get movements_parsed_i".format(
                    fin_ent_account_id,
                    page_ix
                ))
                break

            # Prepare next iter
            resp_movs_prev = resp_movs_i

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
