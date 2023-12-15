import datetime
import json
import random
import time
import traceback
from collections import OrderedDict
from concurrent import futures
from typing import List, Tuple, Optional

from custom_libs import date_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    LeasingContractParsed, LeasingContractScraped, MainResult,
    LeasingFeeParsed, ScraperParamsCommon
)

from scrapers.bbva_scraper import parse_helpers_es_empresas_leasing
from scrapers.bbva_scraper.bbva_es_empresas_scraper import BBVAEsEmpresasScraper

__version__ = '1.2.0'
__changelog__ = """
1.2.0 2023.10.04
_request_leasing_contracts: added pagination to get all contract for companies with more than 26 contracts
_get_contract_bill_details: get details for all bills even those set as 'LIQUIDADO' in DB
get_leasing_contract_details: deleted use of contract_saved_paid_fees_keyvalues
process_leasing_contract: find statement_id for all fees not only those without statement_id in DB
1.1.0 2023.07.28
get_leasing_contract_details: added contract_saved_paid_fees_keyvalues on call to 
parse_helpers_es_empresas_leasing.get_leasing_fees_parsed_with_bill_details_from_bills_details_json_resps
_get_contract_bill_details: added contract_saved_paid_fees_keyvalues to return 
1.0.0            
JFM: init
"""

from scrapers.bbva_scraper.custom_types import LeasingCompany

USER_AGENT = ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.22 '
              '(KHTML, like Gecko) Chrome/25.0.1364.97 Safari/537.22')

PROCESS_LEASING_MAX_WORKERS = 1

DOWNLOAD_LEASING_DAYS_BEFORE_DATE_TO = 15


class BBVAEsEmpresasLeasingScraper(BBVAEsEmpresasScraper):
    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BBVAEsEmpresasLeasingScraper') -> None:

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

    def download_leasing(self, s: MySession) -> Tuple[bool, List[LeasingContractScraped]]:

        if not self.basic_should_download_leasing():
            return False, []

        s, companies_w_contracts = self.get_companies_w_leasing_contracts(s)
        if not companies_w_contracts:
            return False, []

        for company in companies_w_contracts:
            self.process_company_leasing_contracts(s, company)
        return True, []

    def get_companies_w_leasing_contracts(self, s: MySession) -> Tuple[MySession, List[LeasingCompany]]:

        resp = self._request_companies_w_leasing_contracts(s)
        if not resp:
            # already logged
            return s, []

        ok, companies_parsed = parse_helpers_es_empresas_leasing.get_leasing_companies_from_json(resp.text)
        return s, companies_parsed

    def process_company_leasing_contracts(
            self,
            s: MySession,
            company: dict) -> Tuple[bool, List[LeasingContractParsed]]:
        """Process the leasing contracts for the current company"""
        self.logger.info('Processing leasing contracts of company: cif={} with id={} and name name={}'.format(
            company.cif,
            company.id,
            company.name,
        ))

        leasing_contracts_parsed = self._request_leasing_contracts(s, company)
        if not leasing_contracts_parsed:
            return False, []

        self.logger.info("Company cif {} id {}: got {} leasing contracts: {}".format(
            company.cif,
            company.id,
            len(leasing_contracts_parsed),
            leasing_contracts_parsed
        ))
        leasing_contracts_to_process = self._get_leasing_contracts_to_process(leasing_contracts_parsed)
        self.logger.info('Company cif {} id {}: got {} leasing contracts to process'.format(
            company.cif,
            company.id,
            len(leasing_contracts_to_process)
        ))

        if not project_settings.IS_CONCURRENT_SCRAPING or PROCESS_LEASING_MAX_WORKERS <= 1:
            for idx, contract_parsed in enumerate(leasing_contracts_to_process):
                #0182-5425-0501-00000001731368
                self.logger.info('Company cif {} id {}, processing leasing contract {} of {}: {}'.format(
                    company.cif,
                    company.id,
                    idx+1,
                    len(leasing_contracts_to_process),
                    contract_parsed
                ))
                self.process_leasing_contract(
                    s,
                    company,
                    contract_parsed
                )
        else:
            with futures.ThreadPoolExecutor(max_workers=PROCESS_LEASING_MAX_WORKERS) as executor:
                futures_dict = {
                    executor.submit(
                        self.process_leasing_contract,
                        s,
                        company,
                        contract_parsed
                    ):
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

    # def _refresh_tsec(
    #         self,
    #         s: MySession):
    #
    #     req_headers = self.req_headers.copy()
    #     req_headers.update({
    #         'Accept': '*/*',
    #         'Accept-Encoding': 'gzip, deflate, br',
    #         'Accept-Language': 'en,es-ES;q=0.8,es;q=0.5,en-US;q=0.3',
    #         'Connection': 'keep-alive',
    #         'Content-Type': 'application/json',
    #         'DNT': '1',
    #         'Host': 'tsec2jwt.live.global.platform.bbva.com',
    #         'Origin': 'https://empresas.bbva.es',
    #         'x-consumer-id': 'cashweb@com.bbva.es.channels',
    #         'Sec-Fetch-Dest': 'empty',
    #         'Sec-Fetch-Mode': 'cors',
    #         'Sec-Fetch-Site': 'cross-site',
    #         'x-tsec-token': self.tsec_header,
    #         'x-validation-policy': 'bbva_es'
    #     })
    #
    #     resp_tsec = s.get(
    #         'https://tsec2jwt.live.global.platform.bbva.com/v1/Token',
    #         headers=req_headers,
    #         proxies=self.req_proxies,
    #     )
    #
    #     if not resp_tsec.status_code == 200:
    #         self.logger.error("{}: can't renew tsec")
    #         return
    #
    #     #self.tsec_header = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(resp_tsec.text)['accessToken']
    #

    def process_leasing_contract(
            self,
            s: MySession,
            company: dict,
            contract_parsed: LeasingContractParsed) -> Optional[LeasingContractParsed]:
        """Process a specific leasing contract"""

        self.logger.info('Process Leasing Contract: {}: from_date={} to_date={}'.format(
            contract_parsed['contract_reference'],
            self.date_from_filter,
            self.date_to_filter
        ))

        # self._refresh_tsec(s)
        self.login()

        try:
            s, contract_parsed, leasing_fees_parsed = self.get_leasing_contract_details(
                s,
                company,
                contract_parsed
            )
            if not leasing_fees_parsed:
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
                PendingRepayment=contract_pending_repayment,
                KeyValue=contract_parsed['keyvalue'],
                CustomerId=self.db_customer_id,
                FinancialEntityId=self.db_financial_entity_id,
                AccountId=None,
                AccountNo=None,
            )

            leasing_fees_scraped = []
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
                    leasing_fee_scraped, "OPERACIÓN DE LEASING {}".format(leasing_contract_scraped.ContractReference)
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

                leasing_fees_scraped.append(leasing_fee_scraped)

            leasing_contract_scraped = leasing_contract_scraped._replace(
                PendingRepayment=contract_pending_repayment,
            )
            if project_settings.IS_UPDATE_DB:
                # JFM: for Transactional Leasing Contract and Fees Insertion and Update
                self.basic_save_or_update_leasing_contract(leasing_contract_scraped, leasing_fees_scraped)

        except:
            self.logger.error("{}: can't save leasing_contract: EXCEPTION\n{}".format(
                contract_parsed['contract_reference'],
                traceback.format_exc()
            ))

        return contract_parsed

    def _get_common_headers(self) -> OrderedDict:
        req_headers = {
            'Accept': 'application/json, text/plain, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en,es-ES;q=0.8,es;q=0.5,en-US;q=0.3',
            'Connection': 'keep-alive',
            'contactid': self.contact_id,
            'Content-Type': 'application/json',
            'DNT': '1',
            'Host': 'bbvanetcash.com',
            'Origin': 'https://empresas.bbva.es',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'TE': 'trailers',
            'tsec': self.tsec_header,
            'x-rho-traceid': self.contact_id,
        }
        return req_headers

    def _get_contract_installments(
            self,
            s: MySession,
            contract_parsed: LeasingContractParsed) -> Tuple[MySession, OrderedDict]:

        self.logger.info('Getting Leasing Contract Installments: contract_id {}, contract_reference {}, kv {}'.format(
            contract_parsed['contract_id'],
            contract_parsed['contract_reference'],
            contract_parsed['keyvalue']
        ))

        req_headers = self.req_headers.copy()
        req_headers.update(self._get_common_headers())

        resp_installments = s.get(
            'https://bbvanetcash.com/ASO/leasings/v0/leasings/{}/installments?pageSize=100'.format(
                contract_parsed['contract_id']),
            headers=req_headers,
            proxies=self.req_proxies,
        )
        if not resp_installments.status_code == 200:
            self.logger.error("Can't get contract installments. id: {}, reference: {}".format(
                contract_parsed['contract_id'],
                contract_parsed['contract_reference']
            ))
            return s, []

        try:
            resp_installments_json = json.JSONDecoder(
                object_pairs_hook=OrderedDict).decode(
                resp_installments.text)['data']['installments']

        except Exception as e:
            self.logger.warning(
                "{}: can't parse resp_installments\nRESPONSE:\n{}".format(
                    contract_parsed,
                    resp_installments,
                )
            )
            time.sleep(1 + random.random() * 0.5)

        return s, resp_installments_json

    def _get_contract_bills(
            self,
            s: MySession,
            contract_parsed: LeasingContractParsed) -> Tuple[MySession, OrderedDict]:

        self.logger.info('Getting Leasing Contract Bills: contract_id {}, contract_reference {}, kv {}'.format(
            contract_parsed['contract_id'],
            contract_parsed['contract_reference'],
            contract_parsed['keyvalue']
        ))

        req_headers = self.req_headers.copy()
        req_headers.update(self._get_common_headers())

        resp_bills = s.get(
            'https://bbvanetcash.com/ASO/leasings/v0/leasings/{}/bills?pageSize=100'.format(
                contract_parsed['contract_id']),
            headers=req_headers,
            proxies=self.req_proxies,
        )
        if not resp_bills.status_code == 200:
            return s, []

        try:
            resp_bills_json = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(resp_bills.text)['data']['bills']

        except Exception as e:
            self.logger.error(
                "{}: can't parse resp_bills_json \nRESPONSE:\n{}. Exception: {}".format(
                    contract_parsed,
                    resp_bills,
                    e
                )
            )
            time.sleep(1 + random.random() * 0.5)

        return s, resp_bills_json

    def get_leasing_contract_details(
            self,
            s: MySession,
            company: dict,
            contract_parsed: LeasingContractParsed) -> Tuple[MySession, LeasingContractParsed,
                                                             List[LeasingFeeParsed]]:
        """Get the leasing contract data and its fees data"""

        # Get leasing contract data from the "Datos del contrato" option.
        self.logger.info('Getting Leasing Contract Details: contract_id {}, contract_reference {}, kv {}'.format(
            contract_parsed['contract_id'],
            contract_parsed['contract_reference'],
            contract_parsed['keyvalue']
        ))

        req_headers = self.req_headers.copy()
        # Contract request
        req_headers.update(self._get_common_headers())

        resp_0 = s.get(
            'https://bbvanetcash.com/ASO/leasings/v0/leasings/{}/current-financial-statements'.format(
                contract_parsed['contract_id']),
            headers=req_headers,
            proxies=self.req_proxies,
        )

        if not resp_0.status_code == 200:
            self.logger.error("Can't get detailed contract information. id: {}, reference: {}".format(
                contract_parsed['contract_id'],
                contract_parsed['contract_reference']
            ))
            return s, contract_parsed, []

        resp_1 = s.get(
            'https://bbvanetcash.com/ASO/leasings/v0/leasings/{}/historic-interest?pageSize=100'.format(
                contract_parsed['contract_id']),
            headers=req_headers,
            proxies=self.req_proxies,
        )
        if not resp_1.status_code == 200:
            self.logger.warning("Can't get historic interest. id: {}, reference: {}".format(
                contract_parsed['contract_id'],
                contract_parsed['contract_reference'],
            ))
            return s, contract_parsed, []

        # Get leasing contract data from the "Datos del contrato" option, "Histórico revisión de intereses" suboption.
        contract_parsed = parse_helpers_es_empresas_leasing.get_leasing_contract_details_from_json_resps(
            resp_0.text,
            resp_1.text,
            contract_parsed
        )

        # Get leasing fees data. We have to do 2 more GET requests:
        # First to get the "Plan de Amortización" as installments.
        # Second to get 'Facturas' as bills.

        s, resp_installments_json = self._get_contract_installments(s, contract_parsed)
        s, resp_bills_json = self._get_contract_bills(s, contract_parsed)

        # Adding details from bills to fees to get invoice_number, etc ..
        leasing_fees_parsed = parse_helpers_es_empresas_leasing.get_leasing_fees_parsed_from_installments_and_bills_json_resps(
            resp_installments_json,
            resp_bills_json,
            contract_parsed)
        resp_bills_json = self._get_contract_bill_details(s, resp_bills_json, leasing_fees_parsed, contract_parsed)
        leasing_fees_parsed = parse_helpers_es_empresas_leasing.get_leasing_fees_parsed_with_bill_details_from_bills_details_json_resps(
            resp_bills_json,
            leasing_fees_parsed
        )

        return s, contract_parsed, leasing_fees_parsed

    def _get_contract_bill_details(
            self,
            s: MySession,
            resp_bills_json: OrderedDict,
            leasing_fees_parsed: List[LeasingFeeParsed],
            contract_parsed: LeasingContractParsed,
    ) -> OrderedDict:

        resp_bills_json_with_details = []

        req_headers = self.req_headers.copy()
        req_headers.update(self._get_common_headers())

        leasing_fees_parsed_with_associated_bill = [x for x in leasing_fees_parsed if 'bill_id' in x]
        for idx, fee_parsed in enumerate(leasing_fees_parsed_with_associated_bill):

            bill_id = fee_parsed['bill_id']

            self.logger.info('Bill Detail {:3d} of {}: bill {}, contract {}'.format(
                idx+1,
                len(leasing_fees_parsed_with_associated_bill),
                bill_id,
                contract_parsed['contract_id'],
            ))

            # Filter leasing fees by date to avoid retrieving fees detail
            # bill_date = date_funcs.convert_dt_to_scraper_date_type3(date_funcs.get_date_from_str(bill['maturity'], '%Y-%m-%d'))
            # if bill_date < self.date_from_filter or bill_date > self.date_to_filter:
            #     self.logger.warning("{} {}: Not getting {} bill {} detail due to dates filter from {} to {}.".format(
            #         contract_parsed['contract_id'],
            #         contract_parsed['contract_reference'],
            #         bill['id'],
            #         bill_date,
            #         self.date_from_filter,
            #         self.date_to_filter,
            #     ))
            #     continue

            resp_bill_detail = s.get(
                'https://bbvanetcash.com/ASO/leasings/v0/leasings/{}/bills/{}'.format(
                    contract_parsed['contract_id'],
                    bill_id),
                headers=req_headers,
                proxies=self.req_proxies,
                )

            if not resp_bill_detail.status_code == 200:
                self.logger.error(
                "{}, {}: can't get resp_bill_detail \nRESPONSE:\n{}.".format(
                    contract_parsed['contract_id'],
                    contract_parsed['contract_reference'],
                    resp_bill_detail
                ))
                continue

            resp_bill_detail_json = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(resp_bill_detail.text)
            bills = [x for x in resp_bills_json if x['id'] == bill_id]
            if bills:

                resp_bill_json_with_details = bills[0]
                resp_bill_json_with_details['bill_detail'] = resp_bill_detail_json['data']
                resp_bills_json_with_details.append(resp_bill_json_with_details)

        return resp_bills_json_with_details


    def _get_leasing_contracts_to_process(
            self,
            contracts_parsed: List[LeasingContractParsed]) -> List[LeasingContractParsed]:
        """
        It returns the leasing contracts to process: the new ones + the incomplete processed ones
        """

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

    def _request_companies_w_leasing_contracts(self, s: MySession) -> Optional[Response]:
        """
        Get the json response with the list of companies with leasing contracts
        """
        req_headers = self.req_headers.copy()
        # Companies request
        req_headers.update(self._get_common_headers())

        url_companies = 'https://bbvanetcash.com/ASO/financial-management-companies/v0/financial-management-companies/{}/businesses?productId=201'.format(
            self.username
        )

        resp = s.get(
            url_companies,
            headers=req_headers,
            proxies=self.req_proxies,
        )

        if not resp.status_code == 200:
            self.logger.warning('No companies with leasing contracts')
            return None
        return resp

    def _request_leasing_contracts(self,
                                   s: MySession,
                                   company: dict) -> Optional[LeasingContractParsed]:
        """
        Get the json response with the list of leasing contracts for a company.
        """
        req_headers = self.req_headers.copy()
        req_headers.update(self._get_common_headers())
        self.login()
        leasing_contracts_parsed = [LeasingContractParsed]
        url_contracts = 'https://bbvanetcash.com/ASO/leasings/v0/leasings?businessId={}C'.format(
            company.id
        )
        resp = s.get(
            url_contracts,
            headers=req_headers,
            proxies=self.req_proxies,
        )
        if resp.status_code == 204:
            self.logger.warning("{}: company hasn't leasing contracts. Continue".format(company))
            return None
        if not resp.status_code == 200:
            self.logger.error("{}: can't get leasing contracts. Abort".format(company))
            return None
        leasing_contracts_parsed = parse_helpers_es_empresas_leasing.get_leasing_contracts_from_json_resp(resp.text)
        resp_json = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(resp.text)
        total_pages = resp_json['pagination']['totalPages']
        for i in range(1, total_pages):
            url_next_page = 'https://bbvanetcash.com/ASO/{}'.format(resp_json['pagination']['links']['next'])
            resp = s.get(
            url_next_page,
            headers=req_headers,
            proxies=self.req_proxies,
            )
            if resp.status_code == 204:
                self.logger.warning("{}: company second page hasn't leasing contracts. Continue".format(company))
                return None
            if not resp.status_code == 200:
                self.logger.error("{}: can't get leasing contracts from second page. Abort".format(company))
                return None
            page_leasging_contracts_parsed = parse_helpers_es_empresas_leasing.get_leasing_contracts_from_json_resp(resp.text)
            leasing_contracts_parsed.extend(page_leasging_contracts_parsed)

        return leasing_contracts_parsed

    def main(self) -> MainResult:

        s, resp, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp.url, resp.text, reason)

        self.download_leasing(s)
        self.basic_log_time_spent('GET LEASING')

        return self.basic_result_success()
