import datetime
import os
import random
import time
import traceback
from concurrent import futures
from typing import List, Tuple, Optional
from urllib.parse import urljoin

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    LeasingContractParsed, LeasingContractScraped,
    LeasingFeeParsed, ScraperParamsCommon,
    DOUBLE_AUTH_REQUIRED_TYPE_OTP
)
from scrapers.bankoa_scraper_from_ruralvia import parse_helpers_leasing
from scrapers.ruralvia_scraper import ruralvia_scraper
from .bankoa_scraper import BankoaScraper
from .custom_types import (
    SettlementReqParams,
    SettlementParsed,
    PDFReqParams,
    PDFParsed,
)

__version__ = '2.3.0'
__changelog__ = """
2.3.0 2023.10.04
process_leasing_contract: find statement_id for all fees not only those without statement_id in DB
2.2.1
aligned double auth msg
2.2.0
InitialId support for leasings fees
2.1.0
parse_helpers_leasing: get_pdf_req_params: check tds' length to avoid exceptions
2.0.0
many fixes mostly for handling unsuccessful execution branches:
bankoa_leasing_scraper.py
    __init__()
        set correct self.date_from_str if date_from_param_str is not provided
        removed self.date_to_filter (was copied from another scraper)
    download_leasing()
        - uncommented condition check self.basic_should_download_leasing()
        - aligned return type for the both exec branches
    process_leasing_contract()
        - use self.date_from_str, self.date_to_str
    get_leasing_contract_situation()
        - use self.date_from_str instead of possible blank self.date_from_param_str
        - handle 2FA at this step -- may occur here !! (-a 16907)
    get_leasing_contract_details()
        - fixed unpacked vars from self.get_leasing_contract_settlements() (messed positions of resp_last and settlements_parsed)
    get_leasing_contract_settlements()
        - fixed unpacked vars from self.get_settlements_details() (messed positions of resp_settlements_details and settlements_parsed)
        - use self.date_from_str instead of possible blank self.date_from_param_str
    get_data_from_pdf_file()
        - fixed returning vals on wrong layout (could raise an Exc on unpacking)
    get_settlements_details()
        - handle nones (pdf_file_parsed, resp_fee) 
        - use self.date_from_str instead of possible blank self.date_from_param_str
parse_helpers_leasing.py
    added FIXME: DEADCODE for the appropriate code (should be removed after a test period)
    get_leasing_contract_details_from_html_resp()
        - type annotation for fc (Dict[str, str]) to pass type checker
        - fixed fee_parsed - remove duplicated convert.to_float for fee_amount (will raise Exc)
        - fixed amount calculation - removed comma in the end (it made float to (float,))
        - handle wrong layout
    get_leasing_fee_details_from_text_pdf_receipt()
        - correct type annotation (optional data)
1.0.0
init
"""

PROCESS_LEASING_MAX_WORKERS = 1

DOWNLOAD_LEASING_DAYS_BEFORE_DATE_TO = 15


class BankoaLeasingScraper(BankoaScraper):
    """Only serial processing"""

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BankoaLeasingScraper') -> None:

        super().__init__(scraper_params_common, proxies, scraper_name)
        self.req_headers = ruralvia_scraper.REQ_HEADERS  # VB: necessary for Ruralvia-based scrapers

        # VB: if self.date_from_param_str is not provided,
        # we process leasing from 15 days before from "date_to"
        if self.date_from_param_str:
            self.date_from_str = self.date_from_param_str  # 15/01/2020
        else:
            date_from_dt = self.date_to - datetime.timedelta(days=DOWNLOAD_LEASING_DAYS_BEFORE_DATE_TO)
            self.date_from_str = date_funcs.convert_dt_to_scraper_date_type1(date_from_dt)

    def download_leasing(self, s: MySession, resp_pos_global: Response) -> bool:
        if not self.basic_should_download_leasing():
            return False

        self.process_leasing_contracts(s, resp_pos_global)
        return True

    def process_leasing_contracts(
            self,
            s: MySession,
            resp_pos_global: Response) -> Tuple[bool, List[LeasingContractParsed]]:

        self.logger.info('Processing leasing contracts.')
        leasing_contracts_parsed = parse_helpers_leasing.get_leasing_contracts_from_html_resp(resp_pos_global.text)
        self.logger.info("Got {} leasing contracts: {}".format(
            len(leasing_contracts_parsed),
            leasing_contracts_parsed
        ))

        if not leasing_contracts_parsed:
            return False, []

        leasing_contracts_to_process = self._get_leasing_contracts_to_process(leasing_contracts_parsed)
        self.logger.info("Got {} leasing contracts to process".format(
            len(leasing_contracts_to_process),
        ))

        if not leasing_contracts_to_process:
            return False, []

        if not project_settings.IS_CONCURRENT_SCRAPING or PROCESS_LEASING_MAX_WORKERS <= 1:
            for contract_parsed in leasing_contracts_to_process:
                self.process_leasing_contract(
                    s,
                    resp_pos_global,
                    contract_parsed
                )
        else:
            with futures.ThreadPoolExecutor(max_workers=PROCESS_LEASING_MAX_WORKERS) as executor:
                futures_dict = {
                    executor.submit(self.process_leasing_contract, s, resp_pos_global, contract_parsed):
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
            resp_pos_global: Response,
            contract_parsed: LeasingContractParsed) -> Optional[LeasingContractParsed]:

        self.logger.info('Process Leasing Contract: {}: from_date={} to_date={}'.format(
            contract_parsed,
            self.date_from_str,
            self.date_to_str
        ))

        try:
            s, contract_parsed, leasing_fees_parsed = self.get_leasing_contract_details(
                s,
                resp_pos_global,
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
                    leasing_fee_scraped, "RECIBO LEASING%{}".format(contract_parsed['post_data'][8:17])
                )
                if not statement_data:
                    statement_data = self.db_connector.get_movement_initial_id_from_leasing_fee_data(
                        leasing_fee_scraped, "RECIBO LEASING%"
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

    def get_leasing_contract_situation(
            self,
            s: MySession,
            resp_pos_global: Response,
            last_url: str,
            leasing_contract: LeasingContractParsed) -> Tuple[bool, MySession, Response]:

        self.logger.info("Get leasing contract situation: {}".format(
            leasing_contract
        ))
        s, resp_financiacion_tab = self.switch_to_financiacion_tab(s, resp_pos_global, last_url)
        s, resp_situacion = self.switch_to_situacion_menu(s, resp_financiacion_tab)

        contract_id = leasing_contract['post_data']
        # Emulate Cuenta selection, Fecha desde selection, Hasta selection and click on Aceptar.
        req_params = parse_helpers_leasing.get_form_data_for_situation_form(contract_id, self.date_from_str)

        # The same for all accounts
        req_link, _ = extract.build_req_params_from_form_html_patched(resp_situacion.text, 'FORM_RVIA_0')
        req_url = urljoin('https://bankoa.bankoaonline.com/', req_link)
        resp_account = s.post(
            req_url,
            data=req_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_situacion.url  # VB: necessary
            }),
            proxies=self.req_proxies,
        )
        if 'NECESITAMOS TU MÓVIL' in resp_account.text:
            self.logger.error('{}. Abort'.format(DOUBLE_AUTH_REQUIRED_TYPE_OTP))
            return False, s, resp_account

        return True, s, resp_account

    def get_leasing_contract_details(
            self,
            s: MySession,
            resp_pos_global: Response,
            contract_parsed: LeasingContractParsed) -> Tuple[MySession,
                                                             LeasingContractParsed,
                                                             List[LeasingFeeParsed]]:
        resp_last = resp_pos_global
        s, resp_last, settlements_parsed = self.get_leasing_contract_settlements(
            s,
            resp_last,
            contract_parsed)

        ok, s, resp_situation = self.get_leasing_contract_situation(
            s,
            resp_pos_global,
            resp_last.url,
            contract_parsed)
        if not ok:
            return s, contract_parsed, []

        # s, resp_text_amortization_schedule, resp_amortization_schedule= self.get_leasing_contract_amortization_schedule(s, resp_situation, contract_parsed)
        # resp_text = resp_text + resp_text_amortization_schedule

        ok, contract_parsed, leasing_fees_parsed = parse_helpers_leasing.get_leasing_contract_details_from_html_resp(
            resp_situation.text,
            contract_parsed,
            settlements_parsed
        )
        if not ok:
            self.basic_log_wrong_layout(resp_situation, "Can't upd contract_parsed. No enough information")

        return s, contract_parsed, leasing_fees_parsed

    def get_leasing_contract_settlements(
            self,
            s: MySession,
            resp_pos_global: Response,
            leasing_contract: LeasingContractParsed) -> Tuple[MySession, Response, List[SettlementParsed]]:
        # switch to Financiacion tab and process each contract from this place
        s, resp_financiacion_tab = self.switch_to_financiacion_tab(s, resp_pos_global)
        # w/ filter conracts (leasing accounts) filter form
        s, resp_liquidaciones_menu = self.switch_to_liquidaciones_menu(s, resp_financiacion_tab)

        contract_id = leasing_contract['post_data']
        self.logger.info('{}: processing leasing contract'.format(contract_id))

        # Emulate Cuenta selection, Fecha desde selection, Hasta selection and click on Aceptar.
        req_params = parse_helpers_leasing.get_form_data_for_settlements_filter_form(
            contract_id,
            self.date_from_str,
            self.date_to_str
        )

        # The same for all accounts
        req_link, _ = extract.build_req_params_from_form_html_patched(resp_liquidaciones_menu.text, 'FORM_RVIA_0')
        req_url = urljoin('https://bankoa.bankoaonline.com/', req_link)

        # Expect 050_resp_financiacion_leasing_liquidaciones_account
        resp_leasing_settlements = s.post(
            req_url,
            data=req_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_liquidaciones_menu.url
            }),
            proxies=self.req_proxies,
        )

        s, resp_settlements_details, settlements_parsed = self.get_settlements_details(
            s,
            resp_leasing_settlements,
            contract_id
        )
        return s, resp_settlements_details, settlements_parsed

    def switch_to_cuentas_tab(
            self,
            s: MySession,
            resp_pos_global: Response) -> Tuple[MySession, Response]:

        req_url_cuentas_tab = extract.get_link_by_text(
            resp_pos_global.text,
            resp_pos_global.url,
            'Cuentas'
        )
        resp_cuentas_tab = s.get(
            req_url_cuentas_tab,
            headers=self.basic_req_headers_updated({
                'Referer': resp_pos_global.url  # VB: necessary
            }),
            proxies=self.req_proxies
        )

        return s, resp_cuentas_tab

    def switch_to_financiacion_tab(
            self,
            s: MySession,
            resp_pos_global: Response,
            last_url: str = '') -> Tuple[MySession, Response]:

        if not last_url:
            last_url = resp_pos_global.url

        req_url_financiacion_tab = extract.get_link_by_text(
            resp_pos_global.text,
            resp_pos_global.url,
            'Financiación'
        )

        resp_financiacion_tab = s.get(
            req_url_financiacion_tab,
            headers=self.basic_req_headers_updated({
                'Referer': last_url
            }),
            proxies=self.req_proxies
        )
        return s, resp_financiacion_tab

    def switch_to_liquidaciones_menu(
            self,
            s: MySession,
            resp_financiacion_tab: Response) -> Tuple[MySession, Response]:
        leasing_settlements_div = extract.re_first_or_blank(
            r'(?si)Leasing.*?</div>.*?Liquidaciones.*?</a>',
            resp_financiacion_tab.text)
        action_url_leasing_settlements = extract.re_last_or_blank(
            '(?si)href=.*?"(.*?)".*?>',
            leasing_settlements_div
        )
        req_url_leasing_settlements = urljoin(resp_financiacion_tab.url, action_url_leasing_settlements)
        # switch to Liquidaciones
        resp_liquidaciones_menu = s.get(
            req_url_leasing_settlements,
            headers=self.basic_req_headers_updated({
                'Referer': resp_financiacion_tab.url  # VB: necessary
            }),
            proxies=self.req_proxies
        )
        return s, resp_liquidaciones_menu

    def switch_to_situacion_menu(
            self,
            s: MySession,
            resp_last: Response) -> Tuple[MySession, Response]:
        leasing_settlements_div = extract.re_first_or_blank(
            r'(?si)Leasing.*?</div>.*?Situaci.*?</a>',
            resp_last.text)
        action_url_leasing_situation = extract.re_last_or_blank(
            '(?si)href=.*?"(.*?)".*?>',
            leasing_settlements_div
        )
        req_url_leasing_situation = urljoin(resp_last.url, action_url_leasing_situation)
        # switch to Situación
        resp_leasing_situation = s.get(
            req_url_leasing_situation,
            headers=self.basic_req_headers_updated({
                'Referer': resp_last.url  # VB: necessary
            }),
            proxies=self.req_proxies
        )
        return s, resp_leasing_situation

    def get_data_from_pdf_file(
            self,
            s: MySession,
            resp_settlement_details: Response,
            contract_id: str,
            liquidation_date: str,
            amount_str_param: str) -> Tuple[MySession, Optional[Response], Optional[PDFParsed]]:

        s, resp_cuentas_tab = self.switch_to_cuentas_tab(s, resp_settlement_details)
        resp_last = resp_cuentas_tab
        pdf_req_params = parse_helpers_leasing.get_pdf_req_params(
            contract_id,
            liquidation_date,
            amount_str_param,
            resp_cuentas_tab.text)
        if not pdf_req_params:
            self.basic_log_wrong_layout(
                resp_cuentas_tab,
                "Can't get pdf_req_params for {} {} {}. Skip".format(contract_id, liquidation_date, amount_str_param)
            )
            return s, None, None

        s, resp_pdf_receipt, pdf_file_content = self.get_leasing_pdf_receipt_of_settlement(
            s,
            resp_last,
            pdf_req_params)

        pdf_text = pdf_funcs.get_text(pdf_file_content)
        pdf_file_parsed = parse_helpers_leasing.get_leasing_fee_details_from_text_pdf_receipt(pdf_text)

        return s, resp_pdf_receipt, pdf_file_parsed

    def get_leasing_pdf_receipt_of_settlement(
            self,
            s: MySession,
            resp_last: Response,
            pdf_req_params: PDFReqParams) -> Tuple[MySession, Response, bytes]:

        req_params = parse_helpers_leasing.get_form_data_for_pdf(pdf_req_params)

        req_link, _ = extract.build_req_params_from_form_html_patched(resp_last.text, 'FORM_RVIA_0')
        req_url = urljoin('https://bankoa.bankoaonline.com/', req_link)
        resp_pdf_file = s.post(
            req_url,
            data=req_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_last.url  # VB: necessary
            }),
            proxies=self.req_proxies,
        )

        return s, resp_pdf_file, resp_pdf_file.content

    def get_settlements_details(
            self,
            s: MySession,
            resp_leasing_settlements: Response,
            contract_id: str) -> Tuple[MySession, Response, List[SettlementParsed]]:
        req_link, _ = extract.build_req_params_from_form_html_patched(
            resp_leasing_settlements.text,
            'FORM_RVIA_0'
        )
        req_details_url = urljoin('https://bankoa.bankoaonline.com/', req_link)

        settlements_list = parse_helpers_leasing.get_settlements_list(resp_leasing_settlements.text)
        resp_last = resp_leasing_settlements
        settlements_parsed = []  # type: List[SettlementParsed]
        for settlement in settlements_list:
            settlement_req_params = SettlementReqParams(
                FECHA_LIQ=settlement[1],
                TIPO_LIQ=settlement[2],
                SITUACION=settlement[3],
                IMPORT=settlement[4],
                PERIODO_LIQ_INI=settlement[5],
                PERIODO_LIQ_FIN=settlement[6]
            )

            req_details_params = parse_helpers_leasing.get_form_data_for_settlement_details(
                contract_id,
                settlement_req_params,
                self.date_from_str,
                self.date_to_str
            )
            # Expect 060_resp_financiacion_leasing_liquidaciones_account_receipt_constitucion
            # FIXME unused

            time.sleep(0.2 + random.random())
            resp_details = s.post(
                req_details_url,
                data=req_details_params,
                headers=self.basic_req_headers_updated({
                    'Referer': resp_last.url
                }),
                proxies=self.req_proxies,
            )

            liquidation_date = settlement_req_params.FECHA_LIQ
            amount_str = settlement_req_params.IMPORT
            s, resp_fee, pdf_file_parsed = self.get_data_from_pdf_file(
                s,
                resp_details,
                contract_id,
                liquidation_date,
                amount_str
            )

            # handle None
            if pdf_file_parsed:
                settlement_parsed = parse_helpers_leasing.get_settlement_from_html_resp(
                    settlement_req_params,
                    pdf_file_parsed,
                    resp_details.text)
                settlements_parsed.append(settlement_parsed)

            # handle None
            if resp_fee:
                resp_last = resp_fee

        return s, resp_last, settlements_parsed

    # method used for testing:
    # gets file text from form i.e. html file at local bankoa scraper folder
    def get_file_text(self, dev_file_name: str):

        file_path = os.path.join(os.path.abspath(os.curdir),
                                 'scrapers/bankoa_scraper_from_ruralvia/dev/' + dev_file_name)
        print(file_path)
        myfile = open(file_path, "r")
        file_text = myfile.read()
        # print(file_text)
        return file_text

    # method used for testing:
    # gets file text from pdf file at local bankoa scraper folder
    def get_pdf_file_text(self, dev_file_name: str):

        file_path = os.path.join(os.path.abspath(os.curdir),
                                 'scrapers/bankoa_scraper_from_ruralvia/dev/' + dev_file_name)
        print(file_path)
        myfile = open(file_path, "rb")
        file_text = myfile.read()
        file_pdf_text = pdf_funcs.get_text(file_text)
        myfile.close()
        # print(file_text)
        return file_pdf_text

    def main(self):
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()
        # a = self.get_pdf_file_text('leasing_receipt_model_1.pdf')
        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        s, resp_pos_global, _, _ = self.select_company(
            s,
            resp_logged_in,
            ruralvia_scraper.REQ_HEADERS
        )

        self.download_leasing(s, resp_pos_global)
        self.basic_log_time_spent('GET LEASING')

        return self.basic_result_success()
