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

from .custom_types import LeasingCompany

from scrapers.santander_scraper import parse_helpers_nuevo_leasing
from scrapers.santander_scraper.santander_empresas_scraper__nuevo import SantanderEmpresasNuevoScraper

__version__ = '1.2.0'

__changelog__ = """
1.2.0 2023.10.04
_get_contract_invoice_details: get details for all invoices even those set as 'LIQUIDADO' in DB
get_leasing_contract_details: deleted use of contract_saved_paid_fees_keyvalues
process_leasing_contract: find statement_id for all fees not only those without statement_id in DB
1.1.0
process_leasing_contract: managed current interest to be updated from last paid invoice
1.0.0 2023.07.28
JFM: init
"""

PROCESS_LEASING_MAX_WORKERS = 1

DOWNLOAD_LEASING_DAYS_BEFORE_DATE_TO = 15


class SantanderEmpresasNuevoLeasingScraper(SantanderEmpresasNuevoScraper):
    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='SantanderEmpresasNuevoLeasingScraper') -> None:

        super().__init__(scraper_params_common, proxies)

        # JFM: if self.date_from_param_str is not provided,
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

        companies_url = 'https://empresas3.gruposantander.es/paas/api/nwe-subsidiary-api/v1/subsidiary?otherSubsidiary=true'
        resp = self._request_companies_w_leasing_contracts(s, companies_url)
        if not resp:
            # already logged
            return s, []

        ok, companies_parsed, next_companies_url = parse_helpers_nuevo_leasing.get_leasing_companies_from_json(resp.text)

        while not next_companies_url == '':
            resp = self._request_companies_w_leasing_contracts(s, next_companies_url)
            if not resp:
                break

            ok, next_companies_parsed, next_companies_url = parse_helpers_nuevo_leasing.get_leasing_companies_from_json(resp.text)

            companies_parsed.extend(next_companies_parsed)

        self.logger.info("Got {} companies: {}".format(
            len(companies_parsed),
            companies_parsed
        ))

        return s, companies_parsed

    def process_company_leasing_contracts(
            self,
            s: MySession,
            company: LeasingCompany) -> Tuple[bool, List[LeasingContractParsed]]:
        """Process the leasing contracts for the current company"""
        self.logger.info('Processing leasing contracts of company: cif={} with personCode={} and companyName={}'.format(
            company.cif,
            company.personCode,
            company.companyName,
        ))

        resp = self._request_leasing_contracts(s, company)
        if not resp:
            return False, []
        leasing_contracts_parsed = parse_helpers_nuevo_leasing.get_leasing_contracts_from_json_resp(resp.text)
        self.logger.info("Company cif {} personCode {}: got {} leasing contracts: {}".format(
            company.cif,
            company.personCode,
            len(leasing_contracts_parsed),
            leasing_contracts_parsed
        ))
        leasing_contracts_to_process = self._get_leasing_contracts_to_process(leasing_contracts_parsed)
        self.logger.info('Company cif {} personCode {}: got {} leasing contracts to process'.format(
            company.cif,
            company.personCode,
            len(leasing_contracts_to_process)
        ))

        if not project_settings.IS_CONCURRENT_SCRAPING or PROCESS_LEASING_MAX_WORKERS <= 1:
            for idx, contract_parsed in enumerate(leasing_contracts_to_process):
                #0182-5425-0501-00000001731368
                self.logger.info('Company cif {} personCode {}, processing leasing contract {} of {}: {}'.format(
                    company.cif,
                    company.personCode,
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

    def process_leasing_contract(
            self,
            s: MySession,
            company: LeasingCompany,
            contract_parsed: LeasingContractParsed) -> Optional[LeasingContractParsed]:
        """Process a specific leasing contract"""

        self.logger.info('Process Leasing Contract: {}: from_date={} to_date={}'.format(
            contract_parsed['contract_number'],
            self.date_from_filter,
            self.date_to_filter
        ))

        #self._refresh_session(s, '')

        try:
            s, contract_parsed, leasing_fees_parsed = self.get_leasing_contract_details(
                s,
                company,
                contract_parsed
            )
            if not leasing_fees_parsed:
                return None

            leasing_contract_scraped = LeasingContractScraped(
                Office=contract_parsed['office'],
                ContractReference=contract_parsed['contract_number'],
                ContractDate=contract_parsed['contract_date'],
                ExpirationDate=contract_parsed['expiration_date'],
                FeesQuantity=contract_parsed['fees_quantity'],
                Amount=contract_parsed['amount'],
                Taxes=None,
                ResidualValue=contract_parsed['residual_value'],
                InitialInterest='',
                CurrentInterest=None,
                PendingRepayment=contract_parsed['pending_repayment'],
                KeyValue=contract_parsed['keyvalue'],
                CustomerId=self.db_customer_id,
                FinancialEntityId=self.db_financial_entity_id,
                AccountId=None,
                AccountNo=None,
            )

            leasing_fees_scraped = []
            last_fee_number_updating_current_interest = 0
            for idx, fee_parsed in enumerate(leasing_fees_parsed):
                leasing_fee_scraped = self.basic_fee_scraped_from_fee_parsed(fee_parsed)

                if leasing_fee_scraped.OperationalDate > date_funcs.now_for_db():
                    leasing_fee_scraped = leasing_fee_scraped._replace(
                        State='PENDIENTE'
                    )
                    leasing_fees_scraped.append(leasing_fee_scraped)
                    continue
                else:
                    # fee_number 0 becomes from invoice expirationNumber == 0 which meains it is not an invoice of a leasing fee, it
                    # is another kind of invoice and it does has it maturity at Cuadro de Amortización
                    if not (fee_parsed['fee_number'] == 0):
                        contract_pending_repayment = fee_parsed['pending_repayment']
                        contract_taxes = fee_parsed['tax_percentage']
                        if 'interest_nominal' in fee_parsed and last_fee_number_updating_current_interest < fee_parsed['fee_number']:
                            last_fee_number_updating_current_interest = fee_parsed['fee_number']
                            leasing_contract_scraped = leasing_contract_scraped._replace(CurrentInterest=fee_parsed['interest_nominal'])
                            if leasing_fee_scraped.FeeNumber == 1:
                                leasing_contract_scraped = leasing_contract_scraped._replace(InitialInterest=fee_parsed['interest_nominal'])

                statement_data = self.db_connector.get_movement_initial_id_from_leasing_fee_data(
                    leasing_fee_scraped, "CUOTA LEASING, ADEUDO CUOTA DEL CONTRATO: {}%{}%".format(
                        leasing_contract_scraped.ContractReference.lstrip('0'),
                        leasing_fee_scraped.InvoiceNumber)
                )

                if statement_data:
                    leasing_fee_scraped = leasing_fee_scraped._replace(
                        StatementId=statement_data['InitialId'],
                        State='LIQUIDADO',
                    )
                    leasing_contract_scraped = leasing_contract_scraped._replace(
                        AccountId=statement_data['AccountId'],
                        AccountNo=statement_data['AccountNo'],
                    )

                leasing_fees_scraped.append(leasing_fee_scraped)

            leasing_contract_scraped = leasing_contract_scraped._replace(
                PendingRepayment=contract_pending_repayment,
                Taxes=contract_taxes,
            )
            if project_settings.IS_UPDATE_DB:
                # JFM: for Transactional Leasing Contract and Fees Insertion and Update
                self.basic_save_or_update_leasing_contract(leasing_contract_scraped, leasing_fees_scraped)

        except:
            self.logger.error("{}: can't save leasing_contract: EXCEPTION\n{}".format(
                contract_parsed['contract_number'],
                traceback.format_exc()
            ))

        return contract_parsed

    def _get_contract_details(
            self,
            s: MySession,
            company: LeasingCompany,
            contract_parsed: LeasingContractParsed) -> Tuple[MySession, OrderedDict]:

        contract_number = contract_parsed['contract_number']
        # Contract request
        url_contract = 'https://empresas3.gruposantander.es/paas/api/nwe-leasingrenting-api/leasing/v1/contract/{}?clientCif={}&personCode={}&contractNumber={}&personType=J&size=10'.format(
            contract_number,
            company.cif,
            company.personCode,
            contract_number
        )

        resp_contract_details = s.get(
            url_contract,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        if not resp_contract_details.status_code == 200:
            self.logger.error("Can't get detailed contract detail. id: {}, reference: {}".format(
                contract_parsed['contract_number'],
                contract_parsed['contract_reference']
            ))
            return s, contract_parsed, []

        try:
            resp_contract_details_json = json.JSONDecoder(
                object_pairs_hook=OrderedDict).decode(
                resp_contract_details.text)

        except Exception as e:
            self.logger.warning(
                "{}: can't parse resp_contract_details\nRESPONSE:\n{}".format(
                    contract_parsed,
                    resp_contract_details,
                )
            )
            time.sleep(1 + random.random() * 0.5)

        return s, resp_contract_details_json


    def _get_contract_maturities(
            self,
            s: MySession,
            company: LeasingCompany,
            contract_parsed: LeasingContractParsed) -> Tuple[MySession, OrderedDict]:

        self.logger.info('Getting Leasing Contract Maturities: contract_number {}, contract_reference {}, kv {}'.format(
            contract_parsed['contract_number'],
            contract_parsed['partenon_contract'],
            contract_parsed['keyvalue']
        ))


        url_maturity = 'https://empresas3.gruposantander.es/paas/api/nwe-leasingrenting-api/leasing/v1/maturity?clientCif={}&personCode={}&personType=J&contractNumber={}&expDateFrom=1984-01-01&expDateTo=2063-12-31&sort=expirationDate,asc'.format(
            company.cif,
            company.personCode,
            contract_parsed['contract_number']
        )

        resp_maturities = s.get(
            url_maturity,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )


        if not resp_maturities.status_code == 200:
            self.logger.error("Can't get contract maturities. id: {}, reference: {}".format(
                contract_parsed['contract_number'],
                contract_parsed['contract_reference']
            ))
            return s, []

        try:
            resp_maturities_json = json.JSONDecoder(
                object_pairs_hook=OrderedDict).decode(
                resp_maturities.text)['_embedded']['maturityList']

        except Exception as e:
            self.logger.warning(
                "{}: can't parse resp_maturities\nRESPONSE:\n{}".format(
                    contract_parsed,
                    resp_maturities,
                )
            )
            time.sleep(1 + random.random() * 0.5)

        return s, resp_maturities_json

    def _get_contract_invoices(
            self,
            s: MySession,
            company: LeasingCompany,
            contract_parsed: LeasingContractParsed) -> Tuple[MySession, OrderedDict]:

        contract_number = contract_parsed['contract_number']

        self.logger.info('Getting Leasing Contract Invoices: contract_number {}, contract_reference {}, kv {}'.format(
            contract_number,
            contract_parsed['partenon_contract'],
            contract_parsed['keyvalue']
        ))
        url_invoices = 'https://empresas3.gruposantander.es/paas/api/nwe-leasingrenting-api/leasing/v1/invoice?clientCif={}&personCode={}&personType=J&contractNumber={}&dateIssueFrom=2002-01-01&dateIssueTo=2063-12-31&sort=invoiceDate%2Casc'.format(
            company.cif,
            company.personCode,
            contract_number,
        )

        resp_invoices = s.get(
            url_invoices,
            headers=self.req_headers,
        )
        if not resp_invoices.status_code == 200:
            return s, []

        try:
            resp_invoices_json = json.JSONDecoder(
                object_pairs_hook=OrderedDict).decode(
                resp_invoices.text)['_embedded']['invoiceList']

        except Exception as e:
            self.logger.error(
                "{}: can't parse resp_invoices_json \nRESPONSE:\n{}. Exception: {}".format(
                    contract_parsed,
                    resp_invoices,
                    e
                )
            )
            time.sleep(1 + random.random() * 0.5)

        return s, resp_invoices_json

    def get_leasing_contract_details(
            self,
            s: MySession,
            company: LeasingCompany,
            contract_parsed: LeasingContractParsed) -> Tuple[MySession, LeasingContractParsed,
                                                             List[LeasingFeeParsed]]:
        """Get the leasing contract data and its fees data"""

        # Get leasing contract data from the "Datos del contrato" option.
        contract_number = contract_parsed['contract_number']
        self.logger.info('Getting Leasing Contract Details: contract_number {}, partenon_contract {}, kv {}'.format(
            contract_number,
            contract_parsed['partenon_contract'],
            contract_parsed['keyvalue']
        ))

        # Get leasing contract details data from "Detalle contrato"
        s, resp_contract_details_json = self._get_contract_details(s, company, contract_parsed)

        contract_parsed = parse_helpers_nuevo_leasing.get_leasing_contract_details_from_json_resp(
            resp_contract_details_json,
            contract_parsed
        )
        # Get leasing fees data. We have to do 2 more GET requests:
        # First to get the "Cuadro de vencimientos" as maturities.
        # Second to get 'Facturacion' as invoices.

        s, resp_maturities_json = self._get_contract_maturities(s, company, contract_parsed)
        s, resp_invoices_json = self._get_contract_invoices(s, company, contract_parsed)

        # Adding details from invoices to fees to get invoice_number, etc ..
        leasing_fees_parsed = parse_helpers_nuevo_leasing.get_leasing_fees_parsed_from_maturities_and_invoices_json_resps(
            resp_maturities_json,
            resp_invoices_json,
            contract_parsed)
        resp_invoices_json = self._get_contract_invoice_details(s, resp_invoices_json, leasing_fees_parsed, company, contract_parsed)
        leasing_fees_parsed = parse_helpers_nuevo_leasing.get_leasing_fees_parsed_with_invoice_details_from_invoices_details_json_resps(
            resp_invoices_json,
            leasing_fees_parsed,
        )

        return s, contract_parsed, leasing_fees_parsed

    def _get_contract_invoice_details(
            self,
            s: MySession,
            resp_invoices_json: OrderedDict,
            leasing_fees_parsed: List[LeasingFeeParsed],
            company: LeasingCompany,
            contract_parsed: LeasingContractParsed,
    ) -> OrderedDict:

        #s, companies = self.get_companies_w_leasing_contracts(s)
        resp_invoices_json_with_details = []

        leasing_fees_parsed_with_associated_invoice = [x for x in leasing_fees_parsed if 'invoice_id' in x]
        for idx, fee_parsed in enumerate(leasing_fees_parsed_with_associated_invoice):

            invoice_id = fee_parsed['invoice_id']

            self.logger.info('Invoice Detail {:3d} of {}: invoice {}, contract {}'.format(
                idx+1,
                len(leasing_fees_parsed_with_associated_invoice),
                invoice_id,
                contract_parsed['contract_number'],
            ))

            # Filter leasing fees by date to avoid retrieving fees detail
            # bill_date = date_funcs.convert_dt_to_scraper_date_type3(date_funcs.get_date_from_str(bill['maturity'], '%Y-%m-%d'))
            # if bill_date < self.date_from_filter or bill_date > self.date_to_filter:
            #     self.logger.warning("{} {}: Not getting {} bill {} detail due to dates filter from {} to {}.".format(
            #         contract_parsed['contract_number'],
            #         contract_parsed['contract_reference'],
            #         bill['id'],
            #         bill_date,
            #         self.date_from_filter,
            #         self.date_to_filter,
            #     ))
            #     continue

            url_invoice_detail = 'https://empresas3.gruposantander.es/paas/api/nwe-leasingrenting-api/leasing/v1/invoice/{}?clientCif={}&personCode={}&personType=J&contractNumber={}&'.format(
                invoice_id,
                company.cif,
                company.personCode,
                contract_parsed['contract_number'],
            )
            resp_invoice_detail = s.get(
                url_invoice_detail,
                headers=self.req_headers,
                )

            if not resp_invoice_detail.status_code == 200:
                self.logger.error(
                "{}, {}: can't get resp_invoice_detail \nRESPONSE:\n{}.".format(
                    contract_parsed['contract_number'],
                    contract_parsed['partenon_contract'],
                    resp_invoice_detail
                ))
                continue

            resp_invoice_detail_json = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(resp_invoice_detail.text)
            invoices = [x for x in resp_invoices_json if x['invoiceNumber'] == invoice_id]

            if invoices:
                resp_invoice_json_with_details = invoices[0]
                resp_invoice_json_with_details['invoice_detail'] = resp_invoice_detail_json
                resp_invoices_json_with_details.append(resp_invoice_json_with_details)

        return resp_invoices_json_with_details


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

    def _request_companies_w_leasing_contracts(self, s: MySession, url_companies: str) -> Optional[Response]:
        """
        Get the json response with the list of companies with leasing contracts
        """
        # Subsidiaries request
        resp = s.get(
            url_companies,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        if not resp.status_code == 200:
            self.logger.warning('No companies with leasing contracts')
            return None

        return resp

    def _request_leasing_contracts(self,
                                   s: MySession,
                                   company: LeasingCompany) -> Optional[Response]:
        """
        Get the json response with the list of leasing contracts for a company.
        """

        url_contracts = 'https://empresas3.gruposantander.es/paas/api/nwe-leasingrenting-api/leasing/v1/contract?clientCif={}&personCode={}&personType=J&contractType=3&expDateFrom=1984-01-01&expDateTo=2063-12-31&dateSignedFrom=1984-01-01&dateSignedTo={}&size=10&sort=contractSignatureDate,desc'.format(
            company.cif,
            company.personCode,
            datetime.date.today().strftime('%Y-%m-%d')
        )

        resp = s.get(
            url_contracts,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )
        if resp.status_code == 204:
            self.logger.warning("{}: company hasn't leasing contracts. Continue".format(company))
            return None
        if not resp.status_code == 200:
            self.logger.error("{}: can't get leasing contracts. Abort".format(company))
            return None
        return resp

    def main(self) -> MainResult:

        s, resp, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp.url, resp.text, reason)

        self.download_leasing(s)
        self.basic_log_time_spent('GET LEASING')

        return self.basic_result_success()
