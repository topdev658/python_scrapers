from collections import OrderedDict
from typing import List, Tuple

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import AccountScraped, ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.bbva_continental_scraper import parse_helpers

__version__ = '1.5.0'

__changelog__ = """
1.5.0
call basic_upload_movements_scraped with date_from_str
1.4.0
skip inactive accounts
1.3.0
use basic_new_session
upd type hints
1.2.0
changed basic url to bbvanetcash.pe
use basic_get_date_from
1.1.0
parse_helpes: get_movements_parsed_from_excel_html:
    use 'Saldo Final' from the excel sheet to sync temp_balance for each date
1.0.0
init
"""


class BBVAContinentalScraper(BasicScraper):
    scraper_name = 'BBVAContinentalScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.update_inactive_accounts = False

    def login(self) -> Tuple[MySession, Response, bool, bool]:
        # Similar with bbva_netcash login method

        s = self.basic_new_session()
        resp_init = s.get(
            'https://www.bbvanetcash.pe/KDPOSolicitarCredenciales_es.html',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        eai_code = '0081' if self.username[0] == '0' else '0001'

        username_upper = self.username.upper()
        username_second_upper = self.username_second.upper()

        req_login_params = OrderedDict([
            ('origen', 'pibee'),
            ('valor', ''),
            ('cod_emp', username_upper),
            ('cod_emp_aux', ''),
            ('cod_usu', username_second_upper),
            ('cod_usu_aux', ''),
            ('eai_password', self.userpass.upper()[:8]),
            ('idioma', 'CAS'),
            ('eai_user', '0026' + eai_code + username_upper + username_second_upper),
            ('eai_URLDestino',
             '/FWPIBEE/kdpo_mult_web/servlet/PIBEE?OPERACION=INICIO_PORTAL&LOCALE=es_PE'),
        ])

        req_login_url = 'https://www.bbvanetcash.pe/DFAUTH/slod_pe_web/DFServlet'
        resp_logged_in = s.post(
            req_login_url,
            data=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = 'kyop-menuBasicItem' in resp_logged_in.text
        is_credentials_error = 'EAI0000' in resp_logged_in.text

        return s, resp_logged_in, is_logged, is_credentials_error

    def process_contract(self, s: MySession) -> bool:

        self.logger.info('Process contract')

        req_position_global_url = ('https://www.bbvanetcash.pe/SPECNET/'
                                   'cent6_pe_web/servlet/PIBEE?proceso=posicion_global_prUX'
                                   '&operacion=posicion_global_opUX&accion=menuPosicion')

        req_position_global_params = OrderedDict([
            ('pb_cod_prod', '007'),
            ('pb_cod_serv', '3300'),
            ('pb_cod_proc', '87000000'),
            ('LOCALE', 'es_PE'),
            ('pb_cod_ffecha', 'dd/MM/yyyy'),
            ('pb_cod_fimporte', '0,000.00'),
            ('pb_husohora', '(GMT-05,00)'),
            ('pb_xti_comprper', 'S'),
            ('pb_url', ' ?proceso=posicion_global_prUX'
                       '&operacion=posicion_global_opUX&accion=menuPosicion'),
            ('pb_segmento', '30'),
            ('xtiTipoProd', 'C'),
            ('pb_isPortalKyop', 'true'),
            ('cod_emp', self.username.upper()),
            ('pb_cod_prod_p', '007'),
            ('kyop-process-id', ''),
        ])

        resp_position_global = s.post(
            req_position_global_url,
            data=req_position_global_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_parsed = parse_helpers.get_accounts_parsed(resp_position_global.text)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                account_parsed['organization_title'],
                account_parsed,
                country_code=account_parsed['country_code'],
                account_no_format=account_parsed['account_no_format']
            )
            for account_parsed in accounts_parsed
        ]

        # It's ok that there are dropdown ids without corresponding
        # account_scraped -those ids just point to inactive accounts
        s, accs_and_dropdown_ids = self.get_accounts_dropdown_ids(s, accounts_scraped)
        if len(accs_and_dropdown_ids) != len(accounts_scraped):
            self.logger.error("Can't extract movements of all accounts: "
                              "len(accs_and_dropdown_ids) != len(accounts_scraped):"
                              "pls, fix the scraper")

        self.logger.info('Got accounts: {}'.format(accounts_scraped))
        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET ACCOUNTS')

        # TO SUPPORT CONCURRENT SCRAPING
        # NEED TO RE-LOGIN and PROVIDE INITIAL STEPS
        # FOR EACH ACCOUNT
        # DELAYED NOW

        # if len(accs_and_dropdown_ids) > 0:
        #     if project_settings.IS_CONCURRENT_SCRAPING:
        #         with futures.ThreadPoolExecutor(max_workers=16) as executor:
        #
        #             futures_dict = {
        #                 executor.submit(self.process_account, s, account_scraped, acc_dropdown_id):
        #                     account_scraped.FinancialEntityAccountId
        #                 for account_scraped, acc_dropdown_id in accs_and_dropdown_ids
        #             }
        #
        #             self.logger.log_futures_exc('process_account', futures_dict)
        #     else:
        #         for account_scraped, acc_dropdown_id in accs_and_dropdown_ids:
        #             self.process_account(s, account_scraped, acc_dropdown_id)

        for account_scraped, acc_dropdown_id in accs_and_dropdown_ids:
            self.process_account(s, account_scraped, acc_dropdown_id)

        return True

    def get_accounts_dropdown_ids(
            self,
            s: MySession,
            accounts_scraped: List[AccountScraped]) -> Tuple[MySession, List[Tuple[AccountScraped, str]]]:
        self.logger.info("Extract accounts' dropdown ids to use as mov req params")

        req_movements_history_url = ('https://www.bbvanetcash.pe/SPETLCL/'
                                     'tlcl_pe_web/servlet/PIBEE?'
                                     'proceso=tlcl_sym_histmov_pr_multipais'
                                     '&operacion=tlcl_sym_hmconfigurarseleccion_op_multipais'
                                     '&accion=consultar')

        req_movements_history_params = OrderedDict([
            ('pb_cod_prod', '007'),
            ('pb_cod_serv', '8700'),
            ('pb_cod_proc', '89990059'),
            ('LOCALE', 'es_PE'),
            ('pb_cod_ffecha', 'dd/MM/yyyy'),
            ('pb_cod_fimporte', '0,000.00'),
            ('pb_husohora', '(GMT-05:00)'),
            ('pb_xti_comprper', 'N'),
            ('pb_url', 'OperacionCBTFServlet?proceso=tlcl_sym_histmov_pr_multipais'
                       '&operacion=tlcl_sym_hmconfigurarseleccion_op_multipais&accion=consultar'),

            ('pb_segmento', '30'),
            ('xtiTipoProd', 'C'),
            ('pb_isPortalKyop', 'true'),
            ('cod_emp', self.username.upper()),
            ('pb_cod_prod_p', '007'),
            ('kyop-process-id', ''),
        ])

        resp_movements_history = s.post(
            req_movements_history_url,
            data=req_movements_history_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accs_and_dropdown_ids = parse_helpers.get_dropdown_ids(resp_movements_history.text,
                                                               accounts_scraped)
        return s, accs_and_dropdown_ids

    def process_account(self,
                        s: MySession,
                        account_scraped: AccountScraped,
                        account_dropdown_id: str) -> bool:

        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        # 1@PEN00110194870100051245 -> 1, 12#PEN00110194870100051245 -> 12
        acc_req_ix = extract.re_first_or_blank(r'\d+', account_dropdown_id)

        req_movs_url = ('https://www.bbvanetcash.pe/SPETLCL/'
                        'tlcl_pe_web/servlet/OperacionCBTFServlet'
                        '?proceso=tlcl_sym_histmov_pr_multipais'
                        '&operacion=tlcl_sym_hmhistoricomovimientos_op_multipais'
                        '&accion=consultar')  # &numOPRequest=8

        req_movs_params = OrderedDict([
            ('numeroCuenta', '0'),
            ('numeroPagina', '0'),
            ('totalPaginas', '0'),
            ('listaAsuntos', '{}#'.format(acc_req_ix)),
            ('numeroAsuntos', '1'),
            ('indiceCodigoOperacionCompleto', ''),
            ('diasAnterioresOK', ''),
            ('codigoOperacion', '-1'),
            ('cBanc', ''),
            ('cOfic', ''),
            ('cCont', ''),
            ('cFoli', ''),
            ('listaCuentas', account_dropdown_id),  # '1@PEN00110194870100051245'
            ('diasAnteriores', '-1'),
            ('op', ''),
            ('fechaDesde', date_from_str.replace('/', '-')),
            ('fechaHasta', self.date_to_str.replace('/', '-')),  # '31-10-2018'
            ('importeDesde', ''),
            ('importeHasta', ''),
            ('codigoOperacionCombo', '-1'),
            ('indiceOrdenacion1', '0'),
            ('indiceOrdenacion2', '2'),
        ])

        resp_movs = s.post(
            req_movs_url,
            data=req_movs_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        if account_scraped.FinancialEntityAccountId.replace('-', '')[-10:] not in resp_movs.text:
            self.logger.error(
                "{}: expected, but didn't find FinancialEntityAccountId digits at the page. "
                "Skip movements scraping. Check the layout:"
                "\nRESPONSE:\n{}".format(
                    account_scraped.FinancialEntityAccountId,
                    resp_movs.text
                )
            )
            return False

        req_movs_excel_url_ix = parse_helpers.get_req_mov_excel_idx(resp_movs.text)
        if req_movs_excel_url_ix == -1:
            self.logger.error(
                "{}: can't extract req_movs_excel_url. Skip movements scraping. Check the layout:"
                "\nRESPONSE:\n{}".format(
                    account_scraped.FinancialEntityAccountId,
                    resp_movs.text
                )
            )
            return False

        req_movs_excel_url = ('https://www.bbvanetcash.pe/SPETLCL/'
                              'tlcl_pe_web/servlet/'
                              'OperacionCBTFServlet'
                              '?proceso=tlcl_sym_histmov_pr_multipais'
                              '&operacion=tlcl_sym_hmhistoricomovimientos_op_multipais'
                              '&accion=verExcel'
                              '&numOPRequest={}'.format(req_movs_excel_url_ix))

        req_movs_excel_headers = self.basic_req_headers_updated({
            'Referer': req_movs_url,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        resp_movs_excel = s.get(
            req_movs_excel_url,
            headers=req_movs_excel_headers,
            proxies=self.req_proxies
        )

        movements_parsed = parse_helpers.get_movements_parsed_from_excel_html(
            resp_movs_excel.text,
            account_scraped.Balance
        )

        movements_scraped, movements_parsed_corresponding = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
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
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url,
                                                                      resp_logged_in.text)

        self.process_contract(s)
        self.basic_log_time_spent('GET MOVEMENTS')

        return self.basic_result_success()
