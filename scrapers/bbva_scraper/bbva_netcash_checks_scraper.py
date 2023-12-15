import datetime
import os
import traceback
from concurrent import futures
from typing import Dict, List, Tuple

from custom_libs import date_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (CheckParsed, CheckCollectionScraped,
                                  MovementParsed, ScraperParamsCommon, MainResult)
from scrapers.bbva_scraper import parse_helpers_netcash
from scrapers.bbva_scraper.bbva_netcash_scraper import BBVANetcashScraper

__version__ = '2.7.0'

__changelog__ = """
2.7.0
InitialId support for checks and checkcollections
2.6.1
upd type hints
2.6.0
parse_helpers_netcash: parse_checks_from_html: handle 'No existen registros'
2.5.0
main: handle reason
2.4.1
fixed assignment and handling of get_checks_parsed_w_details() call results
2.4.0
DAF: 
Now we use new basic_save_check_collection to transactional insert check collection operation
new save_check_image
_delete_checks_without_movement_id removed
2.3.0
DAF: Fixed check scraping not available details results when launch parallel check scraping.
we set PROCESS_CHECK_MAX_WORKERS = 1 and check this value to launch sequential check scraping
change call to get_movement_id_from_check_collection_data
2.2.0
use basic_check_scraped_from_check_parsed
parse_helpers_netcash:parse_checks_from_html: use convert.to_float() for amount
2.1.1
_delete_checks_without_movement_id: return bool instead of List[CheckParsed] 
  (db_func doesn't provide it) 
2.1.0
DAF: added support to check collections
2.0.1
DAF: new _delete_checks_without_movement_id called in get_checks_parsed_w_details 
to avoid duplicated check insertions
2.0.0
moved/renamed from BBVANetcashReceiptsScraper
main: ONLY download_checks
1.0.1
download_checks: fixed type hints and returning vals
check_parsed: fixed log arg check_parsed
log msgs: removed redundant leading colons
1.0.0
init
"""

USER_AGENT = ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.22 '
              '(KHTML, like Gecko) Chrome/25.0.1364.97 Safari/537.22')

# with CONCURRENT_IMG_SCRAPING_EXECUTORS=0  -> no concurrence
CONCURRENT_IMG_SCRAPING_EXECUTORS = 4
PROCESS_CHECK_MAX_WORKERS = 1

DOWNLOAD_CHECKS_DAYS_BEFORE_DATE_TO = 15


class BBVANetcashChecksScraper(BBVANetcashScraper):
    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BBVANetcashChecksScraper') -> None:

        super().__init__(scraper_params_common, proxies, scraper_name)

    def download_checks(self, s: MySession) -> Tuple[bool, List[CheckParsed]]:

        if not self.basic_should_download_checks():
            return False, []

        s, checks_parsed = self.process_checks(s)
        ok, checks_parsed_w_details = self.get_checks_parsed_w_details(s, checks_parsed)
        if not ok:
            # already reported
            return False, []
        for i, check_parsed in enumerate(checks_parsed_w_details):
            try:

                office_dc = ''
                if len(check_parsed['charge_account']) > 10:
                    office_dc = check_parsed['charge_account'][4:10]

                check_collection_scraped = CheckCollectionScraped(
                    OfficeDC=office_dc,
                    CheckType=check_parsed['doc_code'],
                    CollectionReference=check_parsed['check_number'],
                    Amount=check_parsed['amount'],
                    CollectionDate=check_parsed['expiration_date'],
                    State=check_parsed['state'],  # tenemos también collection_parsed['delivered']
                    CheckQuantity=1,
                    KeyValue=check_parsed['keyvalue'],
                    CustomerId=self.db_customer_id,
                    FinancialEntityId=self.db_financial_entity_id,
                    AccountId=None,
                    AccountNo=None,
                    StatementId=None,
                )

                statement_data = self.db_connector.get_movement_initial_id_from_check_collection_data(
                    check_collection_scraped, "ABONO COMP. CHEQUEXPRESS TRU%{}".format(check_parsed['charge_cif'])
                )

                if statement_data:
                    check_collection_scraped = check_collection_scraped._replace(
                        AccountId=statement_data['AccountId'],
                        AccountNo=statement_data['AccountNo'],
                        StatementId=statement_data['InitialId']
                    )
                else:
                    check_collection_scraped = check_collection_scraped._replace(
                        AccountId='4669',
                        AccountNo='ES5401825699620201504494',
                    )

                # DAF: for Transactional Check Collection Insertion.
                # relation 1 check collection to 1 check. But for insert we pass
                # a list with the check_parsed instead check_parsed
                result_ok, error = self.basic_save_check_collection(check_collection_scraped, [check_parsed])
                if result_ok:
                    self.save_check_image(check_parsed, check_collection_scraped.AccountNo)

            except:

                self.logger.error("{}: {}: can't save check: EXCEPTION\n{}".format(
                    check_parsed['check_number'],
                    check_parsed['keyvalue'],
                    traceback.format_exc()
                ))

        return True, checks_parsed_w_details

    def process_checks(self, s: MySession) -> Tuple[MySession, List[MovementParsed]]:

        # DAF: if self.date_from_param_str is not provided, we process checks from 15 days before from "date_to"
        if self.date_from_param_str:
            date_from_filter = date_funcs.convert_date_to_db_format(self.date_from_param_str)
        else:
            date_from_dt = self.date_to - datetime.timedelta(days=DOWNLOAD_CHECKS_DAYS_BEFORE_DATE_TO)
            date_from_filter = date_funcs.convert_dt_to_scraper_date_type3(date_from_dt)

        date_to_filter = date_funcs.convert_date_to_db_format(self.date_to_str)

        self.logger.info('Process Checks: from_date={} to_date={}'.format(
            date_from_filter,
            date_to_filter
        ))

        req_params0 = {
            'pb_cod_prod': '201',
            'pb_cod_serv': '8169',
            'pb_cod_proc': '20020208',
            'LOCALE': 'es_ES',
            'pb_cod_ffecha': 'dd/MM/yyyy',
            'pb_cod_fimporte': '0.000,00',
            'pb_husohora': '(GMT+01:00)',
            'pb_xti_comprper': 'N',
            'pb_url': 'OperacionCBTFServlet?proceso=tlbh_chequexpress_historico_pr'
                      '&operacion=tlbh_chequexpress_historico_op&accion=relacionCriterios&tipoOrden=TRU'
                      '&presentacionAutomatica=SI&tipoColumnaSeleccion=2&columnaEnlace=SI&codigoServicio=8169',
            'pb_segmento': '8',
            'xtiTipoProd': 'C',
            'pb_isPortalKyop': 'true',
            'cod_emp': '20240375',
            'pb_cod_prod_p0': '201',
            'kyop-process-id': ''
        }
        resp0 = s.post(
            'https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/PIBEE?'
            'proceso=tlbh_chequexpress_historico_pr&operacion=tlbh_chequexpress_historico_op'
            '&accion=relacionCriterios&tipoOrden=TRU&presentacionAutomatica=SI&tipoColumnaSeleccion=2'
            '&columnaEnlace=SI&codigoServicio=8169&isInformationalArchitecture=true',
            data=req_params0,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_params = {
            'nifOrdenante': 'B95799664',
            'nombreOrdenante': 'ESERGUI DISTESER SL',
            'destino': 'TOS',
            'diaDesde': date_from_filter[6:8],
            'mesDesde': date_from_filter[4:6],
            'anoDesde': date_from_filter[:4],
            'diaHasta': date_to_filter[6:8],
            'mesHasta': date_to_filter[4:6],
            'anoHasta': date_to_filter[:4],
            'ordenacion': 'NIG',
            'importeDesdeCliente': '',
            'importeHastaCliente': '',
            'importeDesde': '0',
            'importeHasta': '999999999999999.00',
            'fechaDesde': '',
            'fechaHasta': ''
        }

        # https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/OperacionCBTFServlet?
        # proceso=tlbh_chequexpress_historico_pr&operacion=tlbh_chequexpress_historico_op&accion=datosHistorico
        resp = s.post(
            'https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/OperacionCBTFServlet'
            '?proceso=tlbh_chequexpress_historico_pr&operacion=tlbh_chequexpress_historico_op&accion=datosHistorico',
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        checks_parsed = parse_helpers_netcash.parse_checks_from_html(resp.text)

        return s, checks_parsed

    def get_checks_parsed_w_details(
            self,
            s: MySession,
            checks_parsed: List[CheckParsed]) -> Tuple[bool, List[CheckParsed]]:
        """Add check details to checks_parsed"""

        # to put results from checks which require extra request
        # to get extra details
        checks_parsed_details_dict = {}  # type: Dict[str, CheckParsed]

        # obtain extra details
        # only for checks with specific marker 'has_details'
        # - other checks already have all provided info
        # and not saved before
        # we use basic_get_check_collections_to_process: here we have check_collections of only one check
        # in this case they are interchangeable. the function is only keyvalue based
        checks_parsed_to_get_details = self.basic_get_check_collections_to_process(checks_parsed)

        if not project_settings.IS_CONCURRENT_SCRAPING or PROCESS_CHECK_MAX_WORKERS <= 1:
            for check_parsed in checks_parsed_to_get_details:
                checks_parsed_details_dict[check_parsed['keyvalue']] = self.process_check(
                    s,
                    check_parsed
                )

        else:
            if checks_parsed_to_get_details:
                with futures.ThreadPoolExecutor(max_workers=PROCESS_CHECK_MAX_WORKERS) as executor:

                    futures_dict = {
                        executor.submit(self.process_check, s, check_parsed):
                            check_parsed['keyvalue']
                        for check_parsed in checks_parsed_to_get_details
                    }

                    # Extract result from the futures
                    for future in futures.as_completed(futures_dict):
                        future_id = futures_dict[future]
                        try:
                            check_parsed_details = future.result()
                            checks_parsed_details_dict[future_id] = check_parsed_details

                        except Exception:
                            self.logger.error(
                                '{function_title} failed: {future_id}: !!! EXCEPTION !!! {exc}'.format(
                                    function_title='process_check',
                                    future_id=future_id,
                                    exc=traceback.format_exc()
                                )
                            )
                            return False, []

        # combine all extended descriptions
        # from movements_parsed and movements_parsed_extended_descr_dict
        checks_parsed_details = []  # type: List[CheckParsed]

        for check_parsed in checks_parsed_to_get_details:
            if not check_parsed['has_details'] or not checks_parsed_details_dict:
                checks_parsed_details.append(check_parsed)
                continue

            if check_parsed['keyvalue'] in checks_parsed_details_dict.keys():
                check_parsed_details = checks_parsed_details_dict[check_parsed['keyvalue']]
                checks_parsed_details.append(check_parsed_details)

        return True, checks_parsed_details

    def process_check(self, s: MySession,
                      check_parsed: CheckParsed) -> CheckParsed:
        """Check details which can be obtained only after extra http request"""
        self.logger.info('Get Check details: check_number={} amount={} exp_date={} keyvalue={})'.format(
            check_parsed['check_number'],
            check_parsed['amount'],
            check_parsed['expiration_date'],
            check_parsed['keyvalue']
        ))

        req_url = 'https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/{}'.format(check_parsed['details_link'])
        resp = Response()
        try:
            resp = s.get(
                req_url,
                headers=self.req_headers,
                proxies=self.req_proxies,
                timeout=15,
            )

        except:
            raise Exception(
                "Can't get correct resp to extract check details for check_parsed {}:"
                "\n\ncheck_details_request_url :{}\n\n"
                "\n\nRESPONSE\n{}".format(
                    check_parsed,
                    req_url,
                    resp.text
                )
            )

        check_parsed_updated = parse_helpers_netcash.check_parsed_add_details(check_parsed, resp.text)

        if check_parsed_updated['image_link']:
            req_url = 'https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/{}'.format(
                check_parsed_updated['image_link'])
            req_headers = self.req_headers.copy()
            resp = s.get(
                req_url,
                headers=req_headers,
                proxies=self.req_proxies,
                stream=True
            )
            if resp.headers['content-type'] != 'image/jpeg':
                self.logger.error("{}: can't download check image: BAD Content-Type\n{}".format(
                    check_parsed['check_number'],
                    resp.headers['content-type']
                ))

            check_parsed['image_content'] = resp.content

        req_url_return = ('https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/'
                          'OperacionCBTFServlet?proceso=tlbh_chequexpress_historico_pr'
                          '&operacion=tlbh_chequexpress_historico_op&accion=volverHistorico')
        req_headers = self.req_headers.copy()
        resp_return = s.get(
            req_url_return,
            headers=req_headers,
            proxies=self.req_proxies,
            timeout=15,
        )

        return check_parsed_updated

    def save_check_image(self,
                         check: CheckParsed,
                         account_no: str) -> bool:
        """Basic method to save the document and update the DB flag that uses Checksum as file id"""
        # important to use KeyValue bcs it's unique field (at least for the account)

        if not check['image_content']:
            return True

        folder_path = ""
        if account_no:
            folder_path = os.path.join(project_settings.DOWNLOAD_CHECKS_TO_FOLDER, account_no)
        else:
            folder_path = os.path.join(project_settings.DOWNLOAD_CHECKS_TO_FOLDER, "UNCLASSIFIED")

        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path)
            except FileExistsError:
                self.logger.warning(
                    "Can't create folder {}: probable reason: several attempts to create the folder "
                    "from different threads at the same time. Skip".format(folder_path)
                )
        file_path = os.path.join(folder_path, 'check-{}.jpg'.format(check['keyvalue']))

        self.logger.info("Save check to {}".format(os.path.abspath(file_path)))
        try:
            with open(file_path, 'wb') as f:
                f.write(check['image_content'])
        except Exception as exc:
            self.logger.error(
                "{}: Can't save Check Image: {} {}".format(
                    check['check_number'],
                    check['keyvalue'],
                    exc
                )
            )
            return False

        return True

    def main(self) -> MainResult:

        s, resp, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp.url, resp.text, reason)

        self.download_checks(s)
        self.basic_log_time_spent('GET CHECKS')

        return self.basic_result_success()
