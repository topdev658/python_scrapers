import json
import random
import time
import uuid
from typing import Dict, List, Tuple

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    AccountParsed, AccountScraped, MovementParsed,
    ScraperParamsCommon, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_COMMON
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.bbva_scraper import parse_helpers_particulares

__version__ = '4.0.0'

__changelog__ = """
4.0.0 2023.04.17
login: new implementation for login method avoiding splash use based on dev_partic/probe_of_concept_login_without_splash.py
3.2.0
login: 
    extra delay
    no need for several attempts and initial cookie check up (avoid false-positive detections)
3.1.0
login: upd initial cookie check up
3.0.0
uses Splash for initial reqs
process_contract: upd reqs
_get_encrypted: use uuid instead of js lib
2.9.0
increased pagination limit
2.8.0
call basic_upload_movements_scraped with date_from_str
2.7.0
2fa detector
2.6.0
skip inactive accounts
2.5.0
login: upd req params
2.4.0
use basic_new_session
upd type hints
2.3.0
parse_helpers: get_movements_parsed: use accountingBalance instead of availableBalance (sometimes absent)
process_account: handle case if there is no 'pagination' info
2.2.0
new web backend API: 
  changed login, process_company, process_account (incl pagination)
2.1.1
fmt, removed unused and commented code
2.1.0
process_account, parse_helpers_particulares: new backend API for movements
2.0.0
new web backend requests
1.4.0
login: changed assertion: handled case when self.sid == ""
1.3.0
basic_movements_scraped_from_movements_parsed: new format of the result 
1.2.0
parse_helpers_particulares: extract account position from its field, don't calculate it bcs it may be different
end
1.1.0a
parse_helpers: get_accounts_parsed: skip inactive accounts
1.0.0a
Init. Limitation: can extract only last 40 movements 
"""

MOVS_PER_PAGE = 40
UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1'
REF ='https://movil.bbva.es/apps/woody/client'

class BBVAParticularesScraper(BasicScraper):
    scraper_name = 'BBVAParticularesScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.contact_id = ''
        self.aso_sso_params = ''
        self.tsec_param = ''
        self.user_param = ''
        self.update_inactive_accounts = False
        self.req_headers = self.basic_req_headers_updated({'User-Agent': UA})
        self.req_proxies_all = proxies
        self.req_proxies = self._choose_random_proxy()

    def _choose_random_proxy(self) -> List[dict]:
        """Returns list containing only one random proxy"""
        return [random.choice(self.req_proxies_all)]

    def _date_ymd_str(self, date_dmy_str) -> str:
        d, m, y = date_dmy_str.split('/')
        return '{}-{}-{}'.format(y, m, d)

    def _get_encrypted(self) -> str:
        return str(uuid.uuid4())

    def _ts(self) -> str:
        return str(int(time.time() * 1000))

    def _custom_req_headers_new(self) -> Dict[str, str]:

        req_headers = self.basic_req_headers_updated({
            'tsec': self.tsec_param,
            # 'contactid': self.contact_id,
            # 'X-RHO-PARENTSPANID': '',  # 'ns/com.bbva.es.channels/mrs/web/spans/38b3dc35-16b9-455e-ba90-8024d76cc518',
            # 'X-RHO-TRACEID': ''  # '0b5de6ad-b4b3-4c43-8656-fee88665312d'
        })
        return req_headers

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1',
            'Referer': 'https://movil.bbva.es/apps/woody/client',
            }
        s = self.basic_new_session()
        s.headers.update(headers)

        payload = {
            "authentication": {
                "consumerID": "00000031",
                "authenticationData": [
                    {
                        "authenticationData": [
                            self.userpass
                        ],
                        "idAuthenticationData": "password"
                    }
                ],
                "authenticationType": "02",
                "userID": "0019-0{}".format(self.username)
            }
        }
        resp_auth_token = s.post(
            "https://servicios.bbva.es/ASO/TechArchitecture/grantingTickets/V02", json=payload)
        tsec = resp_auth_token.headers.get('tsec')

        if resp_auth_token.status_code == 403 and '"system-error-code":"forbidden"' in resp_auth_token.text:
            is_credentials_error = True
            return s, resp_auth_token, False, is_credentials_error, ''

        user_param = resp_auth_token.json()['user']['id']
        params_financial_overview = {
            'customer.id': user_param,
            'showSicav': 'false',
            'showPending': 'true'
        }
        s.headers.update({
            'tsec': tsec
        })

        is_logged = bool(tsec)

        is_credentials_error = False  # checked earlier

        reason = ''
        if 'multistepProcessId' in resp_auth_token.text:
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        if is_logged:
            self.tsec_param = tsec
            # self.contact_id = contact_id
            self.user_param = json.loads(resp_auth_token.text)['user']['id']

        return s, resp_auth_token, is_logged, is_credentials_error, reason


    def process_contract(self, s: MySession) -> bool:

        req_accounts_params = {
            'customer.id': self.user_param,
            'showSicav': 'false',
            'showPending': 'true',
        }

        resp_accounts = s.get(
            'https://www.bbva.es/ASO/financial-overview/v1/financial-overview',
            params=req_accounts_params,
            headers=self._custom_req_headers_new(),
            proxies=self.req_proxies
        )

        resp_accounts_json = resp_accounts.json()
        accounts_parsed = parse_helpers_particulares.get_accounts_parsed(resp_accounts_json)

        resp_org = s.get(
            'https://www.bbva.es/ASO/contextualData/V02/{}'.format(self.user_param),
            headers=self._custom_req_headers_new(),
            proxies=self.req_proxies
        )
        organization_title = parse_helpers_particulares.get_organization_title(resp_org.json())
        if not organization_title:
            self.basic_log_wrong_layout(resp_org, "Can't parse organization_title. Abort")
            return False

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                organization_title,
                account_parsed,
            )
            for account_parsed in accounts_parsed
        ]
        self.logger.info('Got {} accounts: {}'.format(len(accounts_scraped), accounts_scraped))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        accounts_scraped_dict = self.basic_gen_accounts_scraped_dict(accounts_scraped)

        # there are no accesses with many accounts (2 max) - use serial processing
        for ix, account_parsed in enumerate(accounts_parsed):
            self.process_account(s, account_parsed, accounts_scraped_dict, ix)

        return True

    def process_account(self, s: MySession,
                        account_parsed: AccountParsed,
                        accounts_scraped_dict: Dict[str, AccountScraped],
                        acc_ix: int) -> bool:
        fin_ent_account_id = account_parsed['financial_entity_account_id']
        account_scraped = accounts_scraped_dict[fin_ent_account_id]

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        req_movs_filtered_url = (
            'https://www.bbva.es/ASO/accountTransactions/V02/accountTransactionsAdvancedSearch/'
            '?paginationKey=0&pageSize=40'
        )

        movements_parsed_desc = []  # type: List[MovementParsed]
        req_movs_filtered_url_i = req_movs_filtered_url
        n_movs_parsed_desc = 0
        n_movs_total_expected = 0
        for page_num in range(1, 201):  # limit to avoid hanged loops
            self.logger.info('{}: get movements_parsed from page {}'.format(
                fin_ent_account_id,
                page_num
            ))

            req_movs_filtered_params = {
                "accountContracts": [{
                    "contract": {"id": account_parsed['id']},
                    "account": {
                        "currentBalance": {
                            "accountingBalance": {
                                "currency": {
                                    "id": account_scraped.Currency,
                                    "code": account_scraped.Currency,
                                    "decimalNumber": 0
                                },
                                "amount": account_scraped.Balance
                            },
                            "availableBalance": {
                                "currency": {
                                    "id": account_scraped.Currency,
                                    "code": account_scraped.Currency,
                                    "decimalNumber": 0
                                },
                                "amount": account_parsed['available_balance']
                            }
                        }
                    }
                }],
                "customer": {"id": self.user_param},
                "searchText": None,
                "orderField": "DATE_FIELD",
                "orderType": "DESC_ORDER",
                "filter": {
                    "dates": {
                        "from": "{}T00:00:00.000Z".format(self._date_ymd_str(date_from_str)),
                        "to": "{}T23:59:59.000Z".format(self._date_ymd_str(self.date_to_str))
                    },
                    "amounts": None,
                    "operationType": None
                }
            }

            resp_movs_filtered_i = s.post(
                req_movs_filtered_url_i,
                json=req_movs_filtered_params,
                headers=self._custom_req_headers_new(),
                proxies=self.req_proxies
            )

            resp_movs_filtered_i_json = resp_movs_filtered_i.json()

            # all movements from all pages
            movements_parsed_i = parse_helpers_particulares.get_movements_parsed(
                self.logger,
                resp_movs_filtered_i_json
            )
            movements_parsed_desc.extend(movements_parsed_i)

            # validate n_movs
            n_movs_parsed_desc = len(movements_parsed_desc)
            if 'pagination' in resp_movs_filtered_i_json:
                n_movs_total_expected = resp_movs_filtered_i_json['pagination']['total']
            else:
                # no pagination - no checkups
                n_movs_total_expected = n_movs_parsed_desc
                break

            next_page_link = parse_helpers_particulares.get_next_page_link(resp_movs_filtered_i_json)
            if not next_page_link:
                break

            if n_movs_parsed_desc > n_movs_total_expected:
                break
            # next page
            if not next_page_link.startswith('/accountTransactions'):
                self.basic_log_wrong_layout(
                    resp_movs_filtered_i,
                    '{}: unexpected next_page_link. Continue as is'.format(fin_ent_account_id)
                )
            req_movs_filtered_url_i = 'https://www.bbva.es/ASO' + next_page_link

        if n_movs_parsed_desc != n_movs_total_expected:
            self.logger.error('{}: parsing error. Extracted {} movements != expected {}. Continue as is'.format(
                fin_ent_account_id,
                n_movs_parsed_desc,
                n_movs_total_expected
            ))

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_desc,
            date_from_str
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

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
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        self.process_contract(s)

        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
