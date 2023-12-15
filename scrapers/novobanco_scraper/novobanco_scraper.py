import datetime
import os
import random
import re
import subprocess
import time
import urllib.parse
from collections import OrderedDict
from concurrent import futures
from typing import Dict, Tuple

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.novobanco_scraper import parse_helpers

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'novobanco_encrypter.js'
))

__version__ = '6.0.0'

__changelog__ = """
6.0.0
moved from novobanco_nbnetwork_scraper.py
deleted novobanco nbnet support
5.2.0
check is_active_account
5.1.0
call basic_upload_movements_scraped with date_from_str
5.0.1
upd _get_encrypted (fixed typing)
5.0.0
moved from novobanco_scraper.py
4.8.0
login() returns reason
detect 'service is unavailable'
more 'wrong credentials' markers
4.7.0
set MAX_CONCURRENT_WORKERS = 4
4.6.0
login: more delays
4.5.1
fixed log msg
4.5.0
login: several attempts to open position_global (to handle 'still loading' resp)
4.4.0
more wrong credentials detections
4.3.0
use basic_new_session
upd type hints
fmt
4.2.0
removed _req_headers_updated (now use basic_req_headers)
use basic_get_date_from
parse_helpers:
  added get_account_select_param to be able to process PRT and ESP
  _get_movements_parsed_from_xml:
    use calculated temp_balance and compare it to scraped temp_balance 
    to handle bank-level balance inconsistency and also avoid parsing errors  
process_account: 
  fixed: country_code = 'PRT' for Portugal (was 'PT' - it broke AccountNo)
  re-open resp_acc_mov_init for better concurrent proccessing support
  impl pagination for movements to be able to scrape > 70 movs
login: more delays between requests
more type hints
parse_helpers: more type hints
4.1.0
basic_movements_scraped_from_movements_parsed: new format of the result 
4.0.0
Portugal region support
3.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
2.1.0
fixed: select movements by dates
2.0.0
basic_movements_scraped_from_movements_parsed
OperationalDatePosition, KeyValue support
1.3.0
basic_upload_movements_scraped
1.2.0
login_nbnetwork explicit
1.1.0
log account scraped
"""

CREDENTIALS_ERROR_MARKERS = [
    'Por favor, verifique se ha introducido correctamente su Número de Adhesión y PIN.',
    'Por favor certifique-se que está a introduzir corretamente o N. de Adesão e o PIN.',
    # Blocked user? See dev/resp_logged_in_blocked_user.html
    'Si es cliente Banca a Distancia de NOVO BANCO por favor introduzca el Número de Adhesión/PIN.',
    'O seu acesso está suspenso',  # -a 29310
]

MAX_CONCURRENT_WORKERS = 4  # for accesses with many accs: -a 21302

SERVICE_UNAVAILABLE_MARKER = 'Serviço Temporariamente Indisponível'


def delay() -> None:
    time.sleep(0.1 + random.random())


class NovobancoScraper(BasicScraper):
    """
    NBnetwork login access type only implemented
    Spain and Portugal supported
    """
    scraper_name = 'NovobancoScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.region = 'ESP'  # 'ESP' or 'PT'

    def _ts(self) -> int:
        return int(datetime.datetime.timestamp(datetime.datetime.utcnow()) * 1000)

    def _req_headers_w_referer(self, referer_url: str) -> Dict[str, str]:
        return self.basic_req_headers_updated({'Referer': referer_url})

    def _get_encrypted(self, resp_text: str) -> str:
        # 2 steps for type checker
        extracted = re.findall(
            r"frm.nx.value='(.*?)'\+cvt1\('(.*?)'",
            resp_text
        )[0]  # type: Tuple[str, str]
        prefix, key = extracted

        cmd = '{} "{}" "{}" "{}"'.format(CALL_JS_ENCRYPT_LIB, prefix, key, self.userpass)
        result_bytes = subprocess.check_output(cmd, shell=True)
        encrypted = result_bytes.decode().strip()
        return encrypted

    def login_nbnetwork(self) -> Tuple[MySession, Response, bool, bool, str]:
        """
        NBnetwork login access type only
        """

        s = self.basic_new_session()

        req1_url = 'https://sec.novobanco.pt/web/ESPEW1/tpl.asp?ad={}&selo={}&fca={}'.format(
            self.username,
            self._ts(),
            self.username
        )

        # Sometimes getting wrong 'broken' response - need to open again
        while True:
            resp1 = s.get(
                req1_url,
                headers=self.req_headers,
                proxies=self.req_proxies
            )
            if 'f5_p' in resp1.text:
                break

            delay()
            continue

        s.cookies.set(
            'aaaaaaaaaaaaaaa',
            extract.re_first_or_blank("f5_p:'(.*?)'", resp1.text),
            domain='sec.novobanco.pt'
        )

        passw_encrypted = self._get_encrypted(resp1.text)

        selo_param = str(self._ts())

        req15_params = OrderedDict([
            ('selo', selo_param),
            ('ad', self.username),
            ('app', '115'),
            ('fca', self.username)
        ])

        # detect region by customer
        req15_url = 'https://sec.novobanco.pt/web/LoginHandler/LoginHandler.aspx'

        resp15 = s.post(
            req15_url,
            data=req15_params,
            headers=self._req_headers_w_referer(resp1.url),
            proxies=self.req_proxies
        )

        if 'ESPEW' in resp15.url:
            self.region = 'ESP'
        elif 'PTEW' in resp15.url:
            self.region = 'PT'
        else:
            reason = "Can't extract proper region from resp url: {}".format(resp15.url)
            return s, resp15, False, False, reason

        # expect 'https://sec.novobanco.pt/web/ESPEW1/tpl.asp' - SPAIN
        # or 'https://sec.novobanco.pt/web/PTEW1/tpl.asp' - PORTUGAL
        req2_url = 'https://sec.novobanco.pt/web/{}EW1/tpl.asp'.format(self.region)

        req2_params = OrderedDict([
            ('SRV', extract.re_first_or_blank('name="SRV" value="(.*?)"', resp1.text)),
            ('selo', selo_param),
            ('ad', self.username),
            ('AvisaBrowser', 'true'),
            ('pin', ''),
            ('nx', passw_encrypted)
        ])

        delay()

        resp_logged_in = s.post(
            req2_url,
            data=req2_params,
            headers=self._req_headers_w_referer(resp1.url),
            proxies=self.req_proxies
        )

        is_credentials_error = any(m in resp_logged_in.text for m in CREDENTIALS_ERROR_MARKERS)
        reason = ''

        delay()

        resp_position_global = Response()
        is_logged = False
        for i in range(1, 6):
            self.logger.info('Get resp_position_global: attempt #{}'.format(i))
            time.sleep(1.0 + random.random())
            # Handle case when bank asks to enter contact data - open position global directly
            req_position_global_url = 'https://sec.novobanco.pt/web/{}EW4/service.aspx/3011'.format(self.region)

            resp_position_global = s.get(
                req_position_global_url,
                headers=self._req_headers_w_referer(resp_logged_in.url),
                proxies=self.req_proxies
            )

            is_logged = 'submitLogout' in resp_position_global.text

            # Break the loop here to avoid false-positive 'still loading' response
            if is_logged:
                break

            # No need to do extra attempts
            if not is_logged and SERVICE_UNAVAILABLE_MARKER:
                reason = 'Service is temporarily unavailable'
                break

            # Do several attempts only if got 'still loading' response
            if 'div class="waitImg" alt="Loading"' in resp_position_global.text:
                self.logger.warning("Got 'still loading' response. Retry")
                time.sleep(5 + random.random())
                continue

            break

        return s, resp_position_global, is_logged, is_credentials_error, reason

    def process_contract(self,
                         s: MySession,
                         resp_logged_in: Response,
                         contract_data: Tuple[str, str]) -> bool:

        req0_url = (
            'https://sec.novobanco.pt/web/{}EW1/tpl.asp?srv=38201&srvExe=46&etpExe=100'
            '&cbEmpresa={}&AP={}'
            '&parameters=&mudaUtilizador=1&adesao=&instituicao='
            '&detalheAssinatura=&tipoNavegacao='.format(self.region, contract_data[1], contract_data[0])
        )

        resp0 = s.get(
            req0_url,
            headers=self._req_headers_w_referer(resp_logged_in.url),
            proxies=self.req_proxies
        )

        req1_url = urllib.parse.urljoin(
            resp0.url,
            parse_helpers.get_contract_home_url_raw(resp0.text)
        )

        resp_contract_home = s.get(
            req1_url,
            headers=self._req_headers_w_referer(resp0.url),
            proxies=self.req_proxies
        )

        organization_title = parse_helpers.get_organization_title(resp_contract_home.text)

        req_acc_mov_init_url = 'https://sec.novobanco.pt/web/{}EW4/service.aspx/16?ITG=0&SV=16&AR=&'.format(
            self.region
        )
        resp_acc_mov_init = s.get(
            req_acc_mov_init_url,
            headers=self._req_headers_w_referer(resp_contract_home.url),
            proxies=self.req_proxies
        )

        accounts_ibans = parse_helpers.get_accounts_ibans(resp_acc_mov_init.text)
        self.logger.info('Contract {} {} has accounts with IBANs {}'.format(organization_title,
                                                                            contract_data, accounts_ibans))

        if project_settings.IS_CONCURRENT_SCRAPING and accounts_ibans:
            with futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:

                futures_dict = {
                    executor.submit(self.process_account, s, resp_contract_home,
                                    account_iban, organization_title): account_iban
                    for account_iban in accounts_ibans
                }

                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_iban in accounts_ibans:
                self.process_account(s, resp_contract_home, account_iban, organization_title)

        return True

    def process_account(self,
                        s: MySession,
                        resp_contract_home: Response,
                        account_iban: str,
                        organization_title: str) -> bool:

        if not self.basic_check_account_is_active(account_iban):
            return True

        date_from_str = self.basic_get_date_from(account_iban)
        self.basic_log_process_account(account_iban, date_from_str)

        req_acc_mov_init_url = 'https://sec.novobanco.pt/web/{}EW4/service.aspx/16?ITG=0&SV=16&AR=&'.format(
            self.region
        )
        resp_acc_mov_init = s.get(
            req_acc_mov_init_url,
            headers=self._req_headers_w_referer(resp_contract_home.url),
            proxies=self.req_proxies
        )

        req_url = 'https://sec.novobanco.pt/web/{}EW4/service.aspx/16'.format(self.region)

        date_from_in_req = date_from_str.replace('/', '-')
        date_to_in_req = self.date_to_str.replace('/', '-')

        account_select_param = parse_helpers.get_account_select_param(
            resp_acc_mov_init.text,
            account_iban
        )

        filter_params = OrderedDict([
            ('UndoRedoManager_hidden', '{"actions":[]}'),
            ('M$B$pnlPesquisa$cboContas', account_select_param),
            ('M$B$pnlPesquisa$spnlPesquisa$swpnlPeriodo$x', 'on'),
            ('M$B$pnlPesquisa$spnlPesquisa$swpnlPeriodo$dtpMin$i$date', date_from_in_req),
            ('M$B$pnlPesquisa$spnlPesquisa$swpnlPeriodo$dtpMax$i$date', date_to_in_req),
            ('M$B$pnlPesquisa$spnlPesquisa$btnConsultar', 'Consultar'),
            ('M$B$pnlPesquisa$spnlPesquisa$isCollapsed', 'false')
        ])

        _, req_movs_filtered_params = extract.build_req_params_from_form_html(
            resp_acc_mov_init.text,
            form_id='FormMain'
        )
        req_movs_filtered_params.update(filter_params)

        # similar to `req_movs_filtered_params['M'] = None` with better typing
        if 'M' in req_movs_filtered_params:
            del req_movs_filtered_params['M']

        resp_movs_filtered = s.post(
            req_url,
            data=req_movs_filtered_params,
            headers=self._req_headers_w_referer(resp_acc_mov_init.url),
            proxies=self.req_proxies
        )

        account_parsed = parse_helpers.get_account_parsed(resp_movs_filtered.text, account_iban)
        country_code = 'PRT' if account_parsed['account_no'].startswith('PT') else 'ESP'
        account_scraped = self.basic_account_scraped_from_account_parsed(
            organization_title,
            account_parsed,
            country_code=country_code
        )
        self.logger.info('Got account: {}'.format(account_scraped))

        self.basic_upload_accounts_scraped([account_scraped])
        self.basic_log_time_spent('GET BALANCE: {}'.format(account_iban))

        page_ix_max = 0

        # DO 'More movements' requests if necessary
        # to be able to extract all movs by excel/xml req

        # __sf, __VIEWSTATE, __LASTFOCUS
        _, req_more_movs_params = extract.build_req_params_from_form_html(
            resp_movs_filtered.text,
            form_id='FormMain'
        )

        req_more_params_extra = OrderedDict([
            ('UndoRedoManager_hidden', '{"actions":[]}'),
            ('__EVENTTARGET', 'M$B$grdMov'),
            ('__EVENTARGUMENT', ''),  # page ix, will set later
            ('__VIEWSTATEGENERATOR', extract.form_param(resp_movs_filtered.text,
                                                        param_id='__VIEWSTATEGENERATOR')),
            ('__EVENTVALIDATION', extract.form_param(resp_movs_filtered.text,
                                                     param_id='__EVENTVALIDATION')),
            ('M$B$pnlPesquisa$spnlPesquisa$swpnlPeriodo$x', 'on'),
            ('M$B$pnlPesquisa$spnlPesquisa$swpnlPeriodo$dtpMin$i$date', date_from_in_req),
            ('M$B$pnlPesquisa$spnlPesquisa$swpnlPeriodo$dtpMax$i$date', date_to_in_req),
            ('M$B$pnlPesquisa$spnlPesquisa$swpnlMontante$x', 'on'),
            ('M$B$pnlPesquisa$spnlPesquisa$swpnlMontante$mnMin$i', ''),
            ('M$B$pnlPesquisa$spnlPesquisa$swpnlMontante$mnMax$i', ''),
            ('M$B$pnlPesquisa$spnlPesquisa$isCollapsed', 'false')
        ])

        req_more_movs_params.update(req_more_params_extra)

        resp_last = resp_movs_filtered
        for page_ix in range(2, 100):
            # Do pagination to detect the num of pages w/movements
            # Also, the website returns all movements only after all "More movements"
            prev_page_last_mov_date = extract.re_last_or_blank(
                r'<td align="left"><span>([\d-]+)</span>',
                resp_last.text
            )
            if not prev_page_last_mov_date:
                self.logger.info('{}: no more movements. Stop pagination on page {}'.format(
                    account_iban,
                    page_ix
                ))
                break

            page_ix_max = page_ix
            self.logger.info('{}: open page {} with movements earlier {}'.format(
                account_iban,
                page_ix,
                prev_page_last_mov_date
            ))
            req_more_movs_params['__EVENTARGUMENT'] = 'Page${}'.format(page_ix)
            resp_last = s.post(
                req_url,
                data=req_more_movs_params,
                headers=self._req_headers_w_referer(resp_last.url),
                proxies=self.req_proxies
            )

        # / END of 'More movements'

        # Get mov excel
        req_more_movs_params['M$B$btnExportarSaldoMovimentos'] = 'ExportarDummy'
        req_more_movs_params['__EVENTARGUMENT'] = 'Page${}'.format(page_ix_max)

        resp_movs_excel = s.post(
            req_url,
            data=req_more_movs_params,
            headers=self._req_headers_w_referer(resp_movs_filtered.url),
            proxies=self.req_proxies,
            timeout=20
        )

        movements_parsed = parse_helpers.get_movements_parsed_from_html_excel(
            resp_movs_excel.text,
            account_iban,
            self.logger
        )
        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str
        )

        self.basic_log_process_account(account_scraped.AccountNo, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        return True

    def main(self) -> MainResult:
        self.logger.info('main: started')

        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login_nbnetwork()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        contracts_datas = parse_helpers.get_contracts_datas(resp_logged_in.text)
        self.logger.info('Got contracts: {}'.format(contracts_datas))

        if project_settings.IS_CONCURRENT_SCRAPING and contracts_datas:
            with futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:

                futures_dict = {
                    executor.submit(self.process_contract, s,
                                    resp_logged_in, contract_data): contract_data
                    for contract_data in contracts_datas
                }
                self.logger.log_futures_exc('process_contract', futures_dict)
        else:
            for contract_data in contracts_datas:
                self.process_contract(s, resp_logged_in, contract_data)

        self.basic_log_time_spent('GET ALL BALANCES AND MOVEMENTS')
        return self.basic_result_success()
