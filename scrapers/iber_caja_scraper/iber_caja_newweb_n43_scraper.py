import time
from collections import OrderedDict
from datetime import datetime
from typing import Tuple
from urllib.parse import urljoin

from custom_libs import extract
from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from .custom_types import Contract
from .iber_caja_newweb_scraper import IberCajaScraper

__version__ = '3.0.0'
__changelog__ = """
3.0.0 2023.09.09
_get_auth_param: changed partial url from 'bancadigitalweb' to 'banca-digital-apigw'
2.2.0
_get_auth_param: several attempts to detect 'n43 download has not been activated'
2.1.0
download_n43_file: check for 'NO EXISTE NINGUNA CUENTA' (wrn N43 is not activated)
2.0.0
new web upd: all accounts in one file, upd reqs, upd flow
1.5.0
use WRN_N43_DOWNLOAD_IS_NOT_ACTIVATED
1.4.0
use ERR_N43_DOWNLOAD_IS_NOT_ACTIVATED result code
1.3.0
main: align process_access call
1.2.0
process_contract: check does the contract allow N43 downloading or not (by checking resp_loginpm)
download_n43_file: use n43_funcs.validate_n43_structure
1.1.0
_filter_n43: handle extra digits in account_name for correct fin_ent_account_id
1.0.1
fixed log msg
1.0.0
init
"""


class IberCajaN43Scraper(IberCajaScraper):
    fin_entity_name = 'IBERCAJA'
    scraper_name = 'IberCajaN43Scraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.is_success = True
        # For result. The scraper will save as much N43s as possible
        # (will continue scraping on detection),
        # but then it will set an err code as the result
        self.__is_detected_inactive_contract_for_n43 = False

    def _get_auth_param(self, s: MySession, contract: Contract) -> Tuple[bool, str]:
        s.verify = False

        # Exclude 502 (the resp code for inactive contract)
        resp_codes_bad_for_proxies_default = s.resp_codes_bad_for_proxies

        for att in range(1, 4):
            s.resp_codes_bad_for_proxies = [500, 503, 504, 403, None]
            # {"loginPM":"441445IGNACIO","ticketPM":"798F83B...3F3","code":0,"errors":null}
            resp_loginpm = s.get(
                'https://banca.ibercaja.es/omnicanalidad/canales/banca-digital-apigw/v1/api/User/loginPM',
                headers=self.basic_req_headers_updated({
                    'Referer': 'https://banca.ibercaja.es/omnicanalidad/canales/banca-digital-apigw/v1/',
                }),
                proxies=self.req_proxies,
                timeout=60,
            )
            s.resp_codes_bad_for_proxies = resp_codes_bad_for_proxies_default

            # Check does the contract allow N43 downloading or not (err resp if not)
            # -a 27401, contract "Z78519" ("COMSA ISI SAU Y LEVANTINA ING Y CONST SL UTE LEY")
            # {"loginPM":null,"ticketPM":null,"code":500,"errors":[{"error":-2146233088,
            # "description":"Iniciar Session PM Error - Error al iniciar sesión:
            # Response status code does not indicate success: 502 (Bad Gateway). -
            # Response status code does not indicate success: 502 (Bad Gateway)."}]}
            if resp_loginpm.status_code == 502 or ('502 (Bad Gateway)' in resp_loginpm.text):
                self.logger.warning(
                    "{} ({}): att #{}: it looks like the contract (company) "
                    "is inactive for N43 downloading. Retry.".format(
                        contract.org_title,
                        contract.id,
                        att,
                    )
                )
                time.sleep(att * 2)
            else:
                break  # N43 is active
        else:
            # all attempts with 502
            self.logger.warning(
                "{} ({}): it looks like the contract (company) is inactive for N43 downloading. Skip. "
                "Pls, ask the customer to activate this contract".format(
                    contract.org_title,
                    contract.id
                ))
            self.__is_detected_inactive_contract_for_n43 = True
            return True, ''

        auth_param = ''
        try:
            auth_param = resp_loginpm.json().get('ticketPM', '')
        except Exception as _e:
            pass  # will check by auth_param val
        if not auth_param:
            self.basic_log_wrong_layout(
                resp_loginpm,
                "{}: invalid resp_loginpm".format(contract.org_title)
            )
            self.is_success = False
            return False, ''
        return True, auth_param

    def _open_n43_filter_form(self, s: MySession, auth_param: str) -> Tuple[bool, Response]:
        req_pgmon_url = 'https://www1.ibercajadirecto.com/ibercaja/asp/PMCONGateway.asp?MSCSAuth={}'.format(auth_param)
        req_pgmon_params = {'IdOperacion': 'C0075_2'}
        resp_pgmon = s.post(
            req_pgmon_url,
            data=req_pgmon_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_n43_link, req_n43_filter_params = extract.build_req_params_from_form_html_patched(
            resp_pgmon.text,
            form_name='formData',
            is_ordered=True
        )
        req_n43_filter_form_url = urljoin(resp_pgmon.url, req_n43_link)
        resp_n43_filter_form = s.post(
            req_n43_filter_form_url,
            data=req_n43_filter_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        return True, resp_n43_filter_form

    def process_contract(self, s: MySession, contract: Contract) -> bool:
        org_title = contract.org_title
        self.logger.info('Process contract for N43: {}'.format(org_title))
        if not self.is_success:
            self.logger.info('{}: abort due to the previous failure'.format(org_title))
            return False

        self.set_req_headers({
            'EsNegocio': contract.negocio_param,
            'IdContrato': contract.id,
            'NIPTitular': contract.title,
            'Orden': contract.orden_param,
            'PlaybackMode': 'Real',
        })
        ok, auth_param = self._get_auth_param(s, contract)
        if not ok:
            return False  # already reported
        if not auth_param:
            return True  # already reported

        ok, resp_filter_form = self._open_n43_filter_form(s, auth_param)
        if not ok:
            return False  # already reported
        date_from, date_to = self.basic_get_n43_dates_for_access()
        self.logger.info('{}: download N43 from {} to {}'.format(
            org_title,
            date_from.strftime('%d/%m/%Y'),
            date_to.strftime('%d/%m/%Y'),
        ))
        ok = self.download_n43_file(
            s,
            resp_filter_form,
            org_title=contract.org_title,
            auth_param=auth_param,
            date_from=date_from,
            date_to=date_to
        )

        if not ok:
            self.is_success = False
            return False

        return True

    def download_n43_file(
            self,
            s: MySession,
            resp_filter_form: Response,
            org_title: str,
            auth_param: str,
            date_from: datetime,
            date_to: datetime) -> bool:

        day_from, month_from, year_from = date_from.strftime('%d/%m/%Y').split('/')
        day_to, month_to, year_to = date_to.strftime('%d/%m/%Y').split('/')
        req_n43_url = "https://www1.ibercajadirecto.com/ibercaja/asp/ModuloDirector.asp?MSCSAuth={}".format(
            auth_param
        )
        req_params = OrderedDict([
            ('IdOperacion', '0076_1'),
            ('Entidad', '2085'),
            ('Canal', 'IBE'),
            ('Dispositivo', 'INTR'),
            ('Idioma', 'ES'),
            ('funcseleccionada', 'DesdeFecha'),
            ('fechainiciodia', day_from),
            ('fechainiciomes', month_from),
            ('fechainicioano', year_from),
            ('fechafindia', day_to),
            ('fechafinmes', month_to),
            ('fechafinano', year_to),
            ('image1.x', '17'),
            ('image1.y', '22')
        ])
        resp_n43_file = s.post(
            req_n43_url,
            data=req_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_filter_form.url,
            }),
            proxies=self.req_proxies
        )

        if 'NO HAY DATOS PARA ESTOS VALORES PEDIDOS' in resp_n43_file.text:
            self.logger.info('{}: no movements from {} to {}'.format(
                org_title,
                date_from.strftime('%d/%m/%Y'),
                date_to.strftime('%d/%m/%Y'),
            ))
            return True

        # 40_resp_filtered_failed_no_account.html/png
        if 'NO EXISTE NINGUNA CUENTA' in resp_n43_file.text:
            self.logger.warning('{}: it looks like N43 downloading is not activated for the contract. '
                                'Pls, ask the customer to activate it. Skip'.format(org_title))
            self.__is_detected_inactive_contract_for_n43 = True
            return True

        if not n43_funcs.validate(resp_n43_file.content):
            self.logger.error("{}: invalid N43. Abort. RESPONSE:\n{}".format(
                org_title,
                resp_n43_file.text
            ))
            return False

        if not n43_funcs.validate_n43_structure(resp_n43_file.text):
            self.logger.warning(
                "{}: N43 file with broken structure detected. Skip. CONTENT:\n{}".format(
                    org_title,
                    resp_n43_file.text
                )
            )
            # Still True to allow download other files, because it's not a scraping error
            return True

        self.n43_contents.append(resp_n43_file.text.encode('UTF-8'))
        self.logger.info('{}: downloaded N43 file'.format(org_title))
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
        self.basic_log_time_spent('GET N43')

        if not self.is_success:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )

        if self.__is_detected_inactive_contract_for_n43:
            return result_codes.WRN_N43_DOWNLOAD_IS_NOT_ACTIVATED, None

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
