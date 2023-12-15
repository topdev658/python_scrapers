import hashlib
import random
import time
from datetime import datetime, timedelta
from typing import List, Tuple

from custom_libs import date_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult, MovementTPV
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers_tpv

__version__ = '1.3.0'
__changelog__ = """
1.3.0
upd TEMPLATE_HASH (now for 202109)
_get_date_from_for_tpv: max allowed offset for incremental scraping = 30 days
upd log msg
1.2.0
new approved TEMPLATE_HASH (due to changed web page template)
1.1.0
pagination: don't change psistFinCont, psistInicioCont params 
1.0.0
init
"""

WRONG_CREDENTIALS_MARKERS = [
    # For both: wrong username or password
    'El usuario no existe',
]

# buscar-operaciones_202109.html
TEMPLATE_HASH = '21dfe9445726483a90c7aaa363a37fc7'


class RedsysTPVScraper(BasicScraper):
    """Extracts movements and saves into _TesoraliaTPV table.
    See 'dev/Requisitos Funcionales Movimientos de Tarjeta RedSys v.1.0 ENGLISH VERSION.docx'
    """
    scraper_name = 'RedsysTPVScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    def _save_movs_tpv(self, company_no: str, movs_tpv_asc: List[MovementTPV]) -> bool:
        self.logger.info('Company {}: save movements_tpv_asc'.format(company_no))
        if project_settings.IS_UPDATE_DB:
            self.db_connector.save_movements_tpv(company_no, movs_tpv_asc)
        return True

    def _get_date_from_for_tpv(self, company_no: str) -> datetime:
        movement_tpv_last_opt = self.db_connector.get_last_saved_movement_tpv(company_no)
        if movement_tpv_last_opt is not None and not self.date_from_param_str:
            # -1 day of the last saved movement's date
            # Also, handle case if scraping didn't work for some time,
            # in this case use max offset 30 days (fin entity restriction)
            date_from = max(date_funcs.today() - timedelta(days=30), movement_tpv_last_opt.Fecha - timedelta(days=1))
            return date_from

        # similar approach as for correspondence
        date_from_if_new, _ = self.basic_get_date_from_for_correspondence(
            offset=1,  # 1 day
            max_offset=30  # 1 month
        )

        return date_from_if_new

    def validate_template(self, s: MySession) -> bool:
        resp_template = s.get(
            'https://canales.redsys.es/admincanales-web/static/partials/nuevasoperaciones/buscar-operaciones.html',
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        checksum = hashlib.md5(resp_template.content).hexdigest()
        ok = checksum == TEMPLATE_HASH
        if not ok:
            self.basic_log_wrong_layout(
                resp_template,
                "Updated template detected. Please, check the logic for the required fields"
            )
        return ok

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()

        # To get cookies
        _resp_init = s.get(
            'https://canales.redsys.es/admincanales-web/index.jsp#/login',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_login_params = {
            'username': self.username,
            'password': self.userpass
        }
        resp_logged_in = s.post(
            'https://canales.redsys.es/admincanales-web/services/usuarios/login',
            json=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = 'token' in resp_logged_in.text
        is_credentials_error = any(m in resp_logged_in.text for m in WRONG_CREDENTIALS_MARKERS)

        return s, resp_logged_in, is_logged, is_credentials_error, ''

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        resp_logged_in_json = resp_logged_in.json()
        auth_token = resp_logged_in_json['token']  # type: str
        # "comercios": ["336083456"]
        company_nos = resp_logged_in_json['comercios']  # type: List[str]
        self.logger.info('Got {} companies: {}'.format(len(company_nos), company_nos))
        for company_no in company_nos:
            auth_token = self.process_company(s, auth_token, company_no)
        return True

    def process_company(self, s: MySession, auth_token: str, company_no: str) -> str:
        date_from = self._get_date_from_for_tpv(company_no)
        date_to = date_funcs.today()

        self.logger.info('Process company {}: dates from {} to {}'.format(
            company_no,
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        ))

        date_fmt = '%Y-%m-%d'
        req_movs_params = {
            "comercio": company_no,
            "terminal": "",
            "fechaDesde": date_from.strftime(date_fmt),  # "2021-03-11"
            "fechaHasta": date_to.strftime(date_fmt),  # "2021-03-12"
            "horaDesde": "00:00:00.000000",
            "horaHasta": "23:59:59.999999",
            "laOpcion": "1",
            "marcaTarjeta": -2,
            "tarjeta": "",
            "importe": "",
            "importeMin": "",
            "importeMax": "",
            "estado": "T",
            "tipo": [""],
            "descripcion": "",
            "formaPago": "",
            "ip": "",
            "numeroPedido": "",
            "referencia": "",
            "idRegla": "",
            "accionRegla": "",
            "codError": "",
            "direccion": "0",  # ASC, 1st page
            "filasEnPantalla": "100",  # movs per page
            "paginaActual": 0,
            "psistInicio": "2000-01-01-00.00.00.000000",
            "psistFin": "2999-12-31-23.59.59.999999",
            "psistInicioCont": "2000-01-01-00.00.00.000000",
            "psistFinCont": "2999-12-31-23.59.59.999999"
        }

        # 20_resp_movs.json
        # numPagina	0
        # totalPaginas	4
        movs_tpv_asc = []  # type: List[MovementTPV]
        for page_ix in range(50):  # to avoid inf loop
            self.logger.info('Company {}: page #{}: get movements'.format(company_no, page_ix + 1))
            req_movs_params['paginaActual'] = page_ix
            resp_movs = s.post(
                'https://canales.redsys.es/admincanales-web/services/operaciones/new/consulta',
                json=req_movs_params,
                headers=self.basic_req_headers_updated({
                    'admincanales-auth-token': auth_token,
                }),
                proxies=self.req_proxies
            )

            resp_movs_json = resp_movs.json()
            movs_tpv_i = parse_helpers_tpv.get_movements_tpv(resp_movs_json, company_no)
            movs_tpv_asc.extend(movs_tpv_i)

            # numPagina=0 for 1st page
            has_more_movs = resp_movs_json['totalPaginas'] - resp_movs_json['numPagina'] > 1
            if not has_more_movs:
                self.logger.info('Company {}: no more movements'.format(company_no))
                break
            time.sleep(0.5 + random.random())
            # next page params parsed from the current page
            # "2021-03-10-17.31.09.148"
            req_movs_params['psistInicio'] = resp_movs_json['contenido'][0][
                'fechaOperacion']  # 1st mov date from this page
            req_movs_params['psistFin'] = resp_movs_json['contenido'][-1][
                'fechaOperacion']  # last mov date from this page
            # after 1st page
            req_movs_params['direccion'] = '1'
            req_movs_params['filasEnPantalla'] = 100
            # req_movs_params['psistFinCont'] = ""
            # req_movs_params['psistInicioCont'] = ""

        self.logger.info('Company {}: got {} movements: {}'.format(company_no, len(movs_tpv_asc), movs_tpv_asc))

        self._save_movs_tpv(company_no, movs_tpv_asc)

        return auth_token  # can be changed?

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

        ok = self.validate_template(s)
        if not ok:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None  # already reported

        self.process_access(s, resp_logged_in)

        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.main()
