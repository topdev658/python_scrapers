import os
import random
import subprocess
import time
import uuid

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from custom_libs.scrape_logger import ScrapeLogger
from project import settings as project_settings

# need to add name of dynamically created file
JS_ENCRYPT_SCRIPT_FOLDER_PATH = os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'bankinter_encrypters_temp'
)

__version__ = '1.7.0'

__changelog__ = """
1.7.0
use only first 12 chars of userpass
1.6.0
upd type hints, MySession with logger
1.5.0
reset the session on each login attempt
more delays, upd logs, fmt
1.4.0
increased timeouts for more stable auth
1.3.0
login: short sleep before login attempt to improve stability 
1.2.0
login: loop with early checkers for wrong response
1.1.2
from libs import myrequests as requests  # redefine requests behavior
1.1.1
remove temp js file fixed
1.1.0
_create_temp_js_file
_delete_temp_js_file
"""


def _create_temp_js_file(filepath: str,
                         encoder_js_script_str: str,
                         enc_func_name: str,
                         username: str,
                         userpass: str,
                         p_spyke_param: str) -> None:
    with open(filepath, 'w') as f:
        f.write('var document={};\n')

        f.write(encoder_js_script_str)
        f.write('\n')

        # add standalone call
        f.write("console.log({}('{}', '{}', '{}'));\n".format(
            enc_func_name,
            username,
            userpass,
            p_spyke_param
        ))


def _delete_temp_js_file(filepath: str) -> None:
    os.remove(filepath)


def _handle_blank_var(logger: ScrapeLogger,
                      i: int,
                      var_name: str,
                      resp: Response):
    logger.warning("Attempt #{}. Unexpected blank var {}"
                   "\nRESPONSE:\n{}."
                   "\nCan't continue. RETRY".format(i, var_name, resp.text))


def login(logger: ScrapeLogger,
          username: str,
          userpass: str,
          proxies=project_settings.DEFAULT_PROXIES):
    """
    <form action="" method="post" id="fLogSecurity" name="fLogSecurity">
    <input value="" name="bkcache" id="bkcache" type="hidden">
    <input value="" name="destino" id="destino" type="hidden">
    <input type="hidden" id="INqU8bA0LEzQG2GB5oPl" name="INqU8bA0LEzQG2GB5oPl" value="username,password,psi">
    <input type="hidden" id="tyYdDmyXXHcGGn3Ys2c2" name="tyYdDmyXXHcGGn3Ys2c2" value="">
    """

    req_headers = {'User-Agent': project_settings.DEFAULT_USER_AGENT}

    s = MySession(logger)  # for a linter
    timestamp = date_funcs.now_ts()
    login_form_resp = Response()

    # This login loop is necessary to handle different cases
    # when can't provide proper behavior for an authorization
    for i in range(1, project_settings.LOGIN_ATTEMPTS + 1):
        s = MySession(logger)  # reset the session an each attempt

        if i > 1:
            wait = 5 + 2 * i + random.random()
            logger.warning("Login attempt #{}. Wait {}sec before continuing".format(i, wait))
            time.sleep(wait)

        login_form_resp = s.get(
            'https://empresas.bankinter.com/www/es-es/cgi/empresas+gc+lgin?_={}'.format(timestamp),
            proxies=proxies,
            headers=req_headers,
            timeout=20,
        )

        encoder_js_script_str = extract.re_first_or_blank(
            r'(?si)<script type="text/javascript">\s*(var scificArr.*?)</script>',
            login_form_resp.text
        )
        if len(encoder_js_script_str) < 1000:  # 18k usually
            _handle_blank_var(logger, i, 'encoder_js_script_str', login_form_resp)
            continue

        enc_func_name = extract.re_first_or_blank(r'function (\w+)', encoder_js_script_str)
        if not enc_func_name:
            _handle_blank_var(logger, i, 'enc_func_name', login_form_resp)
            continue

        # '0xf9b41fb7'
        server_code_hex_str = extract.re_first_or_blank(r'var scificArr= new Array\((.*?),',
                                                        encoder_js_script_str)
        if not server_code_hex_str:
            _handle_blank_var(logger, i, 'server_code_hex_str', login_form_resp)
            continue

        server_code_int = int(server_code_hex_str, 16)

        p_spyke_param = "S({timestamp})S({delay};server:{server_code_int})".format(
            timestamp=timestamp,
            delay=random.randint(54467, 89134),
            server_code_int=server_code_int
        )

        filepath = os.path.join(JS_ENCRYPT_SCRIPT_FOLDER_PATH, '{}.js'.format(uuid.uuid4()))

        # Save the script
        # to make a call with standalone params
        _create_temp_js_file(
            filepath,
            encoder_js_script_str,
            enc_func_name,
            username,
            userpass[:12],
            p_spyke_param
        )

        cmd = 'node {}'.format(filepath)
        login_req_token = subprocess.check_output(cmd, shell=True).decode().strip()
        # print(login_req_token)
        if not login_req_token:
            _handle_blank_var(logger, i, 'login_req_token', login_form_resp)
            continue

        _delete_temp_js_file(filepath)

        encoded_param_name1 = extract.re_first_or_blank(
            'name="([^>]*)" value="username,password,psi">',
            login_form_resp.text
        )
        if not encoded_param_name1:
            _handle_blank_var(logger, i, 'encoded_param_name1', login_form_resp)
            continue

        encoded_param_val1 = 'username,password,psi'
        encoded_param_name2 = extract.re_first_or_blank(
            'value="username,password,psi"><input type="hidden" id="(.*?)"',
            login_form_resp.text
        )
        if not encoded_param_name2:
            _handle_blank_var(logger, i, 'encoded_param_name2', login_form_resp)
            continue

        encoded_param_val2 = login_req_token

        login_req_params = {
            'bkcache': '',
            'destino': '',
            encoded_param_name1: encoded_param_val1,
            encoded_param_name2: encoded_param_val2
        }

        # print(login_req_params)

        logged_in_resp = s.post(
            'https://empresas.bankinter.com/www/es-es/cgi/empresas+login',
            params=login_req_params,
            proxies=proxies,
            headers=req_headers,
            timeout=20,
        )
        break
    else:
        logger.error(
            "Can't process. Failed all attempts to build correct req params from login_form_resp."
            "\nRESPONSE:\n{}".format(login_form_resp.text)
        )
        logged_in_resp = Response()

    return s, logged_in_resp


if __name__ == '__main__':
    from custom_libs.scrape_logger import ScrapeLogger

    login(ScrapeLogger("", "", ""), 'IH79850', 'PERM6383')
