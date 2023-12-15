import datetime
import json
import random
import threading
import time
from collections import OrderedDict
from concurrent import futures
from typing import Any, Dict, List, Tuple, Set, Optional

from custom_libs import list_funcs
from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response, RESP_CODES_BAD_FOR_PROXIES
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, MovementParsed, ScraperParamsCommon,
    MOVEMENTS_ORDERING_TYPE_ASC, MainResult,
    DOUBLE_AUTH_REQUIRED_TYPE_COMMON, DOUBLE_AUTH_REQUIRED_TYPE_OTP,
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.bbva_scraper import parse_helpers_netcash

__version__ = '4.17.0'

__changelog__ = """
4.17.0 2023.06.06
process_account: added relogin to avoid expired session on receipts download 
4.16.0
login: added 2FA email detection
4.15.0
use renamed list_funcs
4.14.0
added wrong credentials marker
4.13.0
login: fixed successful loging text markers
4.12.0
login: added successful login text marker
4.11.0
use calculated temp_balance for movements (with temp_balance_parsed validation)
4.10.0
_get_date_from_req_param to extract movs where val_date < oper_date
min rescraping_offset for accounts with custom vals
4.9.0
upd custom mov offset
4.8.0
increased pagination limit
4.7.0
process_account: more detections for hanging pagination
4.6.0
More 2FA markers
4.5.0
call basic_upload_movements_scraped with date_from_str
4.4.1
upd log msgs
4.4.0
'Most probably the ACCESS IS BLOCKED' -> wrong credentials
DOUBLE_AUTH_REQUIRED_TYPE_OTP
4.3.0
set_date_to_for_future_movs
4.2.0
_filter_movements_i (to use in children)
4.1.0
MAX_ALLOWED_FAILED_MOVEMENTS
__n_failed_movements
4.0.0
use basic_get_movements_parsed_w_extra_details
_set_got_critical_scraping_err
_is_got_critical_scraping_err
3.18.0
get_accounts_scraped
3.17.0
renamed to download_correspondence()
3.16.0
skip inactive accounts
3.15.0
download_company_documents
3.14.0
process_account:
  longer timeouts
  several attempts to get resp_movs_i_json
process_movement: 
  longer timeouts
3.13.0
more WRONG_CREDENTIALS_MARKERS
3.12.1
more custom MOVEMENTS_RESCRAPE_OFFSET_DAYS
3.12.0
disabled future movs (no need anymore, commented)
upd pagination
several attempts to open a page during the pagination
3.11.1
aligned double auth msg
3.11.0
use basic_new_session
upd type hints
3.10.0
login: detect '2FA REQUIRED' reason
3.9.0
login: detect 'ACCESS IS BLOCKED' reason
3.8.0
process_account: fixed inf pagination (known case PT50001901920020000021715):
  for loop instead of while to limit n iter
  is_sublist: check only unchanging mov fields (some fields are changing even for the same mov)
  page iteration: send correct temp_balance for the movs of the next page 
3.7.0
custom account-level MOVEMENTS_RESCRAPE_OFFSET_DAYS
process_account: use project-level or account-level offset if provided
3.6.0
increased MOVEMENTS_RESCRAPE_OFFSET_DAYS=7
3.5.0
login: detect SMS AUTH required reason
main: handle reason
3.4.1
deprecation marks 
use basic_mov_parsed_str for logs
3.4.0
parse_helpers_netcash: get_movements_parsed_from_json: use _clean_of_null_char 
3.3.0
added condition should_scrape_ext_descr for 
  basic_update_movements_extended_descriptions_if_necessary
  to reduce number of calls 
3.2.1
upd comments
3.2.0
process_movement:
  upd req_url (for mov details)
  1 retry of got 500 (sometimes bank returns it even during regular web session)
3.1.0
different got_500 for different accounts
reduced a number of concurrent workers (4 -> 2)
fixed log msg if got 500
3.0.0
incremental uploading for movements with extended descriptions even on 500 err
"""

PROCESS_MOVEMENT_MAX_WORKERS = 2
PROCESS_ACCOUNT_MAX_WORKERS = 2

# Some movements has no real extra details even if website initially tells that they have.
# Max allowed failed process_movement()
# Those failed movements will be inserted
# without extra_details (extended descriptions and receipt).
MAX_ALLOWED_FAILED_MOVEMENTS = 5

# Use default extended description if got response
# with the markers below
MOV_EXTRA_DETAILS_NON_CRITICAL_ERR_MARKERS = [
    'El usuario no puede operar con la informaci',  # no permissions to details
    'NO EXISTEN DATOS PARA LA CONSULTA REALIZADA',  # no data yet
]

# DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS = 0  # offset to scrape future movements (09/01 from 05/01)

# custom account-level offset, many movs
MOVEMENTS_RESCRAPE_OFFSET_DAYS = {
    'ES1701825437660208509436': 3,  # -a 16808
    'ES1901825437600208509306': 3,  # -a 16808
    'ES4601822354840201002674': 3
}

WRONG_CREDENTIALS_MARKERS = [
    "enviar('EAI0000')",
    "enviar('EAI0008')",  # 'El usuario está bloqueado',
    "enviar('EAI0025')",
]

LOGGED_IN_MARKERS = [
    "kyop-menuBasicItem",  # 005_resp_logged_in.html
    "kyop_cajacentral",    # 006_resp_logged_in.html
]

MOVEMENTS_MAX_OFFSET = 84  # extra padding to do -5 days from _get_req_param_date_from


class BBVANetcashScraper(BasicScraper):
    """
    Movements uploading logic:
    (process_movement optimization + incremental uploading 'as many as you can extract correctly'):
    - it extracts extended descriptions only for unambiguous new movements (main_launcher)
    - it tries to upload movements with successfully scraped extended descriptions,
      and it will do it if scraped more than already saved movements;
      that means it can add new movements after already saved even if scraped not all recent
    - the scraper can deal with 500 in a special manner:
      it stops the extraction for details of movements of the account
      (instead of proxy rotation as common behaviour).
    - the scraper can continue to extract details of movements of other accounts of the access
    - additional attempt if got 500 during the movement details extraction
      (website sometimes returns 500 even during regular web browsing)
    - it produces useful logs for these cases:
      <account>:<movement>: got 500. Set 'got 500' to interrupt further details extraction
      <account>: it was possible to get extra details only for <N> movs of <M>. ..
      ..Will upload only <N> movs (the last one is <movement>)
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BBVANetcashScraper') -> None:

        self.scraper_name = scraper_name
        super().__init__(scraper_params_common, proxies)

        # VB: disabled future movs since 05/2020
        # to scrape future movements
        self.today = date_funcs.today()
        # self.date_to = self.today + datetime.timedelta(days=DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS)
        # self.date_to_str = self.date_to.strftime(project_settings.SCRAPER_DATE_FMT)  # '30/01/2017'

        # important field for movements processing optimization
        self.is_receipts_scraper = False
        # a set of accounts got 500
        self.__got_critical_sraping_err = set()  # type: Set[str]
        self.__n_failed_movements = 0
        self.__lock = threading.Lock()
        self.update_inactive_accounts = False
        # Allow future movements scraping when the customer required it
        self.set_date_to_for_future_movs()

    def _inc_n_failed_movements(self) -> int:
        with self.__lock:
            self.__n_failed_movements += 1
            return self.__n_failed_movements

    def _set_got_critical_scraping_err(self, fin_ent_account_id: str) -> None:
        """Useful to inform other movements about critical 500 occurred during the
        attempt to get extra details (extended description and receipt_params)"""
        with self.__lock:
            self.__got_critical_sraping_err.add(fin_ent_account_id)

    def _is_got_critical_scraping_err(self, fin_ent_account_id: str) -> bool:
        with self.__lock:
            return fin_ent_account_id in self.__got_critical_sraping_err

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()
        resp1 = s.get(
            'https://www.bbvanetcash.com/local_kyop/KYOPSolicitarCredenciales.html',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # from validateForm()(validator.js)
        eai_code = '0073' if self.username[0] == '3' else '0001'

        username_upper = self.username.upper()
        username_second_upper = self.username_second.upper()

        req2_params = OrderedDict([
            ('origen', 'pibee_es'),
            ('idioma', 'CAS'),
            ('eai_user', '0023' + eai_code + username_upper + username_second_upper),
            ('eai_URLDestino', '/SESKYOP/kyop_mult_web_pub/index.html'),
            ('error', ''),
            ('cod_emp', username_upper),
            ('cod_usu', username_second_upper),
            ('eai_password', self.userpass.upper()[:8])
        ])

        resp2 = s.post(
            'https://www.bbvanetcash.com/DFAUTH/slod_mult_mult/DFServlet',
            data=req2_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = any(m in resp2.text for m in LOGGED_IN_MARKERS)
        is_credentials_error = any(m in resp2.text for m in WRONG_CREDENTIALS_MARKERS)

        reason = ''
        # Also url https://www.bbvanetcash.com/DFAUTH/slod_mult_mult/DFServlet
        if 'Enviar SMS' in resp2.text or 'código de seguridad vía SMS' in resp2.text:
            is_logged = False
            reason = DOUBLE_AUTH_REQUIRED_TYPE_OTP

        if 'Enviar e-mail' in resp2.text:
            is_logged = False
            reason = DOUBLE_AUTH_REQUIRED_TYPE_OTP

        if 'doble factor de seguridad' in resp2.text:
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        if '/DFAUTH/images/errorGeneral_CAS.gif' in resp2.text:
            self.logger.error(
                'Detected "Most probably, the ACCESS IS BLOCKED". '
                'Consider as wrong credentials'
            )
            is_credentials_error = True

        return s, resp2, is_logged, is_credentials_error, reason

    def get_accounts_scraped(
            self,
            s: MySession) -> Tuple[MySession, dict, List[AccountScraped]]:

        # works too, but skips some of accounts
        # req_params = {
        #     'asunto': '',
        #     'bancoAsunto': '',
        #     'favoritas': 'false',
        #     'formatoFecha': 'dd/MM/yyyy',
        #     'formatoImporte': '0.000,00',
        #     'borraCache': 'false',
        #     'iv-cod_emp': self.username,
        #     'pb_isPortalKyop': 'true',
        #     'xtiTipoProd': 'C',
        #     'pb_xti_comprper': '',
        #     'pb_husohora': '(GMT 01:00)',
        #     'pb_cod_prod': '201',  # from cookie; cod prod related to login params too
        #     'pb_cod_serv': '',
        #     'pb_cod_proc': '',
        #     'LOCALE': 'es_ES',
        #     'pb_cod_ffecha': 'dd/MM/yyyy',
        #     'pb_cod_fimporte': '0.000,00'
        # }

        req_params_v2 = {
            'asunto': '',
            'bancoAsunto': '',
            'favoritas': 'false',
            'borraCache': 'false',
            'paginacion': '0'
        }

        resp = s.post(
            'https://www.bbvanetcash.com/SESKYOS/kyos_mult_web_posicioncuentas_01/listarCuentasNivel1',
            data=req_params_v2,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        resp_json = resp.json()
        accounts_parsed = parse_helpers_netcash.get_accounts_parsed(resp_json)

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                account_parsed['organization_title'] or self.db_customer_name,
                account_parsed,
                country_code=account_parsed['country_code'],
                account_no_format=account_parsed['account_no_format'],
                is_default_organization=(not account_parsed['organization_title'])
            )
            for account_parsed in accounts_parsed
        ]

        self.logger.info('Got accounts: {}'.format(accounts_scraped))

        return s, resp_json, accounts_scraped

    def _filter_movements_i(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            date_from_str: str,
            date_to_str: str,
            paginacionMOVDIA_param='1',
            paginacionTLSMT016_param='N00000000000+0000000000000000',
            paginacionTLSMT017_param='N000000000000+0000000000000000000',
            ultimoSaldoPaginacionAnterior_param: str = None,
            ultimaFechaPaginacionAnterior_param: str = None) -> Tuple[bool, dict]:
        """:returns (ok, resp_movs_i_json)"""

        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        # correct for BBAN only
        movements_parsed_desc = []  # type: List[MovementParsed]
        has_next_page = True

        page_retries = 0
        max_page_retries = 2
        # Page iteration

        req_params = OrderedDict([
            ('cuenta', fin_ent_account_id),
            ('bancoAsunto', '1'),
            ('tipoFecha', 'Rango'),
            ('fechaDesde', date_from_str),
            ('fechaHasta', date_to_str),
            ('periodo', ''),
            ('concepto', ''),
            ('importeDesde', ''),
            ('importeHasta', ''),
            ('divisa', account_scraped.Currency),  # get from account now, was 'EUR'
            ('paginacionTLSMT017', paginacionTLSMT017_param),  # last mov amount
            ('paginacionTLSMT016', paginacionTLSMT016_param),  # last mov sign
            ('paginacionMOVDIA', paginacionMOVDIA_param),
            ('ultimoSaldoPaginacionAnterior', ultimoSaldoPaginacionAnterior_param),
            ('ultimaFechaPaginacionAnterior', ultimaFechaPaginacionAnterior_param),
            ('referenciaBBVA', ''),
            ('referenciaCorresponsal', ''),
            ('iuc', fin_ent_account_id),
            ('saldoContable', str(account_scraped.Balance).replace('.', ',')),  # added since prev version
            ('estadoUpdate', '0'),
            ('ordenacion', 'DESC'),
            ('customer', 'null'),
        ])
        # https://www.bbvanetcash.com/SESEYOZ/eyoz_mult_web_posicioncuentas_01/listarResultadoMovNivel2
        req_url = ('https://www.bbvanetcash.com/SESKYOS/'
                   'kyos_mult_web_posicioncuentas_01/listarResultadoMovNivel2')  # kyos_mult

        resp_movs_i = Response()
        for attempt in range(1, 4):
            resp_movs_i = s.post(
                req_url,
                data=req_params,
                headers=self.basic_req_headers_updated({
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': 'https://www.bbvanetcash.com/SESKYOP/'
                                'kyop_mult_web_pub/index-new.html?LOCALE=es_ES',
                    'Connection': 'keep-alive'
                }),
                proxies=self.req_proxies,
                timeout=30,
            )
            # keep fields ordering; max 45 mov from page
            try:
                resp_movs_i_json = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(resp_movs_i.text)
                return True, resp_movs_i_json  # SUCCESS
            except Exception as e:
                self.logger.warning(
                    "{}: attempt #{}: can't parse resp_movs_i_json\nRESPONSE:\n{}".format(
                        fin_ent_account_id,
                        attempt,
                        resp_movs_i
                    )
                )
                time.sleep(1 + random.random() * 0.5)

        self.logger.error("{}: can't parse resp_movs_i_json. Break the loop. RESPONSE:\n{}".format(
            fin_ent_account_id,
            resp_movs_i
        ))
        return False, {}

    def _get_date_from_req_param(self, fin_ent_account_id: str, date_from: datetime.datetime) -> str:
        """The website returns movements filtered by value_date,
        this means that it loses saved movements were value_date < target OperationalDate.
        To deal with it, need to extract movements at least from
        date = date_from - 1 day (but better from the date of the previous movement).
        Again, it is necessary for ability to get movs where, for example
        oper_date = 01/12/2021
        value_date = 30/11/2021.
        It's frequent case for
        ES1701825437660208509436, -a 16808
        ES1901825437600208509306, -a 16808
        """
        date_fmt = project_settings.SCRAPER_DATE_FMT
        movement_before = self.db_connector.get_one_movement_before_date(
            fin_ent_account_id,
            date_from.strftime(date_fmt)
        )

        # prev movement date or prev date
        date_from_upd = (datetime.datetime.strptime(movement_before.OperationalDate, date_fmt)
                         if movement_before
                         else date_from - datetime.timedelta(days=1))

        # respect max offset
        min_allowed_date = date_funcs.offset_dt(MOVEMENTS_MAX_OFFSET + 5)  # it's still < than 90

        # minus one more day (total at least -5 days of target date_from)
        date_from_req_param = max(
            min_allowed_date,
            date_from_upd - datetime.timedelta(days=4)
        ).strftime(date_fmt)

        self.logger.info('{}: set date_from_req_param={} to get movements where value_date < {}'.format(
            fin_ent_account_id,
            date_from_req_param,
            date_from.strftime(date_fmt)
        ))
        return date_from_req_param

    def process_account(self, s: MySession, account_scraped: AccountScraped) -> bool:

        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        rescraping_offset = min(
            MOVEMENTS_RESCRAPE_OFFSET_DAYS.get(
                fin_ent_account_id,
                project_settings.SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_BEFORE_LAST_SCRAPED_MOV
            ),
            project_settings.SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_BEFORE_LAST_SCRAPED_MOV
        )

        date_from, date_from_str = self.basic_get_date_from_dt(
            fin_ent_account_id,
            rescraping_offset=rescraping_offset,
            max_offset=MOVEMENTS_MAX_OFFSET
        )

        should_scrape_ext_descr = self.basic_should_scrape_extended_descriptions()
        # should_scrape_ext_descr = False

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        date_from_req_param_str = self._get_date_from_req_param(fin_ent_account_id, date_from)

        # correct for BBAN only
        req_headers = self.basic_req_headers_updated({
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Referer': 'https://www.bbvanetcash.com/SESKYOP/kyop_mult_web_pub/index-new.html?LOCALE=es_ES'
        })

        movements_parsed_desc = []  # type: List[MovementParsed]
        paginacionMOVDIA_param = '1'
        paginacionTLSMT016_param = 'N00000000000+0000000000000000'
        paginacionTLSMT017_param = 'N000000000000+0000000000000000000'
        ultimoSaldoPaginacionAnterior_param = None
        ultimaFechaPaginacionAnterior_param = None
        has_next_page = True

        page_retries = 0
        max_page_retries = 2
        # Page iteration
        for i in range(300):  # avoid hanging loop
            if not has_next_page:
                break
            # Filters by value_date, see _get_date_from_req_param
            # to deal with it
            req_params = OrderedDict([
                ('cuenta', fin_ent_account_id),
                ('bancoAsunto', '1'),
                ('tipoFecha', 'Rango'),
                ('fechaDesde', date_from_req_param_str),
                ('fechaHasta', self.date_to_str),
                ('periodo', ''),
                ('concepto', ''),
                ('importeDesde', ''),
                ('importeHasta', ''),
                ('divisa', account_scraped.Currency),  # get from account now, was 'EUR'
                ('paginacionTLSMT017', paginacionTLSMT017_param),  # last mov amount
                ('paginacionTLSMT016', paginacionTLSMT016_param),  # last mov sign
                ('paginacionMOVDIA', paginacionMOVDIA_param),
                ('ultimoSaldoPaginacionAnterior', ultimoSaldoPaginacionAnterior_param),
                ('ultimaFechaPaginacionAnterior', ultimaFechaPaginacionAnterior_param),
                ('referenciaBBVA', ''),
                ('referenciaCorresponsal', ''),
                ('iuc', fin_ent_account_id),
                ('saldoContable', str(account_scraped.Balance).replace('.', ',')),  # added since prev version
                ('estadoUpdate', '0'),
                ('ordenacion', 'DESC'),
                ('customer', 'null'),
            ])
            # https://www.bbvanetcash.com/SESEYOZ/eyoz_mult_web_posicioncuentas_01/listarResultadoMovNivel2
            req_url = ('https://www.bbvanetcash.com/SESKYOS/'
                       'kyos_mult_web_posicioncuentas_01/listarResultadoMovNivel2')  # kyos_mult

            resp_movs_i = Response()
            for attempt in range(1, 4):
                resp_movs_i = s.post(
                    req_url,
                    data=req_params,
                    headers=req_headers,
                    proxies=self.req_proxies,
                    timeout=30,
                )
                # keep fields ordering; max 45 mov from page
                try:
                    resp_movs_i_json = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(resp_movs_i.text)
                    break
                except Exception as e:
                    self.logger.warning(
                        "{}: attempt #{}: can't parse resp_movs_i_json\nRESPONSE:\n{}".format(
                            fin_ent_account_id,
                            attempt,
                            resp_movs_i
                        )
                    )
                    time.sleep(1 + random.random() * 0.5)
            else:
                self.logger.error("{}: can't parse resp_movs_i_json. Break the loop. RESPONSE:\n{}".format(
                    fin_ent_account_id,
                    resp_movs_i
                ))
                break

            movements_parsed_i = parse_helpers_netcash.get_movements_parsed_from_json(
                resp_movs_i_json,
                should_scrape_ext_descr
            )
            # repeated movements - hanging loop -> abort it
            if movements_parsed_i:
                # mov_tpls contain only data that don't mutate during
                # page iterations.
                # temp_balance is not suitable bcs it depends on sent ultimoSaldoPaginacionAnterior_param
                mov_tpls = [
                    (m['operation_date'], m['value_date'], m['amount'], m['description'])
                    for m in movements_parsed_desc
                ]
                mov_tpls_i = [
                    (m['operation_date'], m['value_date'], m['amount'], m['description'])
                    for m in movements_parsed_i
                ]
                # -a 4738 (235911 01068378GBP, 235911 01084839GBP):
                # next page contains movs from prev page + repeats them on the next page,
                # it's a hanging pagination
                # (the movs are repeating and actually,
                #   the backend shouldn't return 'More records available')
                # so, to detect this case contains.is_sublist(mov_tpls_i, mov_tpls) is necessary
                # (see dev/20_resp_movs_hanging_i1.json, dev/20_resp_movs_hanging_i2.json)
                if (list_funcs.is_sublist(mov_tpls, mov_tpls_i)
                        or (mov_tpls and list_funcs.is_sublist(mov_tpls_i, mov_tpls))):
                    msg = '{}: got REPEATED {} movements from page since {} till {}.'.format(
                        fin_ent_account_id,
                        len(movements_parsed_i),
                        movements_parsed_i[0]['operation_date'],
                        movements_parsed_i[-1]['operation_date']
                    )
                    page_retries += 1
                    if page_retries < max_page_retries:
                        self.logger.warning(msg + ' It looks like broken pagination. Retry #{}'.format(page_retries))
                        continue  # retry with the same req_params
                    self.logger.warning(msg + ' It looks like broken pagination. Abort the loop')
                    movements_parsed_i = []  # clean broken movs
                    break  # no chance to get correct movements, broken pagination

            page_retries = 0
            movements_parsed_desc += movements_parsed_i

            # date < date_from reached - stop pagination
            if movements_parsed_i:
                if datetime.datetime.strptime(movements_parsed_i[-1]['operation_date'], '%d/%m/%Y') < date_from:
                    self.logger.info('{}: reached page mov operational date < date_from. Abort pagination'.format(
                        fin_ent_account_id
                    ))
                    break

            # update req params

            # -u 92282 -a 2701: 78001601118540EUR: found 'More records available' even if
            # there are no movements_parsed_from_page
            has_next_page = bool(
                movements_parsed_i
                and resp_movs_i_json['data'].get('descripcion', '') == 'More records available'
            )

            paginacionTLSMT016_param = resp_movs_i_json['data'].get('paginacionTLSMT016', '')
            paginacionTLSMT017_param = resp_movs_i_json['data'].get('paginacionTLSMT017', '')
            paginacionMOVDIA_param = resp_movs_i_json['data'].get('paginacionMOVDIA', '')  # critical
            if movements_parsed_i:
                # need to send correct temp_bal of the first mov from the next page
                temp_bal = round(movements_parsed_i[-1]['temp_balance'] - movements_parsed_i[-1]['amount'], 2)
                # backend expects '35.022,46', we end '35022,46'
                ultimoSaldoPaginacionAnterior_param = str(temp_bal).replace('.', ',')
                ultimaFechaPaginacionAnterior_param = movements_parsed_i[-1]['operation_date']
                self.logger.info('{}: got {} movements from page since {} to {}'.format(
                    fin_ent_account_id,
                    len(movements_parsed_i),
                    movements_parsed_i[0]['operation_date'],
                    movements_parsed_i[-1]['operation_date']
                ))
            else:
                self.logger.info('{}: no movements from page'.format(fin_ent_account_id))

            if has_next_page:
                self.logger.info('{}: should open next page with movements'.format(fin_ent_account_id))
            else:
                self.logger.info('{}: no need to open previous page with movements'.format(
                    fin_ent_account_id
                ))

            if has_next_page and not movements_parsed_i:
                self.logger.error(
                    '{}: should open next page with movements, '
                    'but no movement_parsed from the current page. Skip.'
                    '\nRESPONSE:\n{}'.format(
                        fin_ent_account_id,
                        resp_movs_i.text
                    )
                )
                break  # todo retry?

        # End of page iteration

        date_fmt = '%d/%m/%Y'

        # log future movements
        for mov in movements_parsed_desc:
            mov_date = datetime.datetime.strptime(mov['operation_date'], date_fmt)
            if mov_date > self.today:
                self.logger.info("{}: scraped future movement: {}".format(
                    fin_ent_account_id, mov
                ))

        movements_parsed_desc_filtered = [
            m for m in movements_parsed_desc
            if datetime.datetime.strptime(m['operation_date'], date_fmt) >= date_from
        ]
        is_verified_temp_balances = parse_helpers_netcash.verify_temp_balances(movements_parsed_desc_filtered)
        movements_parsed_desc_verified = (
            movements_parsed_desc_filtered if is_verified_temp_balances
            # replace with parsed balances which raise balance err
            else parse_helpers_netcash.replace_temp_balances_calc_by_parsed(movements_parsed_desc_filtered)
        )

        # Avoid further expensive work for bad temp_balances
        if should_scrape_ext_descr and not is_verified_temp_balances:
            self.logger.warning('{}: should_scrape_ext_descr but got unverified temp_balances. '
                                'Set should_scrape_ext_descr=False'.format(fin_ent_account_id))
            should_scrape_ext_descr = False

        # New since 3.0.0 to provide incremental uploading even on 500 errs
        # while extended descriptions scraping
        movements_parsed_asc = list(reversed(movements_parsed_desc_verified))
        movements_parsed_extended_descr_asc = movements_parsed_asc

        if should_scrape_ext_descr:
            # Really get extended descriptions (and receipt params)
            # Note: if got 500, then it returns as many movements as possible to
            # return before 500 occurred

            # Exclude 500 to handle it manually 'service unavailable'
            s.resp_codes_bad_for_proxies = [502, 503, 504, 403, None]
            movements_parsed_extended_descr_asc = self.basic_get_movements_parsed_w_extra_details(
                s,
                movements_parsed_asc,
                account_scraped,
                date_from_str,
                n_mov_details_workers=PROCESS_MOVEMENT_MAX_WORKERS
            )
            # Restore defaults
            s.resp_codes_bad_for_proxies = RESP_CODES_BAD_FOR_PROXIES

        if len(movements_parsed_extended_descr_asc) < len(movements_parsed_asc):
            self.logger.warning(
                '{}: only {} of {} will be saved, '
                'because it was possible to get extra details only for those movements '
                '(the last one is {})'.format(
                    fin_ent_account_id,
                    len(movements_parsed_extended_descr_asc),
                    len(movements_parsed_asc),
                    extract.by_index_or_none(movements_parsed_extended_descr_asc, -1)
                )
            )

        movements_scraped, movements_parsed_corresponding = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_extended_descr_asc,
            date_from_str,
            bankoffice_details_name='Oficina',
            payer_details_name='Observaciones',
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        if should_scrape_ext_descr:
            self.logger.info(
                "{}: update extended descriptions for {} movements "
                "(may take a while)".format(
                    fin_ent_account_id,
                    len(movements_scraped)
                )
            )
            self.basic_update_movements_extended_descriptions_if_necessary(
                account_scraped,
                movements_scraped
            )

        # Relogin to avoid expired session
        self.login()
        self.download_receipts(
            s,
            account_scraped,
            movements_scraped,
            movements_parsed_corresponding
        )

        return True

    def process_movement(self,
                         s: MySession,
                         movement_parsed: MovementParsed,
                         fin_ent_account_id: str,
                         meta: dict = None) -> Optional[MovementParsed]:
        """Some movements have more description details
        which can be obtained only after extra http request

        Optimization:
        - if the scraper is not a receipts_scraper and the movement already saved,
          then it will not process movement (i.e. not open using additional HTTP req).
        - in other cases (movement not saved or it is a receipts_scraper even for saved movement),
          then it will process the movement to extract extra details
          (extended description and pdf req params)
        """

        mov_str = self.basic_mov_parsed_str(movement_parsed)

        # To drop all movements after 500
        if self._is_got_critical_scraping_err(fin_ent_account_id):
            self.logger.info(
                '{}: {}: skip movement processing due to previous critical scraping error'.format(
                    fin_ent_account_id,
                    mov_str
                )
            )
            return None

        # Get extra details only for movements with specific marker,
        # other movements already have all provided info
        if not movement_parsed['has_extra_details']:
            self.logger.info('{}: {}: has no extra details'.format(fin_ent_account_id, mov_str))
            return movement_parsed

        self.logger.info('{}: {}: process movement'.format(fin_ent_account_id, mov_str))

        time.sleep(0.1 + 0.1 * random.random())  # 0.1...0.2 sec
        # since 3.2.0
        # ok for -u 304902 -a 18014, acc 9181; -u 290483 -a 16808
        # was .../kyos_mult_web_posicioncuentas_01/...
        req_url = ('https://www.bbvanetcash.com/SESEYOZ/'
                   'eyoz_mult_web_posicioncuentas_01/getDetalleMovimientoAmpliado')
        req_params = movement_parsed['mov_details_params']

        n_of_500 = 0  # allow n attempts (1 now)
        resp_extra_details = Response()
        for attempt in range(1, 4):
            resp_extra_details = s.post(
                req_url,
                data=req_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
                timeout=30,
            )

            # new since 3.0.0
            # Got 'service unavailable' - can't process more movements
            if (resp_extra_details.status_code == 500
                    and 'Servicio temporalmente no disponible' in resp_extra_details.text):
                n_of_500 += 1
                # allow 1 additional attempt - really can get temp 500
                if n_of_500 <= 1:
                    self.logger.warning("{}: {} got 500 {} time(s). Wait and retry".format(
                        fin_ent_account_id,
                        mov_str,
                        n_of_500
                    ))
                    time.sleep(1 + random.random())
                    continue
                n_failed = self._inc_n_failed_movements()
                if n_failed <= MAX_ALLOWED_FAILED_MOVEMENTS:
                    self.logger.warning(
                        "{}: {}: got 500. increased n_failed_movements. "
                        "Use movement_parsed w/o extended description".format(
                            fin_ent_account_id,
                            mov_str
                        )
                    )
                    return movement_parsed
                else:
                    self._set_got_critical_scraping_err(fin_ent_account_id)
                    self.logger.error(
                        "{}: {}: got 500. Set 'got critical scraping err' to interrupt further details extraction".format(
                            fin_ent_account_id,
                            mov_str
                        )
                    )
                    return None

            # handle err:
            # {'errorInfo': OrderedDict([('errorCode', '2'), ('errorTitle', None),
            # ('errorDescription', 'ObtenerDetalleMovimiento: Error al ...'),
            # ('errorKeyTitle', None), ('errorKeyDescription', None),
            # ('debugMessage', None), ('debugTrace', None)]),
            # 'data': None, 'success': False}

            # correct:
            # {"success":true,
            # "errorInfo":{"errorCode":"0","errorTitle":null,
            # "errorDescription":"OK","errorKeyTitle":null,
            # "errorKeyDescription":null,"debugMessage":null,"debugTrace":null},
            # "data":{"codError":0,"codRetorno":0,"descripcion":"OK",
            # "detalle":[],"reutilizarOperacion":false,
            # "ordenReutilizarOperacion":"","detallesPdf":[]}}

            resp_extra_deatails_json_temp = {}  # type: Dict[str, Any]
            try:
                resp_extra_deatails_json_temp = resp_extra_details.json()
            except:
                # checks final results
                # and raises Exception after the loop
                # if can't extract details
                pass
            if resp_extra_deatails_json_temp.get('success'):
                break

            # In some cases the user doesn't have permissions to extract movement's details

            # {"success":false,"errorInfo":{"errorCode":"2",
            # "errorTitle":null,
            # "errorDescription":"ObtenerDetalleMovimiento:
            #   Error al recibir los detalles del servicio WireTransfersV02,
            #   id: 0011018218112410185789-RE-ES0182002000000000000000000196845849XXXXXXXXX,
            #  filtro: (transactionDate==2018-11-19).\nExcepcion:{\"version\":1,\"severity\":\"FATAL\",
            # \"http-status\":409,\"error-code\":\"contractNotRight\",
            # \"error-message\":\"El usuario no puede operar con la informaciÃ³n de contrato facilitada\",
            # \"consumer-request-id\":\"14097aa7-3199-4ecc-8772-b1a5d249b034\",
            # \"system-error-code\":\"contractNotRight\",
            # \"system-error-description\":
            #   \"El usuario no puede operar con la informaciÃ³n de contrato facilitada\"}",
            # "errorKeyTitle":null,"errorKeyDescription":null,"debugMessage":null,"debugTrace":null},"data":null}

            # OR there are no details yet (but will appear in the future)

            # {"success":false,"errorInfo":{"errorCode":"2","errorTitle":null,
            # "errorDescription":"ObtenerDetalleMovimiento: Error al recibir los detalles del servicio
            # WireTransfersV02,
            # id: 0011018219022727407565-EM-ES0182001000000000000000000402779116XXXXXXXXX,
            # filtro: (transactionDate==2019-02-01).\nExcepcion:{\"version\":1,\"severity\":\"FATAL\",
            # \"http-status\":409,\"error-code\":\"00865022\",\
            # "error-message\":\"NO EXISTEN DATOS PARA LA CONSULTA REALIZADA\",
            # \"consumer-request-id\":\"cfae7cdc-f6b5-49e9-8c44-88ed93855a1a\",
            # \"system-error-code\":\"functionalError\",
            # \"system-error-description\":\"Error funcional por
            # defecto.\",\"system-error-cause\":
            # \"00865022(EBEX): NO EXISTEN DATOS PARA LA CONSULTA REALIZADA\"}",
            # "errorKeyTitle":null,"errorKeyDescription":null,"debugMessage":null,
            # "debugTrace":null},"data":null}

            if any(m in resp_extra_details.text for m in MOV_EXTRA_DETAILS_NON_CRITICAL_ERR_MARKERS):
                self.logger.warning(
                    '{}: invalid but not critical extra details for movement {}.\n'
                    'Use current extended description.\n'
                    'RESPONSE:\n{}'.format(
                        fin_ent_account_id,
                        mov_str,
                        resp_extra_details.text
                    )
                )
                return movement_parsed

            self.logger.warning(
                '{}: {}: mov extra description: attempt #{} to get correct resp. '
                'Now got RESPONSE\n{}'.format(
                    fin_ent_account_id,
                    mov_str,
                    attempt,
                    resp_extra_details.text
                )
            )
            if attempt < 3:  # don't wait after final failed attempt
                time.sleep(attempt * (random.random() + 0.5))
        # else for
        else:
            n_failed = self._inc_n_failed_movements()
            if n_failed <= MAX_ALLOWED_FAILED_MOVEMENTS:
                self.logger.warning(
                    "{}: {}: couldn't get extra details. "
                    "Use movement_parsed w/o extended description and receipt req params".format(
                        fin_ent_account_id,
                        mov_str
                    )
                )
                return movement_parsed
            else:
                self.logger.error(
                    "{}: {}: set 'got critical scraping err' to interrupt further details extraction. "
                    "Reason: can't get correct resp_extra_details."
                    "\n\nmov_details_request_params:{}\n\n"
                    "\n\nRESPONSE\n{}".format(
                        fin_ent_account_id,
                        mov_str,
                        req_params,
                        resp_extra_details.text
                    )
                )
                self._set_got_critical_scraping_err(fin_ent_account_id)
                return None

        resp_extra_details_json = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(resp_extra_details.text)
        movement_parsed_updated, detalle_is_none = parse_helpers_netcash.mov_parsed_add_extra_details(
            movement_parsed,
            resp_extra_details_json
        )
        if detalle_is_none:
            self.logger.error(
                '{}: parsed extra description where "detalle" is None (possible error): {}:'
                '\nRESPONSE\n{}'.format(
                    fin_ent_account_id,
                    movement_parsed,
                    resp_extra_details.text
                )
            )
        return movement_parsed_updated

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

        s, resp_json, accounts_scraped = self.get_accounts_scraped(s)

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        # get and save movements
        if accounts_scraped:
            if project_settings.IS_CONCURRENT_SCRAPING:
                with futures.ThreadPoolExecutor(max_workers=PROCESS_ACCOUNT_MAX_WORKERS) as executor:

                    futures_dict = {
                        executor.submit(self.process_account, s, account_scraped):
                            account_scraped.FinancialEntityAccountId
                        for account_scraped in accounts_scraped
                    }

                    self.logger.log_futures_exc('process_account', futures_dict)
            else:
                for account_scraped in accounts_scraped:
                    self.process_account(s, account_scraped)

        self.basic_log_time_spent('GET MOVEMENTS')

        self.download_correspondence(s, resp_logged_in)

        return self.basic_result_success()
