import time
from typing import Tuple

from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult, AccountParsed
from . import parse_helpers_n43
from .bankinter_scraper import BankinterScraper
from .custom_types import Contract

MAX_OFFSET_DAYS = 75

__version__ = '2.2.0'
__changelog__ = """
2.2.0 2023.06.28
download_n43_file: save resp_n43 content instead of resp_n43 text encoded
2.1.0
process_account_for_n43: activate 'Con movimientos automaticos' option for downloaded file
2.0.0
contract-level programmed daily files download with auto-detection
1.1.0
download_pre_requested_daily_files
1.0.0
init
"""

TESORALIA_FILENAME_LIKE = 'DIARIO_TESORALIA'


class BankinterN43Scraper(BankinterScraper):
    scraper_name = 'BankinterN43Scraper'
    fin_entity_name = 'BANKINTER'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    def process_access_for_n43(self, s: MySession) -> bool:
        auth_identity_id = self.get_auth_identity_id(s)
        contracts = self.get_contracts(s, auth_identity_id)
        for contract in contracts:
            ok = self.process_contract_for_n43(s, auth_identity_id, contract)
            if not ok:
                return False
        return True

    def process_contract_for_n43(self, s: MySession, auth_identity_id: str, contract: Contract) -> bool:
        """
        JF:
        It seems that if we don't download the file it becomes cumulative including all days.
        This is not a problem for us.
        We can manage different extracts from different accounts and different days in the same file
        even if any of these extract were previously managed.
        We must look for a DIARIO_TESORALIA download at any of three tabs
        to confirm programmed download is active.
        This is the way to detect which download should be executed.
        - If programmed download exists it is a programmed and not on demand.
        - If it is a programmed download got to pending tab and download, only pending tab.
        - If contract has not programmed download go to on demand download.
        There is no possibility of mix. If a customer (contract?) has programmed download
        all their accounts will be programmed.
        We can have several programmed download for the same contract, then we will have to download them all.
        """
        org_title = contract.org_title
        self.logger.info('{}: process contract for N43'.format(org_title))

        # First try to download programmed (previously requested and generated) files
        ok, has_programmed_files = self.download_programmed_daily_files(s, auth_identity_id, contract)
        if not ok:
            return False  # already reported

        if has_programmed_files:
            self.logger.info('{}: has programmed files. No need to download files on demand'.format(
                org_title
            ))
            return True

        self.logger.info('{}: no programmed files detected. Start download files on demand'.format(
            org_title
        ))
        accounts_parsed, accounts_multicurrency_parsed = self.get_accounts_parsed(
            s,
            auth_identity_id,
            contract
        )

        for acc in accounts_parsed:
            # On demand (regular) approach
            ok = self.process_account_for_n43(s, auth_identity_id, contract, acc)
            if not ok:
                return False

        accounts_one_subaccount_of_each_multi = [
            list(account_parsed_multicurrency_dict.values())[0]
            for account_parsed_multicurrency_dict
            in accounts_multicurrency_parsed
        ]

        for acc in accounts_one_subaccount_of_each_multi:
            # Regular approach
            ok = self.process_account_for_n43(s, auth_identity_id, contract, acc)
            if not ok:
                return False

        return True

    def download_programmed_daily_files(
            self,
            s: MySession,
            auth_identity_id: str,
            contract: Contract) -> Tuple[bool, bool]:
        """Alternative approach to download programmed previously requested files
        ('Consultar descrargas Norma 43' dropdown -> 'en curso' tab).
        These files must be requested manually before that.
        This is a contract-level option (tabs may contain programmed files for different accounts)

        :return (is_success, found_pending_daily_file)
        """
        org_title = contract.org_title
        self.logger.info("{}: check programmed daily files from 'Consultar descargas Norma 43'".format(
            org_title
        ))
        has_programmed_files = False
        req_headers = self.basic_req_headers_updated({
            'X-BkCompany': contract.id,
            'X-Requested-With': 'XMLHttpRequest'
        })

        # Cuentas -> Norma43 tabs
        tabs = [
            {'title': 'Pendientes de descarga', 'req_param': 'pendiente', 'should_download': True},
            # These tabs contain already downloaded files, only for has_programmed_files detection
            {'title': 'Descardos', 'req_param': 'descargado', 'should_download': False},
            {'title': 'En curso', 'req_param': 'en_curso',  'should_download': False},
        ]

        for tab_dict in tabs:
            tab_name = tab_dict['title']
            tab_req_param = tab_dict['req_param']
            tab_should_download = tab_dict['should_download']

            self.logger.info("{}: {}: check the tab for programmed daily N43 files".format(
                org_title,
                tab_name
            ))

            resp_requested_files = s.get(
                'https://empresasapi.bankinter.com/api/norma43/v2/accountGroups'
                '?status={}&basic=true&authorised={}'.format(tab_req_param, auth_identity_id),
                headers=req_headers,
                proxies=self.req_proxies,
            )
            resp_requested_files_json = resp_requested_files.json()
            daily_files_data = parse_helpers_n43.get_programmed_daily_files_data(resp_requested_files_json)
            for daily_file_data in daily_files_data:
                file_name = daily_file_data['fileRqs'][0]['fileName']

                if TESORALIA_FILENAME_LIKE not in file_name:
                    continue

                has_programmed_files = True

                if not tab_should_download:
                    self.logger.info(
                        "{}: {}: detected already downloaded programmed file '{}'".format(
                            org_title,
                            tab_name,
                            file_name
                        )
                    )
                    continue

                # https://empresasapi.bankinter.com/api/norma43/v2/accountGroups/6b9dc/fileRqs/d981c_B_XBBBB9fcS8/fileId?excel=false
                req_n43_webid_url = (
                    'https://empresasapi.bankinter.com/api/norma43/v2/accountGroups/{}/fileRqs/{}/fileId?excel=false'.format(
                        daily_file_data['id'],
                        daily_file_data['fileRqs'][0]['id']
                    )
                )
                # returns {"webId":"f96e9cfc4f494ea8beeb8dbf9ec579a1.473"}
                resp_n43_webid = s.get(
                    req_n43_webid_url,
                    headers=req_headers,
                    proxies=self.req_proxies
                )

                file_webid = resp_n43_webid.json()['webId']
                ok = self.download_n43_file(
                    s,
                    contract=contract,
                    account_no_or_file_name=file_name,
                    file_webid=file_webid
                )
                if not ok:
                    return False, False  # already reported

                self.logger.info("{}: {}: downloaded daily N43 file with movements '{}'".format(
                    org_title,
                    tab_name,
                    file_name,
                ))

        return True, has_programmed_files

    def process_account_for_n43(
            self,
            s: MySession,
            auth_identity_id: str,
            contract: Contract,
            account_parsed: AccountParsed) -> True:
        org_title = contract.org_title
        req_param_account_id = account_parsed['req_params']['id']
        account_no = account_parsed['account_no']
        # account_no has no currency suffix
        fin_ent_account_id_to_get_dates_and_status = account_no[4:]

        date_from, date_to, is_active_account = self.basic_get_n43_dates_and_account_status(
            fin_ent_account_id_to_get_dates_and_status,
            org_title=org_title,
            max_offset=MAX_OFFSET_DAYS
        )
        if not is_active_account:
            return True  # already reported

        self.logger.info('{}: {}: process_account for N43 from {} to {}'.format(
            org_title,
            account_no,
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        ))

        date_fmt = '%Y-%m-%d'
        req_headers = self.basic_req_headers_updated({
            'X-BkCompany': contract.id,
            'X-Requested-With': 'XMLHttpRequest'
        })

        req_n43_step1_url = 'https://empresasapi.bankinter.com/api/norma43/v2/accounts/{}'.format(req_param_account_id)
        req_n43_step1_params = {
            'to': date_to.strftime(date_fmt),
            'from': date_from.strftime(date_fmt),  # '2022-01-01'
            'isReference': 'false',
            'isValueDate': 'true',
            'isDescription': 'true',
            'isMovements': 'true',
            'authorised': auth_identity_id,
        }

        # {"id":"bcfccDB8c"}
        resp_n43_step1 = s.get(
            req_n43_step1_url,
            params=req_n43_step1_params,
            headers=req_headers,
            proxies=self.req_proxies,
        )
        resp_n43_step1_json = resp_n43_step1.json()

        req_n43_step2_webid_url = 'https://empresasapi.bankinter.com/api/norma43/v2/xmlConverter/fileDownload/{}'.format(
            resp_n43_step1_json['id']
        )

        # {"webId":"5d38d57ea89a4c9bbf5656e447edc8c8.718"}
        resp_n43_step2_webid = s.get(
            req_n43_step2_webid_url,
            headers=req_headers,
            proxies=self.req_proxies,
        )

        ok = self.download_n43_file(
            s,
            contract=contract,
            account_no_or_file_name=account_no,
            file_webid=resp_n43_step2_webid.json()['webId']
        )
        if not ok:
            return False  # already reported

        self.logger.info('{}: {}: downloaded N43 file with movements from {} to {}'.format(
            org_title,
            account_no,
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        ))
        return True

    def download_n43_file(
            self,
            s: MySession,
            contract: Contract,
            account_no_or_file_name: str,
            file_webid: str) -> bool:
        """Common for all initial points"""
        org_title = contract.org_title

        req_headers = self.basic_req_headers_updated({
            'X-BkCompany': contract.id,
            'X-Requested-With': 'XMLHttpRequest'
        })

        resp_n43_step3 = Response()

        for i in range(1, 6):
            req_n43_step3_url = 'https://empresasapi.bankinter.com/api/filetickets/v1/filesDownload/{}/status'.format(
                file_webid
            )
            # {"webId":"5d38d57ea89a4c9bbf5656e447edc8c8.718",
            # "status":"ok",
            # "downloadUrl":"https://empresasapi.bankinter.com/api/filetickets/v1/filesDownload/"
            #               "5d38d57ea89a4c9bbf5656e447edc8c8.718/liftRedirect"}
            resp_n43_step3 = s.get(
                req_n43_step3_url,
                headers=req_headers,
                proxies=self.req_proxies,
            )

            resp_n43_step3_json = resp_n43_step3.json()
            if resp_n43_step3_json['status'] == 'ok':
                break
            # handle "status":"pending"
            # {"webId":"...","status":"pending","downloadUrl":"...ea41.376/liftRedirect"}
            time.sleep(i)
        else:
            self.basic_log_wrong_layout(resp_n43_step3, "{}: {}: can't get valid resp_n43_step3".format(
                org_title,
                account_no_or_file_name
            ))
            return False

        req_n43_step4_url = resp_n43_step3_json['downloadUrl']
        resp_n43 = s.get(
            req_n43_step4_url,
            headers=req_headers,
            proxies=self.req_proxies,
        )

        if not n43_funcs.validate(resp_n43.content):
            self.basic_log_wrong_layout(
                resp_n43,
                "{}: {}: got invalid resp_n43".format(org_title, account_no_or_file_name)
            )
            return False

        self.n43_contents.append(resp_n43.content)

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

        ok = self.process_access_for_n43(s)

        if ok:
            self.basic_save_n43s(
                self.fin_entity_name,
                self.n43_contents
            )

        self.basic_log_time_spent('GET N43')

        if not ok:
            return self.basic_result_common_scraping_error()

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
