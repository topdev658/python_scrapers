from collections import OrderedDict
from typing import Tuple, Set
from urllib.parse import urljoin

from custom_libs import check_resp
from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from . import parse_helpers
from . import parse_helpers_n43
from .custom_types import AccountForN43
from .ruralvia_scraper import RuralviaScraper, DEFAULT_COMPANY_TITLE, ERR_RESP_MARKERS

__version__ = '1.8.1'
__changelog__ = """
1.8.1
upd log msg
1.8.0
use WRN_N43_DOWNLOAD_IS_NOT_ACTIVATED
1.7.0
use ERR_N43_DOWNLOAD_IS_NOT_ACTIVATED result code
1.6.0
use n43_funcs.validate_n43_structure
1.5.0
upd handler for N43_NOT_ACTIVATED_FOR_ACCOUNT_MARKER
added N43_NO_MOVS_MARKERS
added ERROR_RESP_MARKER
1.4.0
__accounts_processed to avoid N43 duplicates
more logs
1.3.0
main: don't check for get_n43_last_successful_result_date_of_access() 
  (now implemented in self.basic_scrape_for_n43())
1.2.0
use basic_save_n43s
1.1.0
use basic_scrape_for_n43
self.fin_entity_name
1.0.0
init
"""

# See 25_resp_n43_no_filter_form.html
# -a 22940, AGROGESTION SUR SL
NO_N43_FILTER_FORM_MARKER = 'MRK_BDP_PAS_CONS_CATALOGO_PORTAL'
# See 26_resp_n43_not_activated_for_account.png
# -a 22940, JUAN MORAL BLANCA: ES0530670141612188696112
N43_NOT_ACTIVATED_FOR_ACCOUNT_MARKER = 'Activación Servicio Norma 43'

# -a 30938 dates 12/06/2021-12/06/2021
N43_NO_MOVS_MARKER = ('Recepción Servicio Norma 43', 'Si lo desea inténtelo de nuevo variando dicha selección')


ERROR_RESP_MARKER = 'Código de error interno'


class RuralviaN43Scraper(RuralviaScraper):
    fin_entity_name = 'RURALVIA'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='RuralviaN43Scraper') -> None:

        super().__init__(scraper_params_common, proxies, scraper_name)
        # Some accounts can be in several companies,
        # this set is to skip repeating accounts
        self.__accounts_processed = set()  # type: Set[str]
        # For result. The scraper will save as much N43s as possible
        # (will continue scraping on detection),
        # but then it will set an err code as the result
        self.__is_detected_inactive_account_for_n43 = False

    def process_access_for_n43(self, s: MySession, resp_logged_in: Response) -> bool:
        # try to parse several companies from companies list
        companies_parsed = self._get_companies_parsed(resp_logged_in)
        for company in companies_parsed:
            ok = self.process_company_for_n43(s, resp_logged_in, company)
            if not ok:
                return False

        return True

    def _open_ficheros_page(self, s: MySession, resp_company_inicio: Response) -> Tuple[bool, Response]:
        req_ficheros_url = extract.get_link_by_text(
            resp_company_inicio.text,
            resp_company_inicio.url,
            'Ficheros'
        )
        if not req_ficheros_url:
            self.basic_log_wrong_layout(
                resp_company_inicio,
                "Can't extract req_ficheros_url"
            )
            return False, Response()

        resp_ficheros = s.get(
            req_ficheros_url,
            headers=self.basic_req_headers_updated({
                'Referer': resp_company_inicio.url
            }),
            proxies=self.req_proxies
        )

        ok = not check_resp.is_error_msg_in_resp(
            ERR_RESP_MARKERS,
            resp_ficheros,
            self.logger,
            '_open_ficheros_page'
        )

        return ok, resp_ficheros

    def _open_n43_filter_form(self, s: MySession, resp_ficheros: Response) -> Tuple[bool, Response]:
        req_filter_form_url = extract.get_link_by_text(
            resp_ficheros.text,
            resp_ficheros.url,
            'Descargas movimientos C43'
        )

        if not req_filter_form_url:
            self.basic_log_wrong_layout(
                resp_ficheros,
                "Can't extract req_filter_form_url"
            )
            return False, Response()

        resp_filter_form = s.get(
            req_filter_form_url,
            headers=self.basic_req_headers_updated({
                'Referer': resp_ficheros.url
            }),
            proxies=self.req_proxies
        )

        ok = not check_resp.is_error_msg_in_resp(
            ERR_RESP_MARKERS,
            resp_ficheros,
            self.logger,
            '_open_n43_filter_form'
        )

        return ok, resp_filter_form

    def process_company_for_n43(self, s: MySession, resp_logged_in: Response, company_parsed: dict) -> bool:
        company_title = company_parsed['title']
        self.logger.info('Process company for N43: {}'.format(company_title))
        ok, s, resp_company_inico, req_url_cuentas_tab, req_headers = self._open_company_inicio_page(
            s,
            resp_logged_in,
            company_parsed
        )
        if not ok:
            return False  # already reported

        # COPIED from RuralviaScraper
        # extract company title from Inicio page
        # it is necessary only if one company per user account
        # or company title was extracted from list of companies
        if company_parsed['title'] == DEFAULT_COMPANY_TITLE:
            company_title = parse_helpers.get_company_title_from_inicio_page(
                self.db_customer_name,
                resp_company_inico.text
            )
            company_parsed['title'] = company_title

        ok, resp_ficheros = self._open_ficheros_page(s, resp_company_inico)
        if not ok:
            return False  # already reported

        ok, resp_n43_filter_form = self._open_n43_filter_form(s, resp_ficheros)
        if not ok:
            return False  # already reported

        ok, accounts_for_n43 = parse_helpers_n43.get_accounts_for_n43(
            resp_n43_filter_form.text
        )
        if not ok:
            if NO_N43_FILTER_FORM_MARKER in resp_n43_filter_form.text:
                self.logger.info('{}: NO_N43_FILTER_FORM_MARKER detected. Skip'.format(company_title))
                return True
            self.basic_log_wrong_layout(
                resp_n43_filter_form,
                "{}: can't extract accounts_for_n43".format(company_title)
            )
            return False

        self.logger.info('{}: got {} account(s) for N43: {}'.format(
            company_title,
            len(accounts_for_n43),
            [a.title for a in accounts_for_n43]
        ))

        for acc in accounts_for_n43:
            ok = self.process_account_for_n43(s, resp_n43_filter_form, acc, company_title)
            if not ok:
                return False

        return True

    def process_account_for_n43(
            self,
            s: MySession,
            resp_filter_form: Response,
            account_for_n43: AccountForN43,
            company_title: str) -> bool:
        fin_ent_account_id = account_for_n43.fin_ent_account_id
        if fin_ent_account_id in self.__accounts_processed:
            self.logger.info('{}: {}: already processed from another company/contract. Skip'.format(
                company_title,
                fin_ent_account_id
            ))
            return True
        date_from, date_to, is_active_account = self.basic_get_n43_dates_and_account_status(
            fin_ent_account_id,
            org_title=company_title
        )
        if not is_active_account:
            return True  # already reported

        self.logger.info('{}: process_account for N43 from {} to {}'.format(
            fin_ent_account_id,
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        ))

        date_fmt = '%d-%m-%Y'
        date_from_str = date_from.strftime(date_fmt)  # '10-01-2021'
        date_to_str = date_to.strftime(date_fmt)  # '31-01-2021
        today_str = date_funcs.today_str(date_fmt)

        req_filter_n43_confirm_params = OrderedDict([
            ('ISUM_OLD_METHOD', 'POST'),
            ('ISUM_ISFORM', 'true'),
            ('SELCTA', account_for_n43.selcta_param),  # '30670141613305048823978CUENTAS CORRIENTES'
            ('SIGPET', 'N'),
            ('FECINI', date_from_str),
            ('FECFIN', date_to_str),
            ('primeraVez', '1'),
            ('paginaActual', '0'),
            ('tamanioPagina', '50'),
            ('campoPaginacion', 'lista'),
            ('numeroPaginas', '0'),
            ('Nmovs', ''),
            ('FechaDesde', date_from_str),
            ('FechaHasta', date_to_str),
            ('Entidad', ''),
            ('NumClave', ''),
            ('cuenta', account_for_n43.cuenta_param),  # '30670141613305048823'
            ('descripcionCuenta', ''),  # 'CUENTAS CORRIENTES', not necessary
            ('fechaComparacion', ''),
            ('fechaTresMeses', ''),
            ('clavePagina', 'CSB_RECEXTRAC'),
            ('fechalimite', today_str),  # '02-02-2020'
            ('DIVISA_COD', account_for_n43.divisa_param),  # '978'
            ('indOperativa', 'N'),
            ('clavePaginaOperativa', 'CSB_RECEXTRAC'),
            ('clavePaginaVolver', 'CSB_MOVIMIENTOS'),
            ('validationToken', 'null')
        ])
        req_filter_n43_link, _ = extract.build_req_params_from_form_html_patched(
            resp_filter_form.text,
            'FORM_RVIA_0'
        )
        if not req_filter_n43_link:
            self.basic_log_wrong_layout(
                resp_filter_form,
                "Can't get req_filter_n43_link"
            )
            return False

        req_filter_n43_url = urljoin(resp_filter_form.url, req_filter_n43_link)

        # 30_resp_n43_filtered_confirm.html
        resp_filter_n43_confirm = s.post(
            req_filter_n43_url,
            data=req_filter_n43_confirm_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_filter_form.url
            }),
            proxies=self.req_proxies
        )

        if (N43_NO_MOVS_MARKER[0] in resp_filter_n43_confirm.text
                and N43_NO_MOVS_MARKER[1] in resp_filter_n43_confirm.text):
            self.logger.info(
                "{}: {}: 'no movements for selected dates' marker detected. Skip".format(
                    company_title,
                    fin_ent_account_id,
                )
            )
            return True

        if N43_NOT_ACTIVATED_FOR_ACCOUNT_MARKER in resp_filter_n43_confirm.text:
            self.logger.warning(
                '{}: {}: it looks like N43 downloading is not activated for the account. '
                'Pls, ask the customer to activate it. Skip'.format(company_title, fin_ent_account_id))
            self.__is_detected_inactive_account_for_n43 = True  # for result
            return True

        if ERROR_RESP_MARKER in resp_filter_n43_confirm.text:
            self.basic_log_wrong_layout(
                resp_filter_n43_confirm,
                "{}: resp_filter_n43_confirm with error code".format(fin_ent_account_id)
            )
            return False

        req_n43_params = OrderedDict([
            ('ISUM_OLD_METHOD', 'POST'),
            ('ISUM_ISFORM', 'true'),
            ('validationToken', 'null'),
            ('clavePagina', 'CSB_ACTUALIZA_C43'),
            ('cuenta', account_for_n43.cuenta_param),  # '30670141613305048823'
            ('RUTAPDF', 'C43.txt'),
            ('SIGPET', 'N'),
            ('FECINI', date_from_str),
            ('FECFIN', date_to_str),
            ('FECACTUAL', today_str),
            ('TIPO_PETICION', ''),
            ('ESTADO', ''),
            ('ENTIDAD', ''),
            ('DIVISA_NAME', ''),
            ('DIVISA_COD', account_for_n43.divisa_param),  # '978'
            ('DIVISA_DESC', '')
        ])

        resp_n43 = s.post(
            req_filter_n43_url,
            data=req_n43_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_filter_form.url
            }),
            proxies=self.req_proxies
        )

        if not n43_funcs.validate(resp_n43.content):
            self.basic_log_wrong_layout(
                resp_n43,
                "{}: got invalid resp_n43".format(fin_ent_account_id)
            )
            return False

        if not n43_funcs.validate_n43_structure(resp_n43.text):
            self.logger.warning(
                "{}: N43 file with broken structure detected. Skip. CONTENT:\n{}".format(
                    fin_ent_account_id,
                    resp_n43.text
                )
            )
            # Still True to allow download other files, because it's not scraping error
            # -a 22940, account ...4022, 15.06.2021-15.06.2021
            return True

        self.n43_contents.append(resp_n43.text.encode('UTF-8'))
        self.__accounts_processed.add(fin_ent_account_id)
        self.logger.info('{}: {}: downloaded N43 file with movements from {} to {}'.format(
            company_title,
            fin_ent_account_id,
            date_from_str,
            date_to_str
        ))
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

        if ok:
            self.basic_save_n43s(
                self.fin_entity_name,
                self.n43_contents
            )

        self.basic_log_time_spent('GET N43')

        if not ok:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        if self.__is_detected_inactive_account_for_n43:
            return result_codes.WRN_N43_DOWNLOAD_IS_NOT_ACTIVATED, None

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
