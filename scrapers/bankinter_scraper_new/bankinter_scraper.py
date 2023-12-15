import hashlib
import json
import os
import random
import subprocess
import time
from base64 import b64decode
from collections import OrderedDict
from datetime import datetime
from typing import Dict, Tuple, List, Set
from urllib.parse import urljoin

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    ScraperParamsCommon, MainResult, AccountScraped, AccountParsed,
    MovementParsed, MOVEMENTS_ORDERING_TYPE_ASC, DOUBLE_AUTH_REQUIRED_TYPE_COMMON
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.bankinter_scraper import parse_helpers
from . import parse_helpers
from .custom_types import Contract

# Like BancoCaminos
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
    'bankinter_encrypter__rsa_keygen.js'
))

CALL_JS_ENCRYPT__RSA_DECRYPT_LIB = '{} {}'.format(NODE_BIN, os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'bankinter_encrypter__decrypt.js'
))

CALL_JS_ENCRYPT__RSA_ENCRYPT_LIB = '{} {}'.format(NODE_BIN, os.path.join(
    project_settings.PROJECT_ROOT_PATH,
    project_settings.JS_HELPERS_FOLDER,
    'bankinter_encrypter__encrypt.js'
))

MAX_AUTOINCREASING_OFFSET_DAYS = 90
MAX_OFFSET = 90

CREDENTIALS_ERROR_MARKER = 'STS00004'

DOUBLE_AUTH_MARKER = 'STS00059'

__version__ = '1.2.0'
__changelog__ = """
1.2.0 2023.10.10 
login: 
    2fa detection
    added credentials error and 2fa markers
1.1.0
_b64decode for incorrect padding
login: wrong credentials detection
1.0.0
init
TODO: process_account_multicurrency
"""


# TODO multi-currency accounts are not fully supported by the new web (2022-03)
#  the 'old web' scraper still must be used to get movements of those accounts
class BankinterScraper(BasicScraper):
    scraper_name = 'BankinterScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.update_inactive_accounts = False
        # 'jwk'-exported keys
        self._client_public_key = {}  # type: Dict[str, str]
        self._client_private_key = {}  # type: Dict[str, str]

        self._server_public_key = {}  # type: Dict[str, str]

    @staticmethod
    def _ts() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _delay() -> None:
        time.sleep(0.5 + random.random())

    @staticmethod
    def _b64decode(text: str) -> str:
        """Handles incorrect padding from web"""
        return b64decode(text + '========').decode('utf-8')

    def _call_cmd(self, cmd: str) -> str:
        result_bytes = subprocess.check_output(cmd, shell=True)
        text = result_bytes.decode().strip()
        return text

    def _decrypt(self, msg: str) -> str:
        cmd = "{} '{}' '{}'".format(
            CALL_JS_ENCRYPT__RSA_DECRYPT_LIB,
            msg,
            json.dumps(self._client_private_key),
        )
        return self._call_cmd(cmd)

    def _encrypt(self, msg_json_str: str) -> str:
        cmd = "{} '{}' '{}' '{}'".format(
            CALL_JS_ENCRYPT__RSA_ENCRYPT_LIB,
            msg_json_str,
            json.dumps(self._client_private_key),
            json.dumps(self._server_public_key),
        )
        return self._call_cmd(cmd)

    def _gen_set_rsa_key_pair(self) -> bool:
        cmd = '{}'.format(
            CALL_JS_ENCRYPT__RSA_KEYGEN_LIB,
        )
        res = self._call_cmd(cmd)
        res_dict = json.loads(res)
        self._client_private_key = res_dict['privateKey']
        self._client_public_key = res_dict['publicKey']
        return True

    def _decrypt_json(self, msg: str) -> dict:
        return json.loads(self._decrypt(msg))

    def _userpass_hash(self, salt: str) -> str:
        # see main.js:50259
        # return l.prototype.decorate = function(l) {
        #                 this._sha1.update(l);
        #                 var n = this._sha1.getHash("HEX");
        #                 return this._sha256.update(n),
        #                   this._sha256.update(this._seed),
        #                   this._sha256.getHash("HEX")
        #             }
        pass_sha1 = hashlib.sha1(self.userpass.encode()).hexdigest()
        pass_sha256 = hashlib.sha256('{}{}'.format(pass_sha1, salt).encode()).hexdigest()
        return pass_sha256

    def _get_fin_ent_account_id_parent(self, account_parsed_multicurrency_dict: dict) -> str:
        """For multi-currency accounts. Extracts data from any first account"""
        fid = list(account_parsed_multicurrency_dict.values())[0]['fin_ent_account_id_parent']
        return fid

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()
        # s, resp, is_logged, is_cred_err, reason = self.scraper_old.login()

        # Step 0: init
        resp_secure = s.get(
            'https://empresas.bankinter.com/secure',
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        dtpc_cookie = s.cookies.get('dtPC', '')

        _resp_login_index = s.get(
            'https://empresas.bankinter.com/resources/companiesBanking/en/index.html?ts={}'.format(
                self._ts()
            ),
            headers=self.basic_req_headers_updated({
                'x-dtpc': dtpc_cookie
            }),
            proxies=self.req_proxies,
        )

        _resp_identity = s.get(
            'https://empresasapi.bankinter.com/api/tokenutilities/v1/token/identity',
            headers=self.basic_req_headers_updated({
                'X-Requested-With': 'XMLHttpRequest',
            }),
            proxies=self.req_proxies,
        )

        resp_authorize = s.get(
            'https://empresasapi.bankinter.com/authorize',
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        # Step 1: handshake

        # c80cXkVDG3uGMGzc7DOExJkpJ32rm5fK40oVU
        auth_id = parse_helpers.get_auth_id(resp_authorize.text)
        self._gen_set_rsa_key_pair()

        req_handshake_params = {
            'key': {
                'e': self._client_public_key['e'],  # 'AQAB'
                'kty': self._client_public_key['kty'],  # 'RSA'
                'n': self._client_public_key['n'],  # key str
            }
        }

        # https://seguridad.bankinter.com/seguridad/companiesbanking/en-gb?authorizationId=2bcfgtlUcGk1taqaC2gH3XHsbPl422pq9j2WZ
        # https://seguridad.bankinter.com/seguridad/acreditacion?action=display&sessionID=3c5baaae-198d-42d0-aa8e-6bf48c82215b&sessionData=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.ew0KICAgICJzZXNzaW9uIjogew0KICAgICAgICAic2Vzc2lvbklEIjoiM2M1YmFhYWUtMTk4ZC00MmQwLWFhOGUtNmJmNDhjODIyMTViIiwNCiAgICAgICAgImV4cCI6MTY0NzIwNzI2OCwNCiAgICAgICAgImN1cnJlbnRfdXNlcm5hbWUiOiIiLA0KICAgICAgICAiY3VycmVudF91c2VyX2NvbnNlbnQiOiJub25lIiwNCiAgICAgICAgImN1cnJlbnRfdXNlcl9yb2xlIjoiIiwNCiAgICAgICAgImN1cnJlbnRfdXNlcl9hY3IiOiIwIiwNCiAgICAgICAgImN1cnJlbnRfdXNlcl9hdXRoVGltZSI6IjAiLA0KICAgICAgICAic2FsdCI6IiIsDQogICAgICAgICJ0aGlyZF9wYXJ0eV9zc29fdG9rZW4iOiIiLA0KICAgICAgICAidGhpcmRfcGFydHlfc3NvX3Rva2VuX3R5cGUiOiIiDQogICAgfSwNCiAgICAicmVxdWVzdF9jb25zZW50Ijogew0KICAgICAgICAiY2xpZW50X25hbWUiOiJlbXByZXNhcy13ZWIiLA0KICAgICAgICAic2NvcGVfdmVyaWZpZWQiOiJiYXNpYytwcml2YXRlIg0KICAgIH0sDQogICAgInJlcXVlc3RfcGFyYW1ldGVycyI6IHsNCiAgICAgICAgImRpc3BsYXkiOiJwYWdlIiwNCiAgICAgICAgInByb21wdCI6ImxvZ2luK2NvbnNlbnQiLA0KICAgICAgICAiaWRfdG9rZW5faGludCI6IiIsDQogICAgICAgICJsb2dpbl9oaW50IjoiIiwNCiAgICAgICAgImFjcl92YWx1ZXMiOiIiLA0KICAgICAgICAiY2xpZW50X2lkIjoiZW1wcmVzYXMtd2ViIiwNCiAgICAgICAgIm5vbmNlIjoiIiwNCiAgICAgICAgInNjb3BlIjoiYmFzaWMrcHJpdmF0ZSIsDQogICAgICAgICJtYXhfYWdlIjogIiINCiAgICB9DQogICAgDQp9.iRxXDmKCWCb-05s-r6NS6D4Fg-FHpaItt2nclmskIts
        # https://api.bankinter.com/auth/oauth/v2/authorize?response_type=code&client_id=empresas-web&redirect_uri=https://empresasapi.bankinter.com/callback&scope=basic+private&state=701f52e9-53b4-489b-9f20-492ac9c2d4a4&display=page

        time.sleep(0.1)
        resp_handshake = s.post(
            'https://seguridad.bankinter.com/seguridad/api/authorization/v0/authorizations/'
            '{}/handshake'.format(auth_id),
            json=req_handshake_params,
            proxies=self.req_proxies,
            headers=self.basic_req_headers_updated({
                'X-Requested-With': 'XMLHttpRequest'
            })
        )

        try:
            resp_handshake_text = self._b64decode(resp_handshake.text)
        except:
            resp_handshake_text = resp_handshake.text

        resp_parts = resp_handshake_text.split('.')

        assert (len(resp_parts)) == 5
        # l.decodeToUTF8String = function (n) {
        #         return decodeURIComponent(atob(n).split('').map(l.toUTF8Char).join(''))
        #       },
        # '{"kid":"client_1f70x7RNoYURISZOp3njoQj5wSmA4lJdnbdTM","enc":"A256GCM","alg":"RSA-OAEP-256"}'
        # key_client_dict = b64decode(resp_parts[0]).decode('utf-8')  #

        resp_handshake_decrypted = self._decrypt(resp_handshake.text)
        # 3 parts
        resp_handshake_decrypted_split = resp_handshake_decrypted.split('.')

        # {'key': {'kty': 'RSA',
        #   'kid': 'server_1f70x7RNoYURISZOp3njoQj5wSmA4lJdnbdTM',
        #   'n': 'ALA8BJEyWZo_VVrUoCE3g-dNHdkDSr6fK9pYdVWE6vNUu1QPY4Z67AFsAv3Y9pxZLzfa1Lr3VksmD3ZdYIleoKXT0XbRud3ed_VmEyDIt0IUx20RptkgzAun7gv5kNq5uEiwh70bX65U61N6l_qjC-oZQWdfaB67V8AsttnRjN43r7fAlrjjyQXYWWxjIkvgKcmY1jnEpxkP2DmMxdrnwD8CNLjU8Fj73NS6mAa8nRc_QzhTfNn7ci8fC_6l-jWQ5j5E6Kcl_47xhSrT_bGbydYDEPpKb8IZB9ydQcKHeiamyw9drcLggFAolAivCs91cJuFDzQX3MTKD78BB4BhNTE=',
        #   'e': 'AQAB'},
        #  'authorization': {'id': '1f70x7RNoYURISZOp3njoQj5wSmA4lJdnbdTM',
        #   'interactionId': '9aff0b34c51444db',
        #   'type': 'ACCESS',
        #   'flow': 'DEFAULT',
        #   'status': 'PENDING',
        #   'validUntil': '2022-03-15T23:43:44',
        #   'visualizationData': {'theme': 'companiesbanking'},
        #   'identificationData': {'clientData': {'clientId': 'empresas-web',
        #     'displayName': 'empresas-web'},
        #    'secondClientData': {}},
        #   'integrationData': {'system': 'CA',
        #    'caSessionId': '268bc66f-64e2-4582-99b6-d1c060ff4f89'},
        #   'challenges': [{'challengeType': 'USER',
        #     'id': '30ccUHDED8ZOj1t',
        #     'challengeStatus': 'PENDING'},
        #    {'challengeType': 'PASSWORD',
        #     'id': '7f0c1i3GLN7IfsC',
        #     'challengeStatus': 'PENDING',
        #     'challengeMethod': 'SALTED_SHA256_SHA1',
        #     'challengeSeed': 'JaKjYABrqLvrJQIGbvovrzkFXMIehWzwEnkCmvjfvQwiDkH6DnjTpQM5epbtMYcu'}],
        #   'consents': [],
        #   'additionalInfo': {},
        #   'messages': [],
        #   'existsAdditionalConsents': False,
        #   'backAllowed': False,
        #   'allowedFlowPreferences': ['REACTIVATION_WITH_IDDOCS']}}

        # TODO handle case when
        # b64decode(resp_handshake_decrypted_split[0]) == {
        #     "kid":"server_9b3fhhZOVPThPORvjctYA3nWZssRZ7SoP08A",
        #    "cty":"application\\/json; charset=UTF-8","alg":"RS256"
        #    }
        # This means that the auth_id (?) already logged in
        # If not logged in then, then b64decode(resp_handshake_decrypted_split[0]) raises.

        handshake_payload_str = self._b64decode(resp_handshake_decrypted_split[1])
        handshake_payload_dict = json.loads(handshake_payload_str)
        self._server_public_key = handshake_payload_dict['key']
        self.logger.info('Got server public RSA key: kid: {}'.format(self._server_public_key['kid']))

        # Step 2: challenge

        # from
        #   'challenges': [
        #   {'challengeType': 'USER',
        #     'id': '30ccUHDED8ZOj1t',
        #     'challengeStatus': 'PENDING'},
        #   {'challengeType': 'PASSWORD',
        #     'id': '7f0c1i3GLN7IfsC',
        #     'challengeStatus': 'PENDING',
        #     'challengeMethod': 'SALTED_SHA256_SHA1',
        #     'challengeSeed': 'JaKjYABrqLvrJQIGbvovrzkFXMIehWzwEnkCmvjfvQwiDkH6DnjTpQM5epbtMYcu'}],
        auth_list = handshake_payload_dict['authorization']['challenges']
        username_challenge = [v for v in auth_list if v['challengeType'] == 'USER'][0]  # type: Dict[str, str]
        userpass_challenge = [v for v in auth_list if v['challengeType'] == 'PASSWORD'][0]  # type: Dict[str, str]
        assert 'SALTED_SHA256_SHA1' == userpass_challenge['challengeMethod']  # implemented one

        req_challenge_params = OrderedDict([
            ('answers', [
                OrderedDict([
                    ('id', username_challenge['id']),
                    ('challengeType', 'USER'),
                    ('pattern',
                     "KD({};tag:INPUT;id:{};mod:2;code:17)KD(154;code:86)KU(69;code:86)KU(115;mod:0;code:17)".format(
                         self._ts(),
                         username_challenge['id']
                     )),
                    ("challengeAnswer", self.username)
                ]),
                OrderedDict([
                    ('id', userpass_challenge['id']),
                    ('challengeType', 'PASSWORD'),
                    ('pattern',
                     'KD({};tag:INPUT;id:{};mod:2;code:17)KD(372)KU(170)KU(33;mod:0;code:17)'.format(
                         self._ts(),
                         userpass_challenge['id']
                     )),
                    ('challengeAnswer', self._userpass_hash(userpass_challenge['challengeSeed']))
                ])
            ]),
            ('backToPrevious', False)
        ])
        req_challenge_params_enc = self._encrypt(json.dumps(req_challenge_params))

        self._delay()
        resp_challenge = s.put(
            'https://seguridad.bankinter.com/seguridad/api/authorization/v0/authorizations/'
            '{}/challengeAnswers'.format(auth_id),
            data=req_challenge_params_enc,
            headers=self.basic_req_headers_updated({
                'Content-Type': 'application/jose',
                'X-Requested-With': 'XMLHttpRequest',
            }),
            proxies=self.req_proxies,
        )
        # {"kid":"client_59b3hNqKevbsKcWzmpTnS0oHUp27omMPcHlE","enc":"A256GCM","alg":"RSA-OAEP-256"}
        # challenge_key = self._b64decode(resp_challenge.text.split('.')[0])
        # self.logger.info('Got challenge key: {}'.format(challenge_key))

        resp_challenge_decrypted = self._decrypt(resp_challenge.text)
        challenge_payload_str = self._b64decode(resp_challenge_decrypted.split('.')[1])
        # {'authorization': {'id': '9721hu0SntHYlmAu0ssRzeoRanhCPYg7hoQde',
        #   'interactionId': 'ad21bf394f19b739',
        #   'type': 'ACCESS',
        #   'flow': 'DEFAULT',
        #   'status': 'GRANTED',
        #   'validUntil': '2022-03-20T23:29:05',
        #   'visualizationData': {'theme': 'companiesbanking'},
        #   'identificationData': {'clientData': {'clientId': 'empresas-web',
        #     'displayName': 'empresas-web'},
        #    'secondClientData': {}},
        #   'integrationData': {'system': 'CA',
        #    'caSessionId': '73964576-f6d0-4f4b-b645-608400120276',
        #    'caSessionData': 'eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..kZDoRg5dSFN04jT4frQ4AQ.UKuquiaaq2fBNwdTIF63m5rsm4svaRMO9Akj53Ar_TvfhGhf-08Sd8YOAX1szyArIfqtM0yBUBpByC64VGVC2vV29k_gvGKacrEUorhYPRomKXDa8nko6Nh38y41nRWGy41US_G6k1cjqPHIQx-sE3UfwsHqeZo4SpndGQXGsWnurs8XQQuJBld3Wu2E5i4gdQJ_PPKNsK3vtOwCURI_tzS9xTkaMOkDXCoPdoeYeq0k7SQ-YUr0KN2GKjg-UVmjtCHA4lS1xVB13kPYWmIP5-lL1CnoEWeTey7kbQz1jlRDSD6yLwfQFAX4laYYdd3gZnur-uCYrAu2LD0zO-q6GY9ncFLdfib20tdpbMU6GZcxO8wW5Ajky-lngGBcDDyeni3PAswopBMFRXQ4vs-Z_i_fxA__lF9ZP_jzw9U2tpzTBL7i_Oel7yf9jClJAvzHFLMRI4PMBwWaPZGX1Ks46cqcwVrcmjjMyryLBMRvCTWDGx5b7mZll_qRGKNdRj7BQKU5PiJIPJruTv3L6-tHEdYAJ3zkKkMHplymxdKoDnLxTq5mAd2VBZSakQNTT-bdeNOfkrbuiSrt9C2v2G72XB-TJ0WIuX7VD0BWaCqQZ__6YLXBIgJNIu2XwuUlLYMdgOzG6PXZxZ3ysr_RA3lNiL1lvfStXLF6bc1v3OdfI4YysMJo1Pxyj6MkrASiHZcZi-RH6fnwE_gYwu7gLZ0CICUh2S6t2YVcO8cFSoXhkXS5fPmXcMrq9dmMqtXA1WXawRgdpg5uCsLszACHPwjHoJzYLrRg42GbCG7DmkTkn9sA-K0BAEyYnZKU4V18l4w7OSs-cNQXvNxdGS-opczJCf57aIbeHnQxeMQ_ngGRMLbKXkBSDQ-arzOjX7u9zG9-3OWIbt01s8ddaXbEosJNCIN4wgR3e_SeXULKqQ2Tel9WOf5eyRtfLRA9cRxaUG2KPHPBcwSo6Xi4LPVbtAz8Xm3_N7QAWM9EBtFekZhPsBD8yzXGtN3koZbj5IgMhtfCXiTJDRfCDnq-a36uDL_OgQfqLFn6uCxAX9Lh_oUcfTuUrV-HTBCFy0SJC8EwO1SY92NAwr8G5bmLNTZd8EO_1Wj3FL18K4DX9ZtaZlfvTYTgSGUOEpY7IlxNB62MUbdjgtV6U0-Bii4iFNHJWRJtUiO2PSBKmRIzpYaJO2Dn8ZcvgS5564rA5qrqyuD9FFiRs72BQz5xwiv7jHD-IGRtKpFnURxq8EwFI6Ja7CbPAl-QogeoPhYjFcjTfOLZZVPSEpoAs6ZeKKgZ_vkL0mQvnD7Lt8aN5Z29sMtq8FWAt6MXmY9-DSJ0D3yC_3zB_mMeHQhZIWIvmR3HkAP1hSEYUK30A-hn0oYgBw46lAv5NIKke0yohTpa4ykIAr6-6W_cmZDKCxXcUNVpsi_E1wrywPEcApO6Do7N0OU2YY2MBUtmCDudMeWckCMfmUeHmSPWepyRT5VPOmOtkoju40GLWYzYeQLHJnnFky26nRkUdzzrsQ_GdPonO-0iyuSa4ueyA_RB5lbNT4hIZwdeud2tB01nKt8QgHPoTd6f2UKnxVC5dXutV497qTrR831dnyfLzwAbBBjhD26IsWpf1Zd7wThxZUt2UURlIlQrjhPiXnx3QNBSVWHgOxJgGtDRE1KarCBNta1xLODFgOjsPfVxyRBX4vVE-xVfXyBBWHypcZpay0K2HSDyTEPvujYuAX32xffix2rwI_JXu8v6eQORrbjOCw-y15aTDjxmKkVcUGZTlW8dlbHxttZ32ejVKmx7V2qUhuFDQM1n9bGA3JXV8LrJBi8LWksk70qFCazX3xHNKlQjlDBYZUqp0WEIoRom5FgIcgScJNJylx-D2ZGj5Wcn4D18C97DtvWtvpvEZBWiMtNAXm4U-gPjR8tYtdthJNLJ7IoRKIpiNudHvZwbPxS_bZEAMFjcyVLMnZs9KCxqYufYAGeQUw8qimyVaoXPk5Jc62LTPPpvc9V4vux7PTrYFz-QEq2reT3WJYlmYSlDGpBEKTJ08YH-FsfykxS60Bvc2gvgXKWDw9OvCTHEO38uDmANK-6-O_hwK0Nkul6w7lgBFCvt26IjxpqbnqgHATuT1u8ZZOkyLZOp69KvlH5cwh63PAEe8Byu_lTcBvuNA64h2fCnvx0_S_3mMCgGzYPtVB2i3j6XSGdyaP7f-oJhihcQdqD3ZkM5EXJaUVTjWd575rp6hY14KK_i0PBs.lHQfFgr6gNMOBIS7w0gGMg',
        #    'caAction': 'grant',
        #    'caReturnURI': 'https://api.bankinter.com/auth/oauth/v2/authorize/consent'},
        #   'challenges': [],
        #   'consents': [],
        #   'messages': [],
        #   'existsAdditionalConsents': False,
        #   'backAllowed': False,
        #   'allowedFlowPreferences': []},
        #  'unlockedChallenges': []}

        # OR with err msgs:
        # ...
        # "message":{"i18nCode":"STS00004","message":"Credenciales incorrectas"},
        # "messages":[{"messageType":"ERROR","data":"Credenciales incorrectas","code":"STS00004"}]
        # ...
        # 'message': {'i18nCode': 'STS00059', 'message': 'Por normativa europea, para completar el acceso es necesario informar la clave solicitada. Le solicitaremos esta clave cada 180 días'},
        # 'messages': [{'code': 'STS00059', 'data': 'Por normativa europea, para completar el acceso es necesario informar la clave solicitada. Le solicitaremos esta clave cada 180 días', 'messageType': 'INFO'}
        # ...
        challenge_payload_dict = json.loads(challenge_payload_str)
        reason = ''
        is_logged = challenge_payload_dict['authorization']['status'] == 'GRANTED'
        if challenge_payload_dict['authorization'].get('message', {}).get('i18nCode', '') == DOUBLE_AUTH_MARKER:
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON
        is_credentials_error = (challenge_payload_dict['authorization']
                                .get('message', {})
                                .get('i18nCode', '') == CREDENTIALS_ERROR_MARKER)
        if not is_logged:
            return s, Response(), is_logged, is_credentials_error, reason

        # Step 3: consent

        req_consent_params = OrderedDict([
            ('action', 'grant'),
            ('sessionID', challenge_payload_dict['authorization']['integrationData']['caSessionId']),
            ('sessionData', challenge_payload_dict['authorization']['integrationData']['caSessionData'])
        ])

        self._delay()
        _resp_consent = s.post(
            'https://api.bankinter.com/auth/oauth/v2/authorize/consent',
            data=req_consent_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        self._delay()
        resp_pos_global = s.get(
            'https://empresas.bankinter.com/secure/en/posicion-global?'
            'x-flow-type=access&x-flow-result=OK&x-flow-blocked-user=false',
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        return s, resp_pos_global, is_logged, is_credentials_error, reason

    def get_contracts(self, s: MySession, auth_identity_id: str) -> List[Contract]:
        resp_contracts = s.get(
            'https://empresasapi.bankinter.com/api/companyprofile/v3/profiles/{}/companies'.format(auth_identity_id),
            headers=self.basic_req_headers_updated({
                'X-Requested-With': 'XMLHttpRequest',
            }),
            proxies=self.req_proxies,
        )
        # 110_resp_companies.json
        resp_contracts_json = resp_contracts.json()
        contracts = parse_helpers.get_contracts(resp_contracts_json)
        return contracts

    def get_auth_identity_id(self, s: MySession) -> str:
        resp_identity = s.get(
            'https://empresasapi.bankinter.com/api/tokenutilities/v1/token/identity',
            headers=self.req_headers,
            proxies=self.req_proxies,
        )
        # 100_resp_identity.json
        resp_identity_json = resp_identity.json()
        auth_identity_id = resp_identity_json['id']  # '5d399MZu5Qk5AEDqx'
        return auth_identity_id

    def get_accounts_parsed(
            self,
            s: MySession,
            auth_identity_id: str,
            contract: Contract) -> Tuple[List[AccountParsed], List[Dict[str, AccountParsed]]]:
        """
        :return (accounts_parsed, accounts_multicurrency_parsed)
        """
        org_title = contract.org_title
        # To avoid duplicates because some multi-currency requests
        # also contain single-currency accounts in responses
        account_nos_extracted = set()  # type: Set[str]
        accounts_parsed = []  # type: List[AccountParsed]
        # Get multi-currency accounts
        # Each subaccount_parsed_for_specific_currency contains fin_ent_account_id_parent (w/o currency)
        # [{parent_2_subaccounts_parsed_for_each_currency},
        #  {parent_2_subaccounts_parsed_for_each_currency}, ...]
        accounts_multicurrency_parsed = []  # type: List[Dict[str, AccountParsed]]

        for url, req_accounts_get_params_i in [
            ('credits/v1/summary', {'type': 'euros'}),
            ('credits/v1/summary', {'type': 'multicurrency'}),
            ('accounts/v1/summary', {'type': 'euros'}),
            ('accounts/v1/summary', {'type': 'multicurrency'}),
            # ('multioptions/v1/summary', {}),
            # ('leasing/v1/summary', {}),
            # ('foreignfinancing/v1/summary', {}),
            # ('directdebitaccounts/v3/summary', {}),
        ]:
            req_accounts_url_i = urljoin('https://empresasapi.bankinter.com/api/', url)
            req_accounts_get_params_i.update({
                'authorised': auth_identity_id
            })

            resp_accounts_i = s.get(
                req_accounts_url_i,
                params=req_accounts_get_params_i,
                headers=self.basic_req_headers_updated({
                    'X-BkCompany': contract.id,  # 'c5cdxcDHDDfs'
                    'X-Requested-With': 'XMLHttpRequest',
                }),
                proxies=self.req_proxies,
            )
            resp_i_json = resp_accounts_i.json()
            self.logger.info('{}: got accounts from {}'.format(org_title, resp_accounts_i.url))

            account_parsed_i = parse_helpers.get_accounts_single_currency_parsed(resp_i_json)
            for acc_multicurr_parsed in account_parsed_i:
                account_no = acc_multicurr_parsed['account_no']
                if account_no not in account_nos_extracted:
                    accounts_parsed.append(acc_multicurr_parsed)
                    account_nos_extracted.add(account_no)

            accounts_multicurrency_parsed_i = parse_helpers.get_accounts_multi_currency_parsed(resp_i_json)
            for acc_multi_dict in accounts_multicurrency_parsed_i:
                account_parent_no = list(acc_multi_dict.values())[0]['account_no']
                if account_parent_no not in account_nos_extracted:
                    accounts_multicurrency_parsed.append(acc_multi_dict)
                    account_nos_extracted.add(account_parent_no)
        return accounts_parsed, accounts_multicurrency_parsed

    def process_access(self, s: MySession) -> bool:
        auth_identity_id = self.get_auth_identity_id(s)
        contracts = self.get_contracts(s, auth_identity_id)
        for contract in contracts:
            self.process_contract(s, auth_identity_id, contract)
        return True

    def process_contract(self, s: MySession, auth_identity_id: str, contract: Contract) -> bool:
        org_title = contract.org_title

        self.logger.info('Process contract: {}'.format(org_title))

        accounts_parsed, accounts_multicurrency_parsed = self.get_accounts_parsed(
            s,
            auth_identity_id,
            contract
        )

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(org_title, acc_parsed)
            for acc_parsed in accounts_parsed
        ]

        # Flat list, just for uploading, not for movement extraction
        subaccounts_multicurrency_scraped = [
            self.basic_account_scraped_from_account_parsed(org_title, subaccount_parsed)
            for account_parsed_multicurrency in accounts_multicurrency_parsed
            for subaccount_parsed in account_parsed_multicurrency.values()
        ]  # type: List[AccountScraped]

        accounts_scraped_all = accounts_scraped + subaccounts_multicurrency_scraped

        self.basic_upload_accounts_scraped(accounts_scraped_all)
        self.basic_log_time_spent('{}: GET BALANCES'.format(org_title))

        self.logger.info('{}: got {} accounts: {}'.format(
            org_title,
            len(accounts_scraped_all),
            accounts_scraped_all
        ))

        if not accounts_scraped_all:
            self.logger.warning('{}: suspicious results: no accounts_scraped_all'.format(
                org_title,
            ))

        accounts_scraped_dict = self.basic_gen_accounts_scraped_dict(accounts_scraped)
        for acc_parsed in accounts_parsed:
            self.process_account(
                s,
                contract,
                acc_parsed,
                accounts_scraped_dict
            )

        # Process multi-currency accounts
        subaccounts_multicurrency_scraped_dict = self.basic_gen_accounts_scraped_dict(
            subaccounts_multicurrency_scraped
        )
        for acc_multicurr_parsed in accounts_multicurrency_parsed:
            self.process_account_multicurrency(
                s,
                contract,
                acc_multicurr_parsed,
                subaccounts_multicurrency_scraped_dict
            )

        return True

    def _get_movements_parsed(
            self,
            s: MySession,
            contract: Contract,
            account_parsed: AccountParsed,
            date_from: datetime) -> List[MovementParsed]:
        date_fmt = '%Y-%m-%d'
        fin_ent_account_id = account_parsed['financial_entity_account_id']
        date_from_str = date_from.strftime(date_fmt)
        self.basic_log_process_account(fin_ent_account_id, date_from_str)
        # 56c2229fB9DsBxw9Je9cccOwxO2cDOODfHDxoxo2
        req_movs_url = 'https://empresasapi.bankinter.com/api/accounts/v1/accounts/{}/transactions'.format(
            account_parsed['req_params']['id']
        )
        req_movs_params = {
            'continuationsNumber': '2',
            'continuationTokenInd': 'true',
            'sort': 'ASC',  # DESC may miss movements (website err)
            'to': self.date_to.strftime(date_fmt),
            'from': date_from.strftime(date_fmt)
        }
        movements_parsed = []  # type: List[MovementParsed]
        for page in range(1, 51):
            self.logger.info('{}: {}: page #{}: get movements'.format(
                contract.org_title,
                fin_ent_account_id,
                page
            ))
            resp_movs_i = s.get(
                req_movs_url,
                params=req_movs_params,
                headers=self.basic_req_headers_updated({
                    'X-BkCompany': contract.id,
                    'X-Requested-With': 'XMLHttpRequest',
                }),
                proxies=self.req_proxies
            )
            resp_movs_i_json = resp_movs_i.json()
            movements_parsed_i = parse_helpers.get_movements_parsed(resp_movs_i_json)
            movements_parsed.extend(movements_parsed_i)

            continuation_token = resp_movs_i_json.get('continuationToken')
            if not continuation_token:
                self.logger.info('{}: {}: no more pages'.format(
                    contract.org_title,
                    fin_ent_account_id
                ))
                break

            req_movs_params['continuationToken'] = continuation_token
            continue
        return movements_parsed

    def process_account(
            self,
            s: MySession,
            contract: Contract,
            account_parsed: AccountParsed,
            accounts_scraped_dict: Dict[str, AccountScraped]) -> bool:
        fin_ent_account_id = account_parsed['financial_entity_account_id']
        account_scraped = accounts_scraped_dict[fin_ent_account_id]

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_dt, date_from_str = self.basic_get_date_from_dt(
            fin_ent_account_id,
            max_autoincreasing_offset=MAX_AUTOINCREASING_OFFSET_DAYS,
            max_offset=MAX_OFFSET
        )
        date_fmt = '%Y-%m-%d'
        self.basic_log_process_account(fin_ent_account_id, date_from_str)
        # 56c2229fB9DsBxw9Je9cccOwxO2cDOODfHDxoxo2
        req_movs_url = 'https://empresasapi.bankinter.com/api/accounts/v1/accounts/{}/transactions'.format(
            account_parsed['req_params']['id']
        )
        req_movs_params = {
            'continuationsNumber': '2',
            'continuationTokenInd': 'true',
            'sort': 'ASC',  # DESC may miss movements (website err)
            'to': self.date_to.strftime(date_fmt),
            'from': date_from_dt.strftime(date_fmt)
        }
        movements_parsed = self._get_movements_parsed(
            s,
            contract=contract,
            account_parsed=account_parsed,
            date_from=date_from_dt
        )

        movements_scraped, movements_parsed_filtered = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        ok = self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )

        if ok:
            self.download_receipts(
                s,
                account_scraped,
                movements_scraped,
                movements_parsed_filtered
            )

        return True

    def process_account_multicurrency(
            self,
            s: MySession,
            contract: Contract,
            account_parsed_multicurrency_dict: Dict[str, AccountParsed],
            subaccounts_multicurrency_scraped_dict: Dict[str, AccountScraped]) -> bool:

        org_title = contract.org_title
        if not account_parsed_multicurrency_dict:
            return True

        # Get fin_ent_account_id_parent from any parsed subaccount
        fin_ent_account_id_parent = self._get_fin_ent_account_id_parent(account_parsed_multicurrency_dict)
        self.logger.info('{}: process multi-currency account: {}'.format(
            org_title,
            fin_ent_account_id_parent
        ))

        # Skip multi-currency account only if all sub-accounts marked as 'inactive'
        is_active = any(self.basic_check_account_is_active(acc['financial_entity_account_id'])
                        for acc in account_parsed_multicurrency_dict.values())
        if not is_active:
            return True

        self.logger.info('{}: active sub-accounts detected: process all of {}'.format(
            org_title,
            account_parsed_multicurrency_dict
        ))

        # TODO continue
        # SWITCH to the old web (-a 31806):
        # https://empresas.bankinter.com/www/es-es/cgi/empresas+cuentas+credito_movimientos?bkCompany=3b7bs9DxcDfD
        self.logger.warning(
            "Multi-currency accounts are not fully supported by the new web (03/2022). "
            "The old web still can be used, but adapter is not implemented for now. Skip"
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

        self.process_access(s)

        self.basic_log_time_spent('GET ALL BALANCES AND MOVEMENTS')
        return self.basic_result_success()
