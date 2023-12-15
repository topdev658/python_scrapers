import uuid
from typing import Tuple

from custom_libs import requests_helpers
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    ScraperParamsCommon, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_COMMON
)
from scrapers._basic_scraper.basic_scraper import BasicScraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
Init 
"""

UA = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'

class BBVAEsEmpresasScraper(BasicScraper):
    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BBVAEsEmpresasScraper') -> None:

        self.scraper_name = scraper_name
        super().__init__(scraper_params_common, proxies)
        self.req_headers = self.basic_req_headers_updated({'User-Agent': UA})
        self.company_id_param = '00230001{}'.format(self.username)
        self.user_id_param = '{}{}'.format(self.company_id_param, self.username_second)
        self.tsec_header = ''
        self.access_token = ''

    def get_access_token(self, s: MySession) -> str:
        req_headers = self.basic_req_headers_updated({
            'x-consumer-id': 'cashweb@com.bbva.es.channels',
            'x-tsec-token': self.tsec_header,
            'x-validation-policy': 'bbva_es'
        })

        resp_token = s.get(
            'https://tsec2jwt.live.global.platform.bbva.com/v1/Token',
            headers=req_headers,
            proxies=self.req_proxies,
        )

        token = resp_token.json()["accessToken"]
        return token

    def _get_encrypted(self) -> str:
        return str(uuid.uuid4())

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()

        is_logged = False
        is_credentials_error = False
        reason = ''

        req_auth_token_params = {
            "authentication":
                {
                    "consumerID": "00000233",
                    "userID": self.user_id_param,
                    "authenticationType":"61",
                    "authenticationData":
                        [{
                            "authenticationData":[self.userpass],
                            "idAuthenticationData":"password"
                        }]
                },
            "backendUserRequest":
                {
                    "userId":"",
                    "accessCode": self.user_id_param,
                    "dialogId":""
                }
        }

        resp_auth_token_first = s.post(
            'https://www.bbvanetcash.com/ASO/TechArchitecture/grantingTickets/V02',
            json=req_auth_token_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        req_auth_token_params["authentication"]["authenticationType"] = "16"
        req_auth_token_params["authentication"]["consumerID"] = "00000222"

        resp_auth_token = s.post(
            'https://www.bbvanetcash.com/ASO/TechArchitecture/grantingTickets/V02',
            json=req_auth_token_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        if resp_auth_token.status_code == 403 and '"system-error-code":"forbidden"' in resp_auth_token.text:
            is_credentials_error = True
            return s, resp_auth_token, is_logged, is_credentials_error, reason


        if 'multistepProcessId' in resp_auth_token.text:
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        is_logged = '"authenticationState":"OK"' in resp_auth_token.text
        self.tsec_header = resp_auth_token.headers['tsec']
        self.access_token = self.get_access_token(s)

        contact_id = self._get_encrypted()
        self.contact_id = contact_id
        s = requests_helpers.update_mass_cookies(s, {
            'HTTP_CONTACTID': contact_id,
        }, '.bbva.es')

        return s, resp_auth_token, is_logged, is_credentials_error, reason

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

        # self.process_contract(s)

        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
