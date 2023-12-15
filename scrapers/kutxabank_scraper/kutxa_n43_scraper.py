import random
import time
import traceback
from datetime import timedelta
from typing import List, Tuple

from custom_libs import date_funcs
from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from . import parse_helpers_n43
from .custom_types import CompanyForN43, N43FromList
from .kutxa_scraper import KutxaScraper

__version__ = '1.5.0'
__changelog__ = """
1.5.0
process_n43_files: extracted n43 file processing to be called from users and no users scenarios
process_company_for_n43: call to process_n43_files inside a selected user
process_access_for_n43: call to process_n43_files when there is no user to be selected
1.4.0
use parse_helpers_n43.get_n43s_from_list__table_tag
    parse_helpers_n43.get_n43s_from_list__tr_tags
    parse_helpers_n43.get_n43s_from_list__incremental_updates
download_n43_file: check for already downloaded contents
1.3.0
upd reqs
process_company_for_n43: more cases:
    'no files' for several companies
    any default company 
use parse_helpers_n43.get_n43s_from_list_updates
1.2.0
date_to = today because the publishing date (Fecha envio) is used
  while target content date = publishing date - 1
date_from = last_success_date + 1 day (the same reason)
1.1.0
check for file type when filtering n43s_to_download (see explanation there)
1.0.0
stable
0.1.0
init
"""

NO_N43_FILES_MARKER = 'No tiene ficheros pendientes de recepci'
HAS_N43_FILES_MARKER = 'formFicherosBuzon:datosBuzon'
HAS_COMPANIES_MARKER = 'formBuzonSeleccion:usuarios'


class KutxaN43Scraper(KutxaScraper):
    """Opposite to web browser, the scraper doesn't mark
    already downloaded files as 'downloaded',
    thus they are still 'pending' all the time.
    """

    fin_entity_name = 'KUTXA'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        # Tricky case:
        # during receiving updates if 2 companies one by one have no N43 files
        # then only 1st will receive 'no files' marker in updates.
        # Thus, to be sure about valid layout, the 2nd one must use this flag from the previous
        # company + extra checks (see process_company_for_n43)
        # 20_resp_recepcion_updates_nofiles.xml
        # 20_resp_recepcion_updates_nofiles_again.xml
        self.company_has_no_files_detected = False

    def _n43_from_list_str(self, n43_from_list: N43FromList, file_ix: int) -> str:
        n43_from_list_str = "file #{} '{}' (created {})".format(
            file_ix,
            n43_from_list.descr,
            n43_from_list.date.strftime('%d/%m/%Y')
        )
        return n43_from_list_str

    def process_access_for_n43(self, s: MySession, resp_logged_in: Response) -> bool:
        resp_ficheros = self._open_ficheros_page(s, resp_logged_in)
        resp_recepcion = self._switch_to_recepcion_tab(s, resp_ficheros)
        companies_for_n43 = parse_helpers_n43.get_companies_for_n43_from_recepcion_tab(resp_recepcion.text)
        self.logger.info('Got {} companies for N43: {}'.format(
            len(companies_for_n43),
            companies_for_n43
        ))
        # Serial
        n43s_from_list = []  # type: List[N43FromList]
        if len(companies_for_n43) > 0:
            for ix, company_for_n43 in enumerate(companies_for_n43):
                ok, n43s_from_list = self.process_company_for_n43(
                    s,
                    resp_recepcion,
                    company_for_n43,
                    ix,
                    n43s_from_list
                )
                if not ok:
                    return False
            return True
        else:
            # There is a case in which no users appear in the banking section 'Reception',
            # so contracts were not being processed (20_resp_recepcion_without_users.html)
            company_title = parse_helpers_n43.get_single_company_title(resp_recepcion.text)
            ok, n43s_from_list = self.process_n43_files(s, resp_recepcion, resp_recepcion, company_title, n43s_from_list)
            if not ok:
                return False
            return True

    def _open_ficheros_page(self, s: MySession, resp_prev: Response) -> Response:
        ice_session_id = self._get_ice_session_id(resp_prev)

        optional_data = {
            'ice.submit.partial': 'false',
            'ice.event.target': 'formMenuLateral:j_id2302',
            'ice.event.captured': 'formMenuLateral:lateralFicheros',
            'formMenuLateral': 'formMenuLateral',
            'formMenuLateral:_idcl': 'formMenuLateral:lateralFicheros',
            'javax.faces.RenderKitId': 'ICEfacesRenderKit',
            'ice.focus': 'formMenuLateral:lateralFicheros',
        }

        _resp_senv_recv_updated = self._send_receive_updates(s, ice_session_id, optional_data)
        _resp_disp_views = self._dispose_views(s, ice_session_id)
        resp_ficheros = s.get(
            self._url('/NASApp/BesaideNet2/pages/ficheros/ficheros_situacion.iface'),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return resp_ficheros

    def _switch_to_recepcion_tab(self, s: MySession, resp_ficheros: Response):
        ice_session_id = self._get_ice_session_id(resp_ficheros)
        optional_data = {
            'ice.submit.partial': 'false',
            'ice.event.target': 'formMenuAcciones:PanelAcciones:1:Accion',
            'ice.event.captured': 'formMenuAcciones:PanelAcciones:1:Accion',
            'formMenuAcciones': 'formMenuAcciones',
            'formMenuAcciones:_idcl': 'formMenuAcciones:PanelAcciones:1:Accion',
            'javax.faces.RenderKitId': 'ICEfacesRenderKit',
            'ice.focus': 'formMenuAcciones:PanelAcciones:1:Accion',
        }
        _resp_senv_recv_updated = self._send_receive_updates(s, ice_session_id, optional_data)
        _resp_disp_views = self._dispose_views(s, ice_session_id)
        # See 20_resp_recepcion__32255_lorena.html
        resp_recepcion = s.get(
            self._url('/NASApp/BesaideNet2/pages/ficheros/ficheros_buzon_detalle.iface'),
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return resp_recepcion

    def _select_n43_company_from_recepcion(
            self,
            s: MySession,
            resp_recepcion: Response,
            company: CompanyForN43) -> Response:
        """Selects a user/company in 'Seleccione el usuario' section on Recepcion tab"""
        self.logger.info('{}: select N43 company from recepcion tab'.format(
            company.title
        ))
        ice_session_id = self._get_ice_session_id(resp_recepcion)
        optional_data = {
            'ice.submit.partial': 'false',  # 'false' not working.. - always partial
            'ice.event.target': company.selection_value,  # 'formBuzonSeleccion:usuarios:_1'
            'ice.event.captured': company.selection_value,
            'formBuzonSeleccion': 'formBuzonSeleccion',  # formBuzonSeleccion
            'icefacesCssUpdates': '',
            'javax.faces.ViewState': '1',
            'javax.faces.RenderKitId': '',
            'formBuzonSeleccion:usuarios': company.input_value,  # '02'
            'ice.focus': company.selection_value,
        }
        resp_senv_recv_updated = self._send_receive_updates(s, ice_session_id, optional_data)
        return resp_senv_recv_updated

    def _validate_selected_company_for_n43(
            self,
            resp_company_selected: Response,
            company: CompanyForN43) -> bool:
        sel_value = parse_helpers_n43.get_selected_company_for_n43_selection_value(resp_company_selected.text)
        if sel_value != company.selection_value:
            self.basic_log_wrong_layout(
                resp_company_selected,
                "Can't select company for N43: {}".format(company)
            )
            return False
        return True

    def process_company_for_n43(
            self,
            s: MySession,
            resp_recepcion: Response,
            company: CompanyForN43,
            comp_ix: int,
            n43s_from_list_prev: List[N43FromList]) -> Tuple[bool, List[N43FromList]]:

        self.logger.info('{}: process company for N43'.format(company.title))
        # Each time compare target company and selected by default
        # (selected can be any, not only 1st in the list)
        resp_company_selected = resp_recepcion
        sel_value = parse_helpers_n43.get_selected_company_for_n43_selection_value(resp_company_selected.text)
        if sel_value != company.selection_value or comp_ix > 0:
            resp_company_selected = self._select_n43_company_from_recepcion(
                s,
                resp_recepcion,
                company
            )
        if not self._validate_selected_company_for_n43(resp_company_selected, company):
            return False, []  # already reported

        # 'No tiene ficheros pendientes de recepción.'
        if (NO_N43_FILES_MARKER in resp_company_selected.text  # 1st case
                or (  # 2nd case just after 1st: NO_N43_FILES_MARKER is not present but still valid layout
                        HAS_COMPANIES_MARKER in resp_company_selected.text
                        and HAS_N43_FILES_MARKER not in resp_company_selected.text
                        and self.company_has_no_files_detected  # previous company detection
                )):
            self.logger.info("{}: 'no N43 files' marker detected. Skip".format(company.title))
            self.company_has_no_files_detected = True
            return True, []
        else:
            self.company_has_no_files_detected = False

        ok, n43s_from_list = self.process_n43_files(s, resp_recepcion, resp_company_selected, company.title, n43s_from_list_prev)
        return ok, n43s_from_list

    def process_n43_files(
            self,
            s: MySession,
            resp_recepcion: Response,
            resp_company_selected: Response,
            company_title: str,
            n43s_from_list_prev: List[N43FromList]) -> Tuple[bool, List[N43FromList]]:

        # WAS:
        # Similar to BBVA or CAIXA incremental download logic
        # Calc like in basic_get_n43_dates_and_account_status
        # Examples:
        # 11.06 (Fri) - first run: date_from=today-90 days, date_to=10.06
        # 12.06 (Sat) - date_from=11.06, date_to=11.06
        # 13.06 (Sun) - no executions (or failure)
        # 14.06 (Mon) - date_from 12.06, date_to 13.06

        # NOW:
        # The difference: Usual approach is to set
        # date_to = date_funcs.today() - 1 day,
        # Kutxa N43's content date == Kutxa N43's publishing date - 1 day,
        # This means that doc with 11.06 content date has 12.06 publishing date,
        # So date_to by publishing date = today is the same as
        # date_to by content date = today - 1 day
        # Examples:
        # 11.06 (Fri) - first run: date_from=today-90 days, date_to=11.06
        # 12.06 (Sat) - date_from=12.06, date_to=12.06
        # 13.06 (Sun) - no executions (or failure)
        # 14.06 (Mon) - date_from 13.06, date_to 14.06
        date_to = date_funcs.today()  # by publishing date (Fecha Envio)
        date_from = (
            self.last_successful_n43_download_dt + timedelta(days=1)
            if self.last_successful_n43_download_dt
            else date_funcs.today() - timedelta(days=project_settings.DOWNLOAD_N43_OFFSET_DAYS_INITIAL)
        )

        self.logger.info('{}: date_from={}, date_to={}'.format(
            company_title,
            date_from.date(),
            date_to.date()
        ))

        n43s_from_list = (
                parse_helpers_n43.get_n43s_from_list__table_tag(resp_company_selected.text)
                or parse_helpers_n43.get_n43s_from_list__tr_tags(resp_company_selected.text)
                # try to get also from recepcion html (see 20_resp_recepcion__32255_lorena.html)
                # because resp_company_selected (send-receive-update) may not contain full info about n43s
                or parse_helpers_n43.get_n43s_from_list__table_tag(resp_recepcion.text)
                or parse_helpers_n43.get_n43s_from_list__incremental_updates(resp_company_selected.text,
                                                                             n43s_from_list_prev)
        )

        if not n43s_from_list:
            self.basic_log_wrong_layout(
                resp_company_selected,
                "{}: expected but didn't extract n43s_from_list".format(
                    company_title,
                )
            )
            return False, []

        # Also, check for file type here (it was in parse_helpers_n43)
        # to avoid false-positive "expected but didn't extract" on prev step
        # if there are only non-AEB-N43 files
        n43s_to_download = [
            f for f in n43s_from_list
            if (date_from.date() <= f.date <= date_to.date()) and f.type == 'AEB-43'
        ]
        n43s_to_download.reverse()  # to asc

        self.logger.info('{}: got N43 file(s): total {}, to download {}'.format(
            company_title,
            len(n43s_from_list),
            len(n43s_to_download)
        ))

        # resp_company_selected may not contain ice_session
        ice_session_id = self._get_ice_session_id(resp_company_selected) or self._get_ice_session_id(resp_recepcion)
        for comp_ix, n43_from_list in enumerate(n43s_to_download):
            ok = self.download_n43_file(
                s,
                ice_session_id,
                company_title,
                n43_from_list,
                comp_ix
            )
            if not ok:
                return False, []
            time.sleep(0.1 * (1 + random.random()))

        time.sleep(0.5 + random.random())
        return True, n43s_from_list

    def download_n43_file(
            self,
            s: MySession,
            ice_session_id: str,
            company_title: str,
            n43_from_list: N43FromList,
            file_ix: int) -> bool:

        n43_from_list_str = self._n43_from_list_str(n43_from_list, file_ix)

        try:
            self.logger.info('{}: download N43: {}'.format(company_title, n43_from_list_str))
            # 1st step
            optional_data = {
                'ice.submit.partial': 'false',
                'ice.event.target': n43_from_list.req_param,  # 'formFicherosBuzon:datosBuzon:0:link_descargar'
                'ice.event.captured': n43_from_list.req_param,
                'formFicherosBuzon': 'formFicherosBuzon',
                'javax.faces.ViewState': '1',
                'javax.faces.RenderKitId': 'ICEfacesRenderKit',
                'formFicherosBuzon:_idcl': n43_from_list.req_param,
                'ice.focus': n43_from_list.req_param,
            }
            resp_senv_recv_updated = self._send_receive_updates(s, ice_session_id, optional_data)
            _resp_disp_views = self._dispose_views(s, ice_session_id)

            req_file_link = parse_helpers_n43.get_n43_file_link(resp_senv_recv_updated.text)
            if not req_file_link:
                self.basic_log_wrong_layout(
                    resp_senv_recv_updated,
                    "{}: {}: can't get req_file_link. Abort".format(
                        company_title,
                        n43_from_list_str
                    )
                )
                return False

            resp_n43_file = s.post(
                self._url(req_file_link),
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            n43_text = resp_n43_file.text
            n43_content = n43_text.encode('UTF-8')

            if not n43_funcs.validate(n43_content):
                self.basic_log_wrong_layout(
                    resp_n43_file,
                    "{}: {}: got invalid resp_n43. Abort".format(
                        company_title,
                        n43_from_list_str
                    )
                )
                return False

            if not n43_funcs.validate_n43_structure(n43_text):
                self.logger.warning(
                    "{}: {}: N43 file with broken structure detected. Skip. CONTENT:\n{}".format(
                        company_title,
                        n43_from_list_str,
                        resp_n43_file.text
                    )
                )
                # Still True to allow download other files, because it's not a scraping error
                return True

            # Some companies point to the same files
            # -a 35522 (Del Castillo.. , Lorena..)
            if n43_content not in self.n43_contents:
                self.n43_contents.append(n43_content)
                self.logger.info('{}: downloaded N43 file: {}'.format(
                    company_title,
                    n43_from_list_str
                ))
            else:
                self.logger.info('{}: downloaded duplicated N43 file (already downloaded content): {}. Skip'.format(
                    company_title,
                    n43_from_list_str
                ))
            return True

        except Exception as _e:
            self.logger.error(
                "{}: {}: can't download. Abort. HANDLED EXCEPTION: {}".format(
                    company_title,
                    n43_from_list_str,
                    traceback.format_exc()
                )
            )
            return False

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

        ok = self.process_access_for_n43(s, resp_logged_in)

        self.basic_log_time_spent('GET N43')

        if not ok:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
