import datetime
import re
from collections import OrderedDict
from typing import Dict, List, Tuple

from custom_libs import convert
from custom_libs import extract
from custom_libs import requests_helpers
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    ACCOUNT_NO_TYPE_UNKNOWN, ACCOUNT_TYPE_DEBIT, AccountParsed,
    AccountScraped, ScraperParamsCommon, MainResult, MovementParsed
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.santander_chile_scraper import parse_helpers
from scrapers.santander_chile_scraper.custom_types import SantanderChileCompany

__version__ = '2.3.0'
__changelog__ = """
2.3.0 2023.05.26
_extract_accounts_parsed: 
    extracted hash_data from the resp_accounts json, necessary for the following requests
    raise exception when we can't extract accounts or hash_data
    removed unnecessary loop to extract debit and credit accounts
process_account: refactored fin_ent_account_id and deleted manual max_offset
2.2.1
process_account: fixed pagination: handled None Result for closed accounts
2.2.0
process_account: pagination
2.1.0
upd requests and parsing
2.0.0
1-contract access support (1 - 31403, multi - 14702)
login, _extract_accounts_parsed: upd reqs 
SantanderChileCompany struct: removed unused fields
use extract module funcs instead of custom
parse_helpers: upd get_companies, removed unused
1.4.0
call basic_upload_movements_scraped with date_from_str
1.3.0
use basic_new_session
upd type hints
fmt
1.2.0
use basic_get_date_from
1.1.0
_extract_accounts_parsed: fixed false positive exception on assertion if balance == 0
replace (try/except -> if) where possible
improved err msgs
1.0.0
init
"""


class SantanderChileScraper(BasicScraper):
    """Only serial processing to avoid auth_token collisions
    (faced as the website)
    """
    scraper_name = 'SantanderChileScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    def _auth_headers(self, auth_token: str) -> Dict[str, str]:
        return self.basic_req_headers_updated({
            'X-Requested-With': 'XMLHttpRequest',
            'Authorization': 'Bearer {}'.format(auth_token),
            'Content-Type': 'application/json'
        })

    def _get_new_auth_token(self, s: MySession, err_msg_payload: str) -> str:
        req_token_url = 'https://eob.officebanking.cl/CTA.UI.Services/Token'
        req_token_headers = self.basic_req_headers_updated({
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://eob.officebanking.cl/CTA.UI.Web/saldoctacte/?servicioId=TRNCNA_SDOCTACTE'
        })
        req_token_params = {'grant_type': 'password'}
        resp_token = s.post(
            req_token_url,
            data=req_token_params,
            headers=req_token_headers,
            proxies=self.req_proxies
        )

        auth_token = resp_token.json().get('access_token', '')
        if not auth_token:
            self.logger.error("{}: can't get access token\nRESPONSE:\n{}\n\nSkip".format(
                err_msg_payload, resp_token.text
            ))
        return auth_token

    def login(self) -> Tuple[MySession, Response, bool, bool]:
        s = self.basic_new_session()

        _resp_init = s.get(
            'https://www.santander.cl/empresas/index.asp',
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        s = requests_helpers.update_mass_cookies(s, {
            'stndr': 'empresas',
            'webmatico': 'no',
            'tmp': 'temporal',
        }, domain='.officebanking.cl')

        req_login_url = 'https://www.officebanking.cl/login.asp'

        req_login_params = OrderedDict([
            ('d_rut', ''),  # self.username
            ('d_pin', ''),  # self.userpass
            ('botonenvio', ''),
            ('hrut', re.sub(r'\D', '', self.username)),
            ('pass', self.userpass[:8]),
            ('optsgd', 'ATN'),
            ('rut', ''),
            ('IDLOGIN', 'BancoSantander'),
            ('tipo', '0'),
            ('pin', ''),
            ('usateclado', 'no'),
            ('dondeentro', 'home'),
            ('rslAlto', '768'),  # screen resolution y
            ('rslAncho', '1366')  # screen resolution x
        ])

        resp_logged_in = s.post(
            req_login_url,
            data=req_login_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_logged = (
                'SANTANDER OFFICE BANKING' in resp_logged_in.text  # many companies
                or 'id="empresas-form"' in resp_logged_in.text  # one company - web does auto submit
        )
        is_credentials_error = 'Se ha detectado un error en los datos ingresados' in resp_logged_in.text

        return s, resp_logged_in, is_logged, is_credentials_error

    def process_companies(self, s: MySession) -> bool:
        req_compaies_url = 'https://www.officebanking.cl/empresas.asp'
        resp_companies = s.get(
            req_compaies_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # https://www.officebanking.cl/in_bie.htm ??
        _, req_select_company_params = extract.build_req_params_from_form_html_patched(
            resp_companies.text,
            form_name='empresas',
            is_ordered=True
        )
        companies = (parse_helpers.get_companies(resp_companies.text) or
                     parse_helpers.get_companies_one_contract(resp_companies.text))

        self.logger.info('Got {} contracts: {}'.format(
            len(companies),
            companies
        ))

        for company in companies:
            self.process_company(s, req_select_company_params.copy(), company)

        return True

    def _extract_accounts_parsed(self, s: MySession,
                                 organization_title: str,
                                 auth_token: str) -> List[AccountParsed]:
        accounts_parsed = []  # type: List[AccountParsed]
        req_headers_auth = self._auth_headers(auth_token)

        req_accounts_url = 'https://eob.officebanking.cl/CTA.UI.Services/api/saldocuentacorriente/cuentas'

        # {"Cuentas":[{"NumeroCuenta":"20109939","CodigoProductoCuenta":"0","NumeroCuentaFormated":"0-000-2010993-9"}],
        # "DatosHash":"7gQOrkKmaBIBKgTGgt/X52m4k7CwO48+emq51rWOgQZY/ck0H..."}
        resp_accounts = s.get(
            req_accounts_url,
            headers=req_headers_auth,
            proxies=self.req_proxies
        )
        try:
            # {'20109939': '0-000-2010993-9'}
            accounts = {acc['NumeroCuenta']: acc['NumeroCuentaFormated'] for acc in resp_accounts.json()['Cuentas']}
            # Extract hash_data from the resp_accounts json, necessary for the following requests
            hash_data = resp_accounts.json()['DatosHash']  # '7gQOrkKmaBIBKgTGgt/X52m4k7CwO48+emq51rWOgQZY/ck0H...'
        except Exception as exc:
            self.logger.error(
                "Company {}: can't get accounts: handled exc {}:"
                "\nRESPONSE\n{}".format(
                    organization_title, exc, resp_accounts.text
                )
            )
            raise Exception("Can't extract accounts", exc)

        for fin_ent_account_id, account_no in accounts.items():
            # GET CURRENCY
            # {"Result":{"CodigoMoneda":"CLP","GlosaMoneda":"PESOS DE CHILE",
            # "CuentaNumero":"0-000-2010993-9","GlosaSucursal":"Principal",
            # "CodigoSucursal":"0250","FechaHoy":"0001-01-01T00:00:00"},
            # "ErrorCode":null,"ErrorDescription":null,"ErrorSource":null,"Mensaje":null,"Status":2}
            resp_acc_currency = s.post(
                'https://eob.officebanking.cl/CTA.UI.Services/api/saldocuentacorriente/datoscliente',
                json={"NumeroCuenta": fin_ent_account_id, "DatosHash": hash_data},  # '64578146'
                headers=req_headers_auth,
                proxies=self.req_proxies
            )

            currency = resp_acc_currency.json().get('Result', {}).get('CodigoMoneda', '')  # CLP
            if not currency:
                self.logger.error("Account {}: can't get currency:\nRESPONSE:\n{}\n\nSkip".format(
                    fin_ent_account_id, resp_acc_currency.text
                ))
                continue

            # GET BALANCE
            #  {"Result":{"SaldoTotal":"$ 7.413.469","EsCashPooling":false,
            # "SaldoDisponibleConsolidado":"$ 7.413.469","SaldoDisponible":"$ 7.413.469",
            # "Cheque1":"8190224","Cheque2":"8190225","Cheque3":"1344130","Cheque4":"8190228",
            # "DepositosConRetenciones":"$ 0","Retenciones1Dia":"Sin información",
            # "Retenciones2a4Dias":"Sin información","Retenciones4Mas":"Sin información",
            # "SaldoCuentaAsociada":"$ 0"},"ErrorCode":null,"ErrorDescription":null,"ErrorSource":null,
            # "Mensaje":null,"Status":2}
            resp_acc_balance = s.post(
                'https://eob.officebanking.cl/CTA.UI.Services/api/saldocuentacorriente/saldos',
                # {"NumeroCuenta":"64578146","CodigoMoneda":"CLP"}
                json={"NumeroCuenta": fin_ent_account_id, "CodigoMoneda": currency, "DatosHash": hash_data},
                headers=req_headers_auth,
                proxies=self.req_proxies
            )

            account_balance_str = resp_acc_balance.json().get('Result', {}).get('SaldoTotal')
            if not account_balance_str:
                self.logger.error("Account {}: can't get balance:\nRESPONSE:\n{}\n\nSkip".format(
                    fin_ent_account_id, resp_acc_balance.text
                ))
                continue

            account_balance = convert.to_float(account_balance_str)

            account_parsed = {
                'account_no': account_no,
                'financial_entity_account_id': fin_ent_account_id,
                'account_type': ACCOUNT_TYPE_DEBIT,  # only debit accounts
                'currency': currency,
                'balance': account_balance,
            }
            accounts_parsed.append(account_parsed)

        return accounts_parsed

    def process_company(self, s: MySession,
                        req_select_company_params: Dict[str, str],
                        company: SantanderChileCompany) -> bool:
        org_title = company.org_title
        # Expected req_select_company_params:
        #
        # ModoAcceso	B
        # changeEmp	Falso
        # Autenticado	Verdadero
        # nom_prsna_etcdo	MARIA IGNACIA SILVA ROBLES
        # Autorizado	Verdadero
        # UsuarioNoOFB	0
        # UsuarioOFB	1
        # TipoAutenticacion	NRM
        # GLS_SEGMENTO	CLIENTES
        # nro_prsna_usr	0170892100
        # Login_Autorizado_HE	Verdadero
        # EstadoTCC
        # CLVSP001
        # Cod_srv
        # url_btn_ses	https://www.officebanking.cl
        # btnpnc	0
        # btnDFTN	PantOB_Blanca.asp
        # btnDFT3	https://www.officebanking.cl/campna/CAMPANAS_OB/PAGO_IMPUESTOS/
        # btnDFT4	ERC
        # btnDFT6	ERC
        # btnDFT92	https://www.officebanking.cl/campna/CAMPANAS_OB/APO_DELEGADO/BANNER.ASPX
        # btnDFT00	ERC
        # NoticiaOFB20
        # empSel	0002000100069001456733009684753040COMSA INDUSTRIAL CHILE S.A.
        req_select_company_params['empSel'] = company.empSel_param
        req_company_home_url = 'https://www.officebanking.cl/aceptado.asp'

        # necessary to switch to company
        _resp_company_home = s.post(
            req_company_home_url,
            data=req_select_company_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # to get EOBT cookie
        _resp_pre_token = s.get(
            'https://www.officebanking.cl/EOB/Redirect.asp?cod_srv=TRNCNA_SDOCTACTE',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        auth_token = self._get_new_auth_token(s, 'Company {}'.format(company.empSel_param))
        if not auth_token:
            return False

        accounts_parsed = self._extract_accounts_parsed(s, org_title, auth_token)
        if not accounts_parsed:
            self.logger.warning('{}: suspicious results: no accounts_parsed'.format(org_title))
        accounts_scraped = [self.basic_account_scraped_from_account_parsed(
            org_title or self.db_customer_name,
            account_parsed,
            country_code='CHL',  # Chile
            account_no_format=ACCOUNT_NO_TYPE_UNKNOWN,
            is_default_organization=not org_title
        ) for account_parsed in accounts_parsed]

        self.logger.info('{}: got {} accounts: {}'.format(org_title, len(accounts_parsed), accounts_parsed))
        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET ACCOUNTS')

        for account_scraped in accounts_scraped:
            self.process_account(s, company, account_scraped)

        return True

    def _get_account_max_date_to(self, s: MySession,
                                 fin_ent_acoount_id: str, auth_token: str) -> str:
        """For some accounts impossible to get movements till the current date.
        Get the max date here
        """

        # {"Result":{"CodigoMoneda":"USD","GlosaMoneda":"DOLAR U.S.A.",
        # "CuentaNumero":"0-051-0010162-0","GlosaSucursal":"B. CORPORATIVA",
        # "CodigoSucursal":"0181","FechaHoy":"2018-12-01T00:00:00-03:00"},
        # "ErrorCode":null,"ErrorDescription":null,"ErrorSource":null,"Mensaje":null,"Status":2}
        req_acc_info_url = ('https://eob.officebanking.cl/CTA.UI.Services/api/'
                            'ConsultaMovimientosCtaCte/datoscliente/{}'.format(fin_ent_acoount_id))
        resp_acc_info = s.get(
            req_acc_info_url,
            headers=self._auth_headers(auth_token),
            proxies=self.req_proxies
        )
        resp_json = resp_acc_info.json()
        date_to_max_str = (resp_json.get('Result') or {}).get('FechaHoy', '')  # "2018-12-01T00:00:00-03:00"
        if not date_to_max_str:
            self.logger.error(
                "{}: can't get max_date. Use self.date_to_str\nRESPONSE:\n{}".format(
                    fin_ent_acoount_id,
                    resp_acc_info.text
                )
            )
            return self.date_to_str

        date_to_str = datetime.datetime.strftime(
            datetime.datetime.strptime(date_to_max_str.split('T')[0], '%Y-%m-%d'),
            project_settings.SCRAPER_DATE_FMT
        )
        return date_to_str

    def process_account(
            self,
            s: MySession,
            company: SantanderChileCompany,
            account_scraped: AccountScraped) -> bool:
        org_title = company.org_title
        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)
        auth_token = self._get_new_auth_token(s, 'Account {}'.format(fin_ent_account_id))
        if not auth_token:
            return False

        date_to_str = self._get_account_max_date_to(s, fin_ent_account_id, auth_token)

        d_f, m_f, y_f = date_from_str.split('/')
        d_t, m_t, y_t = date_to_str.split('/')

        req_mov_url = ('https://eob.officebanking.cl/CTA.UI.Services/api/'
                       'ConsultaMovimientosCtaCte/ObtenerMovimientos')
        # for movs 2018-11-16...2018-11-30
        # {"FechaDesde":"2018-11-15T21:00:00.0000000+03:00",
        # "FechaHasta":"2018-11-29T21:00:00.0000000+03:00",
        # "CodigoMoneda":"EUR","NumeroCuenta":"5100101639",
        # "MovimientoDesde":"","MovimientoHasta":"","TimeStamp":""}
        req_movs_params = OrderedDict([
            ("FechaDesde", "{}-{}-{}T00:00:00.0000000+00:00".format(y_f, m_f, d_f)),
            ("FechaHasta", "{}-{}-{}T00:00:00.0000000+00:00".format(y_t, m_t, d_t)),
            ("CodigoMoneda", account_scraped.Currency),  # "CLP"
            ("NumeroCuenta", fin_ent_account_id),  # "20109939"
            ("MovimientoDesde", ""),
            ("MovimientoHasta", ""),
            ("TimeStamp", "")
        ])
        movements_parsed = []  # type: List[MovementParsed]
        for page_ix in range(1, 50):
            self.logger.info('{}: {}: page #{}: get movements'.format(
                org_title,
                fin_ent_account_id,
                page_ix
            ))
            resp_movs_i = s.post(
                req_mov_url,
                json=req_movs_params,
                headers=self._auth_headers(auth_token),
                proxies=self.req_proxies
            )

            resp_movs_i_json = resp_movs_i.json()
            # handle errs but {"Result":null,"ErrorCode":null,"ErrorDescription":null,
            # "ErrorSource":null,
            # "Mensaje":{"Titulo":"","Texto":"No se encontraron datos para la consulta","Tipo":1,
            # "CodigoEmisorError":null,"CodigoError":null},"Status":0}
            if ((resp_movs_i_json.get('Status', -1) != 2)
                    and ('No se encontraron datos para la consulta' not in resp_movs_i.text)):
                self.logger.error('{}: got (probably) unsuccessful movs response. Abort.\nRESPONSE:\n{}'.format(
                    fin_ent_account_id,
                    resp_movs_i.text
                ))
                break

            movements_parsed_i = parse_helpers.get_movements_parsed(resp_movs_i_json)
            movements_parsed.extend(movements_parsed_i)
            resp_result = resp_movs_i_json.get('Result') or {}
            mov_next_page_hasta = resp_result.get('MovimientoHasta')
            mov_next_page_desde = resp_result.get('MovimientoDesde')
            mov_next_ts = resp_result.get('TimeStamp')
            if not mov_next_page_hasta:
                self.logger.info('{}: {}: no more movements'.format(
                    org_title,
                    fin_ent_account_id,
                ))
                break
            # next page
            req_movs_params['MovimientoHasta'] = mov_next_page_hasta
            req_movs_params['MovimientoDesde'] = mov_next_page_desde
            req_movs_params['TimeStamp'] = mov_next_ts

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str
        )
        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )
        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error = self.login()
        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(
                resp_logged_in.url,
                resp_logged_in.text
            )

        self.process_companies(s)
        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
