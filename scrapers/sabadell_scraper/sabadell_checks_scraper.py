import datetime
import time
import traceback
from collections import OrderedDict
from concurrent import futures
from typing import List, Tuple, Optional

from custom_libs import date_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    CheckParsed, CheckCollectionParsed,
    CheckCollectionScraped, ScraperParamsCommon, MainResult
)
from scrapers.sabadell_scraper import parse_helpers
from scrapers.sabadell_scraper.sabadell_scraper import SabadellScraper

__version__ = '2.0.0'

__changelog__ = """
2.0.0
upd init, scraper_name as cls prop
1.5.0
InitialId support for leasings checks and checkcollections
1.4.1
upd type hints
1.4.0
login() changed signature (with reason)
1.3.0
DAF:
Now we use basic_save_check_collection to transactional insert check collection operation
_delete_check_collections_without_movement_id removed
1.2.1
parse_helpers: parse_checks_from_html: use correct field with amount 
1.2.0
DAF: changed call to get_movement_id_from_check_collection_data: now we pass %remesa cheque%
1.1.0
fmt
_delete_check_collections_without_movement_id: use project_settings.IS_UPDATE_DB
use basic_checks_scraped_from_checks_parsed
parse_helpers: use convert.to_float() for amounts
set scraper-level self.date_from_filter and self.date_to_filter in __init__
1.0.0
DAF: init
new functions in parse_helpers: parse_check_collections_from_html, parse_checks_from_html
"""

USER_AGENT = ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.22 '
              '(KHTML, like Gecko) Chrome/25.0.1364.97 Safari/537.22')

PROCESS_CHECK_MAX_WORKERS = 1

DOWNLOAD_CHECKS_DAYS_BEFORE_DATE_TO = 15


class SabadellChecksScraper(SabadellScraper):

    scraper_name = 'SabadellChecksScraper'

    def __init__(self, scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        # DAF: if self.date_from_param_str is not provided,
        # we process checks from 15 days before from "date_to"
        # '20190527' format
        if self.date_from_param_str:
            self.date_from_filter = date_funcs.convert_date_to_db_format(self.date_from_param_str)
        else:
            date_from_dt = self.date_to - datetime.timedelta(days=DOWNLOAD_CHECKS_DAYS_BEFORE_DATE_TO)
            self.date_from_filter = date_funcs.convert_dt_to_scraper_date_type3(date_from_dt)

        self.date_to_filter = date_funcs.convert_date_to_db_format(self.date_to_str)

    def _request_for_check_collections(self, s: MySession) -> Response:

        req_headers = self.req_headers.copy()
        resp0 = s.get(
            'https://www.bancsabadell.com/txempbs/CBPaidDocumentsQuery.init.bs?segmento=Empresas',
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=15,
        )

        req_url = 'https://www.bancsabadell.com/txempbs/CBPaidDocumentsQuery.CBGetListRemesa.bs'
        req_params = OrderedDict([
            ('account.selectable-index', '0'),
            ('combo1', '-1'),
            ('r1', '1'),
            ('fechaDesde.day', self.date_from_filter[6:8]),  # '20190527'
            ('fechaDesde.month', self.date_from_filter[4:6]),
            ('fechaDesde.year', self.date_from_filter[:4]),
            ('fechaHasta.day', self.date_to_filter[6:8]),
            ('fechaHasta.month', self.date_to_filter[4:6]),
            ('fechaHasta.year', self.date_to_filter[:4]),
            ('tipoConsulta', 'O'),
            ('selectedCriteria', '')

        ])
        resp = s.post(
            req_url,
            data=req_params,
            headers=req_headers,
            proxies=self.req_proxies
        )
        return resp

    def download_checks(self, s: MySession) -> Tuple[bool, List[CheckCollectionParsed]]:

        if not self.basic_should_download_checks():
            return False, []

        s, check_collections_parsed = self.get_check_collections(s)

        if not check_collections_parsed:
            return False, []

        if not project_settings.IS_CONCURRENT_SCRAPING or PROCESS_CHECK_MAX_WORKERS <= 1:
            for collection_parsed in check_collections_parsed:
                self.process_check_collection(
                    s,
                    collection_parsed
                )

        else:
            with futures.ThreadPoolExecutor(max_workers=PROCESS_CHECK_MAX_WORKERS) as executor:
                futures_dict = {
                    executor.submit(self.process_check_collection, s, collection_parsed):
                        collection_parsed['keyvalue']
                    for collection_parsed in check_collections_parsed
                }

                # Extract result from the futures
                for future in futures.as_completed(futures_dict):
                    future_id = futures_dict[future]
                    try:
                        future.result()
                    except:
                        self.logger.error('{function_title} failed: {future_id}: !!! EXCEPTION !!! {exc}'.format(
                            function_title='process_check_collection',
                            future_id=future_id,
                            exc=traceback.format_exc())
                        )
                        return False, []

        return True, check_collections_parsed

    def get_check_collections(self, s: MySession) -> Tuple[MySession, List[CheckCollectionParsed]]:

        resp = self._request_for_check_collections(s)
        check_collections_parsed = parse_helpers.parse_check_collections_from_html(resp.text)

        check_collections_to_process = self.basic_get_check_collections_to_process(check_collections_parsed)

        return s, check_collections_to_process

    def process_check_collection(
            self,
            s: MySession,
            collection_parsed: CheckCollectionParsed) -> Optional[CheckCollectionParsed]:

        self.logger.info('Process Check Collection: {}: from_date={} to_date={}'.format(
            collection_parsed,
            self.date_from_filter,
            self.date_to_filter
        ))

        try:
            check_collection_scraped = CheckCollectionScraped(
                OfficeDC='',
                CheckType='',
                CollectionReference=collection_parsed['check_collection'],
                Amount=collection_parsed['amount'],
                CollectionDate=collection_parsed['collection_date'],
                State=collection_parsed['state'],  # tenemos también collection_parsed['delivered']
                CheckQuantity=collection_parsed['doc_quantity'],
                KeyValue=collection_parsed['keyvalue'],
                CustomerId=self.db_customer_id,
                FinancialEntityId=self.db_financial_entity_id,
                AccountId=None,
                AccountNo=None,
                StatementId=None,
            )

            # DAF get the collection details asap, although they will be saved after, only if the collection is saved
            s, checks_parsed = self.get_check_collection_details(s, collection_parsed)
            if not checks_parsed:
                return None

            statement_data = self.db_connector.get_movement_initial_id_from_check_collection_data(
                check_collection_scraped, "%remesa cheque%"
            )
            if statement_data:
                check_collection_scraped = check_collection_scraped._replace(
                    AccountId=statement_data['AccountId'],
                    AccountNo=statement_data['AccountNo'],
                    StatementId=statement_data['InitialId']
                )

            # DAF: for Transactional Check Collection Insertion
            self.basic_save_check_collection(check_collection_scraped, checks_parsed)

        except:
            self.logger.error("{}: can't save check collection: EXCEPTION\n{}".format(
                collection_parsed['check_collection'],
                traceback.format_exc()
            ))

        return collection_parsed

    def get_check_collection_details(
            self,
            s: MySession,
            check_collection: CheckCollectionParsed) -> Tuple[MySession, List[CheckParsed]]:

        time.sleep(0.2)

        req_url = 'https://www.bancsabadell.com/txempbs/CBPaidDocumentsQuery.CBGetDetalle.bs'
        req_params = OrderedDict([
            ('remittance.selectable-index', check_collection['details_selected_index']),
            ('selectedCriteria', '')
        ])
        resp = s.post(
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            stream=False
        )

        checks_parsed = parse_helpers.parse_checks_from_html(resp.text, check_collection)

        self._request_for_check_collections(s)  # FIXME for what?
        return s, checks_parsed

    def main(self) -> MainResult:
        s, resp, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp.url,
                resp.text,
                reason
            )

        self.download_checks(s)
        self.basic_log_time_spent('GET CHECKS')

        return self.basic_result_success()
