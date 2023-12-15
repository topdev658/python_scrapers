import os
import random
import subprocess
import threading
import time
import uuid
from typing import Dict, List, Optional, Tuple

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import MovementParsed, ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from .custom_types import AccProduct, MovsPaginationParams

__version__ = '2.2.0'

__changelog__ = """
2.2.0
added WRONG_CREDETIALS_MARKERS
2.1.0
call basic_upload_movements_scraped with date_from_str
2.0.0
use basic_get_movements_parsed_w_extra_details
1.6.0
MOV_SCRAPING_OFFSET = 7 (need for 2021 to prevent balance integrity errs for 12/2020)
1.5.0
upd logout url
1.4.0
login: report err reason when detected
parse_helpers: handle 'no movs'
1.3.0
use basic_new_session
1.2.1
upd type hints
1.2.0
parse_helpers: handle 0 balance (no NetBalance key in this case)
1.1.0
parse_helpers: use translit to convert greek chars into latin 
  to be able to save
1.0.0
init
"""

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'alphabank_encrypter.js'
))

# for rand
SEQ = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

MOV_DETAILS_MAX_WORKERS = 4
MOV_SCRAPING_OFFSET = 7

WRONG_CREDETIALS_MARKERS = [
    'Wrong entry credentials',
    'Τhe sign-on codes you entered are not correct!'
]


class AlphaBankScraper(BasicScraper):
    """
    The scraper uses transliteration to be able to save greek chars
    in the current DB
    """

    scraper_name = 'AlphaBankScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        self.request_root_id = self.__gen_rand_req_id()
        self.lock = threading.Lock()

    def __gen_rand_req_id(self) -> str:
        # Similar to Microsoft.ApplicationInsights.UtilHelpers.newId()
        # KRDiW, wQVdk, 3ZBCL, Vw/yJ
        acc = ''
        while len(acc) < 5:
            char = random.choice(SEQ)
            if char not in acc:
                acc += char
        return acc

    def _req_params(self, params_dict: dict = None) -> dict:
        """Req params with mandatory details"""
        params_dict = params_dict or {}
        mixin = {
            # 2019-07-07T20:00:22.442Z
            "ActivityDateTime": date_funcs.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            # 99f9f949-b86c-471b-8fb4-ccca947bb9e8
            "UniqueIdentifier": str(uuid.uuid4())
        }
        params_dict.update(mixin)
        return params_dict

    def _req_date(self, date_str: str) -> str:
        """01/08/2019 -> 1/8/2019"""
        return '/'.join(part.lstrip('0') for part in date_str.split('/'))

    def _req_headers(self, resp_prev: Response, is_need_req_id=True) -> Dict[str, str]:
        """Req headers with mandatory details"""
        req_headers = self.basic_req_headers_updated({
            'Accept': 'application/json, text/plain, */*',
            'application-id': 'web-banking',
            # '1Ot400wbIz-HhnF...dCYypakFusC5SQ_fPTAE8rzbBbUhP-FoLCPR6hsFr0EtpJLRk1' (108 chars)
            # found in logoutForm:__RequestVerificationToken;
            'x-xsrf-token': extract.form_param(resp_prev.text, '__RequestVerificationToken'),
            # 'Request-Id': None,
            # 'Request-Context': None,
            # 'x-ms-request-root-id': None,
            'Referer': resp_prev.url,
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive'
        })
        # Some request require additional headers
        if is_need_req_id:
            req_headers['Request-Id'] = '|{}.{}'.format(self.request_root_id,
                                                        self.__gen_rand_req_id())
            req_headers['x-ms-request-root-id'] = self.request_root_id
            req_headers['Request-Context'] = 'appId=cid-v1:{}'.format(
                parse_helpers.get_application_id(resp_prev.text)
            )

        return req_headers

    def _get_encrypted(self, req_params: dict) -> str:
        cmd = '{} "{}" "{}" "{}" "{}" "{}"'.format(
            CALL_JS_ENCRYPT_LIB,
            self.userpass,
            req_params['N'],
            req_params['E'],
            req_params['ActivityDateTime'],
            req_params['UniqueIdentifier']
        )
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def _parse_json(self, resp: Response, err_place='') -> Tuple[bool, dict]:
        """Parses response JSON and logs error if not a valid json"""
        is_success = True
        resp_json = {}  # type: dict
        try:
            resp_json = resp.json()
        except Exception as e:
            is_success = False
            self.logger.error("Can't parse {}. Not a JSON. RESPONSE:\n{}".format(
                err_place,
                resp.text
            ))
        return is_success, resp_json

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:

        s = self.basic_new_session()

        # get init cookies
        resp_init = s.get(
            'https://www.alpha.gr/en/business/myalpha',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        resp_login_form_iframe = Response()
        resp_logged_in = Response()  # suppress linter warnings
        for i in range(2):
            resp_login_form_iframe = s.get(
                'https://secure.alpha.gr/Login/Login/IFramePartial/en/2',
                headers=self.basic_req_headers_updated({'Referer': resp_init.url}),
                proxies=self.req_proxies
            )

            action_link, req_login_params = extract.build_req_params_from_form_html_patched(
                resp_login_form_iframe.text,
                form_id='loginForm',
                is_ordered=True
            )

            req_login_params['Username'] = self.username
            req_login_params['Password'] = self._get_encrypted(req_login_params)
            req_login_params['RedirectTo'] = ''  # missing param

            resp_logged_in = s.post(
                'https://secure.alpha.gr/Login/Login/DoLogin',
                data=req_login_params,
                headers=self.basic_req_headers_updated({'Referer': resp_login_form_iframe.url}),
                proxies=self.req_proxies
            )

            if 'Your subscription is already in use' not in resp_logged_in.text:
                # No active sessions detected. Break the loop and continue auth steps
                break

            # Active session ('subscription in use') detected.
            # In this case the bank interrupts all sessions and invites
            # to try to log in again. Let's try
            self.logger.warning(
                "Active session detected. "
                "The authorization process has been interrupted by the bank. "
                "Let's try one more time."
            )
            time.sleep(1 + random.random())
        else:
            return s, resp_login_form_iframe, False, False, "no multiple sessions allowed"

        is_logged = bool(s.cookies.get('Ebanking'))
        if not is_logged:
            #  id="genericValidationError" or "wrongCredentialsValidationError", use it if getting Greece msgs
            is_credentials_error = any(m in resp_logged_in.text for m in WRONG_CREDETIALS_MARKERS)
            return s, resp_logged_in, is_logged, is_credentials_error, ''

        # different for logged/not logged
        # <meta name="PiraeusClientId" content="1b0b097d-4301-43f6-a55f-3d71cdca4814" />
        resp_logged_in_home = s.get(
            'https://secure.alpha.gr/ebanking/',
            headers=self.basic_req_headers_updated({
                'Referer': resp_init.url,
                'Upgrade-Insecure-Requests': '1',
            }),
            proxies=self.req_proxies
        )

        return s, resp_logged_in_home, is_logged, False, ''

    def process_access(self, s: MySession,
                       resp_logged_in: Response) -> bool:
        # Necessary for further processing
        req_user_session_info = s.post(
            'https://secure.alpha.gr/eBanking/api/Security.svc/getUserSessionInfo',
            json=self._req_params({"UpdateContacts": False}),
            headers=self._req_headers(resp_logged_in, is_need_req_id=False),
            proxies=self.req_proxies
        )

        # Now only 10 accounts can be extracted and processed.
        # Need to impl pagination for accounts (products)
        # if accesses with more than 10 account occurred

        req_acc_products_params = self._req_params({
            "ReturnMode": 0,
            "RequestCriteria": {
                "MaxRecords": 10,
                "MaxRecordsSpecified": True,
                "ProductTypes": ["51"],
                "SearchStringInfo": {
                    "SearchTerm": "", "SearchField": 2,
                    "SearchFieldSpecified": True
                },
                "FromRowNumber": 0
            }
        })

        resp_acc_products = s.post(
            'https://secure.alpha.gr/eBanking/api/products.svc/getProfileProductsNew',
            json=req_acc_products_params,
            headers=self._req_headers(resp_logged_in),
            proxies=self.req_proxies
        )

        ok, resp_acc_products_json = self._parse_json(resp_acc_products, 'resp_acc_products')
        if not ok:
            # already reported
            return False

        acc_products = parse_helpers.get_acc_products(resp_acc_products_json)
        self.logger.info("Got {} accounts: {}".format(
            len(acc_products),
            [a.account_no for a in acc_products]
        ))

        for acc_product in acc_products:
            self.process_account(s, resp_logged_in, acc_product)

        return True

    def process_account(self,
                        s: MySession,
                        resp_logged_in: Response,
                        acc_product: AccProduct) -> bool:

        # Get account_scraped

        req_account_params = self._req_params({
            "ProductCode": acc_product.account_no,
            "ProductTypeID": acc_product.type
        })

        resp_account = s.post(
            'https://secure.alpha.gr/eBanking/api/products.svc/getAccountBalance',
            headers=self._req_headers(resp_logged_in),
            json=req_account_params,
            proxies=self.req_proxies
        )

        ok, resp_account_json = self._parse_json(resp_account, 'resp_account')
        if not ok:
            # already reported
            return False

        organization_title = parse_helpers.get_organization_title(resp_account_json)
        if not organization_title:
            self.logger.error("Can't parse organization_title. Abort. RESPONSE:\n{}".format(
                resp_account.text
            ))
            return False

        account_parsed = parse_helpers.get_account_parsed(resp_account_json)
        account_scraped = self.basic_account_scraped_from_account_parsed(
            organization_title,
            account_parsed,
            country_code=account_parsed['country_code'],
        )

        self.basic_log_time_spent('GET BALANCE')
        self.logger.info("Got account {}".format(account_scraped))
        self.basic_upload_accounts_scraped([account_scraped])

        # Get movements
        time.sleep(0.2 + 0.2 * random.random())

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        date_from_str = self.basic_get_date_from(fin_ent_account_id, rescraping_offset=MOV_SCRAPING_OFFSET)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        movements_parsed = []  # type: List[MovementParsed]
        temp_balance = None  # type: Optional[float]
        pagination_params = MovsPaginationParams(
            has_more_pages=True,
            LastPageIndex_param='',
            LastExtraitKey_param=''
        )

        # limit to avoid handing loop
        for page_ix in range(1, 100):
            if not pagination_params.has_more_pages:
                break

            req_movs_params = self._req_params({
                "ProductCode": acc_product.account_no,
                "ProductTypeID": acc_product.type,
                "GetSummary": {
                    "FromDate": self._req_date(date_from_str),  # '1/6/2019'
                    "ToDate": self._req_date(self.date_to_str),  # '14/7/2019'
                },
                # "H0002000000000000030"
                "LastPageIndex": pagination_params.LastPageIndex_param or None,
                # "000000000000201907100092786"
                "LastExtraitKey": pagination_params.LastExtraitKey_param or None,
            })

            resp_movs = s.post(
                'https://secure.alpha.gr/eBanking/api/products.svc/getAggregatedAccountStatements',
                json=req_movs_params,
                headers=self._req_headers(resp_logged_in),
                proxies=self.req_proxies
            )

            ok, resp_movs_json = self._parse_json(resp_movs, 'resp_movs')
            if not ok:
                # already reported
                return False

            movements_parsed_i, pagination_params, temp_balance = parse_helpers.get_movements_parsed(
                resp_movs_json,
                temp_balance
            )

            movements_parsed.extend(movements_parsed_i)

        movements_parsed_extra_details = movements_parsed
        if self.basic_should_scrape_extended_descriptions():
            meta = {
                'resp_logged_in': resp_logged_in,
                'acc_product': acc_product
            }
            movements_parsed_extra_details = self.basic_get_movements_parsed_w_extra_details(
                s,
                movements_parsed,
                account_scraped,
                date_from_str,
                n_mov_details_workers=MOV_DETAILS_MAX_WORKERS,
                meta=meta
            )

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_extra_details,
            date_from_str
        )
        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        # fill previously absent extended descriptions of recent movements
        if self.basic_should_scrape_extended_descriptions():
            self.basic_update_movements_extended_descriptions_if_necessary(
                account_scraped,
                movements_scraped
            )

        return True

    def process_movement(self,
                         s: MySession,
                         movement_parsed: MovementParsed,
                         fin_ent_account_id: str,
                         meta: Optional[dict]) -> MovementParsed:
        """:returns movement_parsed with extra details (extended description for now)"""
        assert meta
        resp_logged_in = meta['resp_logged_in']  # type: Response
        acc_product = meta['acc_product']  # type: AccProduct
        fin_ent_account_id = acc_product.account_no
        mov_str = self.basic_mov_parsed_str(movement_parsed)

        self.logger.info('{}: process movement: {}'.format(fin_ent_account_id, mov_str))

        req_mov_params = self._req_params({
            "ProductCode": acc_product.account_no,
            "ProductTypeID": acc_product.type,
            "GetDetails": {
                "UN": movement_parsed['un']  # "20190712949044Ξ112"
            },
        })
        resp_mov = s.post(
            'https://secure.alpha.gr/eBanking/api/products.svc/getAggregatedAccountStatements',
            json=req_mov_params,
            headers=self._req_headers(resp_logged_in),
            proxies=self.req_proxies
        )

        ok, resp_mov_json = self._parse_json(resp_mov, 'resp_mov for {}'.format(movement_parsed))
        if not ok:
            # already reported
            return movement_parsed

        description_extended = parse_helpers.get_description_extended(
            resp_mov_json,
            movement_parsed
        )

        movement_parsed_extra_details = movement_parsed.copy()
        movement_parsed_extra_details['description_extended'] = description_extended

        return movement_parsed_extra_details

    def logout(self,
               s: Optional[MySession],
               resp_logged_in: Optional[Response]) -> bool:

        if not s or not resp_logged_in:
            return True

        resp_xhr_logged_out = s.post(
            'https://secure.alpha.gr/eBanking/api/Security.svc/signOff',
            json=self._req_params(),
            headers=self._req_headers(resp_logged_in),
            proxies=self.req_proxies
        )

        is_xhr_logged_out = resp_xhr_logged_out.text == '{"ResultCode":0}'

        # 2nd step
        req_html_params = {
            '__RequestVerificationToken': extract.form_param(resp_logged_in.text,
                                                             '__RequestVerificationToken'),
            'Referer': '2',
            'logoutWay': 'normal',
            'loginType': '2',
        }
        resp_html_logged_out = s.post(
            'https://secure.alpha.gr/eBanking/logout',
            data=req_html_params,
            headers=self.basic_req_headers_updated({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer': resp_logged_in.url
            }),
            proxies=self.req_proxies,
        )

        is_logged_out = resp_html_logged_out.url == 'https://www.alpha.gr/en/business/myAlpha/myalpha-logout'
        if is_logged_out:
            self.logger.info("Logged out successfully")
        else:
            self.logger.warning("Can't log out. May cause further log in errors.")
        return is_logged_out

    def main(self) -> MainResult:
        s = None  # type: Optional[MySession]
        resp_logged_in = None  # type: Optional[Response]
        is_logged_in = False
        try:
            s, resp_logged_in, is_logged_in, is_credentials_error, reason = self.login()

            if is_credentials_error:
                return self.basic_result_credentials_error()

            if not is_logged_in:
                return self.basic_result_not_logged_in_due_reason(
                    resp_logged_in.url,
                    resp_logged_in.text,
                    reason
                )
            self.process_access(s, resp_logged_in)
        finally:
            if bool(s) and is_logged_in:
                self.logout(s, resp_logged_in)

        self.basic_log_time_spent("GET MOVEMENTS")
        return self.basic_result_success()
