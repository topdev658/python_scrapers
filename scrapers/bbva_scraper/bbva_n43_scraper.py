import random
import time
from collections import OrderedDict
from concurrent import futures
from datetime import timedelta
from threading import Lock
from typing import Tuple, List

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult, AccountScraped
from . import parse_helpers_n43
from . import parse_helpers_netcash
from .bbva_netcash_scraper import BBVANetcashScraper, PROCESS_ACCOUNT_MAX_WORKERS
from .custom_types import ISMFileFromList, FilterOperation

__version__ = '2.9.0'
__changelog__ = """
2.9.0 2023.11.14
process_access_for_n43_from_ism_pending_or_hist: avoid mark as success if not ISM file available
2.8.0
use username (código de empresa) as fallback for _get_cod_emp_param
2.7.0
correct order for ISM files (ASC)
ism_files_from_list_to_process_asc
upd log msg
2.6.0
process_access_for_n43_from_ism:
  more delays between peding and historical
  use expecting_ism_activated for historical for better detections
  more SERVICE_UNAVALIABLE_MARKERS
2.5.0
more delays for ISM downloading
2.4.0
process_access_for_n43_from_ism_pending_or_hist: 
  use last_successful_n43_download_dt to calc date_from and date_to
more attempts to get valid resps
more delays
2.3.0
check and retry when resp_filter_form returns 'service unavailable' 
2.2.0
min_allowed_hist_file_date
custom_types: ISMFileFromList.date as date
2.1.0
N43s from ISM files:
  enum FilterOperation, 
  handle another layout for pending files,
  mark downloaded pending files as downloaded (will be moved to historical)
N43s from movements:
  check for movements during the dates, skip if no movements
2.0.0
get N43s from ISM files
1.3.0
main: don't check for get_n43_last_successful_result_date_of_access() 
  (now implemented in self.basic_scrape_for_n43())
fmt
1.2.1
fixed typo
1.2.0
use basic_save_n43s
1.1.0
use basic_scrape_for_n43
self.fin_entity_name
1.0.1
fixed import
1.0.0
init
"""

SERVICE_UNAVALIABLE_MARKERS = [
    'Servicio temporalmente no disponible',
    '<title>BHErrorPage</title>',
]


class BBVAN43Scraper(BBVANetcashScraper):
    fin_entity_name = 'BBVA'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BBVAN43Scraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)
        self._is_success = True
        self.__lock = Lock()

    def _get_cod_emp_param(self, s: MySession) -> Tuple[bool, str]:
        # 35_resp_cod_emp.json
        resp_cod_emp = s.post(
            'https://www.bbvanetcash.com/SESKYOP/kyop_mult_web_kyoppresentation_01/session/sessionPing.json',
            data={'dc': int(time.time() * 1000)},
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        try:
            # '20307270'
            cod_emp_param = resp_cod_emp.json()['data'][0]['referenceId']
            return True, cod_emp_param
        except Exception as _e:
            self.logger.warning(
                "Can't get cod_emp_param. Use username (código de empresa) as fallback.\n"
                "RESPONSE: {}\n{}".format(resp_cod_emp.url, resp_cod_emp.text)
            )
            self.logger.info('Using username (código de empresa) as fallback for cod_emp_param: {}'.format(
                self.username
            ))
            return True, self.username

    def _get_pb_cod_serv_param(self, s: MySession) -> Tuple[bool, str]:
        resp_index_new = s.get(
            'https://www.bbvanetcash.com/SESKYOP/kyop_mult_web_pub/index-new.html?LOCALE=es_ES',
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        pb_cod_serv = extract.re_first_or_blank(
            r'(?si)FORMULARIO PROCESOS.*?name="pb_cod_serv"\s+value="(.*?)"',
            resp_index_new.text
        )

        if not pb_cod_serv:
            self.basic_log_wrong_layout(resp_index_new, "Can't extract pb_cod_serv")
            return False, ''

        return True, pb_cod_serv

    def process_access_for_n43_from_ism(self, s: MySession) -> Tuple[bool, bool]:
        """:returns (ok, is_ism_activated)
        is_ism_activated indicates is ISM option available or not
        """
        self.logger.info('Trying to get N43s as ISM files')

        ok, cod_emp_param = self._get_cod_emp_param(s)
        if not ok:
            return False, False  # already reported

        # 1. Go to pending and process all files,
        # but omit them (don't save), because they will be saved from historical then
        ok, is_ism_activated = self.process_access_for_n43_from_ism_pending_or_hist(
            s,
            filter_operation=FilterOperation.pending
        )
        if not ok:
            return False, is_ism_activated

        if not is_ism_activated:
            self.logger.info('ISM downloading is not activated')
            return True, is_ism_activated

        # Extra delay to be sure that all downloaded pending files now moved to historical
        time.sleep(5)

        # TODO: VB: improve: impl w/o extra auth
        #  Now it's necessary to avoid 'No service available' err
        #  that appears after 2nd opening of the file filter
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()
        if not is_logged:
            self.logger.error("Can't log in to get historical N43s from ISM")
            return False, is_ism_activated

        time.sleep(1 + random.random())
        # 2. Go to historical and download the files from the most recent date
        ok, _ = self.process_access_for_n43_from_ism_pending_or_hist(
            s,
            filter_operation=FilterOperation.historical,
            expecting_ism_activated=True
        )
        if not ok:
            return False, is_ism_activated

        return True, is_ism_activated

    def process_access_for_n43_from_ism_pending_or_hist(
            self,
            s: MySession,
            filter_operation: FilterOperation,
            expecting_ism_activated: bool = False) -> Tuple[bool, bool]:
        """:returns (ok, is_ism_activated)"""

        self.logger.info('process_access_for_n43_from_ism: {}'.format(filter_operation.name))

        operation_param = filter_operation.value
        ok, pb_cod_serv_param = self._get_pb_cod_serv_param(s)
        if not ok:
            return False, False  # already reported

        ok, cod_emp_param = self._get_cod_emp_param(s)  # need to call before each req_filter_form
        if not ok:
            return False, False  # already reported

        # Open filter form
        time.sleep(2 + random.random())

        req_filter_form_params = OrderedDict([
            ('pb_cod_prod', '201'),
            ('pb_cod_serv', pb_cod_serv_param),
            ('pb_cod_proc', '20020230'),
            ('LOCALE', 'es_ES'),
            ('pb_cod_ffecha', 'dd/MM/yyyy'),
            ('pb_cod_fimporte', '0.000,00'),
            ('pb_husohora', '(GMT+01:00)'),
            ('pb_xti_comprper', 'S'),
            ('pb_url', ' ?proceso=BHPrRecRecibirFichero&operacion=BHOpRecConfigurarSeleccion&codigoServicio=6767'),
            ('pb_segmento', '7'),
            ('xtiTipoProd', 'C'),
            ('pb_isPortalKyop', 'true'),
            ('cod_emp', cod_emp_param),  # '20307270'
            ('pb_cod_prod_p', '201'),  # It is always the same
            ('kyop-process-id', '')
        ])

        req_filter_form_url = (
            'https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/PIBEE?proceso=BHPrRecRecibirFichero'
            '&operacion=BHOpRecConfigurarSeleccion&codigoServicio=6767&isInformationalArchitecture=true'
        )

        resp_filter_form = Response()
        for att in range(1, 4):
            #  necessary to open before filtering
            resp_filter_form = s.post(
                req_filter_form_url,
                data=req_filter_form_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            if any(m in resp_filter_form.text for m in SERVICE_UNAVALIABLE_MARKERS):
                time.sleep(att * 2 + random.random())
                continue
            else:
                break
        else:
            self.basic_log_wrong_layout(resp_filter_form, "Can't get valid resp_filter_form")
            return False, False

        is_ism_activated = 'Movimientos de Cuentas Personales (ISM)' in resp_filter_form.text
        if not is_ism_activated:
            # Extra check when expecting as active (for historical for now):
            # ISM area must be detected as active, but it is not - it's an err
            if expecting_ism_activated:
                self.basic_log_wrong_layout(
                    resp_filter_form,
                    "Expecting active ISM, but it's detected as inactive"
                )
                return False, expecting_ism_activated
            self.logger.info('ISM downloading is not activated')
            return True, is_ism_activated

        self.logger.info('ISM downloading is available. Proceed')

        # Logic
        # 11.06 (Fri) - date_from = ..., date_to = 10.06, success
        # 12.06 (Sat) - date_from = 11.06, date_to = 11.06, success
        # 13.06 (Sun) - failure
        # 14.06 (Mon) - date_from = 12.06, date_to = 13.06
        date_to = date_funcs.today() - timedelta(days=1)
        date_from = (
            self.last_successful_n43_download_dt
            if self.last_successful_n43_download_dt
            else date_funcs.today() - timedelta(days=project_settings.DOWNLOAD_N43_OFFSET_DAYS_INITIAL)
        )

        self.logger.info('process_access_for_n43_from_ism ({}): date_from={}, date_to={}'.format(
            filter_operation.name,
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        ))

        req_ism_filtered_params = OrderedDict([
            ('proceso', 'BHPrRecRecibirFichero'),
            ('operacion', operation_param),  # 'BHOpRecSeleccionarFicheroHistorico'
            ('numOPRequest', '2'),  # Global autoincreasing index of request
            ('accion', 'consultar'),
            ('listaAsuntos', 'ISM8102#'),  # 'ISM' selection from 'Tipo de ficheros'
            ('tipoBuzon', 'A'),
            ('descripcionFichero', 'Movimientos de Cuentas Personales (ISM)'),
            ('fechaDesde', date_from.strftime('%Y%m%d')),  # 20210201
            ('fechaHasta', date_to.strftime('%Y%m%d')),  # 20210225
            ('rdIntervalo', '1'),
            ('diaDesde', date_from.strftime('%d')),
            ('mesDesde', date_from.strftime('%m')),
            ('anioDesde', date_from.strftime('%Y')),
            ('diaHasta', date_to.strftime('%d')),
            ('mesHasta', date_to.strftime('%m')),
            ('anioHasta', date_to.strftime('%Y')),
            ('extensionFichero', 'ISM8102#Movimientos de Cuentas Personales (ISM)'),  # ISM selection
            ('NormalizacionFicheros', '')
        ])

        time.sleep(2 + random.random())

        #  All files at one page
        req_ism_filtered_url = 'https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/OperacionCBTFServlet'

        resp_ism_filtered = Response()
        for att in range(1, 4):
            resp_ism_filtered = s.post(
                req_ism_filtered_url,
                data=req_ism_filtered_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            if any(m in resp_ism_filtered.text for m in SERVICE_UNAVALIABLE_MARKERS):
                time.sleep(att * 2 + random.random())
                continue
            else:
                break
        else:
            self.basic_log_wrong_layout(resp_ism_filtered, "Can't get valid resp_ism_filtered ({})".format(
                filter_operation.name
            ))
            return False, is_ism_activated

        ism_files_from_list_desc = parse_helpers_n43.get_ism_files_from_list(
            resp_ism_filtered.text,
            filter_operation
        )  # type: List[ISMFileFromList]

        ism_files_from_list_asc = list(reversed(ism_files_from_list_desc))
        # For pending download all to move to historical
        ism_files_from_list_to_process_asc = ism_files_from_list_asc
        if filter_operation == FilterOperation.historical:
            # For historical download only files between date_from...date_to
            ism_files_from_list_to_process_asc = [
                f for f in ism_files_from_list_asc
                if date_from.date() <= f.date <= date_to.date()
            ]

        self.logger.info('Got total {} ISM files, {} to process ({})'.format(
            len(ism_files_from_list_desc),
            len(ism_files_from_list_to_process_asc),
            filter_operation.name)
        )

        # ASC dates
        for ix, ism_file in enumerate(ism_files_from_list_to_process_asc):
            # The files were reordered, so file.ix (0 means newest) != iter ix (0 means oldest)
            # So, we use iter ix for messages, but file.ix for requests
            self.logger.info('Download file #{}: {} ({})'.format(ix + 1, ism_file, filter_operation.name))
            ficherodescarga_param = '{}{}'.format(ism_file.ix, ism_file.id)
            req_ism_file_url = ('https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/'
                                'TLBHRecHttpServlet?ficherodescarga={}'.format(ficherodescarga_param))

            resp_ism_file = s.get(
                req_ism_file_url,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            if not n43_funcs.validate(resp_ism_file.content):
                self.basic_log_wrong_layout(
                    resp_ism_file,
                    "got invalid resp_n43 for {}".format(ism_file)
                )
                with self.__lock:
                    self._is_success = False
                return False, False

            # Extra request for pending files to move them to historical
            if filter_operation == FilterOperation.pending:
                req_mark_as_downloaded_url = (
                    'https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/OperacionCBTFServlet'
                    '?proceso=BHPrRecRecibirFichero&operacion=BHOpRecActualizarBuzon'
                )
                req_mark_as_downloaded_params = OrderedDict([
                    ('ficherodescarga', ficherodescarga_param),
                    ('registroOrden', '{}$'.format(ism_file.ix))
                ])

                resp_mark_as_downloaded = s.post(
                    req_mark_as_downloaded_url,
                    data=req_mark_as_downloaded_params,
                    headers=self.req_headers,
                    proxies=self.req_proxies
                )

                if ism_file.title not in resp_mark_as_downloaded.text:
                    self.basic_log_wrong_layout(
                        resp_mark_as_downloaded,
                        "Can't mark the pending file as downloaded: {}. Abort".format(ism_file)
                    )
                    return False, is_ism_activated

            # Save only 'Historical' files
            if filter_operation == FilterOperation.historical:
                self.n43_contents.append(resp_ism_file.text.encode('UTF-8'))

            time.sleep(1)

        if ism_files_from_list_to_process_asc or filter_operation == FilterOperation.pending:
            # Historical files downloaded and saved or pending files marked as downloaded
            return True, is_ism_activated
        elif date_funcs.is_weekend_day(date_to):
            # Check if ISM file should be available to download as bank doesn't provide
            # ISM file on Sunday and Monday (no movements at weekend)
            self.logger.info("No ISM file available to download: no movements at weekend. Abort".format(date_to))
            return True, is_ism_activated
        else:
            # No ISM historical file available to download
            self.logger.error("No ISM file available to download yet. Try later")
            return False, is_ism_activated

    def process_account_for_n43_from_movements(self, s: MySession, account_scraped: AccountScraped) -> bool:
        with self.__lock:
            if not self._is_success:
                return False

        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        date_from, date_to, is_active_account = self.basic_get_n43_dates_and_account_status(
            fin_ent_account_id
        )
        if not is_active_account:
            return True  # already reported

        date_fmt = '%d/%m/%Y'
        date_from_str = date_from.strftime(date_fmt)  # '10/01/2021'
        date_to_str = date_to.strftime(date_fmt)  # '31/01/2021'

        self.logger.info('{}: process_account_for_n43_from_movements: date_from={}, date_to={} '.format(
            fin_ent_account_id,
            date_from_str,
            date_to_str
        ))

        # IMPORTANT STEP: let's check that there are movements during this dates
        #  If there are no movements, then websites even doesn't allow to
        #  export results as N43, but if the scraper asks for N43 file,
        #  the website returns it with WRONG currency.
        #  So, the solution is to not download N43 file if there are no movements
        ok, resp_movs_json = self._filter_movements_i(s, account_scraped, date_from_str, date_to_str)
        if not ok:
            return False  # already reported

        movements_parsed_desc = parse_helpers_netcash.get_movements_parsed_from_json(resp_movs_json, False)
        if not movements_parsed_desc:
            self.logger.info("{}: no movements since {} till {}. Skip N43 downloading for the account".format(
                fin_ent_account_id,
                date_from_str,
                date_to_str
            ))
            return True

        req_params = OrderedDict([
            ('cuenta', account_scraped.AccountNo),  # ES4401823150410201561082
            ('bancoAsunto', '1'),
            ('tipoFecha', 'Rango'),
            ('fechaDesde', date_from_str),  # '01/02/2021'
            ('fechaHasta', date_to_str),  # '18/02/2021'
            ('periodo', ''),
            ('concepto', ''),
            ('importeDesde', ''),
            ('importeHasta', ''),
            ('divisa', account_scraped.Currency),  # 'EUR'
            ('paginacionTLSMT017', 'N000000000000+0000000000000000000'),
            ('paginacionTLSMT016', 'N00000000000+0000000000000000'),
            ('ultimosMovimientos', 'false'),
            # We need to fill in this field so it will appear in the N43file.
            ('titular', account_scraped.OrganizationName),  # LLEVATS I MILLORANTS GIRONA S.L.
            ('numMostrar', '0'),
            ('saldoContable', '')  # 15.896,21
        ])

        req_url = 'https://www.bbvanetcash.com/SESEYOZ/eyoz_mult_web_posicioncuentas_01/descargarAEB43'

        # 30_resp_n43_download_step1.json
        resp_n43_step1 = s.post(
            req_url,
            data=req_params,
            headers=self.basic_req_headers_updated({
                "X-Requested-With": "XMLHttpRequest"
            }),
            proxies=self.req_proxies
        )

        # for download_step2 request input
        n43_file_data = resp_n43_step1.json()['data']['datos']

        req_params_step2 = OrderedDict([
            ('datos', n43_file_data),  # 'MTEwMTgyMzE1MDAyMDE1NjEwODIyMTAyMDEyMTAyMTgyM...'
            ('titulo', 'ficheroAEB43.txt')  # This is the file name
        ])

        req_url_step2 = 'https://www.bbvanetcash.com/SESEYOZ/eyoz_mult_web_posicioncuentas_01/descargarFichero'

        resp_n43_step2 = s.post(
            req_url_step2,
            data=req_params_step2,
            headers=self.basic_req_headers_updated({
                "Upgrade-Insecure-Requests": "1"
            }),
            proxies=self.req_proxies
        )
        if not n43_funcs.validate(resp_n43_step2.content):
            self.basic_log_wrong_layout(
                resp_n43_step2,
                "{}: got invalid resp_n43".format(fin_ent_account_id)
            )
            with self.__lock:
                self._is_success = False
            return False

        self.n43_contents.append(resp_n43_step2.text.encode('UTF-8'))

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

        # Try to process file downloading area
        ok, is_ism_activated = self.process_access_for_n43_from_ism(s)
        if not ok:
            self._is_success = False  # to align with movement-based processing

        if ok and not is_ism_activated:
            self.logger.info('Get N43s from movements')
            s, _resp_json, accounts_scraped = self.get_accounts_scraped(s)

            if accounts_scraped:
                if project_settings.IS_CONCURRENT_SCRAPING:
                    with futures.ThreadPoolExecutor(max_workers=PROCESS_ACCOUNT_MAX_WORKERS) as executor:

                        futures_dict = {
                            executor.submit(self.process_account_for_n43_from_movements, s, account_scraped):
                                account_scraped.FinancialEntityAccountId
                            for account_scraped in accounts_scraped
                        }

                        self.logger.log_futures_exc('process_account', futures_dict)
                else:
                    for account_scraped in accounts_scraped:
                        self.process_account_for_n43_from_movements(s, account_scraped)

        self.basic_log_time_spent('GET N43')

        if not self._is_success:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
