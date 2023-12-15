import os
import random
import subprocess
import time
import urllib.parse
from collections import OrderedDict
from datetime import datetime
from typing import Tuple, List, Optional

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import list_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    ScraperParamsCommon, MovementParsed, MovementScraped, MainResult,
    MOVEMENTS_ORDERING_TYPE_ASC, ACCOUNT_NO_TYPE_UNKNOWN
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.bradesco_scraper import parse_helpers
from scrapers.bradesco_scraper.custom_types import AccountToFilter

__version__ = '1.11.0'

__changelog__ = """
1.11.0
Reverted CUSTOM_DATE_TO_OFFSET
1.10.0
CUSTOM_DATE_TO_OFFSET
1.9.0
process_account: use join_uniq_tail to avoid duplicates in movs
use renamed list_funcs
1.8.0
improve stability:
  sleep: longer delays
  process_account: 
    increased N_ATTEMPTS_TO_PROCESS_ACCOUNT
    longer timeouts for mov reqs
1.7.0
use account-level result_codes
1.6.0
call basic_upload_movements_scraped with date_from_str
1.5.0
process_account: upd req params, pagination
1.4.0
skip inactive accounts
1.3.0
sleep before each request to avoid proxy be banned
1.2.0
use basic_new_session
upd type hints
1.1.0
parse_helpers: get_account_parsed: check for correct balance_str to avoid exceptions
process_account:
  try to get account_parsed several times 
  more precise warn and err reports
N_ATTEMPTS_TO_PROCESS_ACCOUNT
1.0.0
"""

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'bradesco_encrypter.js'
))

# Used in proocess_account loop to handle wrong resp_evt
# or absent details for account_parsed
N_ATTEMPTS_TO_PROCESS_ACCOUNT = 5

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'

# days_before_today
# CUSTOM_DATE_TO_OFFSET = 3


class BradescoScraper(BasicScraper):
    scraper_name = 'BradescoScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        # self.req_headers = {'User-Agent': UA}
        self.update_inactive_accounts = False
        self.req_proxies = self.req_proxies[:1]
        # Set custom date_to
        # self.date_to, self.date_to_str = self.custom_date_to()

    # def custom_date_to(self) -> Tuple[datetime, str]:
    #   """:returns (date_to, date_to_str)"""
    #   offset = CUSTOM_DATE_TO_OFFSET
    #   if offset == 0:
    #       return self.date_to, self.date_to_str
    #   date_to = min(self.date_to, date_funcs.today() - timedelta(days=offset))
    #   date_to_str = date_to.strftime(project_settings.SCRAPER_DATE_FMT)
    #   self.logger.info('Set custom date_to={}'.format(date_to_str))
    #   return date_to, date_to_str

    def _sleep(self):
        time.sleep(0.4 * (1 + random.random()))

    def _get_encrypted(self,
                       num_control_enc_param: str,
                       n_internetbanking_enc_param: str,
                       e_internetbanking_enc_param: str) -> str:
        cmd = '{} "{}" "{}" "{}" "{}"'.format(
            CALL_JS_ENCRYPT_LIB,
            self.userpass,
            num_control_enc_param,
            n_internetbanking_enc_param,
            e_internetbanking_enc_param,
        )
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def login(self) -> Tuple[MySession, Response, bool, bool]:
        s = self.basic_new_session()
        resp_init = s.get(
            'https://banco.bradesco/html/pessoajuridica/index.shtm',
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        resp_logged_in = Response()
        is_logged = False
        is_credentials_error = False

        for attempt in range(3):
            self._sleep()
            resp_auth_form = s.get(
                'https://www.ne12.bradesconetempresa.b.br/ibpjlogin/login.jsf',
                headers=self.basic_req_headers_updated({'Referer': resp_init.url}),
                proxies=self.req_proxies,
            )

            self._sleep()
            script1_resp = s.get(
                'https://www.ne13.bradesconetempresa.b.br/ibpj/conteudo/js/crypt/publicKey_InternetBanking.js',
                headers=self.basic_req_headers_updated({'Referer': resp_init.url}),
                proxies=self.req_proxies,
            )

            n_internebanking_enc_param = extract.re_first_or_blank(
                r'var n_InternetBanking\s*=\s*"(.*?)"',
                script1_resp.text
            )
            e_internetbanking_enc_param = extract.re_first_or_blank(
                r'var e_InternetBanking\s*=\s*"(.*?)"',
                script1_resp.text
            )

            req_login_params = {
                "tcl": "J",
                "rdoTipoAcesso": "7",  # Usuário e senha
                "identificationForm:txtUsuario": self.username,
                "identificationForm:VERSAO_LOGIN": "1,0,1,16",
                "codigoTagueamento": "undefined",
                "hascsscp": "false",
                "ncsscopus": "",
                "ncsibm": '{"v4a":{"rapport_version":"NOT_AVAILABLE"},'
                          '"ki":"",'
                          '"timestamp":"%s",'
                          '"v5":{"virtual_machine":null},'
                          '"v4":{"download_link":null,"rapport_id":null,"rapport_running":0,"compatible":0},'
                          '"v8":{"rapport_pending_restart":0},'
                          '"v6":{"is_admin":2}}' % date_funcs.now().strftime('%Y-%m-%d %H:%M:%S')}
            # Expect
            # [{
            #  "tipoAut": "",
            #  "CTRL": "",
            #  "proximoTipoAut": "",
            #  "sucesso": true,
            #  "sucessoWarning": false,
            #  "parametroExtra": "/ibpjlogin/autenticacao.jsf;jsessionid=0...nbsq874KX:1au6pvv2c|654319207745677001",
            #  "paramHda":"",
            #  "codigoProximaSequencia":0,
            #  "formaExibicaoProximaSequencia":0,
            #  "acaoCompScopus":  "",
            #  "msgs": []
            # }]
            # Can return if there is an active session
            # 'Sessão encerrada. Por motivo de segurança, acesse novamente o Bradesco Net Empresa.'
            # Need to re-open resp_auth_form
            self._sleep()
            resp_login_step1 = s.post(
                'https://www.ne12.bradesconetempresa.b.br/ibpjlogin/identificacao.jsf',
                data=req_login_params,
                headers=self.basic_req_headers_updated({
                    'Referer': resp_auth_form.url,
                    'X-Requested-With': 'XMLHttpRequest',
                }),
                proxies=self.req_proxies,
            )

            req_autencicacao_link, num_control_enc_param = resp_login_step1.json()[0]['parametroExtra'].split('|')
            req_autencicacao_url = urllib.parse.urljoin(resp_login_step1.url, req_autencicacao_link)
            session_id = extract.re_first_or_blank('jsessionid[=](.*)', req_autencicacao_url)

            encrypted = self._get_encrypted(
                num_control_enc_param,
                n_internebanking_enc_param,
                e_internetbanking_enc_param
            )

            req_login_step2_params = {'senhaCript': encrypted}

            # Expect
            # [{
            #     "tipoAut": "USUARIOSENHA",
            #     "CTRL": "176094494931697081",
            #     "proximoTipoAut": "COMPHASHSCOPUS",
            #     "sucesso": true,
            #     "sucessoWarning": false,
            #     "parametroExtra": "",
            #     "paramHda":"",
            #     "codigoProximaSequencia":0,
            #     "formaExibicaoProximaSequencia":4,
            #     "acaoCompScopus":  "",
            #     "msgs": []
            # }]
            self._sleep()
            resp_login_step2 = s.post(
                req_autencicacao_url,
                data=req_login_step2_params,
                headers=self.basic_req_headers_updated({
                    'Referer': resp_auth_form.url,
                    'X-Requested-With': 'XMLHttpRequest',
                }),
                proxies=self.req_proxies,
            )

            self._sleep()
            resp_login_step3 = s.post(
                'https://www.ne12.bradesconetempresa.b.br/ibpjlogin/tipoAutenticacao.jsf;jsessionid={}?'.format(
                    session_id
                ),
                data={},
                headers=self.basic_req_headers_updated({
                    'Referer': resp_auth_form.url,
                    'X-Requested-With': 'XMLHttpRequest',
                }),
                proxies=self.req_proxies,
            )

            # Necessary additional security step
            self._sleep()
            resp_login_step4 = s.post(
                req_autencicacao_url,
                data={},
                headers=self.basic_req_headers_updated({
                    'Referer': resp_auth_form.url,
                    'X-Requested-With': 'XMLHttpRequest',
                }),
                proxies=self.req_proxies,
            )

            # ctrl_param = resp_login_step2.json()[0].get('CTRL')
            is_credentials_error = 'Senha inválida' in resp_login_step2.text

            if is_credentials_error:
                break

            # Pagina inicio
            self._sleep()
            resp_logged_in = s.get(
                'https://www.ne12.bradesconetempresa.b.br/ibpjlogin/proxAutenticacao.jsf;jsessionid={}'.format(
                    session_id
                ),
                headers=self.basic_req_headers_updated({'Referer': resp_auth_form.url}),
                proxies=self.req_proxies
            )

            # Can be redirected to login page with the web message
            # 'Sessão encerrada. Por motivo de segurança, acesse novamente o Bradesco Net Empresa.'
            # Reason: unclosed active session
            is_logged = 'Acesso Seguro' not in resp_logged_in.text  # or try 'Sair' in resp_logged_in.text
            if is_logged:
                break
            self.logger.warning('Declined auth (not a credentials error). Retry.')

        return s, resp_logged_in, is_logged, is_credentials_error

    def process_access(self,
                       s: MySession,
                       resp_logged_in: Response) -> bool:
        """Process Saldos e Extratos -> Extrato Mensal / Por Período"""
        company_title = parse_helpers.get_organization_title(resp_logged_in.text)
        ctrl_param = parse_helpers.get_ctrl_param_from_url(resp_logged_in.url)

        self._sleep()
        resp_filter_form = s.get(
            'https://www.ne12.bradesconetempresa.b.br/ibpjsaldosextratos/extratoMensalCC.jsf'
            '?CTRL={}'.format(ctrl_param),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_to_filter = parse_helpers.get_accounts_to_filter(
            resp_filter_form.text
        )  # type: List[AccountToFilter]

        self.logger.info("Company {} has accounts {}".format(
            company_title,
            [a.fin_ent_account_id for a in accounts_to_filter]
        ))

        for account_to_filter in accounts_to_filter:
            self.process_account(
                s,
                company_title,
                account_to_filter,
                ctrl_param
            )

        return True

    def _do_check_req_evt(self,
                          s: MySession,
                          resp_filter_form: Response,
                          fin_ent_account_id: str,
                          ctrl_param: str,
                          attempt: int) -> Tuple[bool, MySession]:
        self._sleep()
        resp_evt = s.post(
            'https://www.ne12.bradesconetempresa.b.br/ibpjcampanhas/campanhaEvento.jsf',
            data={"CTRL": ctrl_param, "CAR": "SMC", "agConta": "null",
                  "numConta": "null", "digConta": "null", "razoesDasContas": "cc"},
            headers=self.basic_req_headers_updated({
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': resp_filter_form.url,
                'Accept': '*/*'
            }),
            proxies=self.req_proxies
        )

        return resp_evt.status_code == 200, s

    def process_account(self,
                        s: MySession,
                        company_title: str,
                        account_to_filter: AccountToFilter,
                        ctrl_param: str) -> bool:

        fin_ent_account_id = account_to_filter.fin_ent_account_id

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        d_f, m_f, y_f = date_from_str.split('/')
        d_t, m_t, y_t = self.date_to_str.split('/')
        today = date_funcs.today()
        today_str = today.strftime('%d/%m/%Y')
        today_10yrs_ago_str = \
            datetime(year=today.year - 10, month=today.month, day=today.day).strftime('%d/%m/%Y')

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        resp_evt = Response()
        # Several attempts to handle failed resp_evt (and following resp_movs_filtered)
        for i in range(N_ATTEMPTS_TO_PROCESS_ACCOUNT):
            # Repeat this step as for process_access
            # to reproduce the same behavior for all accounts one by one
            self._sleep()
            resp_filter_form = s.get(
                'https://www.ne12.bradesconetempresa.b.br/ibpjsaldosextratos/extratoMensalCC.jsf'
                '?CTRL={}'.format(ctrl_param),
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            ok, s = self._do_check_req_evt(s, resp_filter_form, fin_ent_account_id, ctrl_param, i + 1)
            if not ok:
                if i < (N_ATTEMPTS_TO_PROCESS_ACCOUNT - 1):
                    self.logger.warning('{}: unsuccessful resp_evt. Retry #{}'.format(
                        fin_ent_account_id,
                        i + 1
                    ))
                    continue
                else:
                    # the last iter
                    # after 3 failed attempts
                    self.logger.error(
                        "{}: can't process account due to unsuccessful resp_evt. Skip. "
                        "RESP_HEADERS:\n{}\nRESP_TEXT:\n{}".format(
                            fin_ent_account_id,
                            resp_evt.headers,
                            resp_evt.text,
                        )
                    )
                    break

            req_movs_filtered_url = ('https://www.ne12.bradesconetempresa.b.br/ibpjsaldosextratos/'
                                     'selecaoPeriodoContasWebCanaisCC.jsf')

            req_select_filter_by_dates_params = OrderedDict([
                ('jsf_tree_64', extract.form_param(resp_filter_form.text, 'jsf_tree_64')),
                ('jsf_state_64', extract.form_param(resp_filter_form.text, 'jsf_state_64')),
                ('conteudoExternoMessage', extract.form_param(resp_filter_form.text,
                                                              'conteudoExternoMessage') or None),
                ('jsf_viewid', '/selecaoPeriodoContasWebCanaisCC.jsp'),
                ('formularioExtratoMensal:selectMesProgramado', ''),
                ('tipoConsultaPorMes', '1'),
                ('calendarioProgramado_beginDia', d_f),
                ('calendarioProgramado_beginMes', m_f),
                ('calendarioProgramado_beginAno', y_f),
                ('calendarioProgramado_begin', date_from_str),
                ('calendarioProgramadoDtInicio', [today_10yrs_ago_str, '']),
                ('calendarioProgramadoDtFim', [today_str, '']),
                ('calendarioProgramadoRequired', ['false', '']),
                ('calendarioProgramado_endDia', d_t),
                ('calendarioProgramado_endMes', m_t),
                ('calendarioProgramado_endAno', y_t),
                ('calendarioProgramado_end', self.date_to_str),
                ('contas', account_to_filter.select_option_ix),
                ('formularioExtratoMensal:_id83', ''),
                ('formularioExtratoMensal_SUBMIT', '1'),
                ('autoScroll', '0,0'),
                ('formularioExtratoMensal:_link_hidden_', ''),
            ])

            # Necessary for further processing
            self._sleep()
            resp_select_filter_by_dates = s.post(
                req_movs_filtered_url + '?javax.portlet.faces.DirectLink=true',
                data=req_select_filter_by_dates_params,
                headers=self.basic_req_headers_updated({'Referer': resp_filter_form.url}),
                proxies=self.req_proxies,
                timeout=120,
            )

            req_movs_filtered_params = req_select_filter_by_dates_params.copy()
            req_movs_filtered_params['AJAXREQUEST'] = None
            req_movs_filtered_params['formularioExtratoMensal:_id45'] = None
            req_movs_filtered_params['formularioExtratoMensal:_id78'] = ''

            # NOTE:
            # The page with movs_filtered has 2 tables:
            # 1. Extrato de: Ag: 54 | CC: 0001529-6 | Entre 01/08/2019 e 04/09/2019
            #    - all movements EXCEPT 2 last days - paginated (max 500 movs)
            # 2. Últimos Lançamentos
            #    - movs of 2 last days on 1st page with filtered movements
            self._sleep()
            resp_movs_filtered = s.post(
                req_movs_filtered_url,
                data=req_movs_filtered_params,
                headers=self.basic_req_headers_updated({'Referer': resp_filter_form.url}),
                proxies=self.req_proxies,
                timeout=120,
            )

            # Always without 2 last days (of today)
            movs_parsed_asc_1st_page = parse_helpers.get_movements_parsed_except_recent(resp_movs_filtered.text)

            # Available on the 1st page
            movs_parsed_asc_recent = parse_helpers.get_movements_parsed_recent(resp_movs_filtered.text)

            movs_parsed_next_pages = []  # type: List[MovementParsed]
            resp_prev = resp_movs_filtered
            # Pagination
            for page_ix in range(2, 20):
                if 'proxima_ultima' not in resp_prev.text:
                    break
                if 'proxima desabilitado' in resp_prev.text:  # inactive link - no more movs
                    break
                self.logger.info('{}: open page #{} with movements'.format(fin_ent_account_id, page_ix))
                req_movs_next_page_params = OrderedDict([
                    ('AJAXREQUEST', '_viewRoot'),
                    ('jsf_tree_64', extract.form_param(resp_prev.text, 'jsf_tree_64')),
                    ('jsf_state_64', extract.form_param(resp_prev.text, 'jsf_state_64')),
                    ('jsf_viewid', '/extratoMensalWebCanaisCC.jsp'),
                    ('conteudoExternoMessage', extract.form_param(resp_prev.text, 'conteudoExternoMessage')),
                    ('formularioExtratoMensal_SUBMIT', '1'),
                    ('autoScroll', ''),
                    ('formularioExtratoMensal:_link_hidden_', ''),
                    # The next page ("PROXIMA" text)
                    # from a class="proxima tabindex" -> A4J.AJAX.Submit
                    ('formularioExtratoMensal:listagem:_id1755', 'formularioExtratoMensal:listagem:_id1755')
                ])
                req_movs_url_i = ('https://www.ne12.bradesconetempresa.b.br/ibpjsaldosextratos/'
                                  'extratoMensalWebCanaisCC.jsf?javax.portlet.faces.DirectLink=true')
                self._sleep()
                resp_movs_i = s.post(
                    req_movs_url_i,
                    data=req_movs_next_page_params,
                    headers=self.basic_req_headers_updated({'Referer': resp_movs_filtered.url}),
                    proxies=self.req_proxies,
                    timeout=120,
                )
                # Parse xml with only new movements, no 'ultima movements' here
                movs_parsed_i = parse_helpers.get_movements_parsed(resp_movs_i.text)
                movs_parsed_next_pages = list_funcs.join_uniq_tail(movs_parsed_next_pages, movs_parsed_i)
                resp_prev = resp_movs_i

            # Too late movements will be filtered in basic_movements_scraped_from_movements_parsed
            movements_parsed_asc = list_funcs.join_uniq_tail(
                list_funcs.join_uniq_tail(movs_parsed_asc_1st_page, movs_parsed_next_pages),
                movs_parsed_asc_recent
            )

            movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
                movements_parsed_asc,
                date_from_str,
                current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
            )

            mov_last = movements_scraped[-1] if movements_scraped else None  # type: Optional[MovementScraped]
            # Can get account_scraped only after movements_scraped to get correct balance if date_to < today
            ok, account_parsed = parse_helpers.get_account_parsed(resp_movs_filtered.text,
                                                                  account_to_filter,
                                                                  mov_last)
            if not ok:
                if i < (N_ATTEMPTS_TO_PROCESS_ACCOUNT - 1):
                    self.logger.warning("{}: can't get account_parsed. Retry #{}".format(
                        fin_ent_account_id,
                        i + 1
                    ))
                    continue
                else:
                    # the last iter
                    self.basic_log_wrong_layout(resp_movs_filtered, "{}: can't get account_parsed. Skip".format(
                        fin_ent_account_id
                    ))
                    break

            account_scraped = self.basic_account_scraped_from_account_parsed(
                company_title,
                account_parsed,
                country_code='BRA',  # Brazil
                account_no_format=ACCOUNT_NO_TYPE_UNKNOWN
            )

            self.logger.info("Got account {}".format(account_scraped))
            self.basic_upload_accounts_scraped([account_scraped])
            self.basic_log_time_spent("GET ACCOUNT")

            self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

            self.basic_upload_movements_scraped(
                account_scraped,
                movements_scraped,
                date_from_str=date_from_str
            )
            return True

        # finished the loop above w/o movs uploading
        self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
        return False

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url, resp_logged_in.text)

        self.process_access(s, resp_logged_in)
        self.basic_log_time_spent('GET MOVEMENTS')

        return self.basic_result_success()
