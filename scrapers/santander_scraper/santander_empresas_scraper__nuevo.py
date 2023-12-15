import os
import subprocess
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    ScraperParamsCommon, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_OTP,
    AccountScraped, MOVEMENTS_ORDERING_TYPE_ASC,
    MovementParsed, AccountParsed, PASSWORD_CHANGE_TYPE_COMMON
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from . import parse_helpers_nuevo
from . import parse_helpers_nuevo_nwe_v1
from .custom_types import Contract, OrganizationParsed
from .santander_empresas_scraper import (
    CREDENTIALS_ERROR_MARKERS, USER_AGENT,
    DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS,
    CREDENTIALS_ERROR_MARKERS_URL
)

__version__ = '4.14.0'
__changelog__ = """
4.14.0 2023.10.24
login: fixed false wrong credentials deleting use of 'username_second' used by deprecated 'Empresas e instituciones'
4.13.0 2023.07.13
_refresh_session: added log in method call
4.12.0 2023.07.07
_get_accounts_parsed_from_tesoreria: added "FINANCIACION IMPORTACION" account detection log
4.11.0 2023.05.16
added PASSWORD_CHANGE_MARKER
login: managed password change detection
4.10.0
_refresh_session: added 'refresh' call to avoid session expiration
4.9.0
_get_encrypted: added support for windows encryption
4.8.0
upd ACCOUNTS_CUSTOM_OFFSET
4.7.0
api v2:
    handle 'PRODUCTO NO CONSULTABLE POR ESTA APLICACION'
    multi-contract access support
    'no movements' detector
4.6.0
process_account_api_v2
_get_movements_parsed_api_v2 w/ several atempts
4.5.0
ACCOUNTS_CUSTOM_OFFSET
process_account: up to 300 pages
4.4.0
use basic_is_in_process_only_accounts
4.3.0
login: upd 2fa detector
4.2.0
_get_accounts_parsed_from_productos: more try-except coverage for floating errs
4.1.1
main: resp_contract_i
switch_to_contract: org title in reason
4.1.0
switch_to_contract: detect 2FA
upd log msg
main: continue (next contract) if can't login to a contact (was break) 
4.0.0
important: nwe_v1 api only:
    login
    _get_contracts
    switch_to_contract
removed login and switch_contract for prev auth method
3.14.0
Optional support for 'nwe_v1' auth method: only one-contract accesses if 'loginwe' is not working
3.13.0
use account-level result_codes
upd log msgs
3.12.0
use is_reached_pagination_limit
3.11.0
call basic_result_credentials_error with resp
3.10.0
process_account: call basic_set_movements_scraping_finished on failure
3.9.0
'restricted by ip address' detector
3.8.0
call basic_upload_movements_scraped with date_from_str
3.7.0
use set_date_to_for_future_movs
3.6.0
_get_accounts_parsed_from_productos
_get_accounts_parsed_from_tesoreria
3.5.0
login(self):
  added detection login error from response url for:
    CREDENTIALS_ERROR_MARKERS_URL
3.4.0
switch_to_contract: report 2FA reason
main: handle 2FA reason from switch_to_contract()
3.3.0
switch to contract: generate secret cookie (useful for N43 scraper)
3.2.0
abort if contracts are forbidden
3.1.1
_get_accounts_parsed: added necessary method for children (used by Popular)
3.1.0
handle 'no movements' resp
3.0.0
independent of 'Empresas e Instituciones' access type
use latest backend API (12/2020)
disabled filiales, see explanations in dev_newweb/SANTANDER_FILIAL_ACCS_9603.xlsx
2.13.0
process_filial_account: abort processing due to unsynced balances from prev backend
2.12.0
fixed process_filial_account: added missed methods: 
  basic_upload_accounts_scraped, basic_check_account_is_active
2.11.0
renamed to download_correspondence()
2.10.0
login: trim passwords > 8 chars
2.9.0
login: double auth detection, reason support
2.8.0
login: v2
2.7.0
download_company_documents for multi-contract accesses
2.6.1
commented download_company_documents for multi-contract accesses
2.6.0
download_company_documents
2.5.0
login: extra stepRedirect action to handle notifications
2.4.0
process_filial_account: use general self.process_account to get receipt PDFs
2.3.2
aligned double auth msg
2.3.1
use basic_new_session
2.3.0
MySession with self.logger
2.2.1
more type hints
2.2.0
s.resp_codes_bad_for_proxies w/o 403 - it's in usage by the website
2.1.0
2FA detector, extra manual actions detector
2.0.0
multi-contract support
1.0.0
init
"""

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'santander_particulares_encrypter.js'
))

PUBLIC_KEY = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwYq0hHQayVsX3xuFDnuH\nhDg6oBgSAq33oNjgrzH3wbLeIIs/++CpypGzg/5W26GC50MOMuakL+UfIAk9mDxL\n5QhB6XkkDRVhyUOGrTLwGDnyXE5+MPYZmf8wPy7sESzLFTw/3isEgmJh6WRnYH2F\nnHWnvCsE3Ow710OKLpG8eh0/kjH0rYP+KrqcxTfD72SABytNcyXFjT1hhW4YFEMV\nLASKpkzo8mxhiiXNcha+x1oekxoVPmD/FtF9PPvWKn2yhzSfo4TPOtspA5GNIB+T\nz+v6kjc3nwBB1LDOat9+lVI0VxxQ0+PxPFPyurSGhoTL9p0JC+bRmrZkWzALh+jY\nFwIDAQAB\n-----END PUBLIC KEY-----"  # noqa

# Due to too many movs
ACCOUNTS_CUSTOM_OFFSET = {
    '0030 1041 22 0002570271': 2,
    '0049 4341 27 2210037486': 2,
}

PASSWORD_CHANGE_MARKER = 'NEED_CHANGE_PASSWORD_SANTANDER'


class SantanderEmpresasNuevoScraper(BasicScraper):
    """
    Redefines login method
    and implements multi-contract support
    """

    scraper_name = 'SantanderEmpresasNuevoScraper'
    FUTURE_MOVEMENTS_OFFSET = 0  # already set by DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS, see the reason

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.req_headers = {'User-Agent': USER_AGENT}
        # IMPORTANT
        # set +N days to filter movements to be sure
        # that all future movements will be extracted
        # to calculate correct temp_balance for future movements
        # (acc balance is with the future movs)
        # fixme: this is the same as for the prev version
        #  find examples with missed temp_balances for future movs
        #  and delete this future date_to if no need
        self.date_to = self.date_to + timedelta(days=DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS)
        self.date_to_str = self.date_to.strftime(project_settings.SCRAPER_DATE_FMT)  # '30/01/2017'
        self.update_inactive_accounts = False
        self.set_date_to_for_future_movs()
        self._auth_token = ''
        self._req_api_headers = self.basic_req_headers_updated({
            'x-user-language': 'es_ES',
            'x-frame-channel': 'EMP',
            'Content-Type': 'application/json',
        })

    def _get_encrypted(self, msg: str) -> str:
        # trailing 0 -> isCustom = false (use default pkcs1pad2)
        cmd = """{} "{}" '{}' 0""".format(CALL_JS_ENCRYPT_LIB, PUBLIC_KEY, msg)

        # Check current operative system ("posix": linux, mac, "nt": windows)
        if not 'nt' in os.name:
            result_bytes = subprocess.check_output(cmd, shell=True)
        else:
            # avoid "Illegal character at offset 0" error at Windows
            result_bytes = subprocess.check_output(["powershell", cmd])

        text_encrypted = result_bytes.decode().strip()

        return text_encrypted

    def _is_credentials_error(self, resp_logged_in: Response) -> bool:
        is_credentials_error = any(marker in resp_logged_in.text for marker in CREDENTIALS_ERROR_MARKERS)

        if not is_credentials_error:
            is_credentials_error = any(marker in resp_logged_in.url for marker in CREDENTIALS_ERROR_MARKERS_URL)
        return is_credentials_error

    def _auth_headers(self, is_json=True, extra: Dict[str, str] = None) -> Dict[str, str]:
        req_headers = self.basic_req_headers_updated({
            'Authorization': 'Bearer {}'.format(self._auth_token),
            'X-ClientId': 'nwe',
            'x-frame-channel': 'EMP',
            'x-user-language': 'es_ES',
        })
        if is_json:
            req_headers['Content-Type'] = 'application/json'
            req_headers['Accept'] = 'application/json, text/plain, */*'
        if extra:
            req_headers.update(extra)
        return req_headers

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        """nwe_v1 API"""
        self.logger.info("Regular web site: 'nwe_v1' auth method for organizations: start")
        s = self.basic_new_session()
        # remove 403
        s.resp_codes_bad_for_proxies = [500, 502, 503, 504, None]

        _resp_init = s.get(
            'https://www.bancosantander.es/es/empresas',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        _resp_login_form = s.get(
            'https://empresas3.gruposantander.es/paas/loginnwe/',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_login_url = 'https://empresas3.gruposantander.es/paas/api/v2/nwe-login-api/public/v1/login'

        encrypted = self._get_encrypted(self.userpass[:8])

        req_step1_params = OrderedDict([
            ('userAlias', self.username),
            # max 8 chars, but passwords in DB may have more chars (-a 28108, 28110)
            ('userPassword', encrypted),
            ('documentType', ''),
            ('documentNumber', ''),
            ('serviceType', ''),
            ('serviceOperation', ''),
            ('serviceData', ''),
            ('source', ''),
            ('OBSEmpresasLang', 'es_ES'),
        ])

        # LOGGED IN
        # '{"operative":"PORTAL",
        # "data":{"lastAccessTime":"23:51:44",
        # "lastAccessDate":"20211128","hasOTP":"false",
        # "passwordUpdateDate":"28-04-2021","status":"25"},
        # "newPGO":false}'
        resp_logged_in = s.post(
            req_login_url,
            json=req_step1_params,
            headers=self.basic_req_headers_updated({
                'X-ClientId': 'nwe',
                'x-frame-channel': 'EMP',
                'x-user-language': 'es_ES'
            }),
            proxies=self.req_proxies
        )

        is_credentials_error = self._is_credentials_error(resp_logged_in)
        if is_credentials_error:
            return s, resp_logged_in, False, is_credentials_error, ''

        is_logged = '"operative":"PORTAL"' in resp_logged_in.text \
                    or '"operative":"CONTRACTS_LIST"' in resp_logged_in.text

        reason = ''
        if 'sca?scaValidationType' in resp_logged_in.url or '"operative":"SCA"' in resp_logged_in.text:
            reason = DOUBLE_AUTH_REQUIRED_TYPE_OTP
        elif PASSWORD_CHANGE_MARKER in resp_logged_in.text:
            reason = PASSWORD_CHANGE_TYPE_COMMON
        elif 'EL ACCESO ESTA RESTRINGIDO POR DIRECCIÓN IP' in resp_logged_in.text:
            # -a 26308
            reason = 'Access has been RESTRICTED by IP address'

        self._auth_token = resp_logged_in.headers.get('x-authorization-nwe', '')

        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def _get_contracts(self,
                       s: MySession,
                       resp_logged_in: Response) -> Tuple[bool, MySession, Response, List[Contract]]:
        """
        nwe_v1 API
        :return: (is_success, session, resp_contracts, contacts)
        """
        contracts = parse_helpers_nuevo_nwe_v1.get_contracts(resp_logged_in.json())

        return True, s, resp_logged_in, contracts

    def switch_to_contract(
            self,
            s: MySession,
            resp_logged_in: Response,
            contract: Contract,
            resp_contracts: Response) -> Tuple[bool, MySession, Response, str]:
        """nwe_v1 API"""
        # Contract(org_title='LAGUARDIA & MOREIRA S.A.', details={'companyCif': 'A28080695', 'companyName': 'LAGUARDIA & MOREIRA S.A.', 'contract': {'company': '0049', 'center': '0091', 'product': '520', 'number': '0001293', 'id': '004900915200001293'}, 'holderData': {'holderName': 'LAGUARDIAM001'}, 'lastAccessDate': '2021-12-18-04.12.34.000000'}),
        self.logger.info('{}: switching to the contract'.format(contract.org_title))
        req_url = "https://empresas3.gruposantander.es/paas/api/v2/nwe-login-api/public/v1/portal-access"
        req_params = OrderedDict([
            ('userAlias', contract.details['holderData']['holderName']),
            ('userPassword', self._get_encrypted(self.userpass[:8]))
        ])
        # dev_newweb/202111_nwe_v1/30_resp_conrtact_switched.json
        resp_contract = s.post(
            req_url,
            json=req_params,
            headers=self.basic_req_headers_updated({
                'X-ClientId': 'nwe',
                'x-frame-channel': 'EMP',
                'x-user-language': 'es_ES',
                'NWEAuthoritationToken': resp_logged_in.json()['data']['token']
            }),
            proxies=self.req_proxies
        )

        resp_contract_json = resp_contract.json()
        if resp_contract_json.get('sca') is not None:
            self.logger.warning(
                "{}: can't switch to contract: 2FA required".format(
                    contract.org_title
                )
            )
            reason = 'Contract {}: {}'.format(contract.org_title, DOUBLE_AUTH_REQUIRED_TYPE_OTP)
            return False, s, resp_contract, reason

        self.logger.info('{}: generate secret cookie'.format(contract.org_title))
        secret_cookie = s.cookies.get('CookieSecreto')

        req_generate = 'https://empresas3.gruposantander.es/empresas/s/cookie/generate'
        req_generate_params = OrderedDict([
            ('fechaUltimoAcceso', resp_contract_json['data']['lastAccessDate']),
            ('horaUltimoAcceso', resp_contract_json['data']['lastAccessTime']),
            ('fechaCambioClave', ''),  # 20210531
            ('moreContracts', 'y'),
            ('secreto', secret_cookie),
            ('menuID', '')
        ])
        # Should be redirected to https://empresas3.gruposantander.es/empresas/
        _resp_generated_cookie = s.post(
            req_generate,
            data=req_generate_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        self._auth_token = resp_contract.headers.get('x-authorization-nwe', '')

        return True, s, resp_contract, ''

    def _get_organizations(self, s: MySession) -> Tuple[bool, MySession, List[OrganizationParsed]]:
        """Returns all organizations for the sub-contract, including branches (filiales)"""
        # req_orgs_url = 'https://empresas3.gruposantander.es/paas/api/nwe-subsidiary-api/v2/subsidiary?otherSubsidiary=true'
        req_orgs_url = 'https://empresas3.gruposantander.es/paas/api/nwe-subsidiary-api/v1/subsidiary'
        resp_orgs = s.get(
            req_orgs_url,
            headers=self.basic_req_headers_updated({
                'Content-Type': 'application/json',
                'x-frame-channel': 'EMP'
            }),
            proxies=self.req_proxies
        )

        try:
            resp_orgs_json = resp_orgs.json()
        except:
            self.logger.error("Can't get resp_orgs_json. Abort. RESPONSE:\n{}".format(
                resp_orgs.text
            ))
            return False, s, []

        organizations_parsed = parse_helpers_nuevo.get_organizations_parsed(
            self.logger,
            resp_orgs_json
        )
        return True, s, organizations_parsed

    def _get_accounts_parsed_from_productos(self, s: MySession, org_title: str) -> Tuple[bool, List[AccountParsed]]:
        """PRODUCTOS (main page) ->  Cuentas Corrientes y de Crédito -> Todas"""
        self.logger.info("{}: get accounts from 'Productos'".format(org_title))

        # -a 23404 has more than 100 active accounts,
        # but this list return only 60
        resp_accs = s.get(
            'https://empresas3.gruposantander.es/paas/api/nwe-global-balance-api/'
            'v1/account?segment=TODOS&pagination.limit=100',  # default was limit=5
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if not resp_accs.text:
            self.logger.info('{}: no accounts. Skip'.format(org_title))
            return True, []

        try:
            resp_accs_json = resp_accs.json()
            accounts_parsed = parse_helpers_nuevo.get_accounts_parsed_from_productos(resp_accs_json)
        except Exception as _e:
            self.basic_log_wrong_layout(resp_accs, "{}: can't get accounts_parsed".format(org_title))
            return False, []

        return True, accounts_parsed

    def _get_accounts_parsed_from_tesoreria(self, s: MySession, org_title: str) -> Tuple[bool, List[AccountParsed]]:
        """Tesorería -> Cuentas corrientes y de crédito
        Some accesses have more accounts available via this area, but not available via Productos:
            -a 23404
            accounts:
                ...3401,
                ...7287,
                ...4318
        """
        accounts_parsed = []  # type: List[AccountParsed]
        req_accs_params = OrderedDict([
            ("tokenRepos", ""),
            ("filiales", "C"),
            ("alias", ""),
            ("active", "findByAlias"),
            ("idRepos", "")
        ])
        token_repos_param = ''
        for page_ix in range(1, 100):
            self.logger.info("{}: page #{}: get accounts from 'Tesoreria'".format(
                org_title,
                page_ix
            ))

            if token_repos_param:
                req_accs_params['tokenRepos'] = token_repos_param

            resp_accs_i = s.post(
                'https://empresas3.gruposantander.es/paas/api/nwe-cuentas-phoenix/public/filteraccount/findByAlias',
                json=req_accs_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )
            try:
                resp_accs_i_json = resp_accs_i.json()
            except Exception as _e:
                self.basic_log_wrong_layout(resp_accs_i, "{}: page #{}: can't get resp_accs_json".format(
                    org_title,
                    page_ix
                ))
                return False, []

            accounts_parsed_i, has_accounts_from_financiacion = parse_helpers_nuevo.get_accounts_parsed_from_tesoreria(resp_accs_i_json)
            accounts_parsed.extend(accounts_parsed_i)

            # Temporary log to detect customers with "FINANCIACION IMPORTACION" accounts
            if has_accounts_from_financiacion:
                self.logger.info('{}: has "FINANCIACION IMPORTACION" accounts'.format(org_title))

            token_repos_param = resp_accs_i_json.get('tokenRepos', '')
            if not token_repos_param:
                if resp_accs_i_json['endList'] is True:
                    self.logger.info('{}: no more pages with accounts'.format(org_title))
                else:
                    # Let's report an error but allow to continue with already parsed accounts
                    self.basic_log_wrong_layout(
                        resp_accs_i,
                        "{}: expected more pages with accounts".format(org_title)
                    )
                break

        return True, accounts_parsed

    def _get_accounts_parsed(self, s: MySession, org_title: str) -> Tuple[bool, List[AccountParsed]]:
        """Can be overwritten in children"""

        ok, accounts_parsed_from_productos = self._get_accounts_parsed_from_productos(s, org_title)
        if not ok:
            return False, []  # already reported

        ok, accounts_parsed_from_tesoreria = self._get_accounts_parsed_from_tesoreria(s, org_title)
        if not ok:
            return False, []  # already reported

        # Join unique accounts, can't use sets due to unhashable dict
        accounts_parsed = accounts_parsed_from_productos.copy()
        accounts_parsed_dict = {acc['account_no']: acc for acc in accounts_parsed}
        for acc_tes in accounts_parsed_from_tesoreria:
            acc_tes_no = acc_tes['account_no']
            if acc_tes_no not in accounts_parsed_dict.keys():
                accounts_parsed.append(acc_tes)
            else:
                acc_prod = accounts_parsed_dict[acc_tes_no]
                if acc_prod != acc_tes:
                    self.logger.warning("Got non-equal accounts with the same account_no: "
                                        "from 'Productos' {}, from 'Tesoreria' {}".format(acc_prod, acc_tes))
                    pass

        return True, accounts_parsed

    def _refresh_session(self, s: MySession, account_no: str) -> Tuple[bool, MySession]:
        """Get updated 'NewUniversalCookieSep' to avoid session expiration in the download process"""

        resp_refresh = s.post(
            'https://empresas3.gruposantander.es/paas/api/scc/refresh',
            json={'secreto': 'undefined'},
            headers=self._req_api_headers
        )

        ok = bool(s.cookies.get('NewUniversalCookieSEP'))
        if not ok:
            self.basic_log_wrong_layout(
                resp_refresh,
                "{}: can't get resp_refresh with NewUniversalCookieSEP".format(account_no)
            )
        self.logger.info("{}: refresh session with NewUniversalCookieSEP".format(account_no))
        return ok, s

    def process_contract(self, s: MySession, resp_contract: Response, contract: Contract) -> bool:
        org_title = contract.org_title

        ok, accounts_parsed = self._get_accounts_parsed(s, org_title)
        if not ok:
            return False, False

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                account_parsed['org_title'],
                account_parsed
            ) for account_parsed in accounts_parsed
        ]
        self.logger.info('{}: got {} accounts: {}'.format(
            org_title,
            len(accounts_scraped),
            accounts_scraped
        ))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        # Only serial mode is allowed
        results = []  # type: List[bool]
        for account_scraped in accounts_scraped:
            ok, has_no_movs = self.process_account(s, account_scraped)
            if not ok:
                results.append(ok)
                continue
            if has_no_movs:
                self.logger.info('{}: no movements extracted using api v1, trying api v2'.format(
                    account_scraped.FinancialEntityAccountId
                ))
                ok = self.process_account_api_v2(s, account_scraped)

        return all(results)

    def _open_movements(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            date_from: datetime,
            page_ix: int,
            token_repos_param='',
            last_mov_date_str='') -> Tuple[bool, Response, dict]:
        """
        :return: Tuple[is_success, resp, resp_json_if_success]
        """

        # with PDF receipt status
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        req_url = ('https://empresas3.gruposantander.es/paas/api/nwe-account-api'
                   '/v2/account/{}/movement'.format(account_scraped.AccountNo))

        req_data = {
            "currencyAccount": account_scraped.Currency,
            "dateFilterType": "byDates",
            "queryType": "S",
            "dateType": "operationDate",
            "appointmentType": "all",
            "dateFrom": date_from.strftime('%Y-%m-%d'),  # "2017-12-01"
            "dateTo": self.date_to.strftime('%Y-%m-%d')  # "2018-01-21"
        }
        if token_repos_param:
            req_data['tokenRepos'] = token_repos_param

        resp_movs = Response()
        req_exc = None  # type: Optional[Exception]
        if not last_mov_date_str:
            self.logger.info('{}: page #{}: open movements'.format(
                fin_ent_account_id,
                page_ix
            ))
        else:
            self.logger.info('{}: page #{}: open movements (last mov date={})'.format(
                fin_ent_account_id,
                page_ix,
                last_mov_date_str
            ))

        # Several attempts to get resp_movs
        for i in range(2):
            try:
                resp_movs = s.post(
                    req_url,
                    json=req_data,
                    headers=self.req_headers,
                    proxies=self.req_proxies,
                    timeout=30
                )
                break
            except Exception as exc:
                self.logger.error("{}: page #{}: can't get resp_movs. Retry. HANDLED EXCEPTION: {}".format(
                    fin_ent_account_id,
                    page_ix,
                    req_exc,
                ))
                time.sleep(2)
                req_exc = exc
        else:
            self.logger.error("{}: page #{}: can't get resp_movs:\nHANDLED EXCEPTION: {}".format(
                fin_ent_account_id,
                page_ix,
                req_exc,
            ))
            return False, resp_movs, {}

        if resp_movs.status_code == 204:  # no movs, No existen datos para esta consulta
            return True, resp_movs, {}

        try:
            resp_movs_json = resp_movs.json()
        except Exception as exc:
            self.logger.error(
                "{}: page #{}: can't get resp_movs_json:\n"
                "HANDLED EXCEPTION: {}\nRESPONSE: {}".format(
                    fin_ent_account_id,
                    page_ix,
                    exc,
                    resp_movs.text,
                ))
            return False, resp_movs, {}
        return True, resp_movs, resp_movs_json

    def _open_movements_i(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            date_from: datetime,
            resp_movs_prev_json: dict,
            movs_for_logs: List[MovementParsed],
            page_ix: int) -> Tuple[bool, Response, dict]:

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        date_from_str = date_from.strftime(project_settings.SCRAPER_DATE_FMT)

        is_end_list_of_movs = resp_movs_prev_json.get('endList', True)
        token_repos_param = resp_movs_prev_json.get('tokenRepos')
        if is_end_list_of_movs or not token_repos_param:
            self.logger.info('{}: no more movements'.format(fin_ent_account_id))
            return False, Response(), {}

        if not movs_for_logs:
            self.logger.warning('{}: page #{}: an attempt to open more movements, but there are no previous. '
                                'Abort pagination'.format(fin_ent_account_id, page_ix))
            return False, Response(), {}

        last_mov_date_str = movs_for_logs[-1]['operation_date']

        ok, resp_movs_i, resp_movs_i_json = self._open_movements(
            s,
            account_scraped,
            date_from,
            page_ix,
            token_repos_param,
            last_mov_date_str
        )
        if not ok:
            self.basic_log_wrong_layout(
                resp_movs_i,
                '{}: process_account: page #{}: dates from {} to {}: error in reps_mov_more'.format(
                    fin_ent_account_id,
                    page_ix,
                    date_from_str,
                    self.date_to_str,
                )
            )
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
            return False, Response(), {}
        return True, resp_movs_i, resp_movs_i_json

    def process_account(
            self,
            s: MySession,
            account_scraped: AccountScraped) -> Tuple[bool, bool]:
        """
        :return: (ok, has_no_movements)
        """
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_is_in_process_only_accounts(account_scraped.AccountNo):
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.SKIPPED_EXPLICITLY)
            return True, False  # already reported

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True, False

        ok, s = self._refresh_session(s, fin_ent_account_id)
        if not ok:
            return False, False  # already reported

        date_from_str = self.basic_get_date_from(
            fin_ent_account_id,
            max_offset=ACCOUNTS_CUSTOM_OFFSET.get(fin_ent_account_id, project_settings.MAX_OFFSET)
        )
        date_from = datetime.strptime(date_from_str, project_settings.SCRAPER_DATE_FMT)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        ok, resp_movs, resp_movs_initial_json = self._open_movements(
            s,
            account_scraped,
            date_from,
            page_ix=1
        )
        if not ok:
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
            return False, False  # already reported

        movs_parsed_desc = parse_helpers_nuevo.get_movements_parsed(resp_movs_initial_json)

        # Pagination
        movs_prev = movs_parsed_desc
        resp_movs_prev_json = resp_movs_initial_json
        is_reached_page_limit = False
        for page_ix in range(2, 301):  # -a 18620, acc ES6300301041220002570271
            ok, resp_movs_i, resp_movs_i_json = self._open_movements_i(
                s,
                account_scraped,
                date_from,
                resp_movs_prev_json,
                movs_prev,
                page_ix,
            )
            if not ok:
                break  # already reported
            movs_i = parse_helpers_nuevo.get_movements_parsed(resp_movs_i_json)
            movs_parsed_desc.extend(movs_i)
            movs_prev = movs_i
            resp_movs_prev_json = resp_movs_i_json
        else:
            is_reached_page_limit = True
        # Drop movements of the oldest day: they will have wrong OperatioanDatePosition due to interruption

        movs_parsed_asc = parse_helpers.reorder_and_calc_temp_balances(movs_parsed_desc)

        movements_scraped, movements_parsed_corresponding = self.basic_movements_scraped_from_movements_parsed(
            movs_parsed_asc,
            date_from_str,
            bankoffice_details_name='Oficina',
            payer_details_name='Concepto',
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC,
            is_reached_pagination_limit=is_reached_page_limit,
            fin_ent_account_id=fin_ent_account_id
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        self.download_receipts(
            s,
            account_scraped,
            movements_scraped,
            movements_parsed_corresponding
        )

        self.download_checks(
            account_scraped,
            movements_scraped,
        )

        return True, len(movements_scraped) == 0

    def _get_movements_parsed_api_v2(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            date_from: datetime) -> Tuple[bool, List[MovementParsed], bool]:
        """
        :return: (ok, movs_parsed, is_reached_page_limit)
        """
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        req_url_i = (
            'https://empresas3.gruposantander.es/paas/api/v2/nwe-cuentas-api/v1/cuentas/'
            '{acc}/movimientos?fechaDesde={date_from}'
            '&fechaHasta={date_to}&tipoFecha=fechaOperacion&size={size}'.format(
                acc=account_scraped.AccountNo,
                date_from= date_from.strftime('%Y-%m-%d'),
                date_to=self.date_to.strftime('%Y-%m-%d'),
                size=15
            )
        )

        movs_parsed = []  # type: List[MovementParsed]
        is_reached_page_limit = False
        last_mov_date_str = ''
        resp_movs_i = Response()
        for page_ix in range(1, 300):
            self.logger.info('{}: page #{}: get movements{}'.format(
                fin_ent_account_id,
                page_ix,
                ' (last mov date={})'.format(last_mov_date_str) if last_mov_date_str else ''
            ))
            req_exc = ''
            for att in range(3):
                try:
                    resp_movs_i = s.get(
                        req_url_i,
                        headers=self._auth_headers(),
                        proxies=self.req_proxies,
                    )

                    if resp_movs_i.status_code == 204:
                        self.logger.info("{}: 'no movements' marker detected. Skip".format(
                            fin_ent_account_id
                        ))
                        self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.SUCCESS)
                        return True, [], False

                    resp_movs_i_json = resp_movs_i.json()
                    break
                except Exception as e:
                    self.logger.error("{}: page #{}: can't get resp_movs_i. Retry. HANDLED EXCEPTION: {}".format(
                        fin_ent_account_id,
                        page_ix,
                        e,
                    ))
                    time.sleep(2)
                    req_exc = str(e)
            else:
                self.basic_log_wrong_layout(
                    resp_movs_i,
                    '{}: page #{}: dates from {} to {}: error in resp_movs_i with exc: {}'.format(
                        fin_ent_account_id,
                        page_ix,
                        date_from.strftime(project_settings.SCRAPER_DATE_FMT),
                        self.date_to_str,
                        req_exc
                    )
                )
                self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
                return False, [], False

            if 'PRODUCTO NO CONSULTABLE POR ESTA APLICACION' in resp_movs_i.text:
                self.logger.info("{}: api v2: 'account is not available' marker detected. Skip".format(
                    fin_ent_account_id
                ))
                self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.SUCCESS)
                return True, [], False

            movs_parsed_i = parse_helpers_nuevo.get_movements_parsed_api_v2(resp_movs_i_json)
            movs_parsed.extend(movs_parsed_i)

            resp_prev_json = resp_movs_i_json
            if movs_parsed_i:
                last_mov_date_str = movs_parsed_i[-1]['operation_date']

            if '_links' not in resp_prev_json:
                self.basic_log_wrong_layout(resp_movs_i, '{}: no _links in response'.format(fin_ent_account_id))
                self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
                return False, [], False

            req_url_i = resp_prev_json['_links'].get('next', {}).get('href')
            if not req_url_i:
                self.logger.info('{}: no more pages w/ movements'.format(fin_ent_account_id))
                break
        else:
            is_reached_page_limit = True

        return True, movs_parsed, is_reached_page_limit

    def process_account_api_v2(
            self,
            s: MySession,
            account_scraped: AccountScraped):
        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        if not self.basic_is_in_process_only_accounts(account_scraped.AccountNo):
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.SKIPPED_EXPLICITLY)
            return True  # already reported

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(
            fin_ent_account_id,
            max_offset=ACCOUNTS_CUSTOM_OFFSET.get(fin_ent_account_id, project_settings.MAX_OFFSET)
        )
        date_from = datetime.strptime(date_from_str, project_settings.SCRAPER_DATE_FMT)

        self.basic_log_process_account('{} (using api v2)'.format(fin_ent_account_id), date_from_str)

        ok, movs_parsed_desc, is_reached_page_limit = self._get_movements_parsed_api_v2(
            s,
            account_scraped,
            date_from
        )

        movs_parsed_asc = parse_helpers.reorder_and_calc_temp_balances(movs_parsed_desc)

        movements_scraped, movements_parsed_corresponding = self.basic_movements_scraped_from_movements_parsed(
            movs_parsed_asc,
            date_from_str,
            bankoffice_details_name='Oficina',
            payer_details_name='Concepto',
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC,
            is_reached_pagination_limit=is_reached_page_limit,
            fin_ent_account_id=fin_ent_account_id
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        # TODO: impl receipts api v2, checks api v2

        return

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error(resp_logged_in)

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        results = []  # type: List[bool]
        ok, s, resp_contracts, contracts = self._get_contracts(s, resp_logged_in)
        if not ok:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        resp_contract = Response()
        reason_contract = ''
        if contracts:
            self.logger.info('Got {} contracts'.format(len(contracts)))
            # Many contracts - scrape each one by one
            for contract in contracts:
                ok, s, resp_contract_i, reason_contract_i = self.switch_to_contract(
                    s,
                    resp_logged_in,
                    contract,
                    resp_contracts
                )
                # Set only if not empty
                reason_contract = reason_contract_i if reason_contract_i else reason_contract
                resp_contract = resp_contract_i if reason_contract_i else resp_contract
                if not ok:
                    results.append(False)  # already reported
                    continue
                is_success = self.process_contract(s, resp_contract, contract)
                results.append(is_success)
                # Need to get resp_contracts with a new 'nweauthoritationtoken' token
                ok, s, resp_contracts, _ = self._get_contracts(s, resp_logged_in)
                if not ok:
                    results.append(False)
                    break
                # Extra actions for correspondence
                if self.is_receipts_scraper and self.basic_should_download_correspondence():
                    # No need to handle reason, we already checked it
                    ok, s, resp_contract, _ = self.switch_to_contract(s, resp_logged_in, contract, resp_contracts)
                    if ok:
                        # Correspondence documents are contract-level
                        self.download_correspondence(s)
        else:
            # One contract - default scraping process
            contract = Contract(
                org_title='DEFAULT CONTRACT',
                details={}
            )
            is_success = self.process_contract(s, resp_logged_in, contract)
            results.append(is_success)
            if self.is_receipts_scraper and self.basic_should_download_correspondence():
                self.download_correspondence(s)

        self.basic_log_time_spent('GET MOVEMENTS')

        if not all(results):
            # The only case of to get non-empty reason_contract is auth err on attempt switching to a contract
            if reason_contract:
                return self.basic_result_not_logged_in_due_reason(
                    resp_contract.url,
                    resp_contract.text,
                    reason_contract
                )
            else:
                return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        return self.basic_result_success()
