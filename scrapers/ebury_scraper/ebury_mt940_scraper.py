import random
import time
from collections import OrderedDict
from typing import Tuple, List

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import requests_helpers
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    ScraperParamsCommon, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_COOKIE, AccountParsed,
    MT940FileDownloaded
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from .custom_types import CurrencyBalance, AccountForMT940, Contract
from .environs import ENVS, ENV_DEFAULT

__version__ = '2.7.0'

__changelog__ = """
2.7.0
process_account_for_mt940: use date_to_offset
2.6.0
upd log msg
parse_helpers: get_account_parsed: handle null iban (bank_account_number)
2.5.0
date_from & date_to for the new account_no_for_file:
    _account_no__to__account_no_for_file
    use both account_no (backward comp) and account_no_for_file to get date_from
    get contract for single-contract access (was 'default')
2.4.0
process_account_for_mt940: upd req params
_upd_file_content (:25:GB40BARC20060578787099 -> :25:7099-EBPCLI466830-USD)
MUST_UPDATE_CONTENT local conf flag
2.3.0
login: added wrong credential marker
2.2.0
_upd_file_content (:25:GB40BARC20060578787099 -> :25:GB40BARC20060578787099-EBPCLI466830-USD)
2.1.1
upd scraper name
2.1.0
use basic_get_mt940_dates_and_account_status
2.0.0
multi-contract support
1.0.0
init
"""

WRONG_CREDENTIALS_MARKERS = ['Alguno de sus datos no es correcto.', 'var loginError = true']
# VB: pre/prod temp conf
MUST_UPDATE_FILE_CONTENT = True
DATE_TO_OFFSET = 2


class EburyMT940Scraper(BasicScraper):
    scraper_name = 'EburyMT940Scraper'
    fin_entity_name = 'EBURY'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    def _account_no__to__account_no_for_file(self, contract_id: str, account_no: str, currency: str):
        """GB68EBUR23122876803326 -> 3326-EBPCLI427344-EUR"""
        file_account_no = '{}-{}-{}'.format(account_no[-4:], contract_id, currency)
        return file_account_no

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()

        env = ENVS.get(self.db_financial_entity_access_id, ENV_DEFAULT)
        if not env:
            return s, Response(), False, False, DOUBLE_AUTH_REQUIRED_TYPE_COOKIE

        self.logger.info('Set confirmed environment for access {}'.format(
            self.db_financial_entity_access_id
        ))
        s = requests_helpers.update_mass_cookies_from_str(s, env['cookies'], '.ebury.com')
        self.req_headers = self.basic_req_headers_updated({
            'User-Agent': env['user_agent']
        })

        req_login_url = 'https://online.ebury.com/login/?next=/dashboard/'

        resp_init = s.get(
            req_login_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        csrf_token = parse_helpers.get_csrf_token(resp_init.text)
        if not csrf_token:
            return s, resp_init, False, False, "Can't extract csrf_token. Abort"

        req_login_params = OrderedDict([
            ('csrfmiddlewaretoken', csrf_token),
            ('username', self.username),
            ('password', self.userpass)
        ])

        time.sleep(1 + random.random())

        resp_logged_in = s.post(
            req_login_url,
            data=req_login_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_init.url,
            }),
            proxies=self.req_proxies
        )

        reason = ''

        is_logged = 'dashboard' in resp_logged_in.url
        is_credentials_error = any(m in resp_logged_in.text for m in WRONG_CREDENTIALS_MARKERS)
        if 'verify' in resp_logged_in.url:
            return s, resp_logged_in, False, False, DOUBLE_AUTH_REQUIRED_TYPE_COOKIE

        return s, resp_logged_in, is_logged, is_credentials_error, reason

    # not used for MT940
    def _get_accounts_parsed(self, s: MySession) -> List[AccountParsed]:

        csrf_token = s.cookies.get('csrftoken')
        accounts_parsed = []  # type: List[AccountParsed]

        # Step1: currencies and balances
        # 30_resp_inicio_balances.json
        resp_balances = s.get(
            'https://online.ebury.com/api/client/balances/',
            headers=self.basic_req_headers_updated({
                'accept': 'application/json',
                'x-csrftoken': csrf_token,
            }),
            proxies=self.req_proxies
        )

        resp_balances_json = resp_balances.json()
        cnc_balances = parse_helpers.get_currency_balances(resp_balances_json)  # type: List[CurrencyBalance]

        # Step2: account details for each currency
        for currency_balance in cnc_balances:
            # 35_resp_account_details_eur.json
            resp_account_details = s.get(
                'https://online.ebury.com/api/account-details/{}/'.format(currency_balance.currency),
                headers=self.basic_req_headers_updated({
                    'accept': 'application/json',
                    'x-csrftoken': csrf_token,
                }),
                proxies=self.req_proxies
            )
            resp_account_json = resp_account_details.json()
            account_parsed = parse_helpers.get_account_parsed(resp_account_json, currency_balance.balance)
            accounts_parsed.append(account_parsed)

        return accounts_parsed

    def _get_accounts_for_mt940(self, s: MySession) -> List[AccountForMT940]:
        csrf_token = s.cookies.get('csrftoken')
        resp_currency_accounts = s.get(
            'https://online.ebury.com/api/client/currency-accounts/',
            headers=self.basic_req_headers_updated({
                'accept': 'application/json',
                'x-csrftoken': csrf_token,
            }),
            proxies=self.req_proxies
        )
        resp_currency_accounts_json = resp_currency_accounts.json()
        accounts_for_mt940 = parse_helpers.get_accounts_for_mt940(resp_currency_accounts_json)
        return accounts_for_mt940

    def _switch_contract(self, s: MySession, contract: Contract) -> bool:
        self.logger.info("Switch to contract: '{}'".format(contract.contract_name))
        req_url = 'https://online.ebury.com/login/account/?next=/dashboard/'
        csrf_token = s.cookies.get('csrftoken')
        req_params = OrderedDict([
            ('csrfmiddlewaretoken', csrf_token),
            ('client_identifier', contract.contract_id)
        ])
        resp_switched = s.post(
            req_url,
            data=req_params,
            headers=self.basic_req_headers_updated({
                'Referer': req_url
            }),
            proxies=self.req_proxies
        )
        ok = resp_switched.url == 'https://online.ebury.com/dashboard/'
        if not ok:
            self.logger.error("{}: can't switch to contract. Abort".format(
                contract.contract_name
            ))
        return ok

    def process_access_for_mt940(self, s: MySession, resp_logged_in: Response) -> bool:
        contracts = parse_helpers.get_contracts(resp_logged_in.text)
        self.logger.info('Got {} contracts: {}'.format(
            len(contracts),
            contracts
        ))
        for contract in contracts:
            ok = self._switch_contract(s, contract)
            if not ok:
                return False  # already reported
            is_success = self.process_contract_for_mt940(s, contract)
            if not is_success:
                return False

        if not contracts:
            contract = parse_helpers.get_contract(resp_logged_in.text)
            self.logger.info("Got default contract: {}".format(contract))
            is_success = self.process_contract_for_mt940(s, contract)
            return is_success

        return True

    def process_contract_for_mt940(self, s: MySession, contract: Contract) -> bool:
        self.logger.info("Process contract '{}' (id {})".format(
            contract.contract_name,
            contract.contract_id
        ))
        accounts_parsed = self._get_accounts_parsed(s)
        self.logger.info('{}: got {} accounts: {}'.format(
            contract.contract_name,
            len(accounts_parsed),
            accounts_parsed
        ))
        accounts_for_mt940 = self._get_accounts_for_mt940(s)
        for account_for_mt940 in accounts_for_mt940:
            # Must map corresponding account or raise an exception
            account_parsed = [
                acc
                for acc in accounts_parsed
                if acc['financial_entity_account_id'] == account_for_mt940.fin_ent_account_id
            ][0]
            ok = self.process_account_for_mt940(s, contract, account_for_mt940, account_parsed)
            if not ok:
                return False

        return True

    def _upd_file_content(self, filename: str, filecontent: bytes, account_no_for_file: str) -> bytes:
        """Replaces account info from filename to :25 str

        20220104-MT940_Statement-EBPCLI466830-USD.fin

        {1:F01BARCGB22AXXX0001000001}{2:I940BARCGB22AXXXN3}{4:
        :20:220104190707287
        :25:GB40BARC20060578787099
        :28C:4/1
        :60F:C220104USD76538,35
        :62F:C220104USD76538,35
        -}

        replaces
        :25:GB40BARC20060578787099 -> :25:7099-EBPCLI466830-USD
        (last 4 digits of acc + info from filename)
        :returns updated filecontent
        """
        filecontent_str = filecontent.decode('utf8')
        extra_account_info = extract.re_first_or_blank('Statement-(.*?)[.]fin', filename)
        # bad new line: use strip() and replace() to avoid unexpected modifications
        line25 = extract.re_first_or_blank(':25:.*', filecontent_str).strip()
        account_no_suffix = line25[-4:]  # :25:GB40BARC20060578787099  -> 7099
        line25_upd = ':25:{}-{}'.format(account_no_suffix, extra_account_info)
        # verify explicitly
        # failure means that the file name generation method has been changed and dev need ASAP
        assert account_no_for_file in line25_upd
        filecontent_upd_str = filecontent_str.replace(line25, line25_upd)
        return filecontent_upd_str.encode('utf-8')

    def process_account_for_mt940(
            self,
            s: MySession,
            contract: Contract,
            account_for_mt940: AccountForMT940,
            account_parsed: AccountParsed) -> bool:

        csrf_token = s.cookies.get('csrftoken')
        log_date_fmt = '%d/%m/%Y'
        currency = account_for_mt940.currency
        account_no = account_parsed['account_no']

        # GB68EBUR23122876803326 -> 3326-EBPCLI427344-EUR
        # this val will replace account_no in downloaded file
        account_no_for_file = self._account_no__to__account_no_for_file(
            contract_id=contract.contract_id,
            account_no=account_no,
            currency=currency
        )
        self.logger.info('{}: account_no_for_file={}'.format(account_no, account_no_for_file))

        # DETECT DATES FOR OLD AND NEW APPROACH (with replaced account_no)

        date_from, date_to, is_active_account, is_account_level_results = \
            self.basic_get_mt940_dates_and_account_status(account_no, date_to_offset=DATE_TO_OFFSET)

        date_from_f, date_to_f, is_active_account_f, is_account_level_results_f = \
            self.basic_get_mt940_dates_and_account_status(account_no_for_file, date_to_offset=DATE_TO_OFFSET)

        if is_account_level_results_f:
            date_from = date_from_f
            date_to = date_to_f
            is_active_account = is_active_account_f

        if not is_active_account:
            return True  # already reported

        self.logger.info('{} ({}): process account for MT940 from {} to {}'.format(
            account_no,
            account_no_for_file,
            date_from.strftime(log_date_fmt),
            date_to.strftime(log_date_fmt)
        ))
        date_range = date_funcs.get_date_range(date_from, date_to)
        for download_date in date_range:
            download_date_str = download_date.strftime('%Y-%m-%d')

            # "/statements/mt940/528031/USD/20211222"
            # "/statements/mt940/528032/EUR/20211222" -- raw .fin file
            # "/statements/mt940/all/Todos/20211222" -- ZIP

            # https://online.ebury.com/statements/mt940/2022-04-29/?currency_account_id=592066&currency=USD
            req_mt940_url = 'https://online.ebury.com/statements/mt940/{}/'.format(download_date_str)
            req_mt940_params = OrderedDict([
                ('currency_account_id', account_for_mt940.currency_account_id),
                ('currency', currency),
            ])

            # VB: not used since 2.4.0
            # headers=self.basic_req_headers_updated({
            #     'x-csrftoken': csrf_token,
            # })

            resp_mt940 = s.get(
                req_mt940_url,
                params=req_mt940_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            # ('Content-Disposition', 'attachment; filename="20211223-MT940_Statement-EBPCLI466830-EUR.fin"')
            file_name = extract.re_first_or_blank(
                'filename="(.*?)"',
                resp_mt940.headers.get('Content-Disposition')
            )
            assert '.fin' in file_name
            self.logger.info('{} ({}): {}: downloaded MT940 file {}'.format(
                account_no,
                account_no_for_file,
                download_date.strftime(log_date_fmt),
                file_name
            ))
            filecontent_upd = (self._upd_file_content(file_name, resp_mt940.content, account_no_for_file)
                               if MUST_UPDATE_FILE_CONTENT else resp_mt940.content)
            self.mt940_files_downloaded.append(MT940FileDownloaded(
                file_name=file_name,
                file_content=filecontent_upd
            ))
            time.sleep(1 + random.random())
        return True

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

        is_success = self.process_access_for_mt940(s, resp_logged_in)

        if not is_success:
            return self.basic_result_common_scraping_error()

        self.basic_save_mt940s(self.mt940_files_downloaded)

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_mt940()
