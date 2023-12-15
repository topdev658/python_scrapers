import datetime
import random
import time
import urllib.parse
from collections import OrderedDict
from typing import List, Tuple

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (ScraperParamsCommon, MainResult)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from .custom_types import AccountGroup

__version__ = '1.8.0'
__changelog__ = """
1.8.0
use account-level result_codes
1.7.0
'success' flag for basic_set_movements_scraping_finished when it is necessary
1.6.0
call basic_upload_movements_scraped with date_from_str
1.5.0
credentials data assertions -> log err + set inactive
1.4.1
fixed log msgs
1.4.0
login:
  fixed resp_login_step1
  use new pares_helpers.map_ix_to_letter_ix
  check for indexes and lenghts of pin/pinpass to detect wrong credentials
1.3.0
use basic_new_session
upd type hints
fmt
1.2.0
click_back: inc delay
1.1.0
fix daytime balance integrity errors: 
  parse_helpers: get_account_parsed: use Today's cleared balance instead of Today's ledger
1.0.0
init
"""


class RBSScraper(BasicScraper):
    """Future movements are implemented
    and descriptions will be updated when available

    if date_to == today then date_to += dates_offset_for_future_movs

    Only serial processing is allowed
    To provide 'navigation integrity' the scraper
    uses click_back() after each process_account

    Future movements are scraped without full 'Narrative' details
    and will be updated when the details appear
    """
    scraper_name = 'RBSScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

        third_login_pass = self.db_connector.get_third_login_password()
        self.pin = third_login_pass.AccessThirdLoginValue
        self.pinpass = third_login_pass.AccessPasswordThirdLoginValue

        # future/today movs support
        self.today_str = date_funcs.today_str()
        self.today = datetime.datetime.strptime(self.today_str, project_settings.SCRAPER_DATE_FMT)
        self.is_scrape_future_movs = self.date_to >= self.today

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        """
        :return: (session, last_response, is_logged_in, is_credentials_error, err_reason)
        """

        s = self.basic_new_session()

        if not (self.pin and self.pinpass):
            self.logger.error('No pin/pinpass provided, will consider as "wrong credentials"')
            return s, Response(), False, True, ''

        req_init_url = 'https://www.bankline.rbs.com/CWSLogon/logon.do'
        req_init_params = OrderedDict([
            ('CTAuthMode', 'RBSG_CORP4P'),
            ('domain', '.bankline.rbs.com'),
            ('ct-web-server-id', 'Internet'),
            ('CT_ORIG_URL', '/bankline/rbs/default.jsp'),
            ('ct_orig_uri', 'https://www.bankline.rbs.com:443/bankline/rbs/default.jsp')
        ])
        resp_init = s.get(
            req_init_url,
            params=req_init_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        # enter login/passwd
        req_login_step1_url = 'https://www.bankline.rbs.com/CWSLogon/4P/CheckId.do'
        req_login_step1_params = OrderedDict([
            # ('ct_orig_uri', 'https://www.bankline.rbs.com:443/bankline/rbs/default.jsp'),
            # ('RANDOM_ID', parse_helpers.get_random_id(resp_init.text)),
            ('customerId', self.username),
            ('userId', self.userpass),
            # ('submit', 'Continue')
        ])
        resp_login_step1 = s.post(
            req_login_step1_url,
            data=req_login_step1_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_init.url
            }),
            proxies=self.req_proxies,
        )

        # enter pin
        req_login_step2_url = 'https://www.bankline.rbs.com/CWSLogon/4P/CheckPPPP.do'

        pin_ixs = parse_helpers.map_ix_to_letter_ix(resp_login_step1.text, 'pin-keys')
        pinpass_ixs = parse_helpers.map_ix_to_letter_ix(resp_login_step1.text, 'pass-keys')

        if len(pin_ixs) != 3 or len(pinpass_ixs) != 3:
            if 'Bankline is currently unavailable' in resp_login_step1.text:
                return s, resp_login_step1, False, False, "Bankline is unavailable"
            else:
                return s, resp_login_step1, False, False, "parsing error: wrong pin_ixs/pinpass_ixs"

        if max(pin_ixs) >= len(self.pin):
            self.logger.error('Max of required indexes > than length of pin (={}). '
                              'Consider as wrong credentials'.format(pin_ixs))
            is_credentials_error = True
            return s, resp_login_step1, False, is_credentials_error, ''
        if max(pinpass_ixs) >= len(self.pinpass):
            self.logger.error('Max of required indexes > than length of pinpass (={}). '
                              'Consider as wrong credentials'.format(pinpass_ixs))
            is_credentials_error = True
            return s, resp_login_step1, False, is_credentials_error, ''

        req_login_step2_params = OrderedDict([
            ('ct_orig_uri', 'https://www.bankline.rbs.com:443/bankline/rbs/default.jsp'),
            ('RANDOM_ID', parse_helpers.get_random_id(resp_login_step1.text)),
            ('pinIndexed[0].value', self.pin[pin_ixs[0]]),
            ('pinIndexed[1].value', self.pin[pin_ixs[1]]),
            ('pinIndexed[2].value', self.pin[pin_ixs[2]]),
            ('passIndexed[0].value', self.pinpass[pinpass_ixs[0]]),
            ('passIndexed[1].value', self.pinpass[pinpass_ixs[1]]),
            ('passIndexed[2].value', self.pinpass[pinpass_ixs[2]]),
            ('button', 'Continue')
        ])

        resp_login_step2 = s.post(
            req_login_step2_url,
            data=req_login_step2_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        is_credentials_error = 'incorrect credentials' in resp_login_step2.text
        resp_logged_in = resp_login_step2
        if not is_credentials_error:
            # confirm authorization
            req_login_step3_url = 'https://www.bankline.rbs.com/CWSLogon/4P/AcceptWelcome.do'
            req_login_step3_params = OrderedDict([
                ('ct_orig_uri', 'https://www.bankline.rbs.com:443/bankline/rbs/default.jsp'),
                ('RANDOM_ID', parse_helpers.get_random_id(resp_login_step2.text)),
                ('button', 'Confirm')
            ])
            resp_login_step3 = s.post(
                req_login_step3_url,
                data=req_login_step3_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
            )

            resp_home = s.get(
                'https://www.bankline.rbs.com/bankline/rbs/global/home.do',
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            resp_logged_in = resp_home

        is_logged = 'successfully logged onto' in resp_logged_in.text
        return s, resp_logged_in, is_logged, is_credentials_error, ""

    def _fetch_account_groups(self, s: MySession,
                              resp_logged_in: Response) -> List[AccountGroup]:
        """
        Note: groups are named 'sets' at the web page
        We use 'group' instead of 'set' to avoid misunderstanding
        with Python's collection name
        :return (is_success, List[AccountGroup])
        """
        self.logger.info("_fetch_account_groups")
        req_account_information_menu_link = extract.get_link_by_text(
            resp_logged_in.text,
            resp_logged_in.url,
            'Account information'
        )
        if not req_account_information_menu_link:
            self.logger.error(
                "Can't fetch account_groups. No req_account_information_menu_link. Skip. RESPONSE:{}\n".format(
                    resp_logged_in.text
                )
            )
            return []

        resp_account_information = s.get(
            urllib.parse.urljoin(resp_logged_in.url, req_account_information_menu_link),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_account_groups_menu_link = extract.get_link_by_text(
            resp_account_information.text,
            resp_account_information.url,
            'View Account Set balances'
        )

        if not req_account_groups_menu_link:
            self.logger.error(
                "Can't fetch account_groups. "
                "Parsing error: no req_account_groups_menu_link in resp_account_information. "
                "Skip. RESPONSE:\n{}".format(
                    resp_account_information
                )
            )
            return []

        resp_account_sets = s.get(
            urllib.parse.urljoin(resp_logged_in.url, req_account_groups_menu_link),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        account_groups = parse_helpers.get_account_groups(
            resp_account_sets.text,
            resp_account_sets.url
        )  # type: List[AccountGroup]

        # Hardcoded behaviour: if found 'TESORALIA' in account groups titles
        # then remove all other groups from the list to process only this one
        # If 'TESORALIA' not in account groups titles, then all
        # groups will be processed
        for account_group in account_groups:
            if account_group.title == 'TESORALIA':
                self.logger.info("Found 'TESORALIA' account groups: all other groups will be ignored")
                account_groups = [account_group]
                break

        return account_groups

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        account_groups = self._fetch_account_groups(s, resp_logged_in)
        if not account_groups:
            return False

        self.logger.info("Account groups to process: {}".format(str([g.title for g in account_groups])))

        account_groups_len = len(account_groups)
        for group_ix in range(account_groups_len):
            account_group = account_groups[group_ix]
            self.process_account_group(s, resp_logged_in, account_group.url, group_ix)
            # upd after all but the last
            if group_ix < (account_groups_len - 1):
                account_groups_upd = self._fetch_account_groups(s, resp_logged_in)
                # check the next
                if group_ix + 1 >= len(account_groups_upd):
                    self.logger.error("process_access: can't process group with ix={} >= len(groups)."
                                      " Skip. Groups: {}".format(group_ix, account_groups_upd))
                    return False
                account_groups = account_groups_upd

        return True

    def _fetch_account_details_urls(self, s: MySession, acc_group_url: str) -> List[str]:
        self.logger.info("_fetch_account_details_urls")

        resp_accounts_10_per_page = s.get(
            acc_group_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_link_50_accs, req_params_50_accs_basic = extract.build_req_params_from_form_html_patched(
            resp_accounts_10_per_page.text,
            'AccountSummaryForm',
            is_ordered=True
        )

        if 'org.apache.struts.taglib.html.TOKEN' not in req_params_50_accs_basic:
            self.logger.error("_fetch_account_details_urls: can't get correct token. "
                              "Skip. RESPONSE:\n{}".format(resp_accounts_10_per_page.text))
            return []

        req_params_50_accs = OrderedDict([
            ('org.apache.struts.taglib.html.TOKEN',
             req_params_50_accs_basic['org.apache.struts.taglib.html.TOKEN']),
            ('ncn', req_params_50_accs_basic['ncn']),
            ('currencyCode', ''),
            ('balDate', ''),
            ('vlName', 'ai_accountsetbal_vl'),
            ('vlSize', '50'),
            ('submit', 'Go')
        ])

        resp_accounts_50_per_page = s.post(
            urllib.parse.urljoin(resp_accounts_10_per_page.url, req_link_50_accs),
            data=req_params_50_accs,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # page with details and recent movements
        account_details_urls = parse_helpers.get_account_details_urls(resp_accounts_50_per_page.text,
                                                                      resp_accounts_50_per_page.url)

        return account_details_urls

    def process_account_group_old(self, s: MySession, resp_logged_in: Response,
                                  acc_group_url: str, group_ix: int) -> bool:

        account_details_urls = self._fetch_account_details_urls(s, acc_group_url)
        account_details_urls_len = len(account_details_urls)

        self.logger.info("Group #{} has {} accounts".format(group_ix, account_details_urls_len))

        for acc_ix in range(account_details_urls_len):
            account_details_url = account_details_urls[acc_ix]
            self.process_account(s, account_details_url, group_ix, acc_ix)
            # upd after all but the last
            if acc_ix < account_details_urls_len - 1:
                account_groups = self._fetch_account_groups(s, resp_logged_in)
                if group_ix >= len(account_groups):
                    self.logger.error("process_account_group: can't use group with ix={} >= len(groups)."
                                      " Skip. Groups: {}".format(group_ix, account_groups))
                    return False
                account_details_urls_upd = self._fetch_account_details_urls(s, account_groups[group_ix].url)
                # check the next
                if acc_ix + 1 >= len(account_details_urls_upd):
                    self.logger.error("process_account_group: can't process account with ix={} >= len(accs)."
                                      " Skip. Acc urls: {}".format(group_ix, account_details_urls_upd))
                    return False
                account_details_urls = account_details_urls_upd

        return True

    def process_account_group(self, s: MySession, resp_logged_in: Response,
                              acc_group_url: str, group_ix: int) -> bool:

        account_details_urls = self._fetch_account_details_urls(s, acc_group_url)
        account_details_urls_len = len(account_details_urls)

        self.logger.info("Group #{} has {} accounts".format(group_ix, account_details_urls_len))

        for acc_ix in range(account_details_urls_len):
            account_details_url = account_details_urls[acc_ix]
            # we get upd resp_accounts_50_per_page after click_back()
            resp_accounts_50_per_page = self.process_account(s, account_details_url, group_ix, acc_ix)
            # upd after all but the last
            if acc_ix < account_details_urls_len - 1:
                account_details_urls_upd = parse_helpers.get_account_details_urls(
                    resp_accounts_50_per_page.text,
                    resp_accounts_50_per_page.url
                )
                # check the next
                if acc_ix + 1 >= len(account_details_urls_upd):
                    self.logger.error("process_account_group: can't process account with ix={} >= len(accs)."
                                      " Skip. Acc urls: {}".format(acc_ix, account_details_urls_upd))
                    return False
                account_details_urls = account_details_urls_upd

        return True

    def process_account(self, s: MySession, account_details_url: str,
                        group_ix: int, acc_ix: int) -> Response:
        """
        Movements temp_balance calculation:
        1. the website shows the only today's open (Start of day cleared)
        and the current balance (Today's cleared) of an account even during movs filtering
        2. today's movements (future movements) have no temp_balance and extended description information
        3. in an exported excel file, there is no field 'temp_balance'

        Solution:
        if date_to >= today
        then
            set date_to = date of the newest future movement
            calculate temp_balances in excel from the current account balance
        else
            calculate temp balances in excel \
             from the most recent movement's temp_balance from the web page

        Update descriptions of previously scraped movements

        click_back() allows to renew accounts urls to process next accounts
        or many additional actions required (groups -> group -> accounts)
        """

        def click_back(resp_recent: Response) -> Response:
            time.sleep(0.2 + random.random() * 0.2)
            req_back_params = OrderedDict([
                ('org.apache.struts.taglib.html.TOKEN', parse_helpers.get_token(resp_recent.text)),
                ('ncn', parse_helpers.get_ncn(resp_recent.text)),
                ('submit', 'Back'),
                ('isFirstCall', '')
            ])

            resp_back = s.post(
                'https://www.bankline.rbs.com/bankline/rbs/ai/accountstatement.do',
                data=req_back_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )
            return resp_back

        # 1: Get account_scraped
        resp_acc_details_w_recent_movs = s.get(
            account_details_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        account_parsed = parse_helpers.get_account_parsed(resp_acc_details_w_recent_movs.text)
        account_scraped = self.basic_account_scraped_from_account_parsed(
            self.db_customer_name,
            account_parsed,
            country_code='GBR',
            is_default_organization=True
        )
        self.logger.info('Got account: {}'.format(account_scraped))
        self.basic_upload_accounts_scraped([account_scraped])

        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        # calc date_to

        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        date_most_recent_mov = parse_helpers.get_date_of_most_recent_movement(
            resp_acc_details_w_recent_movs.text
        )

        if date_most_recent_mov == '':
            self.logger.info("{}: no recent movements, nothing to scrape. Skip".format(fin_ent_account_id))
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.SUCCESS)
            return click_back(resp_acc_details_w_recent_movs)

        date_to_str = date_most_recent_mov if self.is_scrape_future_movs else self.date_to_str

        self.basic_log_process_account(fin_ent_account_id, date_from_str, date_to_str=date_to_str)

        # 2: Get filtered movements and calc account_balance
        # from account_scraped.Balance OR most_recent_filtered_mov_temp_bal

        # expect
        # link: rbs/ai/accountstatement.do
        # params:
        # OrderedDict([('org.apache.struts.taglib.html.TOKEN',
        #               '52453c0b79c0129382587f4a3c3b3e6c'),
        #              ('ncn', '131'),
        #              ('dateFrom', '01/03/2019'),
        #              ('dateTo', '04/04/2019'),
        #              ('submit', 'Go'),
        #              ('vlName', 'ai_statement_vl'),
        #              ('vlSize', '10')])
        req_movs_filtered_link, req_movs_filtered_params = extract.build_req_params_from_form_html_patched(
            resp_acc_details_w_recent_movs.text,
            form_name='AccountStatementForm'
        )

        req_movs_filtered_params['dateFrom'] = date_from_str
        req_movs_filtered_params['dateTo'] = date_to_str

        resp_movs_filtered = s.post(
            urllib.parse.urljoin(resp_acc_details_w_recent_movs.url, req_movs_filtered_link),
            data=req_movs_filtered_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # Only movements of previous days have temp_balances
        # Will be used to calc temp_balances for movements in excel
        has_movs, most_recent_filtered_mov_temp_bal = parse_helpers.get_temp_balance_of_most_recent_movement(
            resp_movs_filtered.text
        )
        if not has_movs:
            self.logger.info('{}: no movements filtered by dates. Skip'.format(fin_ent_account_id))
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.SUCCESS)
            return click_back(resp_movs_filtered)

        account_balance = (
            account_scraped.Balance
            if self.is_scrape_future_movs
            else most_recent_filtered_mov_temp_bal
        )

        # 3. Get and parse EXCEL with movs
        # Note: today and future movements have no
        # all fields of descripton, should be updated later

        req_movs_excel_url = 'https://www.bankline.rbs.com/bankline/rbs/ai/accountstatement.do'
        req_movs_excel_link, req_movs_excel_params = extract.build_req_params_from_form_html_patched(
            resp_movs_filtered.text,
            form_name='AccountStatementForm',
            is_ordered=True
        )

        req_movs_excel_params = OrderedDict([
            ('org.apache.struts.taglib.html.TOKEN', parse_helpers.get_token(resp_movs_filtered.text)),
            ('ncn', parse_helpers.get_ncn(resp_movs_filtered.text)),
            ('submit', 'Export statement'),
            ('isFirstCall', '')
        ])

        resp_csv = s.post(
            req_movs_excel_url,
            data=req_movs_excel_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            # stream=True
        )

        movements_parsed = parse_helpers.get_movements_parsed(resp_csv.text, account_balance)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str
        )

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        # updates descriptions
        # of previously scraped future (or daytime) movements
        # which don't have temp_balances and all details in descriptions
        self.basic_update_movements_descriptions_if_necessary(
            account_scraped,
            movements_scraped
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        return click_back(resp_movs_filtered)

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if reason:
            return self.basic_result_not_logged_in_due_reason(resp_logged_in.url, resp_logged_in.text, reason)

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url, resp_logged_in.text)

        self.process_access(s, resp_logged_in)

        self.basic_log_time_spent('GET ALL BALANCES AND MOVEMENTS')
        return self.basic_result_success()
