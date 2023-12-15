from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from custom_libs.myrequests import MySession
from project import settings as project_settings
from project.custom_types import (DBTransferAccountConfig, TransferParsed, MovementParsed,
                                  ScraperParamsCommon, MainResult, AccountScraped)
from scrapers.bbva_scraper.bbva_netcash_scraper import BBVANetcashScraper

__version__ = '0.2.0'
__changelog__ = """
0.2.0
fixed import
"""

PROCESS_TRANSFER_MAX_WORKERS = 1
DOWNLOAD_TRANSFERS_DAYS_BEFORE_DATE_TO = 15


# TODO for Joaquin:
#  just copy-paste this code to the scraper you're developing


class BBVANetcashTransfersScraperMov(BBVANetcashScraper):
    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BBVANetcashTransfersScraperMov') -> None:

        super().__init__(scraper_params_common, proxies, scraper_name)

    def date_from_for_transfers(self, active_transfer_account: DBTransferAccountConfig) -> datetime:
        """
        JFM: if self.date_from_param_str is not provided,
        we process transfers from DOWNLOAD_TRANSFERS_DAYS_BEFORE_DATE_TO days before from "date_to"
        """
        if self.date_from_param_str:
            date_from = datetime.strptime(self.date_from_param_str, project_settings.SCRAPER_DATE_FMT)
        else:
            if active_transfer_account.LastScrapedTransfersTimeStamp:
                date_from = active_transfer_account.LastScrapedTransfersTimeStamp
            else:
                date_from = self.date_to - timedelta(days=DOWNLOAD_TRANSFERS_DAYS_BEFORE_DATE_TO)
        return date_from

    # entry point
    def download_transfers(self, s: MySession) -> Tuple[bool, List[TransferParsed]]:
        active_transfers_accounts = self.db_connector.get_active_transfers_accounts()
        if not active_transfers_accounts:
            return True, []

        # VB: my part
        movs_of_accs = self.get_movements_for_transfers(s, active_transfers_accounts)
        # VB: / my part
        # todo impl mov processing
        self.logger.info('Got movements for transfers: total {}'.format(
            {acc: len(movs) for acc, movs in movs_of_accs.items()}
        ))
        self.logger.info('Pls, implement further processing.')
        return True, []

    def get_movements_for_transfers(
            self,
            s: MySession,
            active_transfers_accounts: List[DBTransferAccountConfig]) -> Dict[str, List[MovementParsed]]:
        """
        :return: {fin_ent_account_id: movements_parsed_asc}
        """

        _, resp_json, accounts_scraped = self.get_accounts_scraped(s)
        movs_of_accs = {}  # type: Dict[str, List[MovementParsed]]
        for active_transfer_account in active_transfers_accounts:
            # Expecting 1 acc
            accounts_scraped_filtered = [
                acc
                for acc in accounts_scraped
                if acc.FinancialEntityAccountId == active_transfer_account.FinancialEntityAccountId
            ]
            if len(accounts_scraped_filtered) != 1:  # handle 0 (not found) or >1 (select err)
                self.logger.error('{}: no corresponding account_scraped. Skip'.format(
                    active_transfer_account
                ))
                movs_of_accs[active_transfer_account.FinancialEntityAccountId] = []
                continue

            movs_parsed_asc = self.get_movements_for_transfers_one_acc(
                s,
                accounts_scraped_filtered[0],  # 1 really corresponding AccountScraped
                active_transfer_account
            )
            movs_of_accs[active_transfer_account.FinancialEntityAccountId] = movs_parsed_asc
        return movs_of_accs

    def get_movements_for_transfers_one_acc(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            active_transfer_account: DBTransferAccountConfig) -> List[MovementParsed]:
        self.logger.info('{}: get_movements_for_transfers_one_acc'.format(
            active_transfer_account.FinancialEntityAccountId
        ))

        date_from = self.date_from_for_transfers(active_transfer_account)
        # VB: Need to get all movements and then filter here by codigo_param,
        # otherwise backend returns movements without 'temp_balance' (saldo) data
        movements_parsed_asc, _ = self.get_movements_parsed(
            s,
            account_scraped,
            date_from,
            concepto_params=['0391', '0591']
        )
        self.logger.info('{}: got {} movements for transfers: {}'.format(
            account_scraped.FinancialEntityAccountId,
            len(movements_parsed_asc),
            movements_parsed_asc
        ))
        return movements_parsed_asc

    def main(self) -> MainResult:
        s, resp, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp.url, resp.text, reason)

        self.download_transfers(s)
        self.basic_log_time_spent('GET TRANSFERS')

        return self.basic_result_success()
