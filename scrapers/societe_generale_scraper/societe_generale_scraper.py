import base64
import html
import os
import random
import subprocess
import time
import traceback
import urllib.parse
from collections import OrderedDict
from typing import List, Tuple, Dict

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (AccountScraped, ScraperParamsCommon,
                                  MovementParsed, MainResult)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.societe_generale_scraper import login_helpers
from scrapers.societe_generale_scraper import parse_helpers

__version__ = '1.5.0'

__changelog__ = """
1.5.0
call basic_upload_movements_scraped with date_from_str
1.4.0
use basic_new_session
upd type hints
fmt
1.3.0
use basic_get_date_from
1.2.0
delay to avoid bans
1.1.0
reorder_movements_and_recalculate_temp_balances
1.0.0
init
"""

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'societe_generale_encrypter.js'
))

MOVEMENTS_ON_PAGE_MAX = 15


class SocieteGeneraleScraper(BasicScraper):
    """
    Gotchas:
    - PASSED: can log in only via recognized graphical pinpad
    - PASSED: the pinpad has corrupted size
        (doesn't equal to num_digits * digit_size - width has additional pixel)
    - PASSED: when log in, the back-end sends TLS handshake error
        -- thanks for cookies, I can extract necessary data
    - PASSED: should load each page in 2 steps: left menu and page content (after parsed main menu page)
    - PASSED: can't process accounts in parallel mode: sometimes back-end doesn't switch to next page
    - PASSED: no year in movement's dates - should be calculated similar to la caixa
    - PASSED: no temp balances in movements - should be calculated
    - PASSED: back-end returns movements in descending ordering for several dates
        but in ascending ordering if one date (!)
        -- should be reordered and temp_balances should be recalculated
    - WIP: it looks like they can ban proxies temporary (all subnet), the server just doesn't response
        -- should try to scrape later, added delay
    - WIP: check movements ordering for 2 days in response
    """

    scraper_name = 'SocieteGeneraleScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.req_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0'
        }

    def _delay(self):
        delay = 0.2 + random.random()
        self.logger.info('delay {:.2f}s...'.format(delay))
        time.sleep(delay)

    def _get_img(self, img_encoded: str) -> bytes:
        img_bytes = base64.b64decode(html.unescape(img_encoded))
        # with open("img01.gif", 'wb') as f:
        #     f.write(img_bytes)
        return img_bytes

    def _get_pass_encrypted(self, cle_param: str, exponent_param: str, password_as_letters: str) -> str:
        # then encrypt(cle_param, exponent_param, password_as_shaked_letters)
        # encrypt('c342fsdfmm...", "10001, "cjiiaj")
        cmd = '{} "{}" "{}" "{}"'.format(
            CALL_JS_ENCRYPT_LIB,
            cle_param,
            exponent_param,
            password_as_letters
        )
        result_bytes = subprocess.check_output(cmd, shell=True)
        pass_encrypted = result_bytes.decode().strip()
        return pass_encrypted

    def login(self) -> Tuple[MySession, Response, bool, bool]:
        s = self.basic_new_session()

        # resp_init and resp_login_view to get initial cookies

        resp_init = s.get(
            'https://unified-access.societegenerale.com/portal/index.html#/',
            headers=self.req_headers,
            proxies=self.req_proxies)

        # get login view init
        resp_login_view = s.get(
            'https://unified-access.societegenerale.com/portal/static/login.view.html',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # get encrypt parameters and shaked_digits img
        req_kbrd_url = 'https://unified-access.societegenerale.com/portal/initClavierVirtuel.do'
        req_kbrd_params = {
            'timestamp': str(int(time.time() * 1000))  # 1537730404140 use real
        }
        resp_kbrd = s.post(
            req_kbrd_url,
            data=req_kbrd_params,
            headers=self.req_headers,
            proxies=self.req_proxies

        )

        # {"cle":"c38265e...","exponent":"10001","image":"R0lGODlhngL4APMAAGZmZnBwcHp6eoWFhY&#x2b...;"}
        resp_kbrd_json = resp_kbrd.json()
        cle_param = resp_kbrd_json['cle']
        exponent_param = resp_kbrd_json['exponent']
        img_base64 = resp_kbrd_json['image']

        img_bytes = self._get_img(img_base64)
        pinpad_digits = login_helpers.get_pinpad_digits(img_bytes)
        password_as_letters = login_helpers.pass_digits_to_letters(self.userpass, pinpad_digits)
        password_encrypted = self._get_pass_encrypted(cle_param, exponent_param, password_as_letters)

        req_login_params = OrderedDict([
            ('loginType', 'ClavierVirtuel'),
            ('j_username', self.username),
            ('j_password', password_encrypted),
            ('ongletAppli', 'ongletSGW')
        ])

        req_headers = self.req_headers.copy()
        req_headers['X-Requested-With'] = 'XMLHttpRequest'
        req_headers['Referer'] = 'https://unified-access.societegenerale.com/portal/index.html'
        req_headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        req_headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        req_headers['Connection'] = 'keep-alive'

        req_login_url = 'https://unified-access.societegenerale.com/portal/loginProcess.do'
        # to catch data from cookie even on resp exception
        s.success_on_cookies_even_if_exception = ['DETREPEAUT']
        resp_login_opt = s.post(
            req_login_url,
            data=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # we expect behavior when empty response but useful cookie

        # and can extract necessay data from cookie 'DETREPEAUT'
        # {"codeStatus":"200","codeError":"","codeDetailError":"",
        # "Roles":["19900N",999914N","USER"],
        # "loginStatus":"OK","NEPassword":"52","tokenName":"token",
        # "tokenvalue":"016c35c7-01d0-4b72-bfe6-1c487df95510",
        # "lang":"es","nom":"R2FyY2lh","prenom":"D.","prenomComplet":"RGFuaWVs",
        # "EAcces":"","DC":"1537947939000","CDCon":"SGW","idAbo":"GB16A332",
        # "userName":"59213937","ongletAppli":"ongletSGW",
        # "loginType":"ClavierVirtuel",
        # "raisonSociale":"U1RBTkRBUkQgTElGRSBJTlZFU1RNRU5UUyBMVEQ=",
        # "prefixmessage":"443486","email":"dgj@auxadi.com","fiabilite":"FIABILISE"}

        # the cookie DETREPEAUT contains exact the same text as resp text (if provided)
        resp_login_text = resp_login_opt.text \
            if resp_login_opt else s.cookies.get_dict().get("DETREPEAUT", "")

        is_logged = '"loginStatus":"OK"' in resp_login_text
        is_credentials_error = '"codeError":"UTILISATEURPASSWORDERRONE"' in resp_login_text

        # then handle response usual way
        s.success_on_cookies_even_if_exception = []
        return s, resp_login_opt, is_logged, is_credentials_error

    def process_contract(self, s: MySession) -> bool:
        self.logger.info('Process contract')
        self._delay()
        try:
            resp_position_global = s.get(
                "https://unified-access.societegenerale.com/"
                "portal/site/SogecashWeb/template.LOGIN/action.process/",
                headers=self.req_headers,
                proxies=self.req_proxies
            )
        except:
            self.logger.error(
                "{}\n Probable reason: the proxies were banned (temporary). Try later".format(
                    traceback.format_exc()
                )
            )
            return False

        accounts_list_link = parse_helpers.get_page_content_req_link(resp_position_global.text)
        if accounts_list_link:
            accounts_list_url = urllib.parse.urljoin(resp_position_global.url, accounts_list_link)
        else:
            self.logger.error("Can't get accounts_list_link. Check the layout. Finishing now.\n"
                              "RESPONSE\n{}".format(resp_position_global.text))
            return False

        resp_accounts = s.get(
            accounts_list_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_parsed = parse_helpers.get_accounts_parsed(resp_accounts.text, resp_accounts.url)
        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(
                self.db_customer_name,
                acc_parsed,
                is_default_organization=True
            )
            for acc_parsed in accounts_parsed
        ]

        self.logger.info('Accounts: {}'.format(accounts_scraped))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        # PREPARE PAGE FOR ACCOUNTS PROCESSING
        # 1. Switch to 'Extractos de cuentas' page (from position_global page)
        # 2. Load page content with accounts/mov filter

        # switch to 'Extractos de cuentas' page (from position_global page)
        req_acc_mov_page_url = extract.get_link_by_text(
            resp_position_global.text,
            resp_position_global.url,
            'Extractos de cuentas'
        )

        resp_acc_mov_page = s.get(
            req_acc_mov_page_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # extract url of content with mov filter
        acc_mov_filter_content_link = parse_helpers.get_page_content_req_link(resp_acc_mov_page.text)
        if acc_mov_filter_content_link:
            acc_mov_filter_content_url = urllib.parse.urljoin(resp_position_global.url,
                                                              acc_mov_filter_content_link)
        else:
            self.logger.error("Can't get acc_mov_filter_content_link. Check the layout. "
                              "Finishing now.\nRESPONSE\n{}".format(resp_position_global.text))
            return False

        resp_mov_filter = s.get(
            acc_mov_filter_content_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_dropdown_option_values = parse_helpers.get_accounts_dropdown_option_values(
            resp_mov_filter.text
        )

        # get and save movements
        # 'and accounts_parsed' to avoid exception in max_workers=len(accounts_scraped)

        # unstable opening of previous pages with movements if concurrent processing
        # so, only serial processing implemented
        # or need to log in to process each account
        for account_scraped in accounts_scraped:
            # try to avoid bans
            self._delay()
            self.process_account(s, resp_mov_filter, account_scraped,
                                 accounts_dropdown_option_values)

        return True

    def process_account(self, s: MySession,
                        resp_mov_filter: Response,
                        account_scraped: AccountScraped,
                        accounts_dropdown_option_values) -> bool:

        account_no = account_scraped.AccountNo
        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        account_dropdown_id = accounts_dropdown_option_values.get(fin_ent_account_id)
        if not account_dropdown_id:
            self.logger.error("Can't process_account for {}: "
                              "can't find corresponding account_dropdown_id from {}"
                              "Finishing now.\nRESPONSE\n{}".format(fin_ent_account_id,
                                                                    accounts_dropdown_option_values,
                                                                    resp_mov_filter.text))
            return False

        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(account_no, date_from_str)

        # filter movements
        req_movs_filtered_link, err = parse_helpers.get_movements_filtered_link(resp_mov_filter.text)
        if err:
            self.logger.error("Can't process_account for {}: err {}"
                              "Finishing now.\nRESPONSE\n{}".format(account_no,
                                                                    err, resp_mov_filter.text))
            return False

        req_filtered_movs_url = urllib.parse.urljoin(resp_mov_filter.url, req_movs_filtered_link)

        req_movs_filtered_params = OrderedDict([
            ('_eventId', ''),
            ('service', 'Navigation'),
            ('sgniUrl', '/sgw/NavigationServlet'),
            ('_GOTO', 'RelevesComptes'),
            ('dateDebutPourEdition', date_from_str),  # 01/11/2017
            ('dateFinPourEdition', self.date_to_str),  # 26/09/2018
            ('_CompteSelectionne', account_dropdown_id),  # 1157204
            ('_ClasseurSelectionne', '1'),
            ('_ExtraitSelectionne', ''),
            ('_NumeroPage', '1'),
            ('validation', '1'),
            ('changepage', '0'),
            ('lstCompte', account_dropdown_id),
            ('_banque', ''),
            ('_devise', ''),
            ('_dateSoldeInitial', date_from_str),
            ('_soldeInitial', ''),
            ('_dateSoldeFinal', self.date_to_str),
            ('_soldeFinal', '')
        ])  # type: Dict[str, str]

        # temp_balance and prev_date_obj will be redefined in
        # loop to iterate over pages
        # temp_balance - to calculate temp_balance for each movement
        temp_balance = account_scraped.Balance
        prev_date_obj = self.date_to
        req_headers = self.req_headers.copy()

        movements_parsed = []  # type: List[MovementParsed]

        # iterate pages
        while True:
            resp_mov_page = s.post(
                req_filtered_movs_url,
                data=req_movs_filtered_params,
                headers=req_headers,
                proxies=self.req_proxies
            )

            movements_parsed_from_page, temp_balance, prev_date_obj = parse_helpers.get_movements_parsed(
                fin_ent_account_id,
                resp_mov_page.text,
                temp_balance,
                prev_date_obj,
                self.logger
            )

            movements_parsed += movements_parsed_from_page

            if len(movements_parsed_from_page) < MOVEMENTS_ON_PAGE_MAX:
                break

            # change req params after first req to swith to next page
            req_movs_filtered_params['validation'] = '0'  # no new filter
            req_movs_filtered_params['changepage'] = '1'
            req_movs_filtered_params['_NumeroPage'] = str(int(req_movs_filtered_params['_NumeroPage']) + 1)
            self.logger.info(
                "process_account: {}: open previous page {} with movements (last mov date on page {})".format(
                    fin_ent_account_id,
                    req_movs_filtered_params['_NumeroPage'],
                    prev_date_obj.strftime(project_settings.SCRAPER_DATE_FMT)
                )
            )

            req_headers['Referer'] = resp_mov_page.url
            self._delay()

        # crazy thing:
        # if returned movements from only one date,
        # then movs will be ASC ordered (most recent is last)
        # OR if returned movements from different dates,
        # then movs will be DESC ordered (most recent is first)
        # -> order as DESC if movements from one date
        if len(set(m['operation_date'] for m in movements_parsed)) < 2:
            self.logger.info("There are movements from only from 0/1 day. Should be reordered to be DESC")
            movements_parsed = parse_helpers.reorder_movements_and_recalculate_temp_balances(
                movements_parsed
            )

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str
        )

        self.basic_log_process_account(account_no, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )
        return True

    def main(self) -> MainResult:

        s, resp_logged_in, is_logged, is_credentials_error = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            if resp_logged_in:
                return self.basic_result_not_logged_in_due_unknown_reason(
                    resp_logged_in.url,
                    resp_logged_in.text
                )
            else:
                return self.basic_result_not_logged_in_due_unknown_reason('', '<NO CONTENT>')

        is_success = self.process_contract(s)
        self.basic_log_time_spent('GET MOVEMENTS')
        if not is_success:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        return self.basic_result_success()
