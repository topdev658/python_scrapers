import random
import time
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta
from urllib.parse import urljoin

from custom_libs import date_funcs
from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers.abanca_scraper import parse_helpers
from . import parse_helpers_n43
from .abanca_beabanca_scraper import AbancaBeAbancaScraper
from .custom_types import Company, N43FromList

__version__ = '2.1.0'

__changelog__ = """
2.1.0
_open_n43_filter_form: modified req_params to get resp_filter_form
2.0.0
renamed from abanca_n43_scraper to abanca_beabanca_n43_scraper
1.3.0
more attempts to download N43 file
1.2.0
increased delays between failed file downloading attempts
increased default delay
1.1.0
extra small delays between requests
several attempts to download N43 file
1.0.1
use basic_scrape_for_n43
1.0.0
stable
0.4.0
process_access_for_n43
process_company_for_n43
removed process_account (not used)
upd main
0.3.0
add open_ficheros
0.2.0
add processAccount
add folder dev_n43: 
0.1.0
mainResult, is logged
init
"""

# En estos momentos no se puede realizar la operación solicitada.
# Reinténtelo en unos minutos y, si persiste el error, póngase en contacto con el servicio de Atención al cliente.
TEMP_ERR_MARKER = 'estos momentos no se puede realizar'


class AbancaBeAbancaN43Scraper(AbancaBeAbancaScraper):
    fin_entity_name = 'ABANCA'
    scraper_name = "AbancaBeAbancaN43Scraper"

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.is_success = True

    def _delay(self):
        """Some small delay"""
        time.sleep(0.3 * (1 + random.random()))

    def _n43_from_list_str(self, n43_from_list: N43FromList) -> str:
        n43_from_list_str = "{} (created {})".format(
            n43_from_list.descr,
            n43_from_list.date.strftime('%d/%m/%Y')
        )
        return n43_from_list_str

    def _open_ficheros_page(self, s: MySession, resp_prev: Response) -> Response:
        """ Open Ficheros page from top menu"""
        resp_ficheros = s.get(
            'https://be.abanca.com/BEPRJ001/jsp/app.faces?_flowId=BEPR_ficheros_CON-flow',
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        return resp_ficheros

    def _open_n43_filter_form(
            self,
            s: MySession,
            resp_prev: Response) -> Response:
        """Opens 'Consultar ficheros recibidos' from left menu"""
        self._delay()

        view_state_param = parse_helpers.get_view_state_param(resp_prev.text)
        req_url = 'https://be.abanca.com/BEPRJ001/jsp/BEPR_ficherosEspana.faces'

        req_params = OrderedDict([
            ('formMenu:_idJsp343selectedItemName', 'Ficheros_0196_R'),
            ('panelMenuStateformMenu:_idJsp371', 'opened'),
            ('panelMenuActionformMenu:_idJsp371', 'formMenu:Ficheros_0196_R'),
            ('panelMenuActionformMenu:Ficheros_0197', ''),
            ('panelMenuActionformMenu:Ficheros_0187', ''),
            ('panelMenuActionformMenu:Ficheros_0195', ''),
            ('panelMenuActionformMenu:Ficheros_0196_E', ''),
            ('panelMenuActionformMenu:Ficheros_0196_R', ''),
            ('panelMenuActionformMenu:Ficheros_0422', ''),
            ('panelMenuActionformMenu:Ficheros_0552', ''),
            ('panelMenuStateformMenu:_idJsp373', ''),
            ('panelMenuActionformMenu:_idJsp373', ''),
            ('panelMenuActionformMenu:Ficheros_0623', ''),
            ('panelMenuActionformMenu:Ficheros_0624', ''),
            ('panelMenuActionformMenu:Ficheros_0625', ''),
            ('panelMenuActionformMenu:Ficheros_0626', ''),
            ('panelMenuActionformMenu:Ficheros_0627', ''),
            ('panelMenuActionformMenu:Ficheros_0628', ''),
            ('panelMenuActionformMenu:Ficheros_0572', ''),
            ('panelMenuStateformMenu:_idJsp374', ''),
            ('panelMenuActionformMenu:_idJsp374', ''),
            ('panelMenuActionformMenu:Ficheros_0629', ''),
            ('panelMenuActionformMenu:Ficheros_0630', ''),
            ('panelMenuActionformMenu:Ficheros_0631', ''),
            ('panelMenuStateformMenu:_idJsp375', ''),
            ('panelMenuActionformMenu:_idJsp375', ''),
            ('panelMenuActionformMenu:Ficheros_0643_CON', ''),
            ('panelMenuStateformMenu:_idJsp378', ''),
            ('panelMenuActionformMenu:_idJsp378', ''),
            ('panelMenuActionformMenu:Ficheros_0187I', ''),
            ('formMenu_SUBMIT', '1'),
            ('javax.faces.ViewState', view_state_param)
        ])

        resp_n43_filter_form = s.post(
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return resp_n43_filter_form

    def _click_select_extractos_q43(
            self,
            s: MySession,
            resp_prev: Response,
            company_param: str) -> Response:
        self._delay()

        view_state_param = parse_helpers.get_view_state_param(resp_prev.text)
        today_param = date_funcs.today().strftime('%m/%Y')  # 07/2021
        req_url = 'https://be.abanca.com/BEPRJ001/jsp/BEPR_ficherosEspanaConsultar_LST.faces?javax.portlet.faces.DirectLink=true'
        req_params = OrderedDict([
            ('AJAXREQUEST', '_viewRoot'),
            ('formBusqueda:panelAyudaOpenedState', ''),
            ('formBusqueda:panelListadoFicherosOpenedState', ''),
            ('formBusqueda:idTipoFicheroCon', 'NORM43'),
            ('formBusqueda:idEmpresaCon', company_param),  # '10744630'
            ('formBusqueda:idEstadoFicheroCon', ' '),
            ('formBusqueda:idMedioEnvioCon', ' '),
            ('formBusqueda:idOpcionFechasCon', 'U'),
            ('formBusqueda:idUltimosNDiasCon', '7'),
            ('formBusqueda:idFechaDesdeConInputDate', ''),
            ('formBusqueda:idFechaDesdeConInputCurrentDate', today_param),
            ('formBusqueda:idFechaHastaConInputDate', ''),
            ('formBusqueda:idFechaHastaConInputCurrentDate', today_param),
            ('formBusqueda:idImporteMinimoCon', ''),
            ('formBusqueda:idImporteMaximoCon', ''),
            ('formBusqueda_SUBMIT', '1'),
            ('formBusqueda:_link_hidden_', ''),
            ('formBusqueda:_idcl', ''),
            ('javax.faces.ViewState', view_state_param),
            ('formBusqueda:supportidTipoFicheroCon', 'formBusqueda:supportidTipoFicheroCon')
        ])
        resp_extractos_q43 = s.post(
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        return resp_extractos_q43

    def _click_select_interval(
            self,
            s: MySession,
            resp_prev: Response,
            company_param: str) -> Response:
        view_state_param = parse_helpers.get_view_state_param(resp_prev.text)
        today_param = date_funcs.today().strftime('%m/%Y')  # 07/2021
        req_url = 'https://be.abanca.com/BEPRJ001/jsp/BEPR_ficherosEspanaConsultar_LST.faces?javax.portlet.faces.DirectLink=true'
        req_params = OrderedDict([
            ('AJAXREQUEST', '_viewRoot'),
            ('formBusqueda:panelAyudaOpenedState', ''),
            ('formBusqueda:panelListadoFicherosOpenedState', ''),
            ('formBusqueda:tablaListaFicheros__hiddenSelected', ''),
            ('formBusqueda:tablaListaFicheros__hiddenDeselected', ''),
            ('formBusqueda:tablaListaFicheros_tablaSeleccion', ''),
            ('formBusqueda:idTipoFicheroCon', 'NORM43'),
            ('formBusqueda:idEmpresaCon', company_param),  # '10744630'
            ('formBusqueda:idEstadoFicheroCon', ' '),
            ('formBusqueda:idMedioEnvioCon', ' '),
            ('formBusqueda:idUltimosNDiasCon', '7'),
            ('formBusqueda:idOpcionFechasCon', 'F'),
            ('formBusqueda:idFechaDesdeConInputDate', ''),
            ('formBusqueda:idFechaDesdeConInputCurrentDate', today_param),
            ('formBusqueda:idFechaHastaConInputDate', ''),
            ('formBusqueda:idFechaHastaConInputCurrentDate', today_param),
            ('formBusqueda:idImporteMinimoCon', ''),
            ('formBusqueda:idImporteMaximoCon', ''),
            ('formBusqueda_SUBMIT', '1'),
            ('formBusqueda:_link_hidden_', ''),
            ('formBusqueda:_idcl', ''),
            ('javax.faces.ViewState', view_state_param),
            ('formBusqueda:supportidOpcionFechasCon',
             'formBusqueda:supportidOpcionFechasCon')
        ])
        resp_selected_interval = s.post(
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        return resp_selected_interval

    def _submit_n43_filter_form(
            self,
            s: MySession,
            resp_prev: Response,
            company_param: str,
            date_from: datetime,
            date_to: datetime) -> Response:
        self._delay()

        view_state_param = parse_helpers.get_view_state_param(resp_prev.text)
        req_filter_form_url = "https://be.abanca.com/BEPRJ001/jsp/BEPR_ficherosEspanaConsultar_LST.faces"

        req_params = OrderedDict([
            ('formBusqueda:panelAyudaOpenedState', ''),
            ('formBusqueda:panelListadoFicherosOpenedState', ''),
            ('formBusqueda:tablaListaFicheros__hiddenSelected', ''),
            ('formBusqueda:tablaListaFicheros__hiddenDeselected', ''),
            ('formBusqueda:tablaListaFicheros_tablaSeleccion', ''),
            ('formBusqueda:idTipoFicheroCon', 'NORM43'),
            ('formBusqueda:idEmpresaCon', company_param),  # '10744630'
            ('formBusqueda:idEstadoFicheroCon', ' '),
            ('formBusqueda:idMedioEnvioCon', ' '),
            ('formBusqueda:idOpcionFechasCon', 'F'),
            ('formBusqueda:idFechaDesdeConInputDate', date_from.strftime('%d-%m-%Y')),  # '01-06-2021'
            ('formBusqueda:idFechaDesdeConInputCurrentDate', date_from.strftime('%d/%Y')),  # '06/2021'
            ('formBusqueda:idFechaHastaConInputDate', date_to.strftime('%d-%m-%Y')),  # '30-07-2021'
            ('formBusqueda:idFechaHastaConInputCurrentDate', date_to.strftime('%d/%Y')),  # '07/2021'
            ('formBusqueda:idImporteMinimoCon', ''),
            ('formBusqueda:idImporteMaximoCon', ''),
            ('formBusqueda:btnConsultar', 'Consultar'),
            ('formBusqueda_SUBMIT', '1'),
            ('formBusqueda:_link_hidden_', ''),
            ('formBusqueda:_idcl', ''),
            ('javax.faces.ViewState', view_state_param)
        ])

        resp_n43_filtered = s.post(
            req_filter_form_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )
        return resp_n43_filtered

    def _click_next_page(
            self,
            s: MySession,
            resp_prev: Response,
            company_param: str,
            date_from: datetime,
            date_to: datetime) -> Response:
        self._delay()

        view_state_param = parse_helpers.get_view_state_param(resp_prev.text)
        req_next_page_url = ("https://be.abanca.com/BEPRJ001/jsp/BEPR_ficherosEspanaConsultar_LST.faces?"
                             "javax.portlet.faces.DirectLink=true")

        req_params = OrderedDict([
            ('AJAXREQUEST', '_viewRoot'),
            ('formBusqueda:panelAyudaOpenedState', ''),
            ('formBusqueda:panelListadoFicherosOpenedState', ''),
            ('formBusqueda:idTipoFicheroCon', 'NORM43'),
            ('formBusqueda:idEmpresaCon', company_param),  # '10744630'
            ('formBusqueda:idEstadoFicheroCon', ' '),
            ('formBusqueda:idMedioEnvioCon', ' '),
            # ('formBusqueda:idUltimosNDiasCon', '7'),
            ('formBusqueda:idOpcionFechasCon', 'F'),
            ('formBusqueda:idFechaDesdeConInputDate', date_from.strftime('%d-%m-%Y')),  # '01-06-2021'
            ('formBusqueda:idFechaDesdeConInputCurrentDate', date_from.strftime('%d/%Y')),  # '06/2021'
            ('formBusqueda:idFechaHastaConInputDate', date_to.strftime('%d-%m-%Y')),  # '30-07-2021'
            ('formBusqueda:idFechaHastaConInputCurrentDate', date_to.strftime('%d/%Y')),  # '07/2021'
            # removed file-related params (see dev_n43/5_open_next_page)
            ('formBusqueda:idImporteMinimoCon', ''),
            ('formBusqueda:idImporteMaximoCon', ''),
            ('formBusqueda:transicion', 'ev_ToAccion'),
            ('formBusqueda_SUBMIT', '1'),
            ('formBusqueda:_link_hidden_', ''),
            ('formBusqueda:_idcl', ''),
            ('javax.faces.ViewState', view_state_param),
            ('formBusqueda:sDataFicheros', 'fastforward')
        ])

        resp_n43_filtered_i = s.post(
            req_next_page_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )
        return resp_n43_filtered_i

    def process_access_for_n43(
            self,
            s: MySession,
            resp_logged_in: Response) -> bool:

        companies, req_params, req_url = self._get_companies(resp_logged_in)

        is_multicontract = bool(companies)
        self.logger.info('Is multicontract: {}'.format(is_multicontract))
        ok = True

        # several contracts
        if is_multicontract:
            # iterate over len of companies, each company param could be redefined
            # when logged in again
            for company in companies:
                ok = self.process_company_for_n43(s, resp_logged_in, company, is_multicontract=True)
                if not ok:
                    break
        # one contract
        else:
            company = self._default_company()
            s, resp_company_selected_loaded = self._load_position_global_page_details(
                s,
                company.title,
                resp_logged_in.text
            )
            ok = self.process_company_for_n43(
                s,
                resp_company_selected_loaded,
                company,
                is_multicontract=False
            )

        return ok

    def process_company_for_n43(
            self,
            s: MySession,
            resp_logged_in: Response,
            company: Company,
            is_multicontract: bool) -> bool:
        if is_multicontract:
            ok, s, resp_comp_selected, company, _ = self._open_resp_company_selected(company)
            # not logged in - return empty list of accounts
            # then they will be marked as scraped by state resetter
            if not ok:
                return False
        else:
            resp_comp_selected = resp_logged_in

        # Similar to Kutxa: today's file contains movements from yesterday
        date_to = date_funcs.today()
        date_from = (
            self.last_successful_n43_download_dt + timedelta(days=1)
            if self.last_successful_n43_download_dt
            else date_funcs.today() - timedelta(days=project_settings.DOWNLOAD_N43_OFFSET_DAYS_INITIAL)
        )

        self.logger.info('{}: date_from={}, date_to={}'.format(
            company.title,
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        ))

        resp_ficheros = self._open_ficheros_page(s, resp_comp_selected)
        resp_filter_form = self._open_n43_filter_form(s, resp_ficheros)
        ok, company_param = parse_helpers_n43.get_id_empresa_con_param(resp_filter_form.text)
        if not ok:
            self.basic_log_wrong_layout(
                resp_filter_form,
                "Can't extract company_param for {}. Abort".format(company)
            )
            return False
        resp_selected_extactos_q43 = self._click_select_extractos_q43(s, resp_filter_form, company_param)
        resp_selected_interval = self._click_select_interval(s, resp_selected_extactos_q43, company_param)
        resp_prev = resp_selected_interval
        for page_ix in range(1, 100):
            self.logger.info('{}: page #{}: download N43s'.format(
                company.title,
                page_ix
            ))
            if page_ix == 1:
                resp_n43_filtered_i = self._submit_n43_filter_form(
                    s,
                    resp_prev,
                    company_param,
                    date_from,
                    date_to
                )
            else:
                resp_n43_filtered_i = self._click_next_page(
                    s,
                    resp_prev,
                    company_param,
                    date_from,
                    date_to
                )

            n43s_from_list = parse_helpers_n43.get_n43s_from_list(resp_n43_filtered_i.text)
            for n43_from_list in n43s_from_list:
                # Serial downloading
                ok = self.download_n43_file(
                    s,
                    resp_n43_filtered_i,
                    company,
                    n43_from_list
                )
                if not ok:
                    return False

            has_more_pages = "{'page': 'fastforward'}" in resp_n43_filtered_i.text
            if not has_more_pages:
                self.logger.info('{}: no more pages with N43 files'.format(company.title))
                break
            resp_prev = resp_n43_filtered_i

        return True

    def download_n43_file(
            self,
            s: MySession,
            _resp_prev: Response,
            company: Company,
            n43_from_list: N43FromList) -> bool:

        n43_from_list_str = self._n43_from_list_str(n43_from_list)
        if not n43_from_list.link:
            self.logger.error('{}: {}: no link to file. Abort'.format(company.title, n43_from_list_str))
            return False

        n43_url = urljoin('https://be.abanca.com/', n43_from_list.link)

        try:
            resp_n43_file = Response()
            for att in range(1, 6):
                self.logger.info('{}: att #{}: download N43 file: {}'.format(
                    company.title,
                    att,
                    n43_from_list_str
                ))
                self._delay()
                resp_n43_file = s.get(
                    n43_url,
                    headers=self.req_headers,
                    proxies=self.req_proxies
                )

                if TEMP_ERR_MARKER not in resp_n43_file.text:
                    break

                # Before next attempts
                time.sleep(att * (5 + random.random()))

            n43_text = resp_n43_file.text
            n43_content = n43_text.encode('UTF-8')

            if not n43_funcs.validate(n43_content):
                self.basic_log_wrong_layout(
                    resp_n43_file,
                    "{}: {}: got invalid resp_n43. Abort".format(
                        company.title,
                        n43_from_list_str
                    )
                )
                return False

            if not n43_funcs.validate_n43_structure(n43_text):
                self.logger.warning(
                    "{}: {}: N43 file with broken structure detected. Skip. CONTENT:\n{}".format(
                        company.title,
                        n43_from_list_str,
                        resp_n43_file.text
                    )
                )
                # Still True to allow download other files, because it's not a scraping error
                return True

            self.n43_contents.append(n43_content)
            self.logger.info('{}: downloaded N43 file: {}'.format(
                company.title,
                n43_from_list_str
            ))
            return True

        except Exception as _e:
            self.logger.error(
                "{}: {}: can't download. Abort. HANDLED EXCEPTION: {}".format(
                    company.title,
                    n43_from_list_str,
                    traceback.format_exc()
                )
            )
            return False

    def main(self) -> MainResult:
        self.logger.info('main: started')

        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp_logged_in.url, resp_logged_in.text, reason)

        ok = self.process_access_for_n43(s, resp_logged_in)
        self.basic_log_time_spent('GET N43 FILES')

        if not ok:
            return self.basic_result_common_scraping_error()

        # DESC -> ASC
        self.n43_contents.reverse()

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )
        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
