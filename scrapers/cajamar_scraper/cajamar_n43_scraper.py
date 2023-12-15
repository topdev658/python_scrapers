from collections import OrderedDict
from datetime import datetime
from typing import Tuple

from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings, result_codes
from project.custom_types import ScraperParamsCommon, MainResult
from . import parse_helpers
from . import parse_helpers_n43
from .cajamar_scraper import CajamarScraper

__version__ = '1.5.0'
__changelog__ = """
1.5.0
process_account_for_n43: several attempts 
upd log msg
1.4.0
main: don't check for get_n43_last_successful_result_date_of_access() 
  (now implemented in self.basic_scrape_for_n43())
1.3.0
use basic_save_n43s
1.2.0
use basic_scrape_for_n43
self.fin_entity_name
1.1.0
use CajamarScraper implemented for the new web
1.0.0
init
"""

NO_MOVS_MARKER = 'La cuenta seleccionada no tiene movimientos en el periodo de consulta que ha indicado'


class CajamarN43Scraper(CajamarScraper):
    """From CaixaCallosa (!) to use new web"""

    scraper_name = 'CajamarN43Scraper'
    fin_entity_name = 'CAJAMAR'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.base_url = 'https://www.cajamar.es/'

    def process_access_for_n43(self, s: MySession, resp_logged_in: Response) -> bool:
        cap_param = parse_helpers.get_cap_param(resp_logged_in.text)
        resp_filter_form = self._open_n43_filter_form(s, cap_param)
        acc_nos = parse_helpers_n43.get_acc_nos_for_n43(resp_filter_form.text)
        if not acc_nos:
            self.basic_log_wrong_layout(
                resp_filter_form,
                "Can't get accounts"
            )
            return False

        self.logger.info('Got {} accounts for N43: {}'.format(
            len(acc_nos),
            acc_nos
        ))

        for account_no in acc_nos:
            ok = self.process_account_for_n43(s, cap_param, account_no)
            if not ok:
                return False

        return True

    def _open_n43_filter_form(self, s: MySession, cap_param: str) -> Response:
        req_n43_filter_form_url = self._url('BE/ServletOperation')

        req_n43_filter_form_params = {
            'CHANNEL': 'WEB',
            'MODEL': 'FullModel',
            'OP_CODE': 'O_A_PETIC_EXTRACTO_v1',
            'SERV': '16',
            'NOMBRE_OPERACION': 'O_A_PETIC_EXTRACTO_v1',
            'CAP': cap_param,
        }

        resp_n43_filter_form = s.post(
            req_n43_filter_form_url,
            data=req_n43_filter_form_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=self.ssl_cert
        )

        return resp_n43_filter_form

    def _filter_n43(
            self,
            s: MySession,
            account_no: str,
            date_from: datetime,
            date_to: datetime,
            op_code_param: str) -> Response:

        # '009810210800058' -> '9810210800058'
        acc_n43_alias_param = self._acc_alias_param(account_no)

        date_fmt = '%d%m%Y'
        req_filtered_params = OrderedDict([
            ('CHANNEL', 'WEB'),
            ('MODEL', 'FullModel'),
            ('OP_CODE', op_code_param),
            ('CURRENT_NODE', 'W_S_PETIC_EXTRACTO'),
            ('REACTION_CODE', 'ACEPTAR'),
            ('NCTA_ALIAS', acc_n43_alias_param),  # '9810210800058'
            ('OPC_MOV_FECHAS', '2'),
            ('OP_MOV', '0'),
            ('FINI', date_from.strftime(date_fmt)),  # '05022021'
            ('FFIN', date_to.strftime(date_fmt)),  # '05032021'
            ('TIPODETALLE', '4'),
            ('OPC_FORMATO', 'A')  # not available on prev wev
        ])
        req_filtered_url = self._url('BE/ServletOperation')
        resp_filtered = s.post(
            req_filtered_url,
            data=req_filtered_params,
            headers=self.basic_req_headers_updated({
                'Referer': self._url('BE/ServletOperation')
            }),
            proxies=self.req_proxies,
            verify=self.ssl_cert
        )
        return resp_filtered

    def _get_fileurl(
            self,
            s: MySession,
            fin_ent_account_id: str,
            dtid_param: str,
            download_button_id: str) -> Tuple[bool, str]:
        """Resp with file downloading link.
        See dev_n43/30_file_link.html
        """
        req_filelink_url = self._url('BE/zkau')
        req_filelink_params = OrderedDict([
            ('dtid', dtid_param),  # 'z_hrf'
            ('cmd_0', 'onClick'),
            ('uuid_0', download_button_id),  # 'hS3Q8'
            ('data_0', '{"pageX":340,"pageY":98,"which":1,"x":73,"y":24}')
        ])
        resp_filelink = s.post(
            req_filelink_url,
            data=req_filelink_params,
            headers=self.basic_req_headers_updated({
                'Referer': self._url('BE/ServletOperation'),
            }),
            proxies=self.req_proxies,
            verify=self.ssl_cert,
        )

        # 'BE/zkau/view/{}/dwnmed-0/rdi/Documento.txt'
        filelink = parse_helpers_n43.get_file_link(resp_filelink.text)
        if not filelink:
            self.basic_log_wrong_layout(
                resp_filelink,
                "{}: can't extract filelink".format(fin_ent_account_id)
            )
            return False, ''

        return True, self._url(filelink)

    def process_account_for_n43(self, s: MySession, cap_param: str, account_no: str) -> bool:
        fin_ent_account_id = account_no  # same

        date_from, date_to, is_active_account = self.basic_get_n43_dates_and_account_status(
            fin_ent_account_id
        )
        if not is_active_account:
            return True  # already reported

        self.logger.info('{}: process_account_for_n43 from {} to {} '.format(
            fin_ent_account_id,
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        ))

        resp_n43_filter_form = Response()
        for att in range(1, 5):
            self._delay(minimal=att)
            resp_n43_filter_form = self._open_n43_filter_form(s, cap_param)

            dtid_param = parse_helpers.get_dt_param(resp_n43_filter_form.text)
            self.logger.info('{}: att#{}: resp_n43_filter_form: got dtid_param={}'.format(
                fin_ent_account_id,
                att,
                dtid_param,
            ))

            ok, op_code_param = self._get_op_code(s, fin_ent_account_id, dtid_param)
            if ok:
                break

            self.logger.warning(
                "{}: att#{}: can't open valid resp_n43_filter_form "
                "(failed related op_code). Retry".format(
                    fin_ent_account_id,
                    att,
                )
            )
        else:
            self.basic_log_wrong_layout(
                resp_n43_filter_form,
                "{}: can't open valid resp_n43_filter_form after several attempts. Abort".format(
                    fin_ent_account_id
                )
            )
            return False  # finally failed

        resp_filtered = self._filter_n43(s, account_no, date_from, date_to, op_code_param)

        if NO_MOVS_MARKER in resp_filtered.text:
            self.logger.info('{}: no movements in selected period. Skip'.format(fin_ent_account_id))
            return True

        dtid_param = parse_helpers.get_dt_param(resp_filtered.text)
        if not dtid_param:
            self.basic_log_wrong_layout(
                resp_filtered,
                "{}: can't extract dtid_param from resp_filtered".format(fin_ent_account_id)
            )
            return False

        file_download_button_id = parse_helpers_n43.get_file_download_button_id(resp_filtered.text)
        if not file_download_button_id:
            self.basic_log_wrong_layout(
                resp_filtered,
                "{}: can't extract file_download_button_id".format(fin_ent_account_id)
            )
            return False

        ok, fileurl = self._get_fileurl(s, fin_ent_account_id, dtid_param, file_download_button_id)
        if not ok:
            return False  # already reported

        resp_n43 = s.get(
            fileurl,
            headers=self.req_headers,
            proxies=self.req_proxies,
            verify=self.ssl_cert
        )

        if not n43_funcs.validate(resp_n43.content):
            self.basic_log_wrong_layout(
                resp_n43,
                "{}: got invalid resp_n43".format(fin_ent_account_id)
            )
            return False

        self.n43_contents.append(resp_n43.text.encode('UTF-8'))
        self.logger.info('{}: downloaded N43 file'.format(fin_ent_account_id))

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
