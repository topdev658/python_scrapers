import random
import time
from typing import List, Tuple
from urllib.parse import urljoin

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import requests_helpers
from custom_libs import splash_helpers
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import MovementParsed, ScraperParamsCommon, AccountScraped, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.eurobic_scraper import parse_helpers

__version__ = '2.2.0'

__changelog__ = """
2.2.0
upd auth detector
2.1.0
MOVS_RESCRAPING_OFFSET
time delays during pagination
2.0.0
new web
use Splash to pass Incapsula
1.4.0
call basic_upload_movements_scraped with date_from_str
1.3.1
longer timeouts
1.3.0
use basic_new_session
upd type hints
fmt
1.2.0
Empresas (B.I./Pass.) access type support
1.1.1
parse_helpers: get_description_extended: strip() msg
1.1.0
Skip initial urls protected by Incapsula
1.0.0
init
"""

CREDENTIALS_ERROR_MARKER = 'Utilizador ou Password Inválida'

UA = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'
MOVS_RESCRAPING_OFFSET = 3  # avoid too long pagination, can be unstable


class EuroBicScraper(BasicScraper):
    """Only one account per access supported for now
    (no examples to be able to implement many accounts per access)
    """
    scraper_name = 'EuroBicScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.req_headers = self.basic_req_headers_updated({
            'User-Agent': UA
        })
        self.req_proxies = [self.req_proxies[0]]  # 1 will be used to pass Incapsula

    def _ts(self) -> int:
        return int(time.time() * 1000)

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:

        s = self.basic_new_session()

        # Protected by INCAPSULA
        # SPLASH helps with Incapsula:
        # $ sudo docker pull scrapinghub/splash
        # $ sudo docker run -it -p 8050:8050 --rm scrapinghub/splash

        # Can skip this
        # resp_init = s.get(
        #     'https://www.eurobic.pt/empresas',
        #     headers=self.req_headers,
        #     proxies=self.req_proxies
        # )

        # OPEN LOGIN PAGE
        # (will be redirected to https://login.eurobic.pt/Account/Login?ReturnUrl=.... and then can login)
        # See dev_new/resp_home_har.json
        splash_url = urljoin(project_settings.SPLASH_URL, 'render.har')
        resp_home = s.post(
            splash_url,
            json={
                'url': 'https://apps.eurobic.pt/Login_eUI/Home.aspx',
                'wait': 2,
                'headers': {'User-Agent': UA},
                'proxy': self.req_proxies[0]['http'],  # 'http://192.168.195.114:8115',
                'response_body': 1
            }
        )

        resp_home_har_json = resp_home.json()
        cookies = splash_helpers.get_cookies_from_har(resp_home_har_json)
        # session with only 'eurobic' cookies, omit unspecific ones
        # (used by Incapsula for web browser verification)
        s = requests_helpers.update_mass_cookies_typed(s, cookies)

        ok, resp_home_text = splash_helpers.get_response_text_from_har(
            resp_home_har_json,
            resp_url_re='^https://login.eurobic.pt/Account/Login[?]ReturnUrl'
        )
        if not ok:
            return s, Response(), False, False, "Can't extract resp_home_text"

        if '/Account/Login' not in resp_home_text:
            return s, Response(), False, False, 'Unexpected resp_home_text'

        _link, req_login_step3_params = extract.build_req_params_from_form_html_patched(
            html_str=resp_home_text,
            form_re='(?si)<form action="/Account/Login".*?</form>'
        )

        req_login_step3_params['Username'] = self.username
        req_login_step3_params['Password'] = self.userpass

        time.sleep(1 + random.random())
        resp_login_step3 = s.post(
            # _link
            'https://login.eurobic.pt/Account/Login',
            data=req_login_step3_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_credentials_error = CREDENTIALS_ERROR_MARKER in resp_login_step3.text
        if is_credentials_error:
            return s, resp_login_step3, False, is_credentials_error, ''

        if 'Click to continue' not in resp_login_step3.text:
            return s, resp_login_step3, False, False, 'Unexpected resp_login_step3'

        # from 30_resp_login_step3.html, 'CONTINUE' button
        req_login_step4_link, req_login_step4_params = extract.build_req_params_from_form_html_patched(
            html_str=resp_login_step3.text,
            form_re='(?si)<form.*?</form>'
        )

        resp_login_step4 = s.post(
            # https://apps.eurobic.pt/Login_eUI/NoPermission.aspx
            urljoin(resp_login_step3.url, req_login_step4_link),
            # like {code: ..., scope: ..., state...}
            data=req_login_step4_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # Was 'Perfil Empresarial',
        # but sometimes there is another welcome screen
        is_logged = '>Logout</a>' in resp_login_step4.text

        # acc home
        resp_acc_home = s.get(
            'https://apps.eurobic.pt/Login_eUI/Home.aspx',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        _resp_status = s.get(
            'https://apps.eurobic.pt/Login_eUI/_status.aspx',
            headers=self.basic_req_headers_updated({
                'X-Requested-With': 'XMLHttpRequest'
            }),
            proxies=self.req_proxies
        )

        return s, resp_acc_home, is_logged, is_credentials_error, ''

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        # Only one account supported for now because
        # there are no examples how switch between different accounts
        req_account_url = 'https://apps.eurobic.pt/AccountsCurrent_eUI/AccountsDO.aspx?BackURL=/Common_eUI/Menu.aspx?SubMenuId=9'  # noqa
        resp_account = s.get(
            req_account_url,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=60,
        )

        account_parsed = parse_helpers.get_account_parsed(resp_account.text)
        organization_title = parse_helpers.get_organization_title(resp_account.text)

        account_scraped = self.basic_account_scraped_from_account_parsed(
            organization_title,
            account_parsed,
            country_code='PRT'
        )

        self.basic_upload_accounts_scraped([account_scraped])
        self.basic_log_time_spent('GET BALANCES')

        s.cookies.set(
            name='RT',
            value='s={}&r=https://apps.eurobic.pt/Common_eUI/Menu.aspx?SubMenuId=9"'.format(self._ts())
        )
        s.cookies.set(
            name='DEVICE_TYPE',
            value='desktop big'
        )

        self.process_account(s, resp_account, account_scraped)
        return True

    def process_account(self, s: MySession, resp_account: Response, account_scraped: AccountScraped) -> bool:
        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        date_from, date_from_str = self.basic_get_date_from_dt(
            fin_ent_account_id,
            rescraping_offset=MOVS_RESCRAPING_OFFSET
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        req_movs_url_pattern = 'https://apps.eurobic.pt/AccountsCurrent_eUI/AccountsDO.aspx?_ts={}'
        viewstategenerator_param = parse_helpers.get_viewstategenerator_param(resp_account.text)
        osvstate_param = parse_helpers.get_osvstate_param(resp_account.text)

        # Mandatory
        req_movs_recent_params = parse_helpers.req_movs_recent_params(
            osvstate_param=osvstate_param,
            viewstategenerator_param=viewstategenerator_param
        )
        resp_movs_recent = s.post(
            req_movs_url_pattern.format(self._ts()),
            data=req_movs_recent_params,
            headers=self.basic_req_headers_updated({
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': resp_account.url
            }),
            proxies=self.req_proxies
        )

        resp_prev = resp_movs_recent
        movements_parsed_desc = []  # type: List[MovementParsed]
        for page_ix in range(1, 100):  # limit to avoid inf loop
            self.logger.info('{}: page #{}'.format(
                fin_ent_account_id,
                page_ix
            ))
            osvstate_param = parse_helpers.get_osvstate_param(resp_prev.text)

            req_movs_i_params = parse_helpers.req_movs_i_params(
                osvstate_param=osvstate_param,
                viewstategenerator_param=viewstategenerator_param,
                date_from_str=date_from_str,
                date_to_str=self.date_to_str,
                page_ix=page_ix
            )
            resp_movs_i = s.post(
                req_movs_url_pattern.format(self._ts()),
                data=req_movs_i_params,
                headers=self.basic_req_headers_updated({
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': resp_prev.url
                }),
                proxies=self.req_proxies
            )

            if 'Não tem acesso à conta' in resp_movs_i.text:
                self.logger.info('Session has been interrupted (or bad request). Try later')
                return False

            movements_parsed_i = parse_helpers.get_movements_parsed(resp_movs_i.text)
            if movements_parsed_i:
                self.logger.info('{}: movements from page #{}: min date {}'.format(
                    fin_ent_account_id,
                    page_ix,
                    movements_parsed_i[-1]['operation_date']
                ))

            movements_parsed_desc.extend(movements_parsed_i)

            if (len(movements_parsed_i) < 10
                    or 'icon-menu_arrow_right' not in resp_movs_i.text):
                self.logger.info('No more pages with movements. Break pagination')
                break

            # Old web:
            #  website returns movements out of target dates if 'next' was clicked
            last_mov_date = date_funcs.get_date_from_str(
                movements_parsed_i[-1]['operation_date'],
                date_format='%d-%m-%Y'
            )
            if last_mov_date < date_from:
                self.logger.info('Got last_mov_date < date_from. Break pagination')
                break

            resp_prev = resp_movs_i
            time.sleep(0.1 + 0.1 * random.random())

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
