import random
import threading
import time
from datetime import datetime, timedelta
from typing import Tuple, List, Dict

from custom_libs import date_funcs
from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from . import parse_helpers_n43
from .custom_types import Contract, N43Parsed
from .santander_empresas_scraper__nuevo import SantanderEmpresasNuevoScraper

__version__ = '3.1.0'
__changelog__ = """
3.1.0
process_contract_for_n43: activated Reception
_get_n43_dates_for_access
get_n43_from_recepcion_one_doc: call to _get_n43_dates_for_access
3.0.0
moved from santander_n43_scraper.py (that now contains a mediator that calls different santander scrapers)
2.7.0
main: don't check for get_n43_last_successful_result_date_of_access() 
  (now implemented in self.basic_scrape_for_n43())
2.6.0
main: handle 2FA reason from switch_to_contract()
2.5.1
check 'if n43_content' before adding to n43_contents
2.5.0
use basic_save_n43s
2.4.0
use basic_scrape_for_n43
self.fin_entity_name
2.3.0
skip process_contract_for_n43_from_recepcion (wait for the new Recepcion view)
2.2.1
upd log msg
2.2.0
use basic_get_n43_dates_and_account_status
2.1.2
upd log msgs
2.1.1
upd log msgs
2.1.0
n43 from Recepcion: pagination
don't use ACCESSES_RECEPCION: all accesses will try get info from Recepcion
date_from cache
2.0.0
N43 from Recepcion area
1.4.0
use Contract data type
1.3.0
login: reason support
1.2.0
don't check is the access in a list to process or not: 
  it's not the scraper responsibility
1.1.0
download_n43: check wrong layout
upd log msgs 
custom scrape()
multi-contract support
1.0.0
init
"""


class SantanderEmpresasNuevoN43Scraper(SantanderEmpresasNuevoScraper):
    """The scraper tries to use nuevo access type for
    any access types of Santander accesses.

    It saves N43 docs only of all data were successfully scraped.
    1. Downloads N43 from Recepcion area (Remesas -> Recepcion norma 43)
    2.
        If successful: stop with success
        If failed: abort with failure
        If absent (NO HAY DATOS): step 3
    3. Downloads N43 from Peticion area (Remesas -> Peticion norma 43)
    """
    scraper_name = 'SantanderEmpresasNuevoN43Scraper'
    fin_entity_name = 'SANTANDER'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.__date_to = date_funcs.today() - timedelta(days=1)
        self.__date_to_str = self.__date_to.strftime('%Y-%m-%d')
        self._req_api_headers = self.basic_req_headers_updated({
            'x-user-language': 'es_ES',
            'x-frame-channel': 'EMP',
            'Content-Type': 'application/json',
        })
        # Cache with date_from for already checked account from Recepcion area.
        # N43Parsed don't grouped by account - it's a plain list,
        # So once date_from for an account was calculated,
        # then self._dates_from will be used for the account
        # {fin_ent_account_id: (date_from, date_to, is_active_account)}
        self._dates_and_statuses = {}  # type: Dict[str, Tuple[datetime, datetime, bool]]
        # For further possible multi-thread implementation, used by self._dates_from
        self.__lock = threading.Lock()

    @staticmethod
    def _account_iban_to_fin_ent_id(account_iban: str) -> str:
        """
        For DB queries
        >>> SantanderEmpresasNuevoN43Scraper._account_iban_to_fin_ent_id('ES3100497313532110000239')
        '0049 7313 53 2110000239'
        """
        x = account_iban
        return '{} {} {} {}'.format(x[4:8], x[8:12], x[12:14], x[14:])

    def _check_no_data_err(self, resp_json: dict) -> Tuple[bool, List[str]]:
        """
        No data:
        {"errors":[{"code":"ERROR_PROCESS_PARTENON_APPLICATION",
        "message":"Application Partenon Error","level":"ERROR",
        "description":"NO HAY DATOS","additionalInfo":{"applicationCodeError":"100"}}]}
        or any
        :return: (no_data_err, [all_errs])
        """
        resp_errs = resp_json.get('errors', [])
        if resp_errs:
            if [e['description'] for e in resp_errs] == ['NO HAY DATOS']:
                return True, resp_errs
        return False, resp_errs

    def _get_n43_dates_for_access(self, offset_days=1) -> Tuple[datetime, datetime]:
        """Tries to get from cache self._dates_from
        or calcs initially and updates self_dates_from
        n43_from_reception can't determine account from parsed file.
        :returns (date_from, date_to)
        """
        return self.basic_get_n43_dates_for_access()

    def _get_n43_dates_and_account_status(self, fin_ent_account_id: str) -> Tuple[datetime, datetime, bool]:
        """Tries to get from cache self._dates_from
        or calcs initially and updates self_dates_from
        Useful for n43_from_recepcion bcs N43 docs are not grouped by account
        and there is no possibility to filter
        :returns (date_from, date_to, is_active_account)
        """
        dates_and_status = self.basic_get_n43_dates_and_account_status(
            fin_ent_account_id
        )
        if fin_ent_account_id in self._dates_and_statuses:
            return self._dates_and_statuses[fin_ent_account_id]
        dates_and_status = self.basic_get_n43_dates_and_account_status(
            fin_ent_account_id
        )  # type: Tuple[datetime, datetime, bool]
        with self.__lock:
            self._dates_and_statuses[fin_ent_account_id] = dates_and_status
        return dates_and_status

    # Modified method from SantanderEmpresasScraper - the same method
    def _get_and_set_secreto_cookie(self, s: MySession, contract: Contract) -> Tuple[bool, MySession]:
        """Calls to old web to get 'secreto' cookie"""
        org_title = contract.org_title
        req_url = 'https://empresas3.gruposantander.es/www-empresas/s/cookie/secreto'
        resp_secreto = s.get(
            req_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # from {"cod_operacion":"cs","resultado":"OK","data":{"obj":{"name":"cs","value":"-----BEGIN DAT-----
        # bJZrwgqwnC1R884hBwjxZjQaAzkDB4JJ2K5Uq9Bkeki6uDNmXxJO0utYXnA64jpx
        # K7azWACjSmqiP/WIKu/7ttqIn3lzPfu1JlYgxgkpT5LPlx7iBXStgo3Bi3fxJde6
        # Mhps2JD+8OxCs9eKBUd4sFOajaIE9OlAdrX8rXo0Fh4= -----END DAT-----","underConstruction":false}}}

        ok, resp_secreto_json = self.basic_get_resp_json(
            resp_secreto,
            "{}: can't get resp_secreto_json".format(org_title)
        )
        if not ok:
            return False, s

        secreto = resp_secreto_json.get('data', {}).get('obj', {}).get('value')

        if not secreto:
            self.basic_log_wrong_layout(
                resp_secreto,
                "{}: can't get 'secreto' cookie".format(org_title)
            )
            return False, s
        s.cookies.set('ieSecreto', secreto, domain='.gruposantander.es', path='/')
        return True, s

    def process_contract_for_n43(self, s: MySession, contract: Contract) -> bool:
        org_title = contract.org_title
        self.logger.info('{}: process_contract_for_n43'.format(
            org_title
        ))

        # VB: COMMENTED to skip Recepcion. Wait for the new Recepcion view
        ok, has_n43 = self.process_contract_for_n43_from_recepcion(s, contract)
        # Should return the result if this area has N43s
        if has_n43:
            self.logger.info('{}: no need to process Peticion area'.format(org_title))
            return ok

        # Process Peticion if 'no N43' in Recepcion area
        ok = self.process_contract_for_n43_from_peticion(s, contract)
        return ok

    def _get_new_universal_cookie(self, s: MySession, contract: Contract) -> Tuple[bool, MySession]:

        # Working without this request which only set a cookie that cannot currently be retrieved
        # ok, s = self._get_and_set_secreto_cookie(s, contract)
        # if not ok:
        #    return False, s  # already reported

        # to get updated NewUniversalCookieSep
        resp_refresh = s.post(
            'https://empresas3.gruposantander.es/paas/api/scc/refresh',
            json={'secreto': 'undefined'},
            headers=self._req_api_headers
        )

        ok = bool(s.cookies.get('NewUniversalCookieSEP'))
        if not ok:
            self.basic_log_wrong_layout(
                resp_refresh,
                "{}: can't get resp_refresh with NewUniversalCookieSEP".format(contract.org_title)
            )
        return ok, s

    def process_contract_for_n43_from_recepcion(self, s: MySession, contract: Contract) -> Tuple[bool, bool]:
        """:returns (ok, has_n43)
        If has no N43s, then process_contract_for_n43_peticion() will be used
        Remesas -> Recepcion norma 43
        """
        org_title = contract.org_title
        self.logger.info('{}: process_contract_for_n43_from_recepcion'.format(
            org_title
        ))

        ok, s = self._get_new_universal_cookie(s, contract)
        if not ok:
            return False, False  # already reported

        req_recepcion_url = 'https://empresas3.gruposantander.es/paas/api/nwe-norm43-api/v1/file'
        has_n43 = True
        ok = True
        # ASC by dates, see -a 22957 for pagination
        for page_ix in range(1, 100):  # avoid inf loop
            self.logger.info('{}: recepcion: page #{}: download N43 docs'.format(
                org_title,
                page_ix
            ))
            resp_recepcion_i = s.get(
                req_recepcion_url,
                headers=self._req_api_headers,
                proxies=self.req_proxies,
            )
            # No recepcion data, detecting at page 1
            if resp_recepcion_i.status_code == 204:
                self.logger.info('{}: recepcion: page #{}: no docs for N43 downloading'.format(
                    org_title,
                    page_ix
                ))
                has_n43 = False
                break

            ok, resp_recepcion_i_json = self.basic_get_resp_json(
                resp_recepcion_i,
                "{}: page #{}: can't get resp_recepcion_json".format(org_title, page_ix)
            )
            if not ok:
                break

            # General check for errs (including no_data_err, but basically iy should be
            # handled above by resp.status_code == 204)
            no_data_err, resp_recepcion_errs = self._check_no_data_err(resp_recepcion_i_json)
            if no_data_err:
                self.logger.info('{}: recepcion: page #{}: no docs for N43 downloading'.format(
                    org_title,
                    page_ix
                ))
                has_n43 = False
                break

            if resp_recepcion_errs:
                self.basic_log_wrong_layout(
                    resp_recepcion_i,
                    "{}: recepcion: page #{}: can't get docs for N43 downloading. Abort".format(
                        org_title,
                        page_ix
                    )
                )
                ok = False
                break

            # One N43Parsed per account
            # SMALL WORLD -a 16809 and MIVET -a 35182 have a single file for several accounts, and
            # available information for parsed file show an iban that has nothing to do with internal
            # accounts at n43 file content.
            n43s_parsed = parse_helpers_n43.get_n43s_parsed_from_recepcion(resp_recepcion_i_json)
            if not n43s_parsed:
                self.basic_log_wrong_layout(
                    resp_recepcion_i,
                    "{}: page #{}: expected, but didn't get n43s_parsed".format(
                        org_title,
                        page_ix
                    )
                )
                ok = False
                break

            self.logger.info(
                '{}: recepcion: page #{}: got {} documents to download N43 '
                '(will skip old docs then): {} '.format(
                    org_title,
                    page_ix,
                    len(n43s_parsed),
                    n43s_parsed
                ))

            for n43_parsed in n43s_parsed:
                ok, n43_content = self.get_n43_from_recepcion_one_doc(s, n43_parsed)
                if not ok:
                    break  # already reported
                # Skip empty content for too early n43_parsed (no way to filter from web)
                # Skip inactive account (empty content)
                if n43_content:
                    self.n43_contents.append(n43_content)

            req_recepcion_url_raw = resp_recepcion_i_json.get('_links', {}).get('next', {}).get('href', '')
            if not req_recepcion_url_raw:
                self.logger.info('{}: no more pages with N43'.format(org_title))
                break
            req_recepcion_url = parse_helpers_n43.url_without_empty_get_params(req_recepcion_url_raw)
            time.sleep(0.1 * (1 + random.random()))

        return ok, has_n43

    def get_n43_from_recepcion_one_doc(
            self,
            s: MySession,
            n43_parsed: N43Parsed) -> Tuple[bool, bytes]:

        # Commented as iban at n43_parsed has nothing to do with content of n43 file
        # fin_ent_account_id = self._account_iban_to_fin_ent_id(n43_parsed.account_iban)
        # date_from, date_to, is_active_account = self._get_n43_dates_and_account_status(fin_ent_account_id)
        # if not is_active_account:
        #    return True, b''  # already reported

        date_from, date_to = self._get_n43_dates_for_access()
        # Skip too early n43_parsed
        if n43_parsed.operation_date < date_from:
            self.logger.info('{}: old doc. Skip'.format(n43_parsed))
            return True, b''
        self.logger.info('{}: recepcion: download N43: {}'.format(
            self.db_financial_entity_access_id,
            n43_parsed,
        ))
        # Resp-pre
        req_pre_url = (
            'https://empresas3.gruposantander.es/paas/api/nwe-norm43-api/v1/file/{}'
            '/number_files?disaggregated=false'.format(n43_parsed.file_id_pre)
        )
        resp_pre = s.get(
            req_pre_url,
            headers=self._req_api_headers,
            proxies=self.req_proxies
        )
        # {"numberFiles":1,"fileId":"e3780df9d62fe44cc2018108aac1ead9"}
        ok, resp_pre_json = self.basic_get_resp_json(
            resp_pre,
            "Can't get resp_pre_json"
        )
        if not ok:
            return False, b''
        # Again fileId param, this one exactly to use in req_n43
        file_id = resp_pre_json.get('fileId', '')
        if not file_id:
            self.basic_log_wrong_layout(
                resp_pre,
                "{}: can't get n43 downloading fileId param for {}".format(self.db_financial_entity_access_id, n43_parsed)
            )
            return False, b''
        req_n43_url = ('https://empresas3.gruposantander.es/paas/api/nwe-norm43-api/v1/file/{}'
                       '?cuadernoNumber=1&disaggregated=0&fileNumber=1'.format(file_id))
        resp_n43 = s.get(
            req_n43_url,
            headers=self._req_api_headers,
            proxies=self.req_proxies
        )
        resp_n43_content = resp_n43.content
        if not n43_funcs.validate(resp_n43_content):
            self.basic_log_wrong_layout(
                resp_n43,
                "{}: got invalid resp_n43".format(self.db_financial_entity_access_id)
            )
            return False, b''
        return True, resp_n43_content

    def process_contract_for_n43_from_peticion(self, s: MySession, contract: Contract) -> bool:
        """Contract-level action
        Remesas -> Peticion norma 43
        """
        org_title = contract.org_title
        self.logger.info('{}: process_contract_for_n43_from_peticion'.format(
            org_title
        ))
        resp_accs = s.get(
            'https://empresas3.gruposantander.es/paas/api/nwe-account-api/v1/account?extraInfo=true',
            headers=self._req_api_headers,
            proxies=self.req_proxies,
        )

        ok, resp_accs_json = self.basic_get_resp_json(
            resp_accs,
            "Can't get resp_accs_json"
        )
        if not ok:
            return False  # already reported

        has_no_data_err, resp_accs_errs = self._check_no_data_err(resp_accs_json)
        if has_no_data_err:
            self.logger.info('{}: peticion: no accounts for N43 downloading'.format(org_title))
            return True
        if resp_accs_errs:
            self.basic_log_wrong_layout(
                resp_accs,
                "{}: peticion: can't get accounts for N43 downloading. Abort".format(org_title)
            )
            return False

        acc_ibans_for_n43 = parse_helpers_n43.get_accounts_for_n43_from_peticion(resp_accs_json)
        self.logger.info('{}: peticion: got {} accounts to download N43: {}'.format(
            org_title,
            len(acc_ibans_for_n43),
            acc_ibans_for_n43
        ))
        for account_iban in acc_ibans_for_n43:
            ok, n43_content = self.get_n43_from_peticion_one_acc(s, account_iban)
            if not ok:
                return False  # already reported
            # Skip inactive account (empty content)
            if n43_content:
                self.n43_contents.append(n43_content)

        return True

    def get_n43_from_peticion_one_acc(
            self,
            s: MySession,
            account_iban: str) -> Tuple[bool, bytes]:
        fin_ent_account_id = self._account_iban_to_fin_ent_id(account_iban)
        date_from, date_to, is_active_account = self._get_n43_dates_and_account_status(fin_ent_account_id)
        if not is_active_account:
            return True, b''  # already reported
        self.logger.info('{}: peticion: download N43'.format(fin_ent_account_id))

        req_params = {
            'beginDate': date_from.strftime('%Y-%m-%d'),  # '2020-09-20'
            'endDate': self.__date_to_str,
            'account': [account_iban]
        }
        resp_n43 = s.post(
            'https://empresas3.gruposantander.es/paas/api/nwe-norm43-api/v1/planification/fileinline',
            json=req_params,
            # even for file downloading
            headers=self._req_api_headers,
            proxies=self.req_proxies,
            stream=True
        )
        resp_n43_content = resp_n43.content
        if not n43_funcs.validate(resp_n43_content):
            self.basic_log_wrong_layout(
                resp_n43,
                "{}: got invalid resp_n43".format(fin_ent_account_id)
            )
            return False, b''
        return True, resp_n43_content

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

        scrap_results = []  # type: List[bool]

        resp_contract = Response()
        reason_contract = ''

        _, s, resp_contracts, contracts = self._get_contracts(s, resp_logged_in)
        if contracts:
            self.logger.info('Got {} contracts: {}'.format(
                len(contracts),
                contracts
            ))
            # Many contracts - scrape each one by one
            for contract in contracts:
                self.logger.info("Process company (contract) '{}' for N43".format(contract.org_title))
                # Need to get resp_contracts with a new 'nweauthoritationtoken' token
                ok, s, resp_contracts, _ = self._get_contracts(s, resp_logged_in)
                if not ok:
                    scrap_results.append(False)
                    break
                ok, s, resp_contract, reason_contract = self.switch_to_contract(
                    s,
                    resp_logged_in,
                    contract,
                    resp_contracts
                )
                if not ok:
                    scrap_results.append(False)  # already reported
                    break
                ok = self.process_contract_for_n43(s, contract)
                scrap_results.append(ok)
        else:
            # One contract - default scraping process
            contract = Contract(org_title='DEFAULT contract', details={})
            ok = self.process_contract_for_n43(s, contract)
            scrap_results.append(ok)

        self.basic_log_time_spent('GET N43')

        is_success = all(scrap_results)
        if not is_success:
            # The only case to get non-empty reason_contract is auth err on attempt switching to a contract
            if reason_contract:
                return self.basic_result_not_logged_in_due_reason(
                    resp_contract.url,
                    resp_contract.text,
                    reason_contract
                )
            else:
                return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
