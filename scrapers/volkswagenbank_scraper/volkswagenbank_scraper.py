import os
import urllib.parse
import urllib.parse
import urllib.request
from concurrent import futures
from typing import *

from custom_libs import extract
from project import settings as project_settings
from project.custom_types import AccountScraped, ScraperParamsCommon, MOVEMENTS_ORDERING_TYPE_ASC
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.volkswagenbank_scraper import parse_helpers
from scrapers.volkswagenbank_scraper import req
from scrapers.volkswagenbank_scraper.custom_types import ContractData


__version__ = "3.3.0"

__changelog__ = """
3.3.0
call basic_upload_movements_scraped with date_from_str
3.2.0
use basic_get_date_from
3.1.0
basic_movements_scraped_from_movements_parsed: new format of the result
3.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
2.0.0
basic_movements_scraped_from_movements_parsed
OperationalDatePosition, KeyValue support
1.1.0
accounts_scraped_dict
"""


def read_saved_images_with_digits() -> Dict[int, bytes]:
    """Read saved images with digits to use them to detect place at the page of each digit"""
    folder = os.path.join(os.path.curdir, 'scrapers', 'volkswagenbank_scraper', 'saved_images')
    nums_bytes_dict = {}
    for num in range(0, 10):
        with open(os.path.abspath(os.path.join(folder, '{}.gif').format(num)), 'rb') as f:
            num_bytes = f.read()
            nums_bytes_dict[num] = num_bytes
    return nums_bytes_dict


class VolkswagenBankScraper(BasicScraper):
    """
    The scraper uses custom req.VWSession to obtain correct SSL processing
    """
    scraper_name = 'VolkswagenBankScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    def _get_encrypted(self, s, resp_html, userpass: str):
        """
        Download digits from positions
        Then compare with saved to get map number: position
        Then reproduce password
        """

        saved_images = read_saved_images_with_digits()

        s = req.VWSession()

        digit_positions_named = ['A1', 'A2', 'A3', 'A4', 'A5', 'B1', 'B2', 'B3', 'B4', 'B5']
        digit_to_position = {}

        # todo make concurrent
        for digit_position_named in digit_positions_named:
            digit_url = urllib.parse.urljoin(
                'https://www.volkswagenbank.es/',
                parse_helpers.get_digit_href(resp_html, digit_position_named)
            )
            resp_digit_png = s.get(
                digit_url,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            digit_from_png = parse_helpers.get_digit_from_png(saved_images, resp_digit_png.content)
            digit_to_position[digit_from_png] = digit_position_named

        userpass_encrypted = ''
        for digit_str in userpass:
            userpass_encrypted += digit_to_position[int(digit_str)]

        return userpass_encrypted

    def login(self):

        s = req.VWSession()

        req_init_url = 'https://www.volkswagenbank.es/clientes/central_particular.jsp'

        resp_init_page = s.get(
            req_init_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        login_action_url, req_params = extract.build_req_params_from_form_html(
            resp_init_page.text,
            'myform'
        )

        # fill with leading zeros to 10 digits
        req_params['HB_USU_FINAL_CONEX'] = '{:010}'.format(int(self.username))
        req_params['HB_PSW_FINAL_CONEX'] = self._get_encrypted(s, resp_init_page.text, self.userpass)
        req_params['usuario'] = self.username
        req_params['GSO:SUBSDES'] = 'Inicio'
        req_params['onAnar'] = 'Inicio'

        req_login_url = urllib.parse.urljoin(resp_init_page.url, login_action_url)
        resp_logged_in = s.post(
            req_login_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = 'Nombre del contrato' in resp_logged_in.text
        is_credentials_error = 'acceso incorrectos' in resp_logged_in.text

        return s, resp_logged_in, is_logged, is_credentials_error

    def process_contract(self, s, resp_logged_in, contract_data: ContractData):

        # open contract home page

        contract_url = contract_data.url
        organization_title = contract_data.organization_title

        self.logger.info('Process contract: {}'.format(organization_title))

        resp_contract_home = s.get(
            contract_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_contract_menu_url = parse_helpers.get_contract_menu_frame_url(
            resp_contract_home.url,
            resp_contract_home.text
        )
        resp_contract_menu = s.get(
            req_contract_menu_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_position_global_url = parse_helpers.get_position_global_url(
            resp_contract_menu.url,
            resp_contract_menu.text
        )
        resp_position_global = s.get(
            req_position_global_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_parsed = parse_helpers.get_accounts_parsed(resp_position_global.text)

        accounts_scraped = [self.basic_account_scraped_from_account_parsed(organization_title, acc_parsed)
                            for acc_parsed in accounts_parsed]

        accounts_scraped_dict = self.basic_gen_accounts_scraped_dict(accounts_scraped)

        self.logger.info('Contract {} has accounts {}'.format(organization_title, accounts_scraped))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        if project_settings.IS_CONCURRENT_SCRAPING and accounts_scraped:
            with futures.ThreadPoolExecutor(max_workers=len(accounts_scraped)) as executor:

                futures_dict = {
                    executor.submit(self.process_account, s, resp_position_global,
                                    account_parsed, accounts_scraped_dict): account_parsed['account_no']
                    for account_parsed in accounts_parsed
                }

                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_parsed in accounts_parsed:
                self.process_account(s, resp_position_global, account_parsed, accounts_scraped_dict)

        return accounts_scraped

    def process_account(self, s, resp_position_global, account_parsed,
                        accounts_scraped_dict: Dict[str, AccountScraped]):
        # cuentas -> consulta -> ultimos movimientos
        # filter allows to extract all movements between dates range 1 month
        # if too long list

        fin_ent_account_id = account_parsed['financial_entity_account_id']
        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        date_from_str_param = date_from_str.replace('/', '-')

        mov_req_href = (
            account_parsed['account_movements_href']
            + '&AP_N_ULTIMOS='
            + '&AP_FECHA_INICIO={}'.format(date_from_str_param)
            + '&AP_FECHA_FIN='
            + '&AP_IMP_DESDE='
            + '&AP_IMP_HASTA='
        )

        mov_req_url = urllib.parse.urljoin(resp_position_global.url, mov_req_href)

        resp_mov = s.get(
            mov_req_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        movements_parsed = parse_helpers.get_movements_parsed(resp_mov.text)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_upload_movements_scraped(
            accounts_scraped_dict[fin_ent_account_id],
            movements_scraped,
            date_from_str=date_from_str
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        return movements_scraped

    def main(self):
        s, resp_logged_in, is_logged, is_credentials_error = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url, resp_logged_in.text)

        contracts_data = parse_helpers.get_contracts_data(resp_logged_in.url, resp_logged_in.text)

        if project_settings.IS_CONCURRENT_SCRAPING and contracts_data:
            with futures.ThreadPoolExecutor(max_workers=len(contracts_data)) as executor:

                futures_dict = {
                    executor.submit(self.process_contract,
                                    s, resp_logged_in, contract_data): contract_data
                    for contract_data in contracts_data
                }

                self.logger.log_futures_exc('open_contract_home_page_and_process', futures_dict)
        else:
            for contract_data in contracts_data:
                self.process_contract(s, resp_logged_in, contract_data)

        self.basic_log_time_spent('GET ALL BALANCES AND MOVEMENTS')
        return self.basic_result_success()
