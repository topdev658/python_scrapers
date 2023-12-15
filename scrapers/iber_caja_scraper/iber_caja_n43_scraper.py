from collections import OrderedDict
from datetime import timedelta
from typing import Tuple, List, Optional
from urllib.parse import urljoin

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import iban_builder
from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from . import parse_helpers
from . import parse_helpers_n43
from .iber_caja_scraper import IberCajaScraper

__version__ = '1.1.0'
__changelog__ = """
1.1.0
use basic_get_n43_dates_and_account_status
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
        self.date_to = date_funcs.today() - timedelta(days=1)
        self.date_to_str = self.date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        self.n43_contents = []  # type: List[bytes]

    def _open_n43_filter_form(self, s: MySession, auth_param: str) -> Tuple[bool, Response]:
        req_pre_n43_filter_params = OrderedDict([
            ('IdOperacion', ''),
            ('Entidad', '2085'),
            ('Canal', 'IBE'),
            ('Dispositivo', 'INTR'),
            ('Idioma', 'ES'),
            ('MSCSAuth', auth_param),
            ('Entorno', 'IN'),
            ('comercio', ''),
            ('tipoinformacion', 'T')
        ])
        req_pre_n43_filter_form_url = 'https://www1.ibercajadirecto.com/ibercaja/asp/cobrospagos/ficheros/irecfich.asp?MSCSAUTH={}&Idioma=ES'.format(
            auth_param)
        resp_pre_n43_filter_form = s.post(
            req_pre_n43_filter_form_url,
            data=req_pre_n43_filter_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        # Parse
        #     <input type="hidden" name="idoperacion" value="725_22">
        #     <input type="hidden" name="ticket" value="6E...70">
        #     <input type="hidden" name="lista" value="0">
        #     <input type="hidden" name="error" value="0">
        #     <input type="hidden" name="tipooperacion" value="RF">
        #     <input type="hidden" name="Dispositivo" value="INTR">
        #     <input type="hidden" name="Canal" value="WEB">
        #     <input type="hidden" name="Idioma" value="ES">
        #     <input type="hidden" name="Entidad" value="2085">
        #     <input type="hidden" name="tipocuenta" value="AH">
        #     <input type="hidden" name="subtipocuenta" value="01,02,03,04,07,09,83,93,94">
        #     <input type="hidden" name="tipopermiso" value="OCN">
        req_filter_form_link, req_filter_form_params = extract.build_req_params_from_form_html_patched(
            resp_pre_n43_filter_form.text,
            form_name='formData', is_ordered=True
        )
        req_filter_form_url = urljoin(resp_pre_n43_filter_form.url, req_filter_form_link)
        resp_n43_filter_form = s.post(
            req_filter_form_url,
            data=req_filter_form_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_pre_n43_filter_form.url
            }),
            proxies=self.req_proxies
        )
        return True, resp_n43_filter_form

    def process_access_for_43(self, s: MySession, resp_logged_in: Response) -> bool:
        auth_param = parse_helpers.get_auth_param(resp_logged_in.text)
        ok, resp_n43_filter_form = self._open_n43_filter_form(s, auth_param)
        if not ok:
            return False  # already reported

        account_names_for_n43 = parse_helpers_n43.get_account_names(resp_n43_filter_form.text)
        for account_name in account_names_for_n43:
            ok = self.process_account_for_n43(s, auth_param, account_name, resp_n43_filter_form)
            if not ok:
                return False
        return True

    def _filter_n43(
            self,
            s: MySession,
            auth_param: str,
            account_name: str,
            resp_filter_form: Response) -> Optional[Response]:
        fin_ent_account_id = iban_builder.build_iban('ES', account_name)
        date_from, date_to, is_active_account = self.basic_get_n43_dates_and_account_status(
            fin_ent_account_id
        )
        if not is_active_account:
            return None  # already reported

        date_from_str = date_from.strftime('%d/%m/%Y')
        date_to_str = date_to.strftime('%d/%m/%Y')

        self.logger.info('{}: process_account_for_n43 from {} to {} '.format(
            fin_ent_account_id,
            date_from_str,
            date_to_str
        ))

        day_from, month_from, year_from = date_from_str.split('/')
        day_to, month_to, year_to = date_to_str.split('/')

        # MSCSAUTH=753365DB0ED0492E9CBB9F55EB59C2BEPUFQ20210119123333UTVYED0492E9CBQVKOBMB9F55EB59CJHE55F9BBC9E2940DHJC95BE55F9BMBOKVQBCBBC9E2940DE0BD563357HJC95BE5
        req_filter_url = resp_filter_form.url
        # req_filter_url = 'https://www1.ibercajadirecto.com/ibercaja/asp/modulodirector.asp?MSCSAUTH={}'.format(
        #    auth_param
        # )
        req_filter_params = OrderedDict([
            ('idoperacion', '725_29'),
            ('Entidad', '2085'),
            ('Canal', 'WEB'),
            ('Dispositivo', 'INTR'),
            ('Idioma', 'ES'),
            ('ticket', auth_param),
            ('error', '0'),
            ('tipooperacion', 'RF'),
            ('tipocuenta', 'AH'),
            ('subtipocuenta', '01,02,03,04,07,09,83,93,94'),
            ('tipopermiso', 'OCN'),
            ('operation', '0'),
            ('lista', '1'),
            ('account', account_name),  # '2085/8428/18/0330033048 - C.CTE'
            ('fromday', day_from),  # '14'
            ('frommonth', month_from),  # '01'
            ('fromyear', year_from),  # '2021'
            ('today', day_to),  # '15'
            ('tomonth', month_to),  # '01'
            ('toyear', year_to),
            ('tipo', '04301'),  # '2021'
        ])

        resp_filtered = s.post(
            req_filter_url,
            data=req_filter_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_filter_form.url
            }),
            proxies=self.req_proxies
        )
        # 40_resp_filtered.html, contains IDs of the files to download
        return resp_filtered

    def process_account_for_n43(
            self,
            s: MySession,
            auth_param: str,
            account_name: str,
            resp_filter_form: Response) -> bool:
        # 40_resp_filtered.html
        resp_filtered = self._filter_n43(s, auth_param, account_name, resp_filter_form)
        if resp_filtered is None:
            return True  # already reported
        file_ids = parse_helpers_n43.get_file_ids(resp_filtered.text)
        for file_id in file_ids:
            ok = self.download_n43_file(s, resp_filtered, account_name, file_id)
            if not ok:
                return False
        return True

    def download_n43_file(self, s: MySession, resp_prev: Response, account_name: str, file_id: str) -> bool:

        ticket_param = extract.form_param(resp_prev.text, 'ticket')

        # STEP 1. CONFIRM (selected target file and pressed Aceptar)
        req_confirm_params = OrderedDict([
            ('idoperacion', '725_23'),
            ('Entidad', '2085'),
            ('Canal', 'WEB'),
            ('Dispositivo', 'INTR'),
            ('Idioma', 'ES'),
            ('ticket', ticket_param),
            ('idfile', file_id),  # '4907332'
            ('tipooperacion', 'RF'),
            ('error', '0'),
            ('tipo', '0')
        ])
        req_confirm_url = "https://www1.ibercajadirecto.com/ibercaja/asp/modulodirector.asp?MSCSAUTH={}".format(
            ticket_param
        )

        # 45_resp_confirm.html
        resp_confirm = s.post(
            req_confirm_url,
            data=req_confirm_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_prev.url
            }),
            proxies=self.req_proxies
        )

        #  {'ticket': ..., 'cod_cliente', filesId', 'tipooperacion'}
        _, req_file_name_params = extract.build_req_params_from_form_html_patched(
            resp_confirm.text,
            form_name='ficheros_aceptar',
            is_ordered=True
        )

        # STEP2 GET FILENAME
        # 50_resp_n43_get_filename.html
        resp_file_name = s.get(
            'https://www1.ibercajadirecto.com/InterFicheros/download/request_download.asp',
            params=req_file_name_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_confirm.url
            }),
            proxies=self.req_proxies
        )

        file_name = parse_helpers_n43.get_file_name(resp_file_name.text)

        req_n43_file_params = OrderedDict([
            ('cod_cliente', req_file_name_params['cod_cliente']),  # self.username
            ('targetName', file_name)
        ])

        resp_n43_file = s.get(
            'https://www1.ibercajadirecto.com/InterFicheros/download/perform_download.asp',
            params=req_n43_file_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_confirm.url
            }),
            proxies=self.req_proxies
        )

        if not n43_funcs.validate(resp_n43_file.content):
            self.logger.error("{}: invalid N43. Abort. RESPONSE:\n{}".format(
                account_name,
                resp_n43_file.text
            ))
            return False

        self.n43_contents.append(resp_n43_file.text.encode('UTF-8'))
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

        ok = self.process_access_for_43(s, resp_logged_in)
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
