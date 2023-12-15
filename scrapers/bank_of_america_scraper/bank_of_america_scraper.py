import datetime
import os
import subprocess
import traceback
import time
import urllib.parse
from collections import OrderedDict
from typing import List, Tuple

from custom_libs import extract
from custom_libs import myrequests
from project import settings as project_settings
from project.custom_types import (
    ScraperParamsCommon,
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from .login_helpers import (
    CONFIRMED_ENVIRONMENT_PATTERN, DOM_LOCAL_TAG, EnvPatternParams,
    PM_FP_PARAM, F_VAR_PARAM_PATERN, CC_COOKIE
)

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'bank_of_america_encrypter.js'
))

__version__ = '1.0.0a'
__changelog__ = """
1.0.0a
login: WIP
"""

ERR_PAGES = [
    'Forgot Online ID & Passcode'
]


class BankOfAmericaScraper(BasicScraper):
    scraper_name = 'BankOfAmericaScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        third_log_pass = self.db_connector.get_third_login_password()
        self.secret_answer = third_log_pass.AccessThirdLoginValue
        self.req_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0'
        }

    def _get_encrypted(self, conf_env_json: str):
        cmd = """{} '{}'""".format(CALL_JS_ENCRYPT_LIB, conf_env_json)
        result_bytes = subprocess.check_output(cmd, shell=True)
        text_encrypted = result_bytes.decode().strip()
        return text_encrypted

    def _fetch_login_js_scripts(self, s: myrequests.Session, resp_init_text: str) -> List[str]:
        """Fetches necessary js scripts from login page
        to parse changeable variables from them.
        Scripts names don't matter - we'll try to parse each
        variable from each script (only one will be appropriate)
        """
        script_urls = parse_helpers.get_urls_of_login_js_scripts(resp_init_text)
        scripts_texts = []  # type: List[str]
        for script_url in script_urls:
            resp_script = s.get(
                script_url,
                headers=self.req_headers,
                proxies=self.req_proxies
            )
            scripts_texts.append(resp_script.text)
        return scripts_texts

    def login(self):
        s = myrequests.session()
        req_init_url = 'https://www.bankofamerica.com/smallbusiness/'

        # set special auth cookies
        s.cookies.set(
            name='olb_signin_prefill_multi_secure',
            value='juan*****:D9AD3EFA2722DC394260CB9A05C618B94CD98242DC4F1C0E:02/21/2019'
                  '||elen*****:03AA74BB14B5579DEFDE0739FA1A6C553E95E584CFB70B03:02/21/2019',
            domain='.bankofamerica.com',
            path='/'
        )
        s.cookies.set(
            name='_cc',
            value=CC_COOKIE,
            domain='www.bankofamerica.com',
            path='/'
        )

        resp_init = s.get(
            req_init_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        try:
            # Calculate _ia param
            # get values of necessary vals from js scripts
            js_texts = self._fetch_login_js_scripts(s, resp_init.text)
            js_vals = parse_helpers.get_vals_from_js_texts(js_texts)
            now_ts = time.time() + 180  # TZ
            dt = datetime.datetime.fromtimestamp(now_ts)

            env_pattern_params = EnvPatternParams(
                sid=js_vals['sid'],
                tid=js_vals['tid'],
                t=js_vals['t'],
                cf_flags=js_vals['cf_flags'],
                cookie_cc=CC_COOKIE,
                time_unix_epoch_ms=int(now_ts * 1000),
                time_local=dt.strftime('%m/%d/%Y, %I:%M:%S %p'),  # "2/25/2019, 12:27:02 AM"
                # "Mon Feb 25 2019 00:27:02 GMT+0300 (MSK)"
                time_string=dt.strftime('%a %b %d %Y %H:%M:%S GMT+0300 (MSK)'),
                # time_tz_offset_minutes=-180,  # -180 for "time-tz-offset-minutes"

                # no possibility to get from local storage
                # probably, it causes verification challenge then
                dom_session_tag=js_vals['t'][:24],
                dom_local_tag=DOM_LOCAL_TAG,
            )

            conf_env_json = CONFIRMED_ENVIRONMENT_PATTERN % env_pattern_params._asdict()
            ia_param = self._get_encrypted(conf_env_json)

            req_params = OrderedDict([
                ('pm_fp', PM_FP_PARAM),
                ('f_variable', F_VAR_PARAM_PATERN % env_pattern_params._asdict()),
                ('locale', 'en-US'),
                ('anotherOnlineIDFlag', 'N'),
                ('dltoken', ''),
                ('Access_ID_1', 'juan*****'),  # <<<<!!! part of username
                ('reason', ''),
                ('passcode', 'Juan2017'),
                ('onlineId', ''),
                ('multiID', 'D9AD3EFA2722DC394260CB9A05C618B94CD98242DC4F1C0E'),  # <<<<!!! from cookie
                ('saveMyID', 'N'),
                ('origin', 'sparta_homepage'),
                ('_ia', ia_param)])

            req_login_url = 'https://secure.bankofamerica.com/login/sign-in/entry/signOnV2.go'
            resp_login_step1 = s.post(
                req_login_url,
                data=req_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            is_logged = True
            if 'Verify Your Identity' in resp_login_step1.text:
                s, resp_logged_in = self._enter_secret_answer(s, resp_login_step1)

        except Exception as e:
            traceback.print_exc()
            pass

        pass

    def _enter_secret_answer(self, s: myrequests.Session,
                             resp_secret: myrequests.Response) -> Tuple[myrequests.Session, myrequests.Response]:
        question = 'As a child, what did you want to be when you grew up?'  # todo get from DB
        answer = '...'  # todo get from DB

        assert question in resp_secret.text

        action_url, req_params = extract.build_req_params_from_form_html_patched(
            resp_secret.text,
            form_name="VerifyCompForm",
            is_ordered=True
        )
        req_url = urllib.parse.urljoin(resp_secret.url, action_url)
        req_params['rembComp'] = 'Y'  # remember the computer
        req_params['challengeQuestionAnswer'] = answer

        resp_logged_in = s.post(
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        return s, resp_logged_in

    def login_alt_page(self):
        # UA = Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36

        s = myrequests.session()

        # cookies with confirmed environment
        cookie_name = 'olb_signin_prefill_multi_secure'
        cookie_val = ('juan*****:D9AD3EFA2722DC394260CB9A05C618B94CD98242DC4F1C0E:02/21/2019'
                      '||elen*****:03AA74BB14B5579DEFDE0739FA1A6C553E95E584CFB70B03:02/21/2019')
        s.cookies.set(cookie_name, cookie_val, domain='.bankofamerica.com', path='/')
        # get initial cookies
        req_init_url = 'https://secure.bankofamerica.com/login/sign-in/signOnScreen.go'
        resp_init = s.get(
            req_init_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        assert ('juan*****' in resp_init.text)

        encrypt_script_url = ("https://secure.bankofamerica.com/pa/components/bundles/text-decompressed/"
                              "xengine/VIPAA/6.0/script/cm-jawr.js")

        # need to load each time
        cc_go_script_url = 'https://secure.bankofamerica.com/login/sign-in/entry/cc.go'
        resp_cc_go_script = s.get(
            cc_go_script_url,
            hraders=self.req_headers,
            proxies=self.req_proxies
        )

        # https://www.bankofamerica.com/?TYPE=33554433
        # &REALMOID=06-000aea23-f082-1f06-b383-082c0a2840b5&GUID=&SMAUTHREASON=0
        # &METHOD=GET&SMAGENTNAME=-SM-aqqfzgjeqy8S5m8u%2b8h6gZjIC5XifZeAeb5F64xMRkTo1mmai3SO2HDPyq%2bg0LdA
        # &TARGET=-SM-https%3a%2f%2fsecure%2ebankofamerica%2ecom%2fsmallbusiness

        # https://secure.bankofamerica.com/myaccounts/signin/signIn.go?
        # returnSiteIndicator=GAIMW&langPref=en-us&request_locale=en-us&capturemode=N&newuser=false&bcIP=F

        # https://secure.bankofamerica.com/login/sign-in/entry/signOnV2.go
        # https://secure.bankofamerica.com/login/sign-in/signOnScreen.go
        # 'https://www.bankofamerica.com/smallbusiness/',

        # remeber user id
        # https://tilt.bankofamerica.com/0575/698603619/XBW09WEA78JG/jsEvent.json

        # should be resp_init.url
        csrf_token_param = extract.re_first_or_blank(r'name="csrfTokenHidden"\s+value="(.*?)"', resp_init.text)
        req_login_url = 'https://secure.bankofamerica.com/login/sign-in/internal/entry/signOnV2.go'
        req_login_params = OrderedDict([
            ('csrfTokenHidden', csrf_token_param),
            ('f_variable',
             'TF1;015;;;;;;;;;;;;;;;;;;;;;;Mozilla;Netscape;5.0%20%28X11%29;20100101;undefined;true;'
             'Linux%20x86_64;true;Linux%20x86_64;undefined;'
             'Mozilla/5.0%20%28X11%3B%20Linux%20x86_64%3B%20rv%3A56.0%29%20Gecko/20100101'
             '%20Firefox/56.0;en-US;undefined;secure.bankofamerica.com;'
             'undefined;undefined;undefined;undefined;true'
             ';false;1550746537749;3;6/7/2005%2C%209%3A33%3A44%20PM;'
             '1366;768;;;;;;;3;-180;-240;2/21/2019%2C%201%3A55'
             '%3A37%20PM;24;1366;742;0;0;;;;;;;;;;;;;;;;;;;15;'),
            ('lpOlbResetErrorCounter', '0'),
            ('lpPasscodeErrorCounter', '0'),
            ('contGsid', ''),
            ('eligibilityToken', ''),
            ('passcode', self.userpass),
            ('onlineId', ''),
            ('selectedOnlineId', '0'),  # <-- first confirmed and remembered username from cookies above
            ('mouseCapturedEvents', ''),
            ('pm_fp',
             'version%3D1%26pm%5Ffpua%3D'
             'mozilla%2F5%2E0%20%28x11%3B%20linux%20x86%5F64%3B%20rv%3A56%2E0%29%20gecko%2F20100101%20'
             'firefox%2F56%2E0%7C5%2E0%20%28X11%29%7CLinux%20x86%5F64%26pm%5Ffpsc%3D24%7C1366%7C768%7C742'
             '%26pm%5Ffpsw%3D%26pm%5Ffptz%3D3%26pm%5Ffpln%3Dlang%3Den%2DUS%7Csyslang%3D%7C'
             'userlang%3D%26pm%5Ffpjv%3D0'
             '%26pm%5Ffpco%3D1'),
            ('new-passcode', ''),
            ('_ib',
             '{"oidkeypress":false,"oidpaste":false,"pckeypress":true,"pcpaste":true,"userAgent":"Mozilla/5.0 '
             '(X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0","pwMan":false}'),
            ('anotherOnlineIDFlag', 'N'),
            ('_ia', ''),
            ('_u2support', '-1')
        ])

        resp_login = s.post(
            req_login_url,
            data=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_credentials_error = (
                'The Online ID or Passcode you entered does not match our record' in resp_login.text
                or 'msg=InvalidCredentials' in resp_login.url
        )
        pass
        return

    def main(self):
        self.login()
        return self.basic_result_success()
