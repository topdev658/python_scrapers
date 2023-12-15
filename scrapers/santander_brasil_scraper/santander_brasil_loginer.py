import json
import os
import subprocess
import time
from collections import OrderedDict
from typing import Dict, Tuple, Optional

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    ScraperParamsCommon,
)
from scrapers._basic_scraper.basic_scraper import BasicScraper

__version__ = '1.3.0'

__changelog__ = """
1.3.0
use basic_new_session
upd type hints
fmt
1.2.0
INCORRECT_PREV_CLOSING_MARKER
1.1.0
a handler for anti-fraud banner with action
1.0.0
init
"""

CALL_JS_ENCRYPT_LIB = 'node {}'.format(os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'santander_brasil_encrypter.js'
))

INCORRECT_PREV_CLOSING_MARKER = (
    'sua conexão foi encerrada após alguns minutos de inatividade ou pelo fechamento '
    'incorreto da sessão do Internet Banking'  # . Para retornar, digite novamente seus dados
)


class SantanderBrasilLoginer(BasicScraper):
    """SantanderBrasilLoginer provides common_login() method
    that can be used from both scrapers but then
    each of the scrapers should finish the method using its own way.
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='!!! UNSET !!!') -> None:
        self.scraper_name = scraper_name
        super().__init__(scraper_params_common, proxies)
        third_log_pass = self.db_connector.get_third_login_password()

        self.req_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0'
        }
        self.username_third = third_log_pass.AccessThirdLoginValue
        self.password_for_username_third = third_log_pass.AccessPasswordThirdLoginValue

    def _get_fin_ent_account_id(self) -> str:
        return '{}-{}'.format(self.username, self.username_second)

    def _generate_local_pu_key(self) -> Dict[str, str]:
        """
        :return: dict like {"_0xb1a8x2":"249446852405268451423542484724950614481",
        "_0xb1a8x3":"340282366762482138434845932244680310783",
        "_0xb1a8x4":"340282366762482138434845932244680310780",
        "_0xb1a8x5":"308990863222245658030922601041482374867",
        "_0xb1a8x6":"29408993404948928992877151431649155974",
        "_0xb1a8x7":"275621562871047521857442314737465260675",
        "_0xb1a8x8":"340282366762482138443322565580356624661",
        "localPuKey":"041d1fe8599800d1e26aa63f0c9e27abfc02d17c3fbaf3edae92f4251a0d91d20e"}
        to pass page state between HTTP requests-responses
        """
        # call w/o args to get local pu key
        cmd = CALL_JS_ENCRYPT_LIB
        result_bytes = subprocess.check_output(cmd, shell=True)
        text = result_bytes.decode().strip()
        result_dict = json.loads(text)
        return result_dict

    def _get_remote_pu_key(self, s: MySession, context_id: str) -> Tuple[str, Dict[str, str]]:
        req_ksc_url = 'https://www.santandernetibe.com.br/getKscServer.asp'
        resp_ksc_param = s.post(
            req_ksc_url,
            data={},
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        ksc_param = resp_ksc_param.text  # 181216E321410131

        # random from DLECC.init();
        # '04246a8ed82448a81d19ca56733a441518b580c8799ffd0b1e9b2d3229f6273c5a'
        local_pu_key_page_state_dict = self._generate_local_pu_key()
        local_pu_key = local_pu_key_page_state_dict['localPuKey']
        # remote PuKey
        # from https://www.santandernetibe.com.br/js/dlbEcc.js
        req_remote_pu_key_url = 'https://www.santandernetibe.com.br/getdadosServer.asp'
        req_remote_pu_key_params = OrderedDict([
            ('LocalPuKey', local_pu_key),
            ('contextId', context_id)
        ])

        resp_remote_pu_key = s.post(
            req_remote_pu_key_url,
            data=req_remote_pu_key_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # 047f0f10e89fc8c9b4a9528b0155e9dac2ec47b8dc70b5a00bd3453a3fa923e2e5
        return resp_remote_pu_key.text, local_pu_key_page_state_dict

    def _get_encrypted_remote_pu_key(self, remote_pu_key: str, page_state_dict: Dict[str, str]) -> str:

        # window.document.frmEnviar.txtXa.value = DLECC.encryptHashPassword(
        # 	parent.parent.Dummy.getpwd(),   // user pass
        # 	userSalt.value,                 // AVANSIS
        # 	RemotePuKey.value);
        # window.document.frmEnviar.submit();
        # }

        cmd = '{} "{}" "{}" "{}" "{}"'.format(
            CALL_JS_ENCRYPT_LIB,
            self.password_for_username_third,
            self.username_third,
            remote_pu_key,
            json.dumps(page_state_dict).replace('"', '\\"')
        )
        result_bytes = subprocess.check_output(cmd, shell=True)
        txtXa_param_text = result_bytes.decode().strip()
        return txtXa_param_text

    def common_login(self) -> Tuple[MySession, Response, bool]:
        """common_login provides login steps which are common for all scrapers.
        Then each scraper should finish its login() method itself
        :returns (session, resp, ok) where `ok` means that not aborted"""

        s = self.basic_new_session()
        resp_logged_in = None  # type: Optional[Response]
        resp_avisos_confirm = None  # type: Optional[Response]

        # 2 attempts to handle
        # Pls, re-login due to 'incorrect closing of the internet Banking session'
        for i in range(2):
            s = self.basic_new_session()
            req_start_url = 'https://www.santandernetibe.com.br/default.asp'
            # req_start_url = ' https://www.santander.com.br/?segmento=negocios-empresas'
            # git initial cookies
            resp_start = s.get(
                req_start_url,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            agencia = self.username
            conta = self.username_second

            req_pre_bridge_url = 'https://www.santandernetibe.com.br/NIB_Pre_Bridge.asp'
            req_pre_bridge_params = OrderedDict([
                ('txtAgencia', agencia),
                ('txtConta', conta)
            ])
            req_pre_bridge_data = OrderedDict([
                ('browserName', 'firefox'),
                ('browserVersionStr', '56.0'),
                ('browserMajorVersion', '56'),
                ('browserMinorVersion', '0'),
                ('isMobile', 'false'),
                ('isMetro', 'false'),
                ('browserHtml5suport', 'true'),
                ('OSname', 'linux'),
                ('OSversion', ''),
                ('isDeviceMobile', 'N'),
            ])

            # neccessary for the next steps
            resp_pre_bridge = s.post(
                req_pre_bridge_url,
                params=req_pre_bridge_params,
                data=req_pre_bridge_data,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            # neccessary for the next steps
            req_initial_url = 'https://www.santandernetibe.com.br/NIB_Inicial.asp'
            req_initial_params = OrderedDict([
                ('txtMsgErro', ''),
                ('txtAgencia', agencia),
                ('txtConta', conta),
                ('flagCtaDeParada', ''),
            ])
            resp_initial = s.post(
                req_initial_url,
                data=req_initial_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            req_pre_login_url = 'https://www.santandernetibe.com.br/NIB_PreLogin.asp'
            req_pre_login_params = OrderedDict([
                ('txtNome', self.username_third),
                ('txtSenha', '')
            ])

            resp_pre_login = s.post(
                req_pre_login_url,
                data=req_pre_login_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            # 851083008
            context_id = extract.re_first_or_blank(r"var\s+contextoECC\s*=\s*'(\d+)';", resp_pre_login.text)
            if not context_id:
                self.basic_log_wrong_layout(resp_pre_login, "Can't parse context_id. Abort")
                return s, resp_pre_login, False

            remote_pu_key, local_pu_key_page_state_dict = self._get_remote_pu_key(s, context_id)
            txtXa_param = self._get_encrypted_remote_pu_key(remote_pu_key, local_pu_key_page_state_dict)

            if 'CSRFtoken' not in resp_pre_login.text:
                self.basic_log_wrong_layout(resp_pre_login, "Can't parse csrf_token_param. Abort")
                return s, resp_pre_login, False

            csrf_token_param = extract.form_param(resp_pre_login.text, 'CSRFtoken')

            req_login_url = 'https://www.santandernetibe.com.br/NIB_Login.asp'
            req_login_params = OrderedDict([
                ('txtEka', ''),
                ('txtTipoPessoa', 'J'),
                ('txtTipoConta', '1'),
                ('txtStatusConta', ''),
                ('pm_fp', 'version%3D3%2E5%2E0%5F1%26pm%5Ffpua%3Dmozilla'
                          '%2F5%2E0%20%28x11%3B%20linux%20x86%5F64%3B%20rv'
                          '%3A56%2E0%29%20gecko%2F20100101%20firefox%2F56'
                          '%2E0%7C5%2E0%20%28X11%29%7CLinux%20x86%5F64%26pm'
                          '%5Ffpsc%3D24%7C1366%7C768%7C742%26pm%5Ffpsw%3D%26pm'
                          '%5Ffptz%3D3%26pm%5Ffpln%3Dlang%3Den%2DUS%7Csyslang'
                          '%3D%7Cuserlang%3D%26pm%5Ffpjv%3D0%26pm%5Ffpco%3D1'
                          '%26pm%5Ffpasw%3D%26pm%5Ffpan%3DNetscape%26pm%5Ffpacn'
                          '%3DMozilla%26pm%5Ffpol%3Dtrue%26pm%5Ffposp%3D%26pm'
                          '%5Ffpup%3D%26pm%5Ffpsaw%3D1366%26pm%5Ffpspd%3D24%26pm'
                          '%5Ffpsbd%3D%26pm%5Ffpsdx%3D%26pm%5Ffpsdy%3D%26pm%5Ffpslx'
                          '%3D%26pm%5Ffpsly%3D%26pm%5Ffpsfse%3D%26pm%5Ffpsui%3D%26pm'
                          '%5Fos%3DLinux%26pm%5Fbrmjv%3D56%26pm%5Fbr%3DFirefox%26pm'
                          '%5Finpt%3D%26pm%5Fexpt%3D'),
                ('pm_chars', 'windows-1252'),
                ('CSRFtoken', csrf_token_param),
                ('txtMsg', ''),
                ('txtMsgErro', ''),
                ('txtXa', txtXa_param),
            ])

            resp_codes_bad_for_proxies_default = s.resp_codes_bad_for_proxies.copy()
            # w/o 500 to handle response on login errors
            s.resp_codes_bad_for_proxies = [502, 503, 504, 403, None]
            resp_logged_in = s.post(
                req_login_url,
                data=req_login_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )
            s.resp_codes_bad_for_proxies = resp_codes_bad_for_proxies_default

            # anti-fraud banner with action
            resp_avisos_confirm = None
            if 'NIB_Avisos.asp' in resp_logged_in.text:
                _, req_avisos_params = extract.build_req_params_from_form_html(
                    resp_logged_in.text,
                    'frmLogin',
                    is_ordered=True
                )
                resp_avisos_open = s.post(
                    'https://www.santandernetibe.com.br/NIB_Avisos.asp',
                    data=req_avisos_params,
                    headers=self.req_headers,
                    proxies=self.req_proxies
                )

                time.sleep(1.0)

                # Expecting to be redirected to 'logout.asp' with needed
                # <form name="frm" method="post" action="https://pj.santandernetibe.com.br/ibeweb/" target="_top">
                #   <input type="hidden" name="Ticket" value="NkOnrLFSjtv9kwmWndnLl+/z68yfQrsSUArn2wn7IA..." />
                # </form>
                resp_avisos_confirm = s.post(
                    'https://www.santandernetibe.com.br/NIB_Avisos.asp',
                    data=OrderedDict([('hdnAcao', '1'), ('txtPage', '')]),  # must to continue
                    headers=self.req_headers,
                    proxies=self.req_proxies
                )

            if not (resp_avisos_confirm and INCORRECT_PREV_CLOSING_MARKER in resp_avisos_confirm.text):
                break

            if i < 1:
                self.logger.warning('Incorrect closing of the previous session detected. Retry')

        if resp_avisos_confirm and ('form name="frm"' not in resp_avisos_confirm.text):
            self.basic_log_wrong_layout(resp_avisos_confirm, '''Can't parse `form name="frm"`. Abort''')
            return s, resp_avisos_confirm, False

        time.sleep(0.5)
        return s, resp_avisos_confirm or resp_logged_in or Response(), True
