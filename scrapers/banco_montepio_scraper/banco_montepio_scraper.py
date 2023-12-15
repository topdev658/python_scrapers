import datetime
import random
import time
import traceback
import urllib.parse
from collections import OrderedDict
from typing import List, Tuple, Optional

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings, result_codes
from project.custom_types import (
    AccountScraped, MOVEMENTS_ORDERING_TYPE_ASC,
    MovementParsed, ScraperParamsCommon, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_OTP
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.banco_montepio_scraper import parse_helpers
from .custom_types import ReqAccParams

__version__ = '1.13.0'

__changelog__ = """
1.13.0
parse_helpers: get_digits_to_codes: new layout
login: detect CAPTCHA reason (captcha handler is not implemented)
1.12.2
returning DOUBLE_AUTH_REQUIRED_TYPE_OTP
1.12.1
reason = 'DOUBLE AUTH ...' to align with other similar reasons
1.12.0
login: added 2fa detection based on LOGIN_W_STRONG_AUTHENTICATION_MARKER
1.11.0
use account-level result_codes
1.10.0
call basic_upload_movements_scraped with date_from_str
1.9.0
MAX_MOVS_REACHED_MARKER
_open_movs_filtered: upd 'max movs' detector 
1.8.0
skip inactive accounts
1.7.0
_open_movs_filtered: upd reqs
1.6.0
login: better 'is_logged' detector
_open_movs_filtered: handle changed req
1.5.0
login: check for restricted permissions
1.4.0
_get_movements_parsed: str req params
1.3.0
use basic_new_session
1.2.1
upd type hints
1.2.0
_get_account_scraped: handle exception if it occurs and report with details
1.1.0
scrape more than 200 movements day by day if reached the 200 movs limit in period
1.0.0
init
"""

# Need to split interval if the limit was reached
MAX_MOVS_IN_INTERVAL = 200
# Handle if got 200 movs limit
# O RESULTADO DA SUA PESQUISA É SUPERIOR A 207 MOVIMENTOS.
# POR FAVOR, REDUZA OS CRITÉRIOS DE PESQUISA OU SELECIONE A OPÇÃO
# DE DOWNLOAD DE MOVIMENTOS NO MENU LATERAL ESQUERDO.
MAX_MOVS_REACHED_MARKER = 'POR FAVOR, REDUZA OS CRITÉRIOS DE PESQUISA OU SELECIONE A OPÇÃO'
LOGIN_W_STRONG_AUTHENTICATION_MARKER = 'Login com Autenticação Forte'
CAPTCHA_MARKER = 'Falha na validação do Captcha'

class BancoMontepioScraper(BasicScraper):
    """The scraper supports only 1 (ONE)
    account of an access (bcs there were no examples with several accounts)
    """

    scraper_name = 'BancoMontepioScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.update_inactive_accounts = False
        self.req_headers = self.basic_req_headers_updated({
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0'
        })

    def _get_encrypted(self, resp_pass_form: Response) -> str:
        digits_to_codes = parse_helpers.get_digits_to_codes(resp_pass_form.text)
        encrypted = ''
        for digit in self.userpass:
            encrypted += digits_to_codes[digit]
        return encrypted

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()

        resp_init = s.get(
            'https://www.bancomontepio.pt/empresas',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_pass_form = OrderedDict([
            ("loginid_IN", self.username),
            ("cert", "on")
        ])
        resp_pass_form = s.post(
            'https://net24.bancomontepio.pt/Net24-Web/func/acesso/net24eLoginTV.jsp',
            data=req_pass_form,
            headers=self.basic_req_headers_updated({'Referer': resp_init.url}),
            proxies=self.req_proxies
        )

        time.sleep(0.5 + random.random() * 0.5)

        req_login_action_link, req_login_params = extract.build_req_params_from_form_html_patched(
            resp_pass_form.text,
            form_name="formDados"  # pinForm
        )
        req_login_params.update({
            "pin1_IN": self._get_encrypted(resp_pass_form),
            # TODO: VB: this is an example, MUST BE implemented
            'fp': '26aa5ee5da70b9021ba0b35c46601800',  # browser fingerprint
            # 03AGdBq243VH00...IyH7RPII
            'recaptchaResponse': ''
        })

        resp_logged_in = s.post(
            urllib.parse.urljoin(resp_pass_form.url, req_login_action_link),
            data=req_login_params,
            headers=self.basic_req_headers_updated({'Referer': resp_pass_form.url}),
            proxies=self.req_proxies
        )

        is_logged = resp_logged_in.url in [
            'https://net24.bancomontepio.pt/Net24-Web/func/homePages/pagInic.jsp',
            'https://net24.bancomontepio.pt/Net24-Web/func/contasordem/posicaoIntegrada.jsp'
        ]
        is_credentials_error = 'ACESSO INCORRECTO' in resp_logged_in.text
        reason = ''

        if LOGIN_W_STRONG_AUTHENTICATION_MARKER in resp_logged_in.text:
            reason = DOUBLE_AUTH_REQUIRED_TYPE_OTP
        if 'error' in resp_logged_in.url and CAPTCHA_MARKER in resp_logged_in.text:
            reason = 'CAPTCHA validation required'

        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        """Only 1 (ONE) account supported"""

        resp_accounts_dropdown = s.get(
            'https://net24.bancomontepio.pt/Net24-Web/func/contasordem/consultaNIBIBAN.jsp?selectedNode=6006',
            headers=self.basic_req_headers_updated({'Referer': resp_logged_in.url}),
            proxies=self.req_proxies
        )

        # balance will be extracted after the filter by dates
        account_dict = parse_helpers.get_account_parsed_only_fid_iban(
            resp_accounts_dropdown.text
        )

        self.process_account(s, resp_accounts_dropdown, account_dict)

        return True

    def _open_movs_filtered(self, s: MySession,
                            referer_url: str,
                            fin_ent_account_id: str,
                            date_from_str: str,
                            date_to_str: str) -> Tuple[bool, MySession, Response]:
        """Filters movements,
        detects MAX_MOVS_REACHED_MARKER (if detected the is_success=False)
        :returns (is_success, s, resp)
        """
        # Menu "Movimentos", several steps:
        #   open,
        #   select account,
        #   filter by dates

        # TODO add optimization: no need to open resp_movs_select_account_page
        #  if already filtered movements before
        #  check the web: use GET for resp_movs_filtered
        resp_movs_select_account_page = s.get(
            'https://net24.bancomontepio.pt/Net24-Web/func/contasordem/ctaOrdemMovimentos.jsp?selectedNode=6004',
            headers=self.basic_req_headers_updated({'Referer': referer_url}),
            proxies=self.req_proxies
        )

        req_acc_params = parse_helpers.get_req_acc_params(fin_ent_account_id)  # type: ReqAccParams

        req_movs_select_account_params = OrderedDict([
            ('numCtaOrdem', req_acc_params.numCtaOrdem),  # '041100367600'
            ('descproduto_IN', req_acc_params.descproduto_IN),  # 'CONTA EMPRESAS'
            ('tipoPesquisa', ''),
            # '041100367600|041.10.036760-0 CONTA EMPRESAS||CONTA EMPRESAS'
            ('seleccaoConta', req_acc_params.seleccaoConta),
        ])

        resp_movs_dates_filter = s.post(
            'https://net24.bancomontepio.pt/Net24-Web/func/contasordem/ctaOrdemMovimentosCriterios.jsp',
            data=req_movs_select_account_params,
            headers=self.basic_req_headers_updated({'Referer': resp_movs_select_account_page.url}),
            proxies=self.req_proxies
        )

        date_to_param = date_funcs.convert_to_ymd(date_to_str)  # "20190822"
        date_from_param = date_funcs.convert_to_ymd(date_from_str)
        target_path = parse_helpers.get_movs_filtered_dest_page(resp_movs_dates_filter.text)
        req_movs_filtering_params = {
            "ddiactf_IN": date_to_param,
            "ddiact_IN": date_from_param,
            "descricaoTipoOperacao": "",
            "tipoPesquisa": "pesquisa",
            "destino": target_path,
            "numCtaOrdem": req_acc_params.numCtaOrdem,
            "descproduto_IN": req_acc_params.descproduto_IN,
            "tipoMovimento": "",
            "seleccaoConta": req_acc_params.seleccaoConta,
            "tipos": "T|Todos",
            "tipoOperacao": "",
            "selMinImp": "D",
            "importMinima": "",
            "selMaxImp": "C",
            "importMaxima": ""
        }

        resp_movs_filtering_confirm = s.post(
            'https://net24.bancomontepio.pt/Net24-Web/func/contasordem/ctaOrdemMovimentosNRegistos.jsp',
            # 'https://net24.bancomontepio.pt/Net24-Web/func/contasordem/ctaOrdemMovimentosValidacao.jsp',
            data=req_movs_filtering_params,
            headers=self.basic_req_headers_updated({'Referer': resp_movs_dates_filter.url}),
            proxies=self.req_proxies
        )

        if MAX_MOVS_REACHED_MARKER in resp_movs_filtering_confirm.text:
            # no need to send wrn/err - it's expected behavior and will be handled
            self.logger.info('{}: MAX_MOVS_REACHED_MARKER detected'.format(fin_ent_account_id))
            return False, s, resp_movs_filtering_confirm

        req_movs_filtered_url = urllib.parse.urljoin(resp_movs_filtering_confirm.url, target_path)
        resp_movs_filtered = s.post(
            req_movs_filtered_url,
            data={},
            headers=self.basic_req_headers_updated({'Referer': resp_movs_filtering_confirm.url}),
            proxies=self.req_proxies
        )

        return True, s, resp_movs_filtered

    def _get_movements_parsed(
            self,
            s: MySession,
            referer_url: str,
            fin_ent_account_id: str,
            date_from_str: str,
            date_to_str: str) -> Tuple[bool, MySession, Response, List[MovementParsed]]:
        """
        If there are > 200 movs during the date interval, is_success will be False

        :returns (is_success, session, resp, movements_parsed)
        """

        ok, s, resp_movs_filtered = self._open_movs_filtered(
            s,
            referer_url,
            fin_ent_account_id,
            date_from_str,
            date_to_str
        )

        if not ok:
            return False, s, resp_movs_filtered, []  # already reported

        date_to_param = date_funcs.convert_to_ymd(date_to_str)  # "20190822"
        date_from_param = date_funcs.convert_to_ymd(date_from_str)

        movements_parsed = []  # type: List[MovementParsed]
        resp_prev = resp_movs_filtered
        for i in range(1, 30):  # 25 mov per page
            self.logger.info('{}: get movements from {}..{} page {}'.format(
                fin_ent_account_id,
                date_from_str,
                date_to_str,
                i
            ))
            movements_parsed_i = parse_helpers.get_movements_parsed(resp_prev.text)
            movements_parsed.extend(movements_parsed_i)

            next_page_ix = parse_helpers.get_next_page_ix(resp_prev.text)
            if not next_page_ix or int(next_page_ix) <= i:
                break

            # Example for page 3
            # {"ddiact_IN":["20190805","20190805"],
            # "ddiactf_IN":["20190824","20190824"],
            # "tipoPesquisa":["pesquisa","pesquisa"],
            # "numCtaOrdem":["041100367600","041100367600"],
            # "backCurrentPageNumber":["2","1"],
            # "backEncodedPagingTable":["eyIzIj...UAhMCFAISJ9","eyIyIjoiMjY3MjY...QCEwIUAhIn0="],
            # "via":["ultimosMovimentos","ultimosMovimentos"],
            # "origem":["",""],
            # "tipoOperacao":"",
            # "importMinima":"",
            # "descproduto_IN":"CONTA+EMPRESAS",
            # "descricaoTipoOperacao":"",
            # "selMaxImp":"C",
            # "tipoMovimento":"",
            # "tipos":"T|Todos",
            # "importMaxima":"",
            # "destino":"ctaOrdemMovimentosResultadoDC57.jsp",
            # "selMinImp":"D",
            # "seleccaoConta":"041100367600|041.10.036760-0+CONTA+EMPRESAS||CONTA+EMPRESAS",
            # "encodedPagingTable":"eyIzIjoiM...iIwIUAhMCFAISJ9",
            # "currentPageNumber":"3",
            # "hasmore":"true"}
            req_link, req_next_params = extract.build_req_params_from_form_html_patched(
                resp_prev.text,
                'formDados'
            )
            req_next_params['ddiact_IN'] = date_from_param
            req_next_params['ddiactf_IN'] = date_to_param
            req_next_params['tipoPesquisa'] = "pesquisa"

            req_next_params['currentPageNumber'] = str(next_page_ix)

            if 'btnVoltar' in req_next_params:
                del req_next_params['btnVoltar']
            if 'btnConsValoresDisp' in req_next_params:
                del req_next_params['btnConsValoresDisp']

            req_next_url = urllib.parse.urljoin(resp_prev.url, req_link)
            resp_next_page = s.post(
                req_next_url,
                data=req_next_params,
                headers=self.basic_req_headers_updated({'Referer': resp_prev.url}),
                proxies=self.req_proxies
            )

            resp_prev = resp_next_page

        return True, s, resp_movs_filtered, movements_parsed

    def _get_account_scraped(
            self,
            s: MySession,
            referer_url: str,
            account_dict: dict,
            date_to_str: str) -> Tuple[bool, MySession, Response, Optional[AccountScraped]]:

        fin_ent_account_id = account_dict['financial_entity_account_id']

        # To get account_scraped
        # need to open recent movements and get details from the page
        # open only movement of last day to avoid 200 movs limit
        ok, s, resp_movs_filtered = self._open_movs_filtered(
            s,
            referer_url,
            fin_ent_account_id,
            date_to_str,  # only last date
            date_to_str
        )
        if not ok:
            self.logger.error("{}: too many movements during the last day. "
                              "Can't open movements and get account details. Abort".format(fin_ent_account_id))
            return False, s, resp_movs_filtered, None
        try:
            account_parsed = parse_helpers.get_account_parsed(resp_movs_filtered.text, account_dict)
        except:
            self.basic_log_wrong_layout(
                resp_movs_filtered,
                "{}: can't get account_parsed. Abort. HANDLED EXCEPTION: {}".format(
                    fin_ent_account_id,
                    traceback.format_exc()
                ))
            return False, s, resp_movs_filtered, None

        account_scraped = self.basic_account_scraped_from_account_parsed(
            account_parsed['organization_title'],
            account_parsed,
            country_code='PRT'
        )
        return True, s, resp_movs_filtered, account_scraped

    def process_account(self,
                        s: MySession,
                        resp_prev: Response,
                        account_dict: dict) -> bool:

        fin_ent_account_id = account_dict['financial_entity_account_id']

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        ok, s, resp_prev, account_scraped = self._get_account_scraped(s, resp_prev.url, account_dict, self.date_to_str)
        if not ok:
            # already reported
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
            return False

        assert account_scraped is not None  # for linters

        self.logger.info('Got account {}'.format(account_scraped))
        self.basic_upload_accounts_scraped([account_scraped])
        self.basic_log_time_spent('GET ACCOUNT')

        # If the website doesn't return more than 200 movements,
        # we scrape them day by day

        # 1. Try to get all movement from ncessary interval
        ok, s, resp_recent, movements_parsed = self._get_movements_parsed(
            s,
            resp_prev.url,
            fin_ent_account_id,
            date_from_str,
            self.date_to_str
        )

        if not ok:
            # 2. Got 200 movs limit? Get movements day by day
            self.logger.info("{}: there are more than {} movs during the period. Reached the limit. "
                             "Extract movements day by day".format(fin_ent_account_id, MAX_MOVS_IN_INTERVAL, ))
            date_from = date_funcs.get_date_from_str(date_from_str)
            movements_parsed = []
            date_from_to = date_from - datetime.timedelta(days=1)
            while date_from_to < self.date_to:
                date_from_to += datetime.timedelta(days=1)
                date_from_to_str = date_funcs.convert_dt_to_scraper_date_type1(date_from_to)
                self.logger.info("{}: get movements from {}".format(
                    fin_ent_account_id,
                    date_from_to_str
                ))
                ok, s, resp_prev, movements_parsed_day_i = self._get_movements_parsed(
                    s,
                    resp_prev.url,
                    fin_ent_account_id,
                    date_from_to_str,
                    date_from_to_str
                )
                if not ok:
                    self.logger.error("{}: can't get movement even with day by day filter. Skip. "
                                      "RESPONSE:\n{}".format(fin_ent_account_id, resp_prev.text))
                    self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_BREAKING_CONDITIONS)
                    return False
                movements_parsed.extend(movements_parsed_day_i)

        should_scrape_ext_descr = self.basic_should_scrape_extended_descriptions()
        movements_parsed_w_extra_details = movements_parsed
        if should_scrape_ext_descr:
            # Will scrape extended descriptions only for new movements without
            # further re-scraping (all details appear initially)
            movements_parsed_w_extra_details = self.basic_get_movements_parsed_w_extra_details(
                s,
                movements_parsed,
                account_scraped,
                date_from_str,
                n_mov_details_workers=4,
            )

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_w_extra_details,
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

    def process_movement(self,
                         s: MySession,
                         movement_parsed: MovementParsed,
                         fin_ent_account_id: str,
                         meta: Optional[dict]) -> MovementParsed:
        """Will be called for each movement by self.basic_get_movements_parsed_w_extra_details()"""

        # no details, return as is
        if not movement_parsed['has_extra_details']:
            return movement_parsed

        self.logger.info('{}: process movement: {}'.format(
            fin_ent_account_id,
            self.basic_mov_parsed_str(movement_parsed)
        ))

        req_details_params = OrderedDict([
            ('zmovcta', movement_parsed['id']),  # 26761
            ('numCtaOrdem', parse_helpers.get_numcta_ordem_param(fin_ent_account_id)),  # '041100367600'
        ])

        resp_details = s.post(
            'https://net24.bancomontepio.pt/Net24-Web/func/contasordem/detalheMovimento.jsp',
            data=req_details_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        description_extended = parse_helpers.get_description_extended(resp_details.text, movement_parsed)

        movement_parsed_extra_details = movement_parsed.copy()
        movement_parsed_extra_details['description_extended'] = description_extended

        return movement_parsed_extra_details

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged_in, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged_in:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        self.process_access(s, resp_logged_in)

        self.basic_log_time_spent("GET MOVEMENTS")
        return self.basic_result_success()
