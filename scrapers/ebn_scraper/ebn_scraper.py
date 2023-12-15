import hashlib
from collections import OrderedDict
from typing import Tuple

from custom_libs import date_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, AccountScraped, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_COMMON
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers

__version__ = '1.3.0'
__changelog__ = """
1.3.0
parse_helpers: get_movements_parsed: handle 'no movements' + check for unexpected response
1.2.0
login: upd 2fa detector
1.1.0
call basic_upload_movements_scraped with date_from_str
1.0.0
stable
0.1.0
init
"""

UA = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'

DOUBLE_AUTH_MARKERS = [
    'Introduzca el código recibido en su móvil para continuar.',
]

class EbnScraper(BasicScraper):
    scraper_name = 'EbnScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.req_headers = self.basic_req_headers_updated({
            'User-Agent': UA
        })

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()
        if self.access_type != 'EMPRESA':
            reason = "Unsupported access type '{}'".format(self.access_type)
            return s, Response(), False, False, reason

        _resp_init = s.get(
            'https://acceso.ebnbanco.com/bancaelectronica/login',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # From main.js
        # ...
        # pin: i.a.getHashedPin(n.pin)
        # ...
        # t.getHashedPin = function (t) {
        #   return o.SHA512(t.replace(/ /g, '')).toString().toUpperCase()
        # }
        # ...
        encrypted = hashlib.sha512(self.userpass.replace(' ', '').encode('utf8')).hexdigest().upper()

        req_params = OrderedDict([
            ('docCompany', self.username),
            ('docIndividual', self.username_second),
            ('pin', encrypted),
            ('product', 'B'),
            ('type', 'company')  # EMPRESA access type
        ])

        resp_codes_bad_for_proxies_cached = s.resp_codes_bad_for_proxies.copy()
        # Allow 500 - wrong credentials
        s.resp_codes_bad_for_proxies = [502, 503, 504, 403, None]
        resp_logged_in = s.post(
            'https://servicios.ebnbanco.com/egida-ws/login',
            json=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        s.resp_codes_bad_for_proxies = resp_codes_bad_for_proxies_cached

        is_logged = 'userUuid' in resp_logged_in.text
        is_credentials_error = resp_logged_in.status_code == 500
        reason = ''

        if any(m in resp_logged_in.text for m in DOUBLE_AUTH_MARKERS):
            is_logged = False
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        if is_logged:
            auth_header = resp_logged_in.headers.get('Authorization')
            if not auth_header:
                is_logged = False
                reason = "Can't get auth header"
                return s, resp_logged_in, is_logged, is_credentials_error, reason

            # From main.js:
            # (o['content-1ength'] = '42' + ('0' + l.getDate()).slice( - 2))
            content_auth_header = '42' + date_funcs.today().strftime('%d')
            self.req_headers = self.basic_req_headers_updated({
                'Authorization': auth_header,
                'Accept': 'application/json',
                'Referer': 'https://acceso.ebnbanco.com',
                'content-1ength': content_auth_header  # name!
            })

        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        ok, resp_logged_in_json = self.basic_get_resp_json(
            resp_logged_in,
            err_msg="Can't get resp_logged_in_json. Abort"
        )
        if not ok:
            return False

        resp_accounts = s.get(
            'https://servicios.ebnbanco.com/atenea-ws/position/v1',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        ok, resp_accounts_json = self.basic_get_resp_json(
            resp_accounts,
            err_msg="Can't get resp_accounts_json. Abort"
        )
        if not ok:
            return False

        accounts_parsed = parse_helpers.get_accounts_parsed(resp_accounts_json)

        org_title = resp_logged_in_json['companyName']

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(org_title, acc_parsed)
            for acc_parsed in accounts_parsed
        ]

        self.logger.info('Got {} accounts: {}'.format(
            len(accounts_scraped),
            accounts_scraped
        ))

        self.basic_log_time_spent('GET ACCOUNTS')

        self.basic_upload_accounts_scraped(accounts_scraped)

        for account_scraped in accounts_scraped:
            self.process_account(s, account_scraped)

        return True

    def process_account(self, s: MySession, account_scraped: AccountScraped) -> bool:
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from, date_from_str = self.basic_get_date_from_dt(fin_ent_account_id)
        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        req_movs_params = OrderedDict([
            ('accountUuid', fin_ent_account_id),
            ('from', date_from.strftime('%Y-%m-%d')),
            ('to', self.date_to.strftime('%Y-%m-%d')),
        ])

        resp_movs = s.post(
            'https://servicios.ebnbanco.com/atenea-ws/account/movements/v1',
            json=req_movs_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        ok, resp_movs_json = self.basic_get_resp_json(
            resp_movs,
            err_msg="{}: can't get resp_movs_json. Abort".format(fin_ent_account_id)
        )
        if not ok:
            return False

        ok, movements_parsed_desc = parse_helpers.get_movements_parsed(resp_movs_json)
        if not ok:
            self.basic_log_wrong_layout(resp_movs, "{}: can't get valid resp_movs".format(
                fin_ent_account_id
            ))
            return False

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

        self.process_access(s, resp_logged_in)

        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
