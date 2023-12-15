import datetime
import traceback
from collections import OrderedDict
from concurrent import futures
from typing import List, Tuple, Optional

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    LeasingContractParsed, LeasingContractScraped, MainResult,
    LeasingFeeParsed, ScraperParamsCommon
)
from scrapers.bbva_scraper import parse_helpers_netcash
from scrapers.bbva_scraper.bbva_netcash_scraper import BBVANetcashScraper

__version__ = '1.5.1'

__changelog__ = """
1.5.1
fixed type hints
1.5.0
InitialId support for leasings fees
1.4.0
MySession with logger
upd type hints
handle Optional[Response] results (silent) 
1.3.0
DAF: Now we use basic_save_or_update_leasing_contract to transactional store/update leasing contract and fees
save_leasing_contract_fees removed
process_leasing_contract changed to use basic_save_or_update_leasing_contract
1.2.0
main: handle reason
1.1.0
DAF: changes due to LeasingContractScraped and LeasingFeeScraped.
Using self.db_connector.add_or_update_leasing_contract to save or update a leasing contract
1.0.1
save_leasing_contract_fees: use project.IS_UPDATE_DB, fixed log msg
process_company_leasing_contracts: more log msgs
1.0.0
DAF: init
new functions in parse_helpers_netcash:
get_leasing_companies_from_html_resp
get_leasing_contracts_from_html_resp
get_leasing_contract_details_from_html_resp
get_leasing_fees_parsed_from_excel
"""

USER_AGENT = ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.22 '
              '(KHTML, like Gecko) Chrome/25.0.1364.97 Safari/537.22')

PROCESS_LEASING_MAX_WORKERS = 1

DOWNLOAD_LEASING_DAYS_BEFORE_DATE_TO = 15


class BBVANetcashLeasingScraper(BBVANetcashScraper):
    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BBVANetcashLeasingScraper') -> None:

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

        s, nav_data, companies_w_contracts = self.get_companies_w_leasing_contracts(s)
        if not companies_w_contracts:
            return False, []

        for company in companies_w_contracts:
            self.process_company_leasing_contracts(s, company, nav_data)
        return True, []

    def get_companies_w_leasing_contracts(self, s: MySession) -> Tuple[MySession, dict, List[dict]]:

        """Get the companies with leasing contracts"""
        nav_data_default = {'flujo': '', 'ventana': ''}
        resp = self._request_companies_w_leasing_contracts(s)
        if not resp:
            # already logged
            return s, {}, []

        nav_data = self._get_current_navigation_data(resp.text, nav_data_default)

        companies_parsed = parse_helpers_netcash.get_leasing_companies_from_html_resp(resp.text)

        return s, nav_data, companies_parsed

    def process_company_leasing_contracts(
            self,
            s: MySession,
            company: dict,
            nav_data: dict) -> Tuple[bool, List[LeasingContractParsed]]:
        """Process the leasing contracts for the current company"""
        self.logger.info('Processing leasing contracts of company: cif={} with id={}'.format(
            company['cif'],
            company['id']
        ))

        resp = self._request_leasing_contracts(s, company, nav_data)
        if not resp:
            return False, []
        leasing_contracts_parsed = parse_helpers_netcash.get_leasing_contracts_from_html_resp(resp.text)
        self.logger.info("Company {}: got {} leasing contracts: {}".format(
            company['id'],
            len(leasing_contracts_parsed),
            leasing_contracts_parsed
        ))
        leasing_contracts_to_process = self._get_leasing_contracts_to_process(leasing_contracts_parsed)
        self.logger.info('Company {}: got {} leasing contracts to process'.format(
            company['id'],
            len(leasing_contracts_to_process)
        ))

        if not project_settings.IS_CONCURRENT_SCRAPING or PROCESS_LEASING_MAX_WORKERS <= 1:
            for contract_parsed in leasing_contracts_to_process:
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
            company: dict,
            contract_parsed: LeasingContractParsed) -> Optional[LeasingContractParsed]:
        """Process a specific leasing contract"""

        self.logger.info('Process Leasing Contract: {}: from_date={} to_date={}'.format(
            contract_parsed,
            self.date_from_filter,
            self.date_to_filter
        ))

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

            # DAF: fees_with_movement_id_keyvalues is used to avoid searching for fee statement_id again.
            # But also the fee is included to save it. And without your statement_id.
            # This is feasible because basic_save_or_update_leasing_contract
            # before saving the fees will discard all those that are already in BBDD as paid.
            # And the ones that you already have statement_id are always a subset
            # of those that are already in BBDD as paid. Therefore none of the fees with statement_id
            # that we continue to include in the list will be saved again.
            fees_with_movement_id_keyvalues = self.db_connector.get_leasing_fees_with_movement_id_keyvalues(
                leasing_contract_scraped
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

                if leasing_fee_scraped.KeyValue in fees_with_movement_id_keyvalues:
                    leasing_fees_scraped.append(leasing_fee_scraped)
                    continue

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
            company: dict,
            contract_parsed: LeasingContractParsed) -> Tuple[MySession, LeasingContractParsed,
                                                             List[LeasingFeeParsed]]:
        """Get the leasing contract data and its fees data"""

        # For a new contract we first need to get the valid navigation data
        ok, nav_data = self._get_leasing_contract_navigation_data(s, company)
        if not ok:
            return s, contract_parsed, []

        # Get the form with leasing contract options. Mandatory to get it only bcs it'contains new navigation_data
        req_headers = self.req_headers.copy()
        req_params_0 = OrderedDict([
            ('evento', '0X13E01001'),
            ('flujo', nav_data['flujo']),
            ('ventana', nav_data['ventana']),
            ('HD_COD_BANCSB', contract_parsed['post_data']['bank']),
            ('HD_COD_COFICI', contract_parsed['post_data']['office']),
            ('HD_COD_CCONTR', contract_parsed['post_data']['control']),
            ('HD_COD_CFOLIO', contract_parsed['post_data']['folio']),
            ('HD_COD_CDEPEN', contract_parsed['post_data']['depcode']),
            ('HD_COD_CCLIEN', company['id']),
            ('HD_COD_IDFISCAL', company['cif']),
            ('HD_COD_CCLIEN_REG', company['id']),
            ('HD_DES_CLIENTE', ''),
            ('HD_COD_ERROR', '0'),
            ('HD_LONGITUD_LISTA', '8'),
            ('HD_CONTADOR', '1'),
            ('HD_INDPAG_CHQ', 'N'),
            ('cmbCifs', company['id'])
        ])
        resp_0 = s.post(
            'https://www.bbvanetcash.com/SESEBHM/ebhm_es_web/servlet/web?flujo={}'.format(nav_data['flujo']),
            data=req_params_0,
            headers=req_headers,
            proxies=self.req_proxies,
        )
        if not resp_0.status_code == 200:
            return s, contract_parsed, []
        nav_data = self._get_current_navigation_data(resp_0.text, nav_data)

        # Get leasing contract data from the "Datos económicos del contrato" option.
        req_headers = self.req_headers.copy()
        req_params_1 = OrderedDict([
            ('evento', '0x13E01001'),
            ('flujo', nav_data['flujo']),
            ('ventana', nav_data['ventana']),
            ('hd_fila_selec', 'true'),
            ('hd_cod_flujo', 'EBHMFL20102'),  # flow code for this option
            ('Selec', 'on')
        ])

        cookies = {'IV_JCT': '%2FSESEBHM'}
        resp_1 = s.post(
            'https://www.bbvanetcash.com/SESEBHM/ebhm_es_web/servlet/web?flujo={}'.format(nav_data['flujo']),
            cookies=cookies,
            data=req_params_1,
            headers=req_headers,
            proxies=self.req_proxies,
        )
        if not resp_1.status_code == 200:
            return s, contract_parsed, []

        contract_parsed = parse_helpers_netcash.get_leasing_contract_details_from_html_resp(
            resp_1.text,
            contract_parsed
        )

        # Get leasing fees data. We have to do 2 more POST requests:
        # First to navigate to the "Plan de Amortización" option page.
        # And then from there, one more to request the excel file with the data

        # req_params_4 = OrderedDict([
        #     ('evento', '0x13E01001'),
        #     ('flujo', nav_data['flujo']),
        #     ('ventana', nav_data['ventana']),
        #     ('hd_fila_selec', 'true'),
        #     ('hd_cod_flujo', 'EBHMFL20105'),  # flow code for this option
        #     ('Selec', 'on')
        # ])
        #
        # resp_4 = s.post(
        #     'https://www.bbvanetcash.com/SESEBHM/ebhm_es_web/servlet/web?flujo={}'.format(nav_data['flujo']),
        #     cookies=cookies,
        #     data=req_params_4,
        #     headers=req_headers,
        #     proxies=self.req_proxies,
        # )
        # if not resp_4.status_code == 200:
        #     return s, contract_parsed, []
        # nav_data = self._get_current_navigation_data(resp_4.text, nav_data)
        #
        # req_params_5 = OrderedDict([
        #     ('evento', '0X13E0100B'),
        #     ('flujo', nav_data['flujo']),
        #     ('ventana', nav_data['ventana']),
        #     ('HD_COD_ERROR', '0'),
        #     ('HD_COD_BANCSB', '182'),
        #     ('HD_COD_COFICI', '5425'),
        #     ('HD_COD_CCONTR', '501'),
        #     ('HD_COD_CFOLIO', '1712677'),
        #     ('HD_QNU_BLQREQ', '0'),
        #     ('HD_QNU_NUMBLQ', '1'),
        #     ('HD_QNU_TOTBLQ', '2'),
        #     ('HD_IND_FACTUEMI', '')
        # ])
        # resp_5 = s.post(
        #     'https://www.bbvanetcash.com/SESEBHM/ebhm_es_web/servlet/web?flujo={}'.format(nav_data['flujo']),
        #     cookies=cookies,
        #     data=req_params_5,
        #     headers=req_headers,
        #     proxies=self.req_proxies,
        # )
        # if not resp_5.status_code == 200:
        #     return s, contract_parsed, []

        req_params_2 = OrderedDict([
            ('evento', '0x13E01001'),
            ('flujo', nav_data['flujo']),
            ('ventana', nav_data['ventana']),
            ('hd_fila_selec', 'true'),
            ('hd_cod_flujo', 'EBHMFL20103'),  # flow code for this option
            ('Selec', 'on')
        ])

        resp_2 = s.post(
            'https://www.bbvanetcash.com/SESEBHM/ebhm_es_web/servlet/web?flujo={}'.format(nav_data['flujo']),
            cookies=cookies,
            data=req_params_2,
            headers=req_headers,
            proxies=self.req_proxies,
        )
        if not resp_2.status_code == 200:
            return s, contract_parsed, []
        nav_data = self._get_current_navigation_data(resp_2.text, nav_data)

        req_params_3 = OrderedDict([
            ('evento', '0X13E0100A'),
            ('flujo', nav_data['flujo']),
            ('ventana', nav_data['ventana']),
            ('HD_COD_ERROR', '0'),
            ('HD_QNU_NUMBLQ', '1'),
            ('HD_QNU_TOTBLQ', '5'),
            ('HD_QNU_BLQREQ', '')
        ])
        resp_3 = s.post(
            'https://www.bbvanetcash.com/SESEBHM/ebhm_es_web/servlet/web?flujo={}'.format(nav_data['flujo']),
            cookies=cookies,
            data=req_params_3,
            headers=req_headers,
            proxies=self.req_proxies,
        )
        if not resp_3.status_code == 200:
            return s, contract_parsed, []

        leasing_fees_parsed = parse_helpers_netcash.get_leasing_fees_parsed_from_excel(resp_3.content, contract_parsed)

        return s, contract_parsed, leasing_fees_parsed

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

    def _get_leasing_contract_navigation_data(
            self,
            s: MySession,
            company: dict) -> Tuple[bool, dict]:
        """
        Get valid navigation data to the new leasing contract to process.
        We have to navigate first the page with all the companies with leasing contracts and get navigation data.
        Then we have to navigate the leasing contracts page for the current company.
        This navigation is mandatory to get valid data

        :returns (is_success, nav_data)
        """
        resp = self._request_companies_w_leasing_contracts(s)
        if not resp:
            return False, {}
        nav_data = self._get_current_navigation_data(resp.text, {'flujo': '', 'ventana': ''})

        resp = self._request_leasing_contracts(s, company, nav_data)
        if not resp:
            return False, {}
        nav_data = self._get_current_navigation_data(resp.text, nav_data)

        return True, nav_data

    def _request_companies_w_leasing_contracts(self, s: MySession) -> Optional[Response]:
        """
        Get the html response with the list of companies with leasing contracts
        """
        req_headers = self.req_headers.copy()
        req_params = OrderedDict([
            ('pb_cod_prod', '201'),
            ('pb_cod_serv', '8543'),
            ('pb_cod_proc', '89990427'),
            ('LOCALE', 'es_ES'),
            ('pb_cod_ffecha', 'dd/MM/yyyy'),
            ('pb_cod_fimporte', '0.000,00'),
            ('pb_husohora', '(GMT+01:00)'),
            ('pb_xti_comprper', 'N'),
            ('pb_url', 'servlet/web?OPERACION=CONSULTA_LEASING'),
            ('pb_segmento', '8'),
            ('xtiTipoProd', 'C'),
            ('pb_isPortalKyop', 'true'),
            ('cod_emp', '20240375'),  # self['username']
            ('pb_cod_prod_p', '201'),
            ('kyop-process-id', '')
        ])
        resp = s.post(
            'https://www.bbvanetcash.com/SESEBHM/ebhm_es_web/servlet/PIBEE?OPERACION=CONSULTA_LEASING&'
            'isInformationalArchitecture=true',
            data=req_params,
            headers=req_headers,
            proxies=self.req_proxies
        )

        if not resp.status_code == 200:
            self.logger.warning('No companies with leasing contracts')
            return None
        return resp

    def _request_leasing_contracts(self,
                                   s: MySession,
                                   company: dict,
                                   nav_data: dict) -> Optional[Response]:
        """
        Get the html response with the list of leasing contracts for a company.
        Navigation data for the current company are mandatory to get the expected results.
        """
        req_headers = self.req_headers.copy()
        req_params = OrderedDict([
            ('evento', '0X13E01007'),
            ('flujo', nav_data['flujo']),
            ('ventana', nav_data['ventana']),
            ('HD_COD_BANCSB', ''),
            ('HD_COD_COFICI', ''),
            ('HD_COD_CCONTR', ''),
            ('HD_COD_CFOLIO', ''),
            ('HD_COD_CDEPEN', ''),
            ('HD_COD_CCLIEN', company['id']),
            ('HD_COD_IDFISCAL', company['cif']),
            ('HD_COD_CCLIEN_REG', company['id']),
            ('HD_DES_CLIENTE', ''),
            ('HD_COD_ERROR', '0'),
            ('HD_LONGITUD_LISTA', '0'),
            ('HD_CONTADOR', '1'),
            ('HD_INDPAG_CHQ', ''),
            ('cmbCifs', company['cif'])
        ])

        resp = s.post(
            'https://www.bbvanetcash.com/SESEBHM/ebhm_es_web/servlet/web?flujo={}'.format(nav_data['flujo']),
            data=req_params,
            headers=req_headers,
            proxies=self.req_proxies,
        )

        if not resp.status_code == 200:
            self.logger.error("{}: can't get leasing contracts. Abort".format(company))
            return None
        return resp

    def _get_current_navigation_data(self, resp_text: str, nav_data: dict) -> dict:
        """Extract the current navigation data"""
        nav_data['flujo'] = extract.re_first_or_blank(
            '(?si)<input type="hidden" name="flujo" value="(.*?)" />',
            resp_text
        )
        nav_data['ventana'] = extract.re_first_or_blank(
            '(?si)<input type="hidden" name="ventana" value="(.*?)" />',
            resp_text
        )
        return nav_data

    def main(self) -> MainResult:

        s, resp, is_logged, is_credentials_error, reason = self.login()
        url_aso_empresas = 'https://asoempresas.bbva.es/ASO/businesses-apps-settings/v0/available-functionalities/SENDAE000/users?user.id=20166113'
        req_aso_empresas_headers = self.basic_req_headers_updated({
            'Accept': 'application/json, text/html, */*; q=0.1',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en,es-ES;q=0.8,es;q=0.5,en-US;q=0.3',
            'Content-Type': 'application/json',
            'Connection': 'keep-alive',
            'Host': 'asoempresas.bbva.es',
            'x-rho-parentspanid': 'e8813917-2118-4551-89cb-5a3fa295a86b',
            'x-rho-traceid': contact_id,
            'Origin': 'https://empresas.bbva.es',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'tsec': self.tsec_param,
            'TE': 'trailers',
        })
        resp_aso_empresas = s.get(
            url_aso_empresas,
            headers=req_aso_empresas_headers,
            proxies=self.req_proxies,
        )


        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp.url, resp.text, reason)

        self.download_leasing(s)
        self.basic_log_time_spent('GET LEASING')

        return self.basic_result_success()
