import datetime
import re
import time
import traceback
from collections import OrderedDict
from concurrent import futures
from typing import List, Tuple, Optional

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    LeasingContractParsed, LeasingContractScraped,
    LeasingFeeParsed, ScraperParamsCommon, MainResult
)
from scrapers.bankinter_scraper import parse_helpers
from scrapers.bankinter_scraper.bankinter_scraper import BankinterScraper

__version__ = '1.7.0'

__changelog__ = """
1.7.0 2023.10.04
process_leasing_contract: find statement_id for all fees not only those without statement_id in DB
1.6.0
InitialId support for leasings fees
1.5.0
upd type hints, MySession with logger
1.4.0
login() with reason
1.3.0
DAF: Now we use basic_save_or_update_leasing_contract to transactional store/update leasing contract and fees
save_leasing_contract_fees removed
process_leasing_contract changed to use basic_save_or_update_leasing_contract
1.2.0
DAF: changes due to LeasingContractScraped and LeasingFeeScraped. Also in parse_helpers functions
get_leasing_contract_details_from_html_resp, get_leasing_contracts_from_html_resp
using self.db_connector.add_or_update_leasing_contract to save or update a leasing contract
1.1.1
save_leasing_contract_fees: use project_settings.IS_UPDATE_DB
process_leasing_contracts: more log msgs
1.1.0
DAF: process_leasing_contract fixed: only get movement_id for scraped leasing fees without it. not all. 
1.0.1
fixed type hints, log msg parameters
1.0.0
DAF: init
new functions in parse_helpers:
get_leasing_companies_from_html_resp
get_leasing_contracts_from_html_resp
get_leasing_contract_details_from_html_resp
"""

USER_AGENT = ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.22 '
              '(KHTML, like Gecko) Chrome/25.0.1364.97 Safari/537.22')

PROCESS_LEASING_MAX_WORKERS = 1

DOWNLOAD_LEASING_DAYS_BEFORE_DATE_TO = 15


class BankinterLeasingScraper(BankinterScraper):
    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BankinterLeasingScraper') -> None:

        super().__init__(scraper_params_common, proxies, scraper_name)

        # DAF: if self.date_from_param_str is not provided,
        # we process checks from 15 days before from "date_to"
        # '20190527' format
        if self.date_from_param_str:
            self.date_from_filter = date_funcs.convert_date_to_db_format(self.date_from_param_str)
        else:
            date_from_dt = self.date_to - datetime.timedelta(days=DOWNLOAD_LEASING_DAYS_BEFORE_DATE_TO)
            self.date_from_filter = date_funcs.convert_dt_to_scraper_date_type3(date_from_dt)

        self.date_to_filter = date_funcs.convert_date_to_db_format(self.date_to_str)

    def _request_for_leasing_contracts(self, s: MySession) -> Response:  # DAF: quitar

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

    def _get_companies_w_leasing_contracts(self, s: MySession) -> Tuple[MySession, List[dict]]:

        req_headers = self.req_headers.copy()
        resp0 = s.get(
            'https://empresas.bankinter.com/www2/empresas/es/financiacion/mediacion',
            headers=req_headers,
            proxies=self.req_proxies,
            timeout=15,
        )

        resp = s.get(
            'https://empresas.bankinter.com/www/es-es/cgi/empresas+cuentas+subintegral+lea',
            headers=req_headers,
            proxies=self.req_proxies,
            timeout=15,
        )
        companies_parsed = parse_helpers.get_leasing_companies_from_html_resp(resp.text)

        return s, companies_parsed

    def download_leasing(self, s: MySession) -> Tuple[bool, list]:

        if not self.basic_should_download_leasing():
            return False, []

        s, companies_w_contracts = self._get_companies_w_leasing_contracts(s)
        if not companies_w_contracts:
            return False, []

        for company in companies_w_contracts:
            self.process_leasing_contracts(s, company)
        return True, []

    def process_leasing_contracts(self, s: MySession, company: dict) -> Tuple[bool, List[LeasingContractParsed]]:

        self.logger.info('Processing leasing contracts of company: {} with id={}'.format(
            company['name'],
            company['id']
        ))

        req_headers = self.req_headers.copy()
        resp = s.get(
            'https://empresas.bankinter.com/www/es-es/cgi/empresas+cambio_empresa?'
            'ext-solapa=financiacion&ext-subsolapa=leasing&empresa={}'.format(company['id']),
            headers=req_headers,
            proxies=self.req_proxies,
            timeout=15,
        )
        leasing_contracts_parsed = parse_helpers.get_leasing_contracts_from_html_resp(resp.text)
        self.logger.info("Company {}: got {} leasing contracts: {}".format(
            company['name'],
            len(leasing_contracts_parsed),
            leasing_contracts_parsed
        ))

        leasing_contracts_to_process = self._get_leasing_contracts_to_process(leasing_contracts_parsed)
        self.logger.info("Company {}: got {} leasing contracts to process".format(
            company['name'],
            len(leasing_contracts_to_process),
        ))

        if not project_settings.IS_CONCURRENT_SCRAPING or PROCESS_LEASING_MAX_WORKERS <= 1:
            for contract_parsed in leasing_contracts_to_process:
                self.process_leasing_contract(
                    s,
                    contract_parsed
                )
        else:
            with futures.ThreadPoolExecutor(max_workers=PROCESS_LEASING_MAX_WORKERS) as executor:
                futures_dict = {
                    executor.submit(self.process_leasing_contract, s, contract_parsed):
                        contract_parsed['keyvalue']
                    for contract_parsed in leasing_contracts_to_process
                }

                # Extract result from the futures
                for future in futures.as_completed(futures_dict):
                    future_id = futures_dict[future]
                    try:
                        future.result()
                    except:
                        self.logger.error('{function_title} failed: {future_id}: !!! EXCEPTION !!! {exc}'.format(
                            function_title='process_leasing_contract',
                            future_id=future_id,
                            exc=traceback.format_exc())
                        )
                        return False, []

        return True, leasing_contracts_parsed

    def _get_leasing_contracts_to_process(
            self,
            contracts_parsed: List[LeasingContractParsed]) -> List[LeasingContractParsed]:

        all_keyvalues = [
            contract_parsed['keyvalue']
            for contract_parsed in contracts_parsed
            if contract_parsed['has_details']
        ]

        saved_keyvalues = self.db_connector.get_saved_leasing_contracts_keyvalues(all_keyvalues)
        new_keyvalues = list(set(all_keyvalues) - set(saved_keyvalues))

        incomplete_keyvalues = self.db_connector.get_incomplete_leasing_contracts_keyvalues(all_keyvalues)

        keyvalues_to_process = list(set(new_keyvalues + incomplete_keyvalues))

        contracts_to_process = [
            contract_parsed
            for contract_parsed in contracts_parsed
            if (contract_parsed['keyvalue'] in keyvalues_to_process) and contract_parsed['has_details']
        ]

        return contracts_to_process

    def process_leasing_contract(
            self,
            s: MySession,
            contract_parsed: LeasingContractParsed) -> Optional[LeasingContractParsed]:

        self.logger.info('Process Leasing Contract: {}: from_date={} to_date={}'.format(
            contract_parsed,
            self.date_from_filter,
            self.date_to_filter
        ))

        try:
            ok, s, contract_parsed, leasing_fees_parsed = self.get_leasing_contract_details(s, contract_parsed)
            if not ok:
                return None

            contract_pending_repayment = contract_parsed['amount']
            leasing_contract_scraped = LeasingContractScraped(
                Office=contract_parsed['office'],
                ContractReference=contract_parsed['contract_reference'],
                ContractDate=contract_parsed['contract_date'],
                ExpirationDate=contract_parsed['expiration_date'],
                FeesQuantity=contract_parsed['fees_quantity'],
                Amount=contract_parsed['amount'],
                Taxes=contract_parsed['taxes'],
                ResidualValue=contract_parsed['residual_value'],
                InitialInterest=contract_parsed['initial_interest'],
                CurrentInterest=contract_parsed['current_interest'],
                PendingRepayment=contract_parsed['pending_repayment'],
                KeyValue=contract_parsed['keyvalue'],
                CustomerId=self.db_customer_id,
                FinancialEntityId=self.db_financial_entity_id,
                AccountId=None,
                AccountNo=None,
            )

            leasing_fees_scraped = []
            set_previous_fees_paid = False
            for idx, fee_parsed in enumerate(leasing_fees_parsed):

                leasing_fee_scraped = self.basic_fee_scraped_from_fee_parsed(fee_parsed)

                if leasing_fee_scraped.OperationalDate > date_funcs.now_for_db():
                    leasing_fee_scraped = leasing_fee_scraped._replace(
                        State='PENDIENTE'
                    )
                    leasing_fees_scraped.append(leasing_fee_scraped)
                    continue
                else:
                    contract_pending_repayment = fee_parsed['pending_repayment']

                statement_data = self.db_connector.get_movement_initial_id_from_leasing_fee_data(
                    leasing_fee_scraped, "CUOTA LEASING%{}".format(contract_parsed['post_data'][8:17])
                )
                if not statement_data:
                    statement_data = self.db_connector.get_movement_initial_id_from_leasing_fee_data(
                        leasing_fee_scraped, "CUOTA - LEASING"
                    )

                if statement_data:
                    leasing_fee_scraped = leasing_fee_scraped._replace(
                        StatementId=statement_data['InitialId'],
                        State='LIQUIDADO'
                    )
                    leasing_contract_scraped = leasing_contract_scraped._replace(
                        AccountId=statement_data['AccountId'],
                        AccountNo=statement_data['AccountNo']
                    )

                    if not set_previous_fees_paid:
                        for i in range(idx):
                            leasing_fees_scraped[i] = leasing_fees_scraped[i]._replace(
                                State='LIQUIDADO'
                            )
                        set_previous_fees_paid = True

                leasing_fees_scraped.append(leasing_fee_scraped)

            leasing_contract_scraped = leasing_contract_scraped._replace(
                PendingRepayment=contract_pending_repayment,
            )
            if project_settings.IS_UPDATE_DB:
                # DAF: for Transactional Leasing Contract Insertion and Update
                self.basic_save_or_update_leasing_contract(leasing_contract_scraped, leasing_fees_scraped)

        except:
            self.logger.error("{}: can't save leasing_contract: EXCEPTION\n{}".format(
                contract_parsed['contract_reference'],
                traceback.format_exc()
            ))

        return contract_parsed

    def get_leasing_contract_details(
            self,
            s: MySession,
            contract_parsed: LeasingContractParsed) -> Tuple[bool, MySession, LeasingContractParsed,
                                                             List[LeasingFeeParsed]]:
        """:return (is_success, session, contract_parsed, fees)"""

        req_url = 'https://empresas.bankinter.com/www/es-es/cgi/empresas+cuentas+leasing_condEco'
        req_params = OrderedDict([
            ('producto', 'LEA'),
            ('IM5400E_EMPRESA', contract_parsed['post_data'][0:4]),
            ('IM5400E_OFICINA', contract_parsed['post_data'][4:8]),
            ('IM5400E_CONTRATO', contract_parsed['post_data'][8:17]),
        ])

        has_next_movements = True
        resp_text = ""
        while has_next_movements:
            time.sleep(0.1)

            resp_i = Response()  # suppress linter warnings
            for _ in range(3):
                resp_i = s.post(
                    req_url,
                    data=req_params,
                    headers=self.req_headers,
                    proxies=self.req_proxies
                )
                if resp_i.status_code == 200:
                    break
            else:
                self.logger.error("error: can't get html with leasing details\nResponse:\n{}".format(
                    resp_i.text
                ))
                # DAF: if fails once we return None :-> So we are prefering None
                # than an incomplete list of movements
                # VB: False == failed
                return False, s, contract_parsed, []

            resp_text += "\r\n" + resp_i.text

            has_next_movements = bool(re.findall(
                r'(?si)<a class="pag" href="javascript:callContinuation\(\'NEXT\'\)">siguiente</a>',
                resp_i.text
            ))
            if has_next_movements:
                form_sg_val = extract.re_last_or_blank(
                    r'(?si)<form name="frmCont" action="">\n<input value="(.*?)" name="formsg" type="hidden">',
                    resp_i.text
                )
                if form_sg_val:
                    req_params['form-sg'] = form_sg_val
                req_params['ROW'] = "NEXT"

        contract_parsed, leasing_fees_parsed = parse_helpers.get_leasing_contract_details_from_html_resp(
            resp_text,
            contract_parsed
        )

        return True, s, contract_parsed, leasing_fees_parsed

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

        self.download_leasing(s)
        self.basic_log_time_spent('GET LEASING')

        return self.basic_result_success()
