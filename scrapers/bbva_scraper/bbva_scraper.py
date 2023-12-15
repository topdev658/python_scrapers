from typing import Optional

from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.bbva_scraper.bbva_netcash_scraper import BBVANetcashScraper
from scrapers.bbva_scraper.bbva_particulares_scraper import BBVAParticularesScraper

__version__ = '8.1.1'

__changelog__ = """
8.1.1
upd type hints
8.1.0
exception -> error on unsupported access type
8.0.0
Selects concrete scraper based on access type.
Previous BBVA scraper was moved to bbva_netcash_scraper.
Now BBVA scraper supports both: BBVA Netcash and BBVA Particulares access types.
This class is the switcher to select concrete scraper to run scraping process 
7.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
6.0.0
basic_movements_scraped_from_movements_parsed
OperationalDatePosition, KeyValue support
5.0.1
fixed: call basic_upload_movements_scraped descending ordering
5.0.0
extract movements from excel
4.6.0
basic_upload_movements_scraped
4.5.0
parse_helpers: description_additional 
4.4.0
use param 'eai_password' = self.userpass.upper()[:8] (!) or will receive credentials error
4.3.0
req_params upd to fix processing companies without favorite accounts
4.2.0
is_default_organization
4.1.0
from libs import myrequests as requests  # redefine requests behavior
4.0.0
parse_helpers: convert BBAN to IBAN
3.2.0
date_from in upload_mov
3.1.0
basic_log_process_acc
3.0.0
_get_date_from_for_account_str_by_fin_ent_acc_id	
upload_mov_by_fin_ent_acc_id
account_scraped instead of account_parsed in process_account
2.0.0
'account_iban' -> 'account_no'
1.1.0
is_logged_in, is_cred_err 
1.0.1
username, pass upper
1.0.0
init
"""


class BBVAScraper(BasicScraper):
    """The class used to launch concrete scraper based on access type
    due to too different scraping approaches"""

    scraper_name = 'BBVAScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        self.access_type_scraper = None  # type: Optional[BasicScraper]
        if self.access_type == 'BBVA net cash':
            self.access_type_scraper = BBVANetcashScraper(scraper_params_common, proxies)
            self.logger.info('Select BBVANetcash scraper')
        elif self.access_type == 'BBVA Particulares':
            self.access_type_scraper = BBVAParticularesScraper(scraper_params_common, proxies)
            self.logger.info('Select BBVAParticulares scraper')
        else:
            self.logger.error('UNSUPPORTED access type: {}'.format(self.access_type))

    def main(self) -> MainResult:
        if not self.access_type_scraper:
            return self.basic_result_common_scraping_error()

        return self.access_type_scraper.main()
