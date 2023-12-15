import json
import os
import random
import subprocess
from typing import Tuple, Dict, List

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, ScraperParamsCommon,
    AccountParsed, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_COOKIE
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.banco_caminos_scraper import parse_helpers
from .custom_types import Contract
from .environs import Env, ENVS, ENV_DEFAULT

__version__ = '5.2.0'

__changelog__ = """
5.2.0
process_account: impl pagination
5.1.0
envs()
login: more log msgs
5.0.1
login: fixed 2FA detection
5.0.0
multi-contract support
4.2.0
MOVS_RESCRAPING_OFFSET
4.1.1
login: upd reason to DOUBLE_AUTH_REQUIRED_TYPE_COOKIE if no env
4.1.0
_decrypt_json
_login_company_id
process_contract: remove redundant params
cmd_get_encrypted_pwd: send _login_company_id (will be different for children)
_select_contract()
extracted org_title (was db_customer_name)
4.0.0
new web
3.12.0
call basic_upload_movements_scraped with date_from_str
3.11.0
REORDER_MOVEMENTS_FOR_DATES (useful for **00347)
3.10.1
upd log msg
3.10.0
use update_inactive_accounts
process_account: use basic_check_account_is_active
3.9.0
manual sms auth support (usage: $ MANUAL_SMS_AUTH=1 python...) 
3.8.1
aligned double auth msg
3.8.0
environ_cookies
removed concurrent scraping support to avoid 2fa (sms auth) on concurrent account processing
  (only sequential scraping, only one session)
parse_helpers: upd get_a_param
3.7.0
use basic_new_session
3.6.1
upd type hints
3.6.0
login failure reason report (SMS auth)
3.5.0
new user agent, sms auth step detector, more log msgs if can't get req_position_global_url
3.4.0
parse_helpers: get_accounts_parsed: extract account_no_param 
process_account:
  use account_parsed['account_no_param'] 
    (instead of earlier calculated, that wasn't correct in some cases) 
  concurrent scraping: reduce number of workers
3.3.0
basic_get_date_from
USD accounts support: 
  process_account: other req params, 
  parse_helpers: get_movements_parsed: other fields
3.2.0
now SESSION_EFBC cookie is in the response cookies (was on the page)
parse_helpers: handle if temp_balance=0 (blank string) 
3.1.0
basic_movements_scraped_from_movements_parsed: new format of the result
3.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
2.0.0
basic_movements_scraped_from_movements_parsed
OperationalDatePosition, KeyValue support
1.3.0
basic_set_movements_scraping_finished
basic_upload_movements_scraped
1.2.0
process_account: log in each time for correct concurrent scraping
1.1.1
is_credentials_error detector
1.1.0
correct extracting
"""

# Need new version of Node.
# Use local installation bcs can't get required version neither by OS pm nor by asdf
# On local machine alias still 'node', when deployed, it's a path to local installation under proj folder
NODE_BIN = ('node' if not project_settings.IS_DEPLOYED else os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    'node',
    'node-v16.13.1',
    'bin',
    'node'
))

CALL_JS_ENCRYPT__RSA_KEYGEN_LIB = '{} {}'.format(NODE_BIN, os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'banco_caminos_encrypter__rsa_keygen.js'
))

CALL_JS_ENCRYPT__AES_LOGIN_LIB = '{} {}'.format(NODE_BIN, os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'banco_caminos_encrypter__aes_login.js'
))

CALL_JS_ENCRYPT__AES_MSG_DECRYPT_LIB = '{} {}'.format(NODE_BIN, os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'banco_caminos_encrypter__aes_msg_decrypt.js'
))

MOVS_RESCRAPING_OFFSET = 7  # avoid too long msgs, that can't be passed as process cmd


class BancoCaminosScraper(BasicScraper):
    scraper_name = 'BancoCaminosScraper'
    # Scraper-level, 'BC' means BancoCaminos, can change in children (BF - Bancofar)
    _login_company_id = 'BC'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.update_inactive_accounts = False
        self._private_key = ''  # will set in login()
        self._uuid = ''
        # Encrypted {symmetricKey, uuid, seed}
        self._signing_data = ''
        self.req_proxies = [random.choice(self.req_proxies)]  # one proxy

    def envs(self) -> Dict[int, Env]:
        """To redefine in children"""
        return ENVS

    def _call_cmd(self, cmd: str) -> str:
        result_bytes = subprocess.check_output(cmd, shell=True)
        text = result_bytes.decode().strip()
        return text

    def _decrypt(self, msg: str) -> str:
        cmd = '{} "{}" "{}" "{}"'.format(
            CALL_JS_ENCRYPT__AES_MSG_DECRYPT_LIB,
            self._private_key,
            self._signing_data,
            msg
        )
        return self._call_cmd(cmd)

    def _decrypt_json(self, msg: str) -> dict:
        return json.loads(self._decrypt(msg))

    def _set_private_key(self, private_key: str):
        self._private_key = private_key

    def _set_uuid(self, uuid: str):
        self._uuid = uuid

    def _set_signing_data(self, signing_data: str):
        self._signing_data = signing_data

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()
        env = self.envs().get(self.db_financial_entity_access_id, ENV_DEFAULT)
        if not env.device_id:
            self.logger.warning("no configured environ for the access. Consider as 'DOUBLE AUTH required'")
            return s, Response(), False, False, DOUBLE_AUTH_REQUIRED_TYPE_COOKIE

        # Set custom User-Agent
        self.req_headers = self.basic_req_headers_updated({
            'User-Agent': env.user_agent
        })

        self.logger.info('Set confirmed environment for access {}'.format(
            self.db_financial_entity_access_id
        ))

        keys_str = self._call_cmd(CALL_JS_ENCRYPT__RSA_KEYGEN_LIB)
        # {'publicKey':..., 'privateKey':...}
        keys_json = json.loads(keys_str)
        self._set_private_key(keys_json['privateKey'])

        # Generate session data for the next encryption step
        # resp text like Aa0oM5NAFsxksK5WKGw/7L0Sj...oTbjCg== to feed to cmd_get_encrypted
        resp_key_exchange = s.post(
            'https://api.grupocaminos.es/key-exchange',
            headers=self.basic_req_headers_updated({
                'public-key': keys_json['publicKey'],
                'Referer': 'https://www.bancofaronline.es/'
            }),
            proxies=self.req_proxies
        )

        self._set_signing_data(resp_key_exchange.text)

        cmd_get_encrypted_pwd = (
            '{} "{username}" "{password}" "{device_id}" "{company_id}" "{private_rsa_key}" "{signing_data}"'.format(
                CALL_JS_ENCRYPT__AES_LOGIN_LIB,
                username=self.username,
                password=self.userpass,
                device_id=env.device_id,
                company_id=self._login_company_id,
                private_rsa_key=self._private_key,
                signing_data=self._signing_data
            )
        )

        # {'uuid':..., 'encrypted': ...}
        encrypted_pwd_and_uuid_str = self._call_cmd(cmd_get_encrypted_pwd)
        encrypted_pwd_and_uuid_json = json.loads(encrypted_pwd_and_uuid_str)
        self._set_uuid(encrypted_pwd_and_uuid_json['uuid'])

        req_login_params = {'payload': encrypted_pwd_and_uuid_json['encrypted']}

        resp_logged_in = s.post(
            'https://api.grupocaminos.es/login',
            json=req_login_params,
            headers=self.basic_req_headers_updated({
                'uuid': self._uuid,
                'Referer': 'https://www.bancofaronline.es/'
            }),
            proxies=self.req_proxies
        )
        # '{"status":401,"errorCode":"C401000201"}'
        is_logged = 'error' not in resp_logged_in.text
        is_credentials_error = '"errorCode":"C401000201"' in resp_logged_in.text
        reason = ''
        # 2FA
        if '"errorCode":"C4000000"' in resp_logged_in.text:
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COOKIE

        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def _get_contracts(self, s: MySession) -> List[Contract]:
        resp_contracts = s.get(
            'https://api.grupocaminos.es/contracts',
            headers=self.basic_req_headers_updated({
                'Content-Type': 'application/json',
                'uuid': self._uuid
            }),
            proxies=self.req_proxies
        )
        # see dev_new/100_resp_contracts_decrypted.json
        resp_contracts_json = self._decrypt_json(resp_contracts.text)
        contracts = [Contract(id=c['id'], org_title=c['description']) for c in resp_contracts_json['contracts']]
        return contracts

    def _select_contract(self, s: MySession, contract_id: str) -> dict:

        # Select contract
        resp_contract_selected = s.patch(
            'https://api.grupocaminos.es/contracts/{}'.format(contract_id),
            headers=self.basic_req_headers_updated({
                'Content-Type': 'application/json',
                'uuid': self._uuid
            }),
            proxies=self.req_proxies
        )

        resp_contract_selected_json = self._decrypt_json(resp_contract_selected.text)
        # 105_resp_contract_selected_decrypted.json: {'id': ..., 'descryption' ..., type: ...}
        return resp_contract_selected_json

    def process_access(self, s: MySession) -> bool:
        contracts = self._get_contracts(s)
        self.logger.info('Got {} contracts: {}'.format(
            len(contracts),
            contracts
        ))
        for contract in contracts:
            self.process_contract(s, contract)
        return True

    def process_contract(self, s: MySession, contract: Contract) -> bool:
        self.logger.info('Process {}'.format(contract))

        resp_contract_selected_json = self._select_contract(s, contract.id)
        if resp_contract_selected_json['id'] != contract.id:
            self.logger.error("{}: can't select contract. Abort".format(contract))
            return False

        org_title = contract.org_title

        resp_accounts = s.get(
            'https://api.grupocaminos.es/products/',
            headers=self.basic_req_headers_updated({
                'Content-Type': 'application/json',
                'uuid': self._uuid
            }),
            proxies=self.req_proxies
        )

        # 110_resp_products_decrypted.json
        resp_accounts_json = self._decrypt_json(resp_accounts.text)

        accounts_parsed = parse_helpers.get_accounts_parsed(resp_accounts_json)
        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                org_title,
                account_parsed,
            )
            for account_parsed in accounts_parsed
        ]

        self.logger.info('{}: got {} accounts: {}'.format(org_title, len(accounts_scraped), accounts_scraped))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        accounts_scraped_dict = self.basic_gen_accounts_scraped_dict(accounts_scraped)

        for account_parsed in accounts_parsed:
            self.process_account(s, account_parsed, accounts_scraped_dict)

        return True

    def process_account(self,
                        s: MySession,
                        account_parsed: AccountParsed,
                        accounts_scraped_dict: Dict[str, AccountScraped]) -> bool:

        account_scraped = accounts_scraped_dict[account_parsed['account_no']]
        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        account_no = account_scraped.AccountNo
        account_id = account_parsed['id']  # for reqs

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        self.logger.info('Process account {}'.format(account_no))

        date_from, date_from_str = self.basic_get_date_from_dt(
            fin_ent_account_id,
            rescraping_offset=MOVS_RESCRAPING_OFFSET
        )

        req_movs_url = 'https://api.grupocaminos.es/products/{}/movements'.format(account_id)
        req_movs_params = {
            'dateFrom': date_from.strftime('%Y%m%d'),
            'dateTo': self.date_to.strftime('%Y%m%d')
        }

        resp_movs = s.get(
            req_movs_url,
            params=req_movs_params,
            headers=self.basic_req_headers_updated({
                'Content-Type': 'application/json',
                'uuid': self._uuid
            }),
            proxies=self.req_proxies
        )

        resp_movs_json = self._decrypt_json(resp_movs.text)
        movements_parsed = parse_helpers.get_movements_parsed(resp_movs_json)

        resp_movs_i_json = resp_movs_json
        for page_ix in range(2, 50):  # avoid inf loop
            if not resp_movs_i_json['paging']['hasMorePages']:
                self.logger.info('{}: no more pages with movements'.format(fin_ent_account_id))
                break

            self.logger.info('{}: page #{}: get movements'.format(fin_ent_account_id, page_ix))
            pagination_key = resp_movs_i_json['paging']['nextPaginationKey']
            req_movs_params['paginationKey'] = pagination_key
            resp_movs_i = s.get(
                req_movs_url,
                params=req_movs_params,
                headers=self.basic_req_headers_updated({
                    'Content-Type': 'application/json',
                    'uuid': self._uuid
                }),
                proxies=self.req_proxies
            )
            resp_movs_i_json = self._decrypt_json(resp_movs_i.text)
            movements_parsed_i = parse_helpers.get_movements_parsed(resp_movs_i_json)
            movements_parsed.extend(movements_parsed_i)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str
        )

        self.logger.info(
            'Process_account {}: dates from {} to {}: movements: {}'.format(
                account_no,
                date_from_str,
                self.date_to_str,
                movements_scraped
            )
        )

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp_logged_in.url, resp_logged_in.text, reason)

        self.process_access(s)
        self.basic_log_time_spent('GET MOVEMENTS')

        return self.basic_result_success()
