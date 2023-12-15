import html
from collections import OrderedDict
from concurrent import futures
from typing import Dict, Tuple

from custom_libs import date_funcs
from custom_libs import requests_helpers
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    AccountParsed, AccountScraped,
    ScraperParamsCommon, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_COOKIE
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.targo_scraper import parse_helpers
from scrapers.targo_scraper.environ_cookies import ENVIRON_COOKIES, ENVIRON_COOKIES_DEFAULT


__version__ = '5.6.0'
__changelog__ = """
5.6.0 2023.07.10
login, process_company, process_account: upd request url to targobank.es
5.5.0
process_account: upd pagination params (_wxf2_ptarget)
5.4.0
upd DOUBLE_AUTH_MARKERS
5.3.0
process_account: upd mov req params
5.2.0
download_correspondence
5.1.0
call basic_upload_movements_scraped with date_from_str
5.0.0
new website urls tomamosimpulso.com
4.12.1
process_account: del req param instead of set None to suppress mypy warnings
4.12.0
process_account: upd req params
parse_helpers: upd get_accounts_parsed, get_movements_parsed (changed layout)
4.11.0
skip inactive accounts
4.10.0
parse_helpers: get_movements_parsed: upd selectors
4.9.0
'no permissions' detector, double auth detector
4.8.0
parse_helpers: parse_mov_3columns (-a 22622), parse_mov_4columns (-a 22950)
4.7.0
use basic_new_session
upd type hints
fmt
4.6.0
ENVIRON_COOKIES
4.5.0
use basic_get_date_from
parse_helpers: get_movements_parsed:
  get temp_balance from 'registered operations' section if provided
4.4.0
process_account: 
  check mov earliest date during the pagination and interrupt the loop if necessary;
  (even with MORE_MOVEMENTS_MARKERS at the page);
  increasing timeout for requests during the pagination
4.3.0
process_account: filter by dates and load more movs (it was from recent movs before) 
parse_helpers: get_movements_parsed: calc temp balance
4.2.0
parse_helpers: get_accounts_parsed: calculate IBAN
4.1.0
movements pagination (for -u 111059 -a 4054)
4.0.0
scrape the new web UI
3.2.0
parse_helpers: handle case for temp_balance if there is additional column 'Cambio'
3.1.1
fixed type hints
3.1.0
basic_movements_scraped_from_movements_parsed: new format of the result
3.0.0
new project structure, basic_movements_scraped_from_movements_parsed w/ date_from_str
2.1.0
movements_parsed_filtered
2.0.0
basic_movements_scraped_from_movements_parsed
OperationalDatePosition, KeyValue support
1.4.0
basic_upload_movements_scraped
accounts_scraped_dict
basic_set_movements_scraping_finished
1.3.0
handle case if home page not accounts_overviews_page
1.2.0
parse_helpers: filter prestamos properly
1.1.0
date_from correct impl 
1.0.3
fix prestamo processing (mark as mov_scrap_in_progr=0)
1.0.2
+ type annotation for mypy
1.0.1
max_workers=len(accounts_parsed)
"""

MORE_MOVEMENTS_MARKERS = ['Más operaciones', 'M&#225;s operaciones']
MAX_MOVEMENTS_PER_PAGE = 50
DOUBLE_AUTH_MARKERS = [
    'Una petición de confirmación móvil ha sido enviada a su dispositivo',  # for old web back comp
    'Autentificaci&#243;n fuerte',  # Tomamos
    'Autentificación fuerte',
]


class TargoScraper(BasicScraper):
    scraper_name = 'TargoScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.update_inactive_accounts = False

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()
        environ_cookies = ENVIRON_COOKIES.get(self.db_financial_entity_access_id, ENVIRON_COOKIES_DEFAULT)
        if environ_cookies:
            self.logger.info('Set confirmed environment cookies for access {}'.format(
                self.db_financial_entity_access_id
            ))
        s = requests_helpers.update_mass_cookies_from_str(s, environ_cookies, '.targobank.es')

        req_url = 'https://www.targobank.es/es/identification/authentification.html'
        req_params = {
            '_cm_user': self.username,
            'flag': 'password',
            '_charset_': 'UTF-8',
            '_cm_pwd': self.userpass,
            # 'submit.x': str(30 + random.randint(0, 10)),
            # 'submit.y': str(10 + random.randint(0, 10)),
        }

        resp = s.post(
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        reason = ''
        if 'Su usuario no está autorizado para acceder a este servicio' in resp.text:
            reason = 'No permissions. Check the website for confirmation'
        if (any(m in resp.text for m in DOUBLE_AUTH_MARKERS)
                or 'SOSD_OTP_GetTransactionState' in resp.url):
            reason = DOUBLE_AUTH_REQUIRED_TYPE_COOKIE
        is_logged = 'Desconectar' in resp.text if not reason else False
        is_credentials_error = 'Algunos de los datos indicados son incorrectos' in resp.text

        return s, resp, is_logged, is_credentials_error, reason

    def process_company(self, s: MySession, resp_logged_in: Response) -> bool:

        req_accounts_url = 'https://www.targobank.es/es/banque/comptes-et-contrats.html'

        resp_accounts = s.get(
            req_accounts_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # from <p class="_c1 a_titre2 _c1">INCLAM SA, espacio cliente | ANDRES PICAZO EVA</p>
        # organization_title = parse_helpers.get_organization_title(resp_accounts.text)
        accounts_parsed = parse_helpers.get_accounts_parsed(resp_accounts.text, self.logger)

        accounts_scraped = [self.basic_account_scraped_from_account_parsed(
            self.db_customer_name,
            account_parsed,
            is_default_organization=True
        ) for account_parsed in accounts_parsed]

        accounts_scraped_dict = self.basic_gen_accounts_scraped_dict(accounts_scraped)

        self.logger.info('Accounts: {}'.format(accounts_scraped))

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        if project_settings.IS_CONCURRENT_SCRAPING and accounts_parsed:
            with futures.ThreadPoolExecutor(max_workers=len(accounts_parsed)) as executor:

                futures_dict = {
                    executor.submit(self.process_account, s, account_parsed, accounts_scraped_dict):
                        account_parsed['account_no']
                    for account_parsed in accounts_parsed
                }

                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_parsed in accounts_parsed:
                self.process_account(s, account_parsed, accounts_scraped_dict)

        self.download_correspondence(
            s,
            resp_logged_in,
            self.db_customer_name,  # as org title
            accounts_scraped
        )

        return True

    def process_account(self, s, account_parsed: AccountParsed,
                        accounts_scraped_dict: Dict[str, AccountScraped]) -> bool:
        """To get more movements, first filter them by dates.

        Important note: websites displays only actual saldo,
        so, date_to always should be = today.

        We'll "click" "more movements" several times
        and then parse all movements (they all will be at the most recent page)
        """

        req_movs_url = account_parsed['req_movs_url']
        fin_ent_account_id = account_parsed['financial_entity_account_id']

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from, date_from_str = self.basic_get_date_from_dt(fin_ent_account_id, max_offset=365)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        # recent movs to get webid
        resp_movs_recent = s.get(
            req_movs_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # will not be changed
        webid_param = parse_helpers.get_webid_param(resp_movs_recent.text)
        wxf2_pseq_param = 2
        # filter by dates
        req_movs_filter_url = 'https://www.targobank.es/es/banque/mouvements.html'
        req_movs_filter_get_params = OrderedDict([
            ('_pid', 'AccountMasterDetail'),
            ('k_webid', webid_param),
            ('k_cardmonth', ''),
            ('k_rib', ''),
            ('k_viewmode', ''),
            ('k_prcrefresh', ''),
            ('k_cardid', ''),
            ('k_SDSF_I14TRANSACTIONS_VIEW', ''),
            ('k_onglet', ''),
            ('k_asyncaction', '')
        ])

        req_movs_filter_post_params = OrderedDict([
            ('[t:dbt%3adate;]Data_FormSearchParmeters_StartDate', date_from_str),
            ('[t:dbt%3adate;]Data_FormSearchParmeters_EndDate', self.date_to_str),  # '30/01/2022'
            ('[t:xsd%3adecimal;]Data_FormSearchParmeters_StartAmount', ''),
            ('[t:xsd%3adecimal;]Data_FormSearchParmeters_EndAmount', ''),
            ('[t:xsd%3astring;]Data_FormSearchParmeters_Label', ''),
            ('Data_Sort', 'OPEDATE_D'),
            ('_wxf2_cc', 'es-ES'),
            ('_FID_DoSearch', ''),
            ('Data_Persistance', ''),
            ('Data_AccountDetailViewModel_SelectedTabKey', 'SITUATION'),
            ('Data_AccountDetailViewModel_SelectedChartKey', ''),
            ('Data_AccountDetailViewModel_ContractTabTitle', ''),
            ('Data_AccountDetailViewModel_SimulationTitle', ''),
            ('Data_SearchParmetersCurrent_StartDate', ''),  # '20210801'
            ('Data_SearchParmetersCurrent_EndDate', ''),
            ('Data_SearchParmetersCurrent_StartAmount', ''),
            ('Data_SearchParmetersCurrent_EndAmount', ''),
            ('Data_SearchParmetersCurrent_Label', ''),
            ('Data_WATInfoTransactions_OpenFilter',
             '{"Category":"Navigation", "Action":"Clic", "Label":"OuvertureFiltrage"}'),
            ('Data_WATInfoTransactions_DownloadExcel',
             '{"Category":"Navigation", "Action":"Clic", "Label":"Telechargement/Excel"}'),
            ('Data_WATInfoTransactions_DownloadOther',
             '{"Category":"Navigation", "Action":"Clic", "Label":"Telechargement/Autres"}'),
            ('Data_WATInfoTransactions_Print',
             '{"Category":"Navigation", "Action":"Clic", "Label":"Imprimer"}'),
            ('Data_WATInfoTransactions_AnnouncedTransactions',
             '{"Category":"Navigation", "Action":"Clic", "Label":"ProchainesOperations"}'),
            ('Data_WATInfoTransactions_ShowInterco',
             '{"Category":"Navigation", "Action":"Clic", "Label":"Ver empresas asociadas"}'),
            ('Data_WATInfoTransactions_ShowInsurances',
             '{"Category":"Navigation", "Action":"Clic", "Label":"Sus contratos y nuestras ofertas"}'),
            ('Data_WATInfoTransactions_ChangeCard',
             '{"Category":"Navigation", "Action":"Clic", "Label":"ChangementDeCarte"}'),
            ('Data_SearchDateStart', ''),
            ('Data_SearchDateEnd', ''),
            ('Data_SearchAmountStart', ''),
            ('Data_SearchAmountEnd', ''),
            ('Data_SearchLabel', ''),
            ('Data_rib', ''),
            ('Data_AccountLabel1', account_parsed['title']),  # 'CREDITO CON GARANTIA PERSONAL'
            ('Data_YearMonth', ''),
            ('Data_SelectedCardItemKey', ''),
            ('Data_DropDownAccountItemsCurrentLink', ''),
            ('Data_WebId', webid_param),  # 'd7605cffae0f469bd8f908d0d471932efe44dea543dfde3d1bbb03fb0ff2281d'
            ('Data_Searching', 'false'),
            ('Data_TransactionSearchLogId', '0'),
            ('Data_AccountFilter', ''),
            ('Data_FilterString', ''),
            ('Data_ActivedFilter', 'false'),
            ('Data_WebAnalyticsAdditionalInfosJson',
             '{{"url_page":"/mouvements/{}/Situation/","domaine_fonctionnel":"Comptes","fonction":"Detail",'
             '"application_name":"Mouvements"}}'.format(account_parsed['title'])),
            ('Data_WATFilterAccountResult', ''),
            ('Data_WATFilterTransactionResult', ''),
            ('Data_WATPaging',
             '{"Category":"Navigation", "Action":"Pagination", "Label":"2"}'),
            ('Data_WATDefaultAdviceGateway',
             '{"Category":"Navigation", "Action":"Clic", "Label":"TousNosConseils"}'),
            ('_wxf2_pseq', str(wxf2_pseq_param)),  # '2'
            ('_wxf2_pmode', 'Normal'),
            ('_wxf2_ptarget', 'I0:d1.D4:A:ub')
        ])

        resp_movs_filtered_unescaped_text = ''  # most recent

        # fetch until receive resp with 'more movememts' marker
        # then parse: all movement will be available on the last page

        # fixed length loop to avoid hanged loop
        for page in range(1, 21):
            self.logger.info("{}: open page #{} with movements".format(fin_ent_account_id, page))
            resp_movs_filtered_i = s.post(
                req_movs_filter_url,
                params=req_movs_filter_get_params,
                data=req_movs_filter_post_params,
                headers=self.basic_req_headers_updated({
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': resp_movs_recent.url
                }),
                proxies=self.req_proxies,
                # should increase timeout because
                # backend returns the current + all previous pages
                timeout=20 + 2 * page,
            )

            if page > 10:
                self.logger.warning("{}: too many movements, the scraper may fail. "
                                    "Try to set shorter range for dates")

            # xml resp contains escaped symbols which break the parsing
            resp_movs_filtered_unescaped_text = html.unescape(resp_movs_filtered_i.text)

            movements_parsed_i = parse_helpers.get_movements_parsed(
                resp_movs_filtered_unescaped_text,
                fin_ent_account_id,
                self.logger
            )
            if movements_parsed_i:
                mov_earliest = movements_parsed_i[-1]
                self.logger.info("{}: page#{}: got earliest mov of {}, looking for {}".format(
                    fin_ent_account_id,
                    page,
                    mov_earliest['operation_date'],
                    date_from_str
                ))
                # early break if got too early movement (even with MORE_MOVEMENTS_MARKERS at the page)
                date_mov_earliest = date_funcs.get_date_from_str(mov_earliest['operation_date'])
                if date_mov_earliest < date_from:
                    break

            should_fetch_more_movs = any(m in resp_movs_filtered_unescaped_text
                                         for m in MORE_MOVEMENTS_MARKERS)

            # next page and further
            if should_fetch_more_movs:
                if '_FID_DoSearch' in req_movs_filter_post_params:
                    del req_movs_filter_post_params['_FID_DoSearch']
                req_movs_filter_post_params['_FID_DoLoadMoreTransactions'] = ''
                req_movs_filter_post_params['Data_Persistance'] = parse_helpers.get_data_persistence_param(
                    resp_movs_filtered_unescaped_text
                )
                req_movs_filter_post_params['Data_Searching'] = 'true'

                # "20210701"
                req_movs_filter_post_params['Data_SearchParmetersCurrent_StartDate'] = date_from.strftime('%Y%m%d')
                req_movs_filter_post_params['Data_SearchParmetersCurrent_EndDate'] = self.date_to.strftime('%Y%m%d')
                req_movs_filter_post_params['Data_WATFilterTransactionResult'] = \
                    '{"Category":"Filtrage", "Action":"Operations", "Label":"ResultatTrouve"}'
                # targo (-a 20702, 'ES9102167611308300724164')
                # req_movs_filter_post_params['_wxf2_ptarget'] = 'I1:d1.D4:A1:ub.ut'
                # tomamosimpulso (-a 30727 -f 01/03/2021)
                req_movs_filter_post_params['_wxf2_ptarget'] = 'I0:d1.D4:A:ub.ut'
                wxf2_pseq_param += 1
                req_movs_filter_post_params['_wxf2_pseq'] = str(wxf2_pseq_param)
                continue

            break

        movements_parsed = parse_helpers.get_movements_parsed(
            resp_movs_filtered_unescaped_text,
            fin_ent_account_id,
            self.logger
        )

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            accounts_scraped_dict[fin_ent_account_id],
            movements_scraped,
            date_from_str=date_from_str
        )
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

        self.process_company(s, resp_logged_in)

        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
