import random
import time
import urllib.parse
from collections import OrderedDict
from typing import Dict, Tuple

from custom_libs import list_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    AccountParsed, AccountScraped, MOVEMENTS_ORDERING_TYPE_ASC,
    MovementParsed, ScraperParamsCommon, MainResult
)
from scrapers.bancofar_scraper import parse_helpers as bf_parse_helpers
from scrapers.caixa_geral.caixa_geral_scraper import CaixaGeralScraper

__version__ = '1.9.0'

__changelog__ = """
1.9.0
use renamed list_funcs
1.8.0
use account-level result_codes
1.7.0
call basic_upload_movements_scraped with date_from_str
1.6.1
fixed log msgs
1.6.0
skip inactive accounts
1.5.0
access denied detector (due to inactive account)
1.4.0
MySession with self.logger
1.3.1
upd type hints
1.3.0
_get_selected_account_id
process_account: use _check_selected_account
parse_helpers: get_selected_account_id
1.2.0
parse_helpers: get_accounts_parsed: skip accounts without IBAN (they are not current accounts) 
1.1.1
process_account: fixed self.basic_log_wrong_layout(resp_movs_i, ...) instead of resp_movs
1.1.0
extended descriptions impl
1.0.0
init
"""


class BancofarScraper(CaixaGeralScraper):
    """Uses only login() from parent CaixaGeralScraper"""
    scraper_name = 'BancofarScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common,
                         proxies,
                         self.scraper_name,
                         website='https://bancofarnet.bancofar.es',
                         caja_param='0125',
                         camino_param='6125')
        self.update_inactive_accounts = False

    def _auth_url(self) -> str:
        return '{}/BEWeb/{}/{}/'.format(self.website, self.caja_param, self.camino_param)

    def _authreq_post_params(self, pin: str, sello_param: str) -> dict:
        return OrderedDict([
            ('CAJA', self.caja_param),
            ('CAMINO', self.camino_param),
            ('SELLO', sello_param),
            ('OPERACION', '0002'),
            ('BROKER', 'SI'),
            ('IDIOMA', '01'),
            ('PIN', pin),
            ('INDSELLO', '1'),
            ('IDEN', 'CL'),
            ('FLO', ''),
            ('PINV3', 'si'),
            ('NAVEGADOR', ''),
            ('VERSION', ''),
            ('CLAVE', '****'),
            ('acceso', 'P'),
            ('PAN', str(self.username).upper()),
            ('AUXPIN', '****')
        ])

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s, resp_pre_logged, is_logged, is_credentials_error, reason = super().login()
        # extra action required
        req_link, req_params = extract.build_req_params_from_form_html_patched(
            resp_pre_logged.text,
            'login'
        )

        # err message - access denied
        if not reason and 'No hay movimientos para la consulta solicitada' in resp_pre_logged.text:
            reason = 'Access denied due to inactive account (?). Pls, check the website manually.'

        if is_logged or is_credentials_error or not req_link:
            return s, resp_pre_logged, is_logged, is_credentials_error, reason

        resp_logged_in = s.post(
            urllib.parse.urljoin(resp_pre_logged.url, req_link),
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        llamada_param = req_params['LLAMADA']

        # skip 2 factor auth attention
        req_posglobal_params = {
            'OPERACION': 'ont9827_m_COMUN',
            'IDIOMA': '01',
            'OPERAC': '1004',
            'LLAMADA': llamada_param,
            'CLIENTE': self.username,
            'CAJA': self.caja_param,
            'CAMINO': self.camino_param
        }
        resp_pos_global = s.get(
            urllib.parse.urljoin(self._auth_url(), 'ont9827_m_COMUN.action'),  # jsessionid is not necessary
            params=req_posglobal_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = llamada_param and ('Posici&oacute;n global' in resp_pos_global.text)
        # we already don't expect credentials error here (checked earlier)

        return s, resp_pos_global, is_logged, is_credentials_error, reason

    def process_contract(self, s: MySession, resp_logged_in: Response, *args) -> bool:
        ok, accounts_parsed = bf_parse_helpers.get_accounts_parsed(resp_logged_in.text)
        if not ok:
            self.basic_log_wrong_layout(resp_logged_in, "Can't get accounts_parsed. Abort")
            return False

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                self.db_customer_name,
                account_parsed,
                is_default_organization=True
            )
            for account_parsed in accounts_parsed
        ]

        self.logger.info('Got {} account(s): {}'.format(len(accounts_scraped), accounts_scraped))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        accounts_scraped_dict = self.basic_gen_accounts_scraped_dict(accounts_scraped)

        for account_parsed in accounts_parsed:
            self.process_account(s, resp_logged_in, account_parsed, accounts_scraped_dict)

        return True

    def _get_selected_account_id(self, resp_text: str) -> str:
        """Override parent for the specific parsing func"""
        return bf_parse_helpers.get_selected_account_id(resp_text)

    def process_account(self,
                        s: MySession,
                        resp_accs: Response,
                        account_parsed: AccountParsed,
                        accounts_scraped_dict: Dict[str, AccountScraped]) -> bool:

        fin_ent_account_id = account_parsed['financial_entity_account_id']

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        account_scraped = accounts_scraped_dict[fin_ent_account_id]

        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        date_from_str_param = date_from_str.replace('/', '')
        date_to_str_param = self.date_to_str.replace('/', '')

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        _, req_movs_params = extract.build_req_params_from_form_html_patched(
            resp_accs.text,
            'datos'
        )

        if not req_movs_params:
            self.basic_log_wrong_layout(
                resp_accs,
                "{}: can't get req_movs_params. Skip process_account".format(fin_ent_account_id)
            )
            return False

        req_movs_params['GCUENTA'] = fin_ent_account_id
        req_movs_params['FECINI'] = date_from_str_param
        req_movs_params['FECFIN'] = date_to_str_param

        req_mov_url = urllib.parse.urljoin(self._auth_url(), 'not5838_d_5838m.action')

        # resp_movs = s.post(
        #     urllib.parse.urljoin(self._auth_url(), 'not5838_d_5838m.action'),
        #     data=req_movs_params,
        #     headers=self.req_headers,
        #     proxies=self.req_proxies
        # )

        # Retry similar to Caixa Geral
        for i in range(3):
            resp_movs = s.post(
                req_mov_url,
                data=req_movs_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
                timeout=20
            )
            if self._check_selected_account(resp_movs, fin_ent_account_id):
                break
            # wait before the next attempt
            self.logger.warning("{}: can't switch to correct account in resp_mov. Retry".format(
                fin_ent_account_id
            ))
            time.sleep(1 + random.random())
        else:
            self.logger.error("{}: can't switch to correct account in resp_mov. Abort".format(
                fin_ent_account_id
            ))
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_CANT_SWITCH_TO_ACCOUNT)
            return False

        ok, movements_parsed = bf_parse_helpers.get_movements_parsed(resp_movs.text)
        if not ok:
            self.basic_log_wrong_layout(
                resp_movs,
                "{}: can't get movements_parsed. Skip process_account".format(fin_ent_account_id)
            )
            return False

        # The same for all movements on the page except SECUENCIA param (it is a mov['id'])
        req_mov_details_params = bf_parse_helpers.get_req_params_for_mov_details(
            resp_movs.text,
            req_movs_params
        )

        movements_parsed_w_extra_details = self.basic_get_movements_parsed_w_extra_details(
            s,
            movements_parsed,
            account_scraped,
            date_from_str,
            n_mov_details_workers=1,  # fails if many concurrent workers
            meta=req_mov_details_params,
        )

        resp_recent = resp_movs
        for i in range(2, 100):  # avoid inf loop
            if 'form name="masMvtos"' not in resp_recent.text:
                self.logger.info('{}: no more pages with movs'.format(fin_ent_account_id))
                break
            self.logger.info('{}: open page #{} with movs'.format(fin_ent_account_id, i))
            ok, codreanud_param = bf_parse_helpers.get_codreanud_param(resp_recent.text)
            if not ok:
                self.basic_log_wrong_layout(
                    resp_movs,
                    "{}: can't get codreanud_param at page #{}. Break the loop".format(fin_ent_account_id, i)
                )
                break
            req_movs_link_i, req_movs_params_i = extract.build_req_params_from_form_html_patched(
                resp_recent.text,
                'masMvtos'
            )
            req_movs_params_i['CODREANUD'] = codreanud_param
            resp_movs_i = s.post(
                urllib.parse.urljoin(self._auth_url(), req_movs_link_i),
                data=req_movs_params_i,
                headers=self.req_headers,
                proxies=self.req_proxies
            )
            ok, movements_parsed_i = bf_parse_helpers.get_movements_parsed(resp_movs_i.text)
            if not ok:
                self.basic_log_wrong_layout(
                    resp_movs_i,
                    "{}: can't get movements_parsed_i at page #{}. Break the loop".format(fin_ent_account_id, i)
                )
                break

            if list_funcs.is_sublist(movements_parsed, movements_parsed_i):
                self.logger.info('{}: got duplicated movements. Break the loop'.format(fin_ent_account_id))
                break

            # Get extra details baing on the current page due to codreanud_param
            req_mov_details_params_i = bf_parse_helpers.get_req_params_for_mov_details(
                resp_movs_i.text,
                req_movs_params_i
            )

            movements_parsed_w_extra_details_i = self.basic_get_movements_parsed_w_extra_details(
                s,
                movements_parsed_i,
                account_scraped,
                date_from_str,
                n_mov_details_workers=1,  # fails if many concurrent workers
                meta=req_mov_details_params_i
            )

            movements_parsed_w_extra_details.extend(movements_parsed_w_extra_details_i)
            resp_recent = resp_movs_i

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
                         meta: dict) -> MovementParsed:
        """Will be called for each movement by self.basic_get_movements_parsed_w_extra_details()
        Need to open each movement to find is it conatins extra details or not

        meta is a req_mov_params dict

        To get extended description, need
        1. get resp_mov - it's a page with form with params for optional req_extra_details,
                          also it contains Oficina.
        2. get resp_mov_extra_details - for other details if there is 'Detalle del documento'
        """

        mov_str = self.basic_mov_parsed_str(movement_parsed)
        self.logger.info('{}: process movement: {}'.format(
            fin_ent_account_id,
            mov_str
        ))

        req_mov_params = meta.copy()
        req_mov_params['SECUENCIA'] = movement_parsed['id']
        req_mov_params['FECHMOVI'] = movement_parsed['operation_date'].replace('/', '')

        # 'Consulta de movimientos' page

        resp_mov = s.post(
            urllib.parse.urljoin(self._auth_url(), 'not8400_d_5838m.action'),
            data=req_mov_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if 'Detalle del movimiento' not in resp_mov.text:
            self.basic_log_wrong_layout(
                resp_mov,
                "{}: {}: can't find 'Detalle del movimiento' text. Skip process_movement".format(
                    fin_ent_account_id,
                    mov_str
                )
            )

        # 'Detalle de un documento' page

        # OPTIONAL, if the movement has details
        req_extra_details_link, req_extra_details_params = extract.build_req_params_from_form_html_patched(
            resp_mov.text,
            'datos'
        )
        resp_mov_extra_details = Response()
        # req_extra_details_link may points to 'Volver' if no 'Detalle del documento' on the page
        if req_extra_details_link and 'Detalle del documento' in resp_mov.text:
            resp_mov_extra_details = s.post(
                urllib.parse.urljoin(self._auth_url(), req_extra_details_link),
                data=req_extra_details_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

        ok, description_extended = bf_parse_helpers.get_description_extended(
            resp_mov.text,  # for Oficina
            resp_mov_extra_details.text,
            movement_parsed
        )
        if not ok:
            self.basic_log_wrong_layout(
                resp_mov_extra_details if resp_mov_extra_details.text else resp_mov,
                "{}: {}: can't parse extra details. Skip process_movement".format(
                    fin_ent_account_id,
                    mov_str
                )
            )
            return movement_parsed

        movement_parsed_w_extra_details = movement_parsed.copy()
        movement_parsed_w_extra_details['description_extended'] = description_extended

        return movement_parsed_w_extra_details

    def main(self) -> MainResult:

        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp_logged_in.url, resp_logged_in.text,
                                                              reason)

        self.process_contract(s, resp_logged_in)

        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
