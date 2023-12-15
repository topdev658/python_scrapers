import os
import random
import subprocess
import time
import urllib.parse
from typing import List, Tuple, Optional, Dict

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    AccountParsed, MOVEMENTS_ORDERING_TYPE_ASC,
    MovementParsed, ScraperParamsCommon, MainResult,
    DOUBLE_AUTH_REQUIRED_TYPE_COMMON
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.caixa_geral import parse_helpers
from .custom_types import ContractSwitchParams

__version__ = '5.15.0'

__changelog__ = """
5.15.0 2023.06.15
process_contract: get resp_accs_url calling get_link_by_text extract method 
5.14.0
upd ACCOUNTS_CUSTOM_OFFSET
5.13.0
use account-level result_codes
5.12.0
call basic_upload_movements_scraped with date_from_str
5.11.0
skip inactive accounts
5.10.0
process_account:
  custom rescraping_offset based on ACCOUNTS_CUSTOM_OFFSET
  notification if many movements
5.9.0
login: more detectors for double auth and wrong credentials
5.8.0
more wrong credentials markers (suitable for bancofar too)
5.7.2
aligned double auth msg
5.7.1
upd comments: now it's only a parent for some other scrapers
5.7.0
use basic_new_session
upd type hints
5.6.0
process_contract: serial process_account, removed concurrent processing (messed movs)
5.5.0
_check_selected_account (to use also from children)
_get_selected_account_id
parse_helpers: get_selected_account_id
5.4.0
_check_selected_account (always True here, must override by children)
process_account: 
  several attempts if selected wrong account (may occur while parallel scraping)
5.3.0
_after_login_hook
parse_helpers: continue if can't parse contract params, upd log msgs (WRONG LAYOUT marker)
more type hints
5.2.0
detect sms auth reason, changed login() signature
5.1.0
use basic_get_date_from
5.0.0
multicontract support
4.3.0
more credentials error markers
4.2.0
increased timeout for requests (handle long latency) 
4.1.0
basic_movements_scraped_from_movements_parsed: new format of the result 
4.0.0
adopted to be parent for vwbank scraper
3.2.0
parse_helpers: skip credit accounts with 'FIN.EXPORT' and 'FIN.IMPORT' in descr
3.1.0
parse helpers: logger warnings
parse helpers: parse movements: handle movements if there are no value date -> skip
3.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
2.0.0
basic_movements_scraped_from_movements_parsed
OperationalDatePosition, KeyValue support
"""

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'caixa_geral_encrypter.js'
))

CREDENTIALS_ERROR_MARKERS = [
    'Usuario bloqueado',
    'Usuario o clave incorrecto',
    'Está bloqueado por excesivos intentos de PIN',  # bancofar
    'El numero de identificacion no aparece como correcto',  # bancofar
    'El Usuario está bloqueado de forma anomala',  # bancofar
]

DOUBLE_AUTH_MARKERS = [
    'Código de seguridad SMS',
    'ecibirá en su teléfono móvil un código que debe introducir',  # bancofar
]

ACCOUNTS_CUSTOM_OFFSET = {
    # VolkswagenBank, too many movements.
    # Websites strips movs over 500 (450?)
    '1480-0010-99-0100043260': 7,
    '1480-0010-96-0100007890': 7,
}


class CaixaGeralScraper(BasicScraper):
    """This scraper implementation is only used as a parent for
    VolkswagenScraper and CajaIngenierosScraper.
    CiaxaGeral scraper since 03/2020 uses become Abanaca.
    caixa_geral_from_abanca/.. is correct CaixaGeralScraper now.
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='CaixaGeralScraper',
                 website='https://bancaporinternet.bancocaixageral.es',
                 camino_param='0130',
                 caja_param='0130') -> None:

        self.scraper_name = scraper_name
        self.website = website
        self.camino_param = camino_param
        self.caja_param = caja_param

        super().__init__(scraper_params_common, proxies)

        self.update_inactive_accounts = False

    # for explicit redefining from child
    def _get_contracts_switch_params(self, resp_contracts: Response) -> List[ContractSwitchParams]:
        return parse_helpers.get_contracts_params(resp_contracts.text, resp_contracts.url, self.logger)

    # for explicit redefining from child
    def _get_accounts_parsed(self, resp_accs) -> List[AccountParsed]:
        return parse_helpers.get_accounts_parsed(resp_accs.text, self.logger)

    # for explicit redefining from child
    def _get_movements_parsed(self, resp_mov, fin_ent_account_id: str) -> List[MovementParsed]:
        return parse_helpers.get_movements_parsed(resp_mov.text, fin_ent_account_id, self.logger)

    def _auth_url(self) -> str:
        return '{}/BEWeb/{}/{}/'.format(self.website, self.camino_param, self.caja_param)

    def _authreq_post_params(self, pin: str, sello_param: str) -> Dict[str, str]:
        return {
            'CAMINO': self.camino_param,
            'CAJA': self.caja_param,
            'IDIOMA': '01',
            'PARTICULAR': '',
            'OPERACION': '0002',
            'SELLO': sello_param,
            'PINV3': 'si',
            'IDEN': '',
            'BROKER': 'SI',
            'PAN': self.username_second,
            'PIN': pin,
            'USUARIOEMPRESA': self.username.upper(),
            'MENU': '',
            'VERSIONJJ': ''
        }

    def _movreq_post_params(self, basic_params: dict, date_from_str: str) -> dict:
        # OPERAC=5838?
        req_mov_params = basic_params
        date_from_str_formatted = date_from_str.replace('/', '-')
        date_to_str_formatted = self.date_to_str.replace('/', '-')

        req_mov_params['FECINI'] = date_from_str_formatted
        req_mov_params['FECFIN'] = date_to_str_formatted
        req_mov_params['FECINIAUX'] = date_from_str_formatted
        req_mov_params['FECFINAUX'] = date_to_str_formatted

        return req_mov_params

    def _get_encrypted(self, clave: str) -> str:
        cmd = '{} "{}" "{}"'.format(CALL_JS_ENCRYPT_LIB, clave, self.userpass)
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def _after_login_hook(
            self,
            s: MySession,
            resp_logged_in: Response) -> Tuple[MySession, Response, bool, str]:
        """Additional step when logged in, mostly to click 'continue' on notices etc.
        Will be called ONLY IF is_logged is True.
        This parent method doesn't take any action, redefine it in a child if necessary.

        :returns (session, resp_logged_in, is_logged_after_this_step, reason_after_this_step)
        """
        return s, resp_logged_in, True, ''

    def _get_selected_account_id(self, resp_text: str) -> str:
        """Set specific function here, can redefine in a child"""
        return parse_helpers.get_selected_account_id(resp_text)

    def _check_selected_account(self,
                                resp_movs: Response,
                                fin_ent_account_id: str) -> bool:
        """Allows to check that switched to correct account
        during the parallel scraping

        Use it for resp_mov

        :param resp_movs: response with filtered movements
        :param fin_ent_account_id: str
        """
        fin_ent_account_id_selected = self._get_selected_account_id(resp_movs.text)
        if not fin_ent_account_id_selected:
            self.basic_log_wrong_layout(
                resp_movs,
                "Can't extract selected_account_id. Expected '{}', got ''".format(
                    fin_ent_account_id
                )
            )
        # [-7:] due to possible changes in prev digits even for the same acc
        is_correct = (fin_ent_account_id_selected.replace('-', '')[-7:] ==
                      fin_ent_account_id.replace('-', '')[-7:])
        return is_correct

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()

        # to get cookies
        s.get(
            self._auth_url() + 'inicio_identificacion.action',
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20
        )

        resp2 = s.get(
            self._auth_url() + 'inicio_identificacion_sello.action',
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20
        )

        sello_param = extract.re_first_or_blank(r'sello\s*:\s*"(.*?)"', resp2.text)
        clave_calcula_param = extract.re_first_or_blank(r'claveCalcula\s*:\s*"(.*?)"', resp2.text)
        # sessionId = extract.re_first_or_blank('sessionId\s*:\s*"(.*?)"', resp2.text)

        pin = self._get_encrypted(clave_calcula_param)

        req_login_params = self._authreq_post_params(pin, sello_param)
        resp_logged_in = s.post(
            self._auth_url() + 'identificacion.action',
            data=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20
        )

        is_logged = self._auth_url() + 'pag0002m.action' in resp_logged_in.url
        reason = ''
        if any(m in resp_logged_in.text for m in DOUBLE_AUTH_MARKERS):
            is_logged = False
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON
        is_credentials_error = any(m in resp_logged_in.text for m in CREDENTIALS_ERROR_MARKERS)

        if is_logged:
            s, resp_logged_in, is_logged, reason = self._after_login_hook(s, resp_logged_in)

        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        self.logger.info('process_access')

        # expect
        # https://bancaporinternet.bancocaixageral.es/
        # BEWeb/0130/0130/pagContenidoLogoCargando.action
        # ?OPERACION=pagContenidoLogoCargando&IDIOMA=01&OPERAC=1004
        # &LLAMADA=B123Z140H2C0H0E1W0E1&CLIENTE=0130900261
        # &CAJA=0130&CAMINO=0130
        req_after_login_hid_step_url = urllib.parse.urljoin(
            resp_logged_in.url,
            extract.re_first_or_blank(
                'id="contenedor" src="(.*?)"',
                resp_logged_in.text
            )
        )

        resp_after_login_hid_step = s.get(
            req_after_login_hid_step_url,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20
        )

        contracts_switch_params = self._get_contracts_switch_params(resp_after_login_hid_step)

        if not contracts_switch_params:
            # one contract
            self.logger.info('One contract detected')
            self.process_contract(s, resp_after_login_hid_step, 0)
        else:
            self.logger.info('Multicontract detected. Found contracts {}'.format(
                [c.title for c in contracts_switch_params]
            ))
            # only serial processing allowed
            for ix, contract_params in enumerate(contracts_switch_params):
                self.process_contract(s, resp_after_login_hid_step, ix, contract_params)

        return True

    def _open_contract_by_idx(self,
                              s: MySession,
                              contract_switch_params: ContractSwitchParams,
                              ix: int) -> Tuple[MySession, Response, bool, str]:
        """If ix > 0, need to log in again and extracts new params
        or it opens first contract each time
        Also, need to log in each time (not just switch) because if there are no accounts
        ('NO HAY DATOS PARA LA CONSULTA' marker) - the website logout automatically

        :param ix: index of contract in the list
        :returns (session, resp_contract, is_logged_in, reason)
        """

        if ix == 0:
            # first contract of multicontract
            resp_contract = s.post(
                contract_switch_params.url,
                data=contract_switch_params.req_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
                timeout=20
            )
            return s, resp_contract, True, ''

        s, resp_logged_in, is_logged_in, is_credentials_error, reason = self.login()
        if not is_logged_in:
            return s, Response(), False, reason

        # several steps when logged in
        req_after_login_hid_step_url = urllib.parse.urljoin(
            resp_logged_in.url,
            extract.re_first_or_blank(
                'id="contenedor" src="(.*?)"',
                resp_logged_in.text
            )
        )

        resp_after_login_hid_step = s.get(
            req_after_login_hid_step_url,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20
        )

        contracts_switch_params = self._get_contracts_switch_params(resp_after_login_hid_step)
        contract_switch_params = contracts_switch_params[ix]
        resp_contract = s.post(
            contract_switch_params.url,
            data=contract_switch_params.req_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20
        )
        return s, resp_contract, True, ''

    def process_contract(
            self,
            s: MySession,
            resp_after_login_hid_step: Response,
            ix: int,
            contract_switch_params: Optional[ContractSwitchParams] = None) -> bool:

        contract_title = contract_switch_params.title if contract_switch_params else '<default>'
        self.logger.info('process_contract {}: {}'.format(ix, contract_title))
        # one contract
        if not contract_switch_params:
            resp_contract = resp_after_login_hid_step
        # multicontract
        else:
            s, resp_contract, is_logged_in, reason = self._open_contract_by_idx(s, contract_switch_params, ix)
            if not is_logged_in:
                self.logger.error("Can't log in to process contract {}: {}. Reason: {}. Abort".format(
                    ix,
                    contract_title,
                    reason
                ))
                return False

        # expect
        # https://bancaporinternet.bancocaixageral.es/
        # BEWeb/0130/0130/oper9827_m_mcd.action?OPERACION=oper9827_m_mcd
        # &IDIOMA=01&OPERAC=1004&LLAMADA=B123Z140H2C0H0E1W0E1
        # &CLIENTE=0130900261&CAJA=0130&CAMINO=0130'
        req_accs_url = extract.get_link_by_text(resp_contract.text, resp_contract.url, 'Posición Global')

        if req_accs_url:
            # accounts overview
            resp_accs = s.post(
                req_accs_url,
                headers=self.req_headers,
                proxies=self.req_proxies,
                timeout=20
            )
        else:
            resp_accs = resp_contract

        accounts_parsed = self._get_accounts_parsed(resp_accs)
        company_title = (contract_switch_params.title
                         if contract_switch_params
                         else parse_helpers.get_company_title(resp_accs.text))

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                company_title or self.db_customer_name,
                account_parsed,
                is_default_organization=False if company_title else True
            )
            for account_parsed in accounts_parsed
        ]

        self.logger.info('Contract {} has accounts: {}'.format(contract_title, accounts_scraped))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        # ONLY SINCE 5.6.0, serial processing
        # to avoid messed movements even if selected account confirmed
        for account_parsed in accounts_parsed:
            self.process_account(s, resp_accs, account_parsed, company_title)

        # Temporary commented since 5.6.0 to avoid movements
        # returned for another account

        # if accounts_scraped:
        #     if project_settings.IS_CONCURRENT_SCRAPING:
        #         with futures.ThreadPoolExecutor(max_workers=len(accounts_scraped)) as executor:
        #
        #             futures_dict = {
        #                 executor.submit(self.process_account, s, resp_accs,
        #                                 account_parsed, company_title): account_parsed['account_no']
        #                 for account_parsed in accounts_parsed
        #             }
        #
        #             self.logger.log_futures_exc('process_account', futures_dict)
        #     else:
        #         for account_parsed in accounts_parsed:
        #             self.process_account(s, resp_accs, account_parsed, company_title)

        return True

    def process_account(
            self,
            s: MySession,
            resp: Response,
            account_parsed: AccountParsed,
            company_title: str) -> bool:

        account_no = account_parsed['account_no']
        fin_ent_account_id = account_parsed['financial_entity_account_id']

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        rescraping_offset = ACCOUNTS_CUSTOM_OFFSET.get(fin_ent_account_id, None)
        date_from_str = self.basic_get_date_from(fin_ent_account_id, rescraping_offset=rescraping_offset)

        self.basic_log_process_account(account_no, date_from_str)

        req_mov_url = urllib.parse.urljoin(resp.url, account_parsed['mov_req_url_raw'])
        req_mov_params = self._movreq_post_params(account_parsed['mov_req_params'], date_from_str)

        for i in range(3):
            resp_mov = s.post(
                req_mov_url,
                data=req_mov_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
                timeout=20
            )
            if self._check_selected_account(resp_mov, fin_ent_account_id):
                break
            # wait before the next attempt
            self.logger.warning("{}: can't switch to correct account in resp_mov. Retry")
            time.sleep(1 + random.random())
        else:
            self.logger.error("{}: can't switch to correct account in resp_mov. Abort")
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_CANT_SWITCH_TO_ACCOUNT)
            return False

        movements_parsed = self._get_movements_parsed(resp_mov, fin_ent_account_id)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        if len(movements_scraped) >= 450:  # limit is 500, but notice on 450
            self.logger.warning(
                "{}: too many movements. "
                "Probably, some of the movements from {} weren't displayed, "
                "that may cause a balance integrity error. "
                "Pls, scrape from later date OR set custom offset in "
                "ACCOUNTS_CUSTOM_OFFSET".format(fin_ent_account_id, movements_scraped[0].OperationalDate)
            )

        self.basic_log_process_account(account_no, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            self.basic_account_scraped_from_account_parsed(company_title, account_parsed),
            movements_scraped,
            date_from_str=date_from_str
        )
        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp_logged_in.url, resp_logged_in.text,
                                                              reason)

        self.process_access(s, resp_logged_in)

        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
