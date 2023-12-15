import random
import threading
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    AccountParsed, AccountScraped,
    MovementParsed, ScraperParamsCommon, MainResult
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.caixa_geral_depositos import parse_helpers

__version__ = '2.3.0'

__changelog__ = """
2.3.0
call basic_upload_movements_scraped with date_from_str
2.2.0
skip inactive accounts
2.1.0
use basic_new_session
upd type hints
2.0.0
incremental scraping: early stop by basic_get_oper_date_position_start  
1.1.0
parse_helpers: get_movements_parsed_from_tsv: skip title row
1.0.0
init
"""

MOVS_RESCRAPE_OFFSET = 2  # 2 days because got more than 4500 movs during 15 days
MAX_MOVS_PER_PAGE = 65
MOVS_PER_BATCH_FOR_EXT_DESCR = 65  # 65 because it should <1 min per request (>65 may take >1 min)


def _split_list(l, n) -> List[list]:
    """Split list to lists by number of items per batch"""
    ll = []
    while True:
        if len(l) > n:
            ll.append(l[:n])
            l = l[n:]
        else:
            ll.append(l)
            break
    return ll


class CaixaGeralDepositosScraper(BasicScraper):
    """
    Many sessions not allowed
    Only serial processing of accounts is possible
    """

    scraper_name = 'CaixaGeralDepositosScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.lock = threading.Lock()
        self.update_inactive_accounts = False

    def login(self) -> Tuple[MySession, Response, bool, bool]:

        s = self.basic_new_session()
        resp_init = s.get(
            'https://www.cgd.pt/Empresas/Pages/Empresas_V2.aspx',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_login_1st_step_data = {
            'USERNAME': self.username,
            'login_btn_2': 'OK'
        }
        # if there is an active session, then this step fails
        resp_login_1st_step = s.post(
            'https://caixaebankingonline.cgd.pt/ceb/login.seam',
            data=req_login_1st_step_data,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20
        )

        if 'Código de utilizador' not in resp_login_1st_step.text:
            self.logger.error("Can't log in. Active session detected. Abort")
            return s, resp_login_1st_step, False, False

        req_login_data = {
            "target": "/ceb/private/home.seam",
            "username": "CEB{}_{}".format(self.username, self.username_second),
            "compInput": self.username,  # 774..508
            "userInput": self.username_second,  # "269..11"
            "passwordInput": "******",
            "loginForm:submit": "Entrar",
            "password": self.userpass  # "20..12"
        }
        resp_logged_in = s.post(
            'https://caixaebankingonline.cgd.pt/ceb/auth/forms/login.fcc?channel=CEB',
            data=req_login_data,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20
        )

        # or Últimos acessos
        is_logged = 'Sair' in resp_logged_in.text
        is_credentials_error = 'Autenticação incorrecta' in resp_logged_in.text

        return s, resp_logged_in, is_logged, is_credentials_error

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:

        # 1. open 'Total à ordem' to get acc_ids and balances
        resp_accounts_total = s.get(
            'https://caixaebankingonline.cgd.pt/ceb/private/contasaordem/consultaTotalOrdem.seam',
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20,
        )

        accounts_parsed_wo_iban = parse_helpers.get_accounts_wo_iban_parsed(resp_accounts_total.text)

        # 2. for each account open 'IBAN e BIC SWIFT' to get IBAN
        req_account_iban_url = 'https://caixaebankingonline.cgd.pt/ceb/private/contasaordem/consultaNibIban.seam'

        # 2.1 default page with dropdown of accounts
        # need to open each time or fails
        resp_iban_dropdown = s.get(
            req_account_iban_url,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20,
        )

        accounts_parsed = []  # type: List[AccountParsed]
        resp_prev = resp_iban_dropdown
        # get IBANs for other accounts
        for acc_wo_iban in accounts_parsed_wo_iban:
            self.logger.info("{}: fetch IBAN".format(acc_wo_iban['financial_entity_account_id']))
            view_state_param = parse_helpers.get_view_state_param(resp_prev.text)
            req_account_iban_params = OrderedDict([
                ('consultaNibIban', 'consultaNibIban'),
                ('consultaNibIban_downloadPDF_downloadId', ''),
                ('consultaNibIban_downloadTSV_downloadId', ''),
                ('consultaNibIban_downloadCSV_downloadId', ''),
                # 'PT+00350127057193730EUR0' in browser == 'PT 00350127057193730EUR0' here
                # PT+00350127058171130EUR0
                ('consultaNibIban:selectedAccount', acc_wo_iban['select_account_param']),
                # '6795976708711172635:-9030036522942924297'
                ('javax.faces.ViewState', view_state_param),
            ])
            resp_account_iban = s.post(
                req_account_iban_url,
                data=req_account_iban_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
                timeout=20
            )
            account_parsed = parse_helpers.get_account_parsed(resp_account_iban.text, acc_wo_iban)
            accounts_parsed.append(account_parsed)
            resp_prev = resp_account_iban
            time.sleep(0.2 + random.random())

        accounts_scraped = [self.basic_account_scraped_from_account_parsed(
            self.db_customer_name,  # didn't find real organization title
            acc_parsed,
            country_code='PRT',
            is_default_organization=True
        ) for acc_parsed in accounts_parsed]

        self.basic_log_time_spent('GET BALANCE')
        self.logger.info("Got {} account(s) {}".format(len(accounts_scraped), accounts_scraped))
        self.basic_upload_accounts_scraped(accounts_scraped)

        accounts_scraped_dict = self.basic_gen_accounts_scraped_dict(accounts_scraped)

        for account_parsed in accounts_parsed:
            self.process_account(s, account_parsed, accounts_scraped_dict)

        return True

    def _get_movs_parsed_w_details_from_html(
            self,
            s: MySession,
            account_parsed: AccountParsed,
            date_from_str: str,
            req_movs_url: str,
            resp_movs_filtered_html: Response,
            req_movs_params: dict) -> Tuple[List[MovementParsed], int]:
        """When filter by dates - new pages will contain all previous movements

        Extra logic: early stop if got movements_parsed which
                     already in movements_saved using
                     _get_intersection_offset_at_movs_saved
        :return (movements_parsed, oldest_mov_operational_date_position)
        """

        fin_ent_account_id = account_parsed['financial_entity_account_id']

        movs_saved_desc, checksums_saved_desc = self.basic_get_movements_saved_desc_and_checksums(
            fin_ent_account_id,
            date_from_str
        )

        # total filtered movements in period, example: "Número total de registos: 245"
        n_movs_total = parse_helpers.get_total_num_of_movements(resp_movs_filtered_html.text)
        n_pages = n_movs_total // MAX_MOVS_PER_PAGE + 1
        self.logger.info('{}: has total {} movements at {} pages'.format(
            fin_ent_account_id,
            n_movs_total,
            n_pages
        ))

        resp_recent = resp_movs_filtered_html
        oper_date_position_start = 1
        is_found = False
        # 1. Open all movements at one page
        # limit number of iters to avoid inf loop (with padding)
        for page_ix in range(1, n_pages + 5):
            time.sleep(0.2 + 0.1 * random.random())
            self.logger.info('{}: open page {} with new and previous movements'.format(
                fin_ent_account_id,
                page_ix
            ))

            # additional param to be added - this allows to paginate
            movs_next_page_param = parse_helpers.get_next_page_req_param(resp_recent.text)
            if not movs_next_page_param:
                self.logger.info('{}: no more pages with movements. Stop the loop.'.format(
                    fin_ent_account_id,
                ))
                break
            # All movs from prev pages + from the current
            movs_parsed_at_page = parse_helpers.get_movements_parsed(resp_recent.text)
            is_found, oper_date_position_start = self.basic_get_oper_date_position_start(
                fin_ent_account_id,
                movs_parsed_at_page,
                movs_saved_desc,
                checksums_saved_desc,
                MAX_MOVS_PER_PAGE
            )
            if is_found:
                # already informed
                break

            # when 'Consultar mais movimentos +' clicked
            req_movs_next_params = req_movs_params.copy()
            req_movs_next_params['javax.faces.ViewState'] = parse_helpers.get_view_state_param(resp_recent.text)
            req_movs_next_params.update(movs_next_page_param)

            # has also movements from the previous page
            resp_movs_next_page = s.post(
                req_movs_url,
                data=req_movs_next_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
                timeout=120
            )
            resp_recent = resp_movs_next_page

        # without extra details (extended descriptions)
        movements_parsed_desc = parse_helpers.get_movements_parsed(resp_recent.text)
        if len(movements_parsed_desc) != n_movs_total and (not is_found):
            self.logger.warning('{}: got {} movements of total expected {}. Continue as is'.format(
                fin_ent_account_id,
                len(movements_parsed_desc),
                n_movs_total
            ))
        self.logger.info('{}: get extra details of the movements'.format(fin_ent_account_id))

        # 2. Get extra details for batches of movements
        # NOTE: website raises error if it can't handle request in 1 minute.
        #  Request with details takes up to 20 seconds for 1 page (65 movements) and has O(n_movs) by time.
        #  Solution: get details by batches.
        movements_parsed_w_extra_details_desc = []  # type: List[MovementParsed]
        movs_details_params_recent = {}  # type: Dict[str, str]
        # use batches with 130 movs (2 pages) to get details
        movs_batches = _split_list(movements_parsed_desc, MOVS_PER_BATCH_FOR_EXT_DESCR)
        self.logger.info('{} has {} movs_batches'.format(fin_ent_account_id, len(movs_batches)))
        for i, movs_batch in enumerate(movs_batches):
            self.logger.info('{}: get movs_batch {} with extended descriptions'.format(fin_ent_account_id, i + 1))
            req_movs_details_params = req_movs_params.copy()
            req_movs_details_params["javax.faces.ViewState"] = parse_helpers.get_view_state_param(resp_recent.text)
            movs_details_params = {mov['req_details_param_id']: mov['req_details_param_id']
                                   for mov in movs_batch}
            # add additional params to open extra details of selected movements
            req_movs_details_params.update(movs_details_params)
            # also send previous movs_details_params to collapse previous batch
            # (the 1st call w/ details param opens movement details, 2nd call - closes)
            req_movs_details_params.update(movs_details_params_recent)

            resp_movs_details = s.post(
                req_movs_url,
                data=req_movs_details_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
                timeout=300,  # very long response delay, backend failed after 1 min, need to split movs
            )

            movements_parsed_w_extra_det_i = parse_helpers.get_movements_parsed_w_details(
                self.logger,
                fin_ent_account_id,
                movs_batch,
                resp_movs_details.text
            )
            if len(movements_parsed_w_extra_det_i) != len(movs_batch):
                self.logger.error('{}: got {} movements w/ extra details of expected {}. Abort'.format(
                    fin_ent_account_id,
                    len(movements_parsed_desc),
                    n_movs_total
                ))
                break

            movements_parsed_w_extra_details_desc.extend(movements_parsed_w_extra_det_i)
            resp_recent = resp_movs_details
            movs_details_params_recent = movs_details_params

        return movements_parsed_w_extra_details_desc, oper_date_position_start

    # reserved approach
    def _get_movs_parsed_from_tsv(
            self,
            s: MySession,
            req_movs_url: str,
            req_movs_params: dict,
            resp_movs_filtered_html: Response) -> List[MovementParsed]:
        """Call only after applied filter by dates.
        Returns movements_scraped w/o extended descriptions
        (3000 movs at once => max 3000 movs for now)
        """

        view_state_param = parse_helpers.get_view_state_param(resp_movs_filtered_html.text)
        req_movs_params["javax.faces.ViewState"] = view_state_param

        req_movs_params["consultaMovimentos:ignoreFieldsComp"] = "all"  # TSV
        req_movs_params["consultaMovimentos:downloadTSV"] = 'consultaMovimentos:downloadTSV'
        download_id = int(time.time() * 1000)
        req_movs_params["consultaMovimentos_downloadTSV_downloadId"] = (
            'consultaMovimentos_downloadTSV_downloadId{}'.format(download_id)
        )

        resp_movs_filtered_tsv = s.post(
            req_movs_url,
            data=req_movs_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20,
            stream=True,
        )

        # max 3000 movs
        movements_parsed_desc = parse_helpers.get_movements_parsed_from_tsv(resp_movs_filtered_tsv.text)
        return movements_parsed_desc

    def process_account(self,
                        s: MySession,
                        account_parsed: AccountParsed,
                        accounts_scraped_dict: Dict[str, AccountScraped]) -> bool:

        fin_ent_account_id = account_parsed['financial_entity_account_id']
        account_scraped = accounts_scraped_dict[fin_ent_account_id]

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id, rescraping_offset=MOVS_RESCRAPE_OFFSET)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        select_account_param = account_parsed['select_account_param']

        req_movs_url = 'https://caixaebankingonline.cgd.pt/ceb/private/contasaordem/consultaSaldosMovimentos.seam'

        # open 'Saldos e movimentos' to get correct req_rarams
        resp_recent_movs = s.get(
            req_movs_url,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20
        )

        view_state_param = parse_helpers.get_view_state_param(resp_recent_movs.text)
        if not view_state_param:
            self.logger.error(
                "{}: can't parse view_state_param. Skip process_account. RESPONSE:\n{}".format(
                    fin_ent_account_id,
                    resp_recent_movs.text
                )
            )
            return False

        _, req_movs_params = extract.build_req_params_from_form_html_patched(
            resp_recent_movs.text,
            'consultaMovimentos',
            is_ordered=True
        )

        date_from_field, date_to_field = parse_helpers.get_date_fields(resp_recent_movs.text)

        req_movs_params["consultaMovimentos:periodo"] = "SELECTCEB"
        req_movs_params["movementTypesRadio"] = "0"
        req_movs_params["consultaMovimentos:selectedAccount"] = select_account_param
        req_movs_params[date_from_field] = date_from_str.replace("/", "-")
        req_movs_params[date_to_field] = self.date_to_str.replace("/", "-")

        # Delete req params which break the requests (need to delete for further pagination)
        # Expect after this filter like:
        # req_movs_params = OrderedDict([
        #     ('consultaMovimentos', 'consultaMovimentos'),
        #     ('consultaMovimentos:ignoreFieldsComp', ''),
        #     ('consultaMovimentos_downloadPDF_downloadId', ''),
        #     ('consultaMovimentos_downloadTSV_downloadId', ''),
        #     ('consultaMovimentos_downloadCSV_downloadId', ''),
        #     ('consultaMovimentos:selectedAccount', select_account_param),
        #     ('consultaMovimentos:infoEmail', ''),  # SAMPAIO.MARQUES@SMALLWORLDFS.COM
        #     ('consultaMovimentos:periodo', 'SELECTCEB'),
        #     ('consultaMovimentos:kid_j_idt3021_inputField', '18-07-2019'),
        #     ('consultaMovimentos:kid_j_idt3022_inputField', '18-08-2019'),
        #     ('consultaMovimentos:j_idt303_block_Start0', '0'),
        #     ('consultaMovimentos:j_idt303_block_Start1', '00'),
        #     ('consultaMovimentos:j_idt303_block_End0', '0'),
        #     ('consultaMovimentos:j_idt303_block_End1', '00'),
        #     ('movementTypesRadio', '0'),
        #     ('realPrintIndex', ''),
        #     ('javax.faces.ViewState', ''),  # fill later
        # ])
        req_movs_params = OrderedDict([
            (k, v) for k, v in req_movs_params.items()
            if v not in ['Pesquisar', 'Gravar', 'Enviar']
        ])

        # 1st request just switches to 'Selecione periodo' mode
        resp_movs_select_filter_by_period = s.post(
            req_movs_url,
            data=req_movs_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20,
        )

        # 2nd request returns really filtered movements
        req_movs_params["javax.faces.ViewState"] = parse_helpers.get_view_state_param(
            resp_movs_select_filter_by_period.text
        )

        resp_movs_filtered_html = s.post(
            req_movs_url,
            data=req_movs_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20,
        )

        movements_parsed_desc = []  # type: List[MovementParsed]
        oper_date_position_start = 1
        if self.basic_should_scrape_extended_descriptions():
            movements_parsed_desc, oper_date_position_start = self._get_movs_parsed_w_details_from_html(
                s,
                account_parsed,
                date_from_str,
                req_movs_url,
                resp_movs_filtered_html,
                req_movs_params
            )
        else:
            # quick
            movements_parsed_desc = self._get_movs_parsed_from_tsv(
                s,
                req_movs_url,
                req_movs_params,
                resp_movs_filtered_html
            )

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_desc,
            date_from_str,
            operational_date_position_start=oper_date_position_start
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )
        return True

    def logout(self, s: MySession) -> bool:
        resp_logged_out = s.get(
            'https://caixaebankingonline.cgd.pt/ceb/private/logout.seam',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return 'Aguarde, por favor' in resp_logged_out.text

    def main(self) -> MainResult:

        s = None  # type: Optional[MySession]
        resp_logged_in = None  # type: Optional[Response]
        is_logged_in = False
        try:
            s, resp_logged_in, is_logged_in, is_credentials_error = self.login()

            if is_credentials_error:
                return self.basic_result_credentials_error()

            if not is_logged_in:
                return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url,
                                                                          resp_logged_in.text)
            self.process_access(s, resp_logged_in)
        finally:
            if (s is not None) and is_logged_in:
                self.logout(s)

        self.basic_log_time_spent("GET MOVEMENTS")
        return self.basic_result_success()
