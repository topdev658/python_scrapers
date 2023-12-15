from collections import OrderedDict
from typing import Tuple

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_COMMON, \
    MOVEMENTS_ORDERING_TYPE_ASC
from scrapers._basic_scraper.basic_scraper import BasicScraper
from . import parse_helpers
from .custom_types import AccountFromDropdown

__version__ = '1.2.0'

__changelog__ = """
1.2.0
use downloaded SSL cert
1.1.0
call basic_upload_movements_scraped with date_from_str
1.0.1
correct account country (ESP)
country_prefix -> tipo_cuenta_param
1.0.0
init
"""

MAX_MOV_DATE_OFFSET = 365


class InversisScraper(BasicScraper):
    scraper_name = 'InversisScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.ssl_cert = 'www-inversis-com-chain.pem'

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()
        s.verify = self.ssl_cert

        resp_init = s.get(
            'https://www.inversis.com/',
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        req_login_pre_params = {
            'codigoUsuario': self.username,
            'claveUsuario': self.userpass,
        }

        # Check for OTP
        resp_login_pre = s.post(
            'https://www.inversis.com/trans/inversis/SvlAjaxControl?accion=validaLoginOtp',
            data=req_login_pre_params,
            headers=self.basic_req_headers_updated({
                'TE': 'Trailers',
                'X-Requested-With': 'XMLHttpRequest',
            }),
            proxies=self.req_proxies,
        )
        if '"TIENE_OTP":"N"' not in resp_login_pre.text:
            return s, resp_login_pre, False, False, DOUBLE_AUTH_REQUIRED_TYPE_COMMON

        id_tds_param = parse_helpers.get_id_tds_param(resp_init.text)
        if not id_tds_param:
            return s, resp_init, False, False, "Can't get id_tds_param"

        req_login_params = {
            'codigoUsuario': self.username,
            'claveUsuario': self.userpass,
            'cobranding': 'cbInversiones',
            'destino': 'null',
            'accion': 'identificarUsuario',
            'olvido': 'olvido',
            '_id_tds': id_tds_param,
            'esLH': 'N',
        }

        resp_logged_in = s.post(
            'https://www.inversis.com/trans/inversis/SvlAutentificar',
            data=req_login_params,
            headers=self.basic_req_headers_updated({
                'TE': 'Trailers',
            }),
            proxies=self.req_proxies
        )

        is_logged = 'Mi cuenta' in resp_logged_in.text and 'DESCONECTAR' in resp_logged_in.text
        is_credentials_error = 'El usuario o la password no es correcta' in resp_logged_in.text

        return s, resp_logged_in, is_logged, is_credentials_error, ''

    def _open_accs_dropdown(self, s: MySession) -> Response:
        resp_accs_dropdown = s.get(
            'https://www.inversis.com/trans/inversis/'
            'SvlConsultaCC?accion=resumenSaldosPI&tipo=S&pathMenu=1_0&esLH=N',
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        return resp_accs_dropdown

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        resp_accs_dropdown = self._open_accs_dropdown(s)
        id_tds_param = parse_helpers.get_id_tds_param(resp_logged_in.text)
        if not id_tds_param:
            self.basic_log_wrong_layout(
                resp_logged_in,
                "process_access: can't get id_tds_param from resp_logged_in"
            )
            return False
        fin_ent_acc_ids = parse_helpers.get_fin_ent_acc_ids_from_dropdown(resp_accs_dropdown.text)
        self.logger.info('Got fin_ent_acc_ids: {}'.format(fin_ent_acc_ids))
        for fin_ent_account_id in fin_ent_acc_ids:
            self.process_account(s, fin_ent_account_id, id_tds_param)
        return True

    def process_account(
            self,
            s: MySession,
            fin_ent_account_id: str,
            id_tds_param: str) -> bool:

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        date_from_str = self.basic_get_date_from(
            fin_ent_account_id,
            max_offset=MAX_MOV_DATE_OFFSET,
            max_autoincreasing_offset=MAX_MOV_DATE_OFFSET,
        )
        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        # Step 1: get all data for AccountFromDropdown (need it for movs)

        req_acc_from_dropdown_url = (
            'https://www.inversis.com/trans/inversis/SvlAjaxControl?'
            'accion=procesaBusquedaCuenta&numeroCuenta={}'
            '&nombreSelect=productos0&estadoProductoBuscador0='
            '&ordenante=&numeroCuentaExterna=&tipoProducto=C'
            'E&divisaFiltro=&indMostrarEuros='
            '&origen=posicionIntegrada&tipoPeticion=ajax'.format(fin_ent_account_id)
        )
        resp_acc_from_dropdown = s.post(
            req_acc_from_dropdown_url,
            headers=self.basic_req_headers_updated({
                'TE': 'Trailers',
                'X-Requested-With': 'XMLHttpRequest'
            }),
            proxies=self.req_proxies
        )
        try:
            resp_acc_from_dropdown_json = resp_acc_from_dropdown.json()  # type: dict
        except Exception as _e:
            self.basic_log_wrong_layout(
                resp_acc_from_dropdown,
                "{}: can't get resp_acc_from_dropdown_json".format(fin_ent_account_id)
            )
            return False

        # There is no balance information, will get later from the page with movements
        account_from_dropdown = parse_helpers.get_account_from_dropdown(
            resp_acc_from_dropdown_json
        )  # type: AccountFromDropdown

        # Step 2: get movs

        req_movs_url = 'https://www.inversis.com/trans/inversis/SvlConsultaCC'
        req_movs_params = OrderedDict([
            ('accion', 'consultaMovimientos'),
            ('origen', 'consultarMovimientos'),
            ('numeroOperacion', ''),
            ('claseOperacion', ''),
            ('fecha', ''),
            ('ordenMiInversis', ''),
            ('fechaHoy', self.date_to_str),  # '11/12/2020'
            ('CABECERA.TIPO_PRODUCTO', 'CE,RE'),
            ('formatoFecha', 'dd/MM/yyyy'),
            ('cuenta', fin_ent_account_id),  # '0029493443'
            ('indMovimientoMigrado', ''),
            ('detalleFechaOperacion', ''),
            ('detalleFechaValor', ''),
            ('detalleTipoOperacion', ''),
            ('detalleConcepto', ''),
            ('detalleImporte', ''),
            ('detalleReferenciaMov', ''),
            ('refFicheroMigrado', ''),
            ('totalRegistros', '1'),
            ('numeroRegistrosMostrar', '500'),  # '50'
            ('numeroPagina', '1'),
            ('indCargoAbono', ''),
            ('cuentaSeleccionada', fin_ent_account_id),  # '0029493443'
            ('esSW', 'false'),
            ('nombreForm', ''),
            ('productos0', fin_ent_account_id),  # '0029493443'
            ('cuentaCompleta0', ''),  # not mandatory: '0232-0105-00-0029493443'
            ('divisaFiltro0', ''),
            ('divisaCuenta0', account_from_dropdown.currency),
            ('institucionTriangulacion', account_from_dropdown.codigo_insitucion_param),  # '5000'
            ('divisaInstitucion', account_from_dropdown.divisa_institucion_param),  # 'EUR'
            ('divisaDecimalesInstitucion', '2'),
            ('c_codigoProducto', ''),
            ('c_numeroCtaExterna', ''),
            ('c_tipoProducto', ''),
            ('c_descripcionCorta', ''),
            ('c_estadoProducto', ''),
            ('c_estadoPersonaProducto', ''),
            ('c_tipoTitular', ''),
            ('c_tipoFirma', ''),
            ('c_descripcionTipoProducto', ''),
            ('nombreSelect', ''),
            ('inicio', ''),
            ('saldoInternacionalizado', 'S'),
            ('multiDivisa0', 'S'),
            ('indMostrarEuros0', ''),
            ('hinstitucionCuenta', account_from_dropdown.codigo_insitucion_param),  # '5000'
            ('tipoCuenta', account_from_dropdown.tipo_cuenta_param),  # 'AG'
            ('institucionColectiva', account_from_dropdown.institucion_collectiva_param),  # '5358217'
            ('institucionlogado', '5000'),  # fixed val
            ('tipoProductoBuscador0', 'CE,RE'),
            ('estadoProductoBuscador0', ''),
            ('fechaDesde', date_from_str),  # '01/10/2020'
            ('fechaHasta', self.date_to_str),  # '11/12/2020'
            ('_id_tds', id_tds_param),  # 'JZtTqnw-HNAD7Z...69633915'
            ('esLH', 'N'),
        ])
        resp_movs = s.post(
            req_movs_url,
            data=req_movs_params,
            headers=self.basic_req_headers_updated({
                'TE': 'Trailers'
            }),
            proxies=self.req_proxies
        )

        # No pagination implemented (no examples)
        # Page with movements displays current balance
        account_parsed = parse_helpers.get_account_parsed(resp_movs.text, account_from_dropdown)
        account_scraped = self.basic_account_scraped_from_account_parsed(
            organization_title=self.db_customer_name,
            account_parsed=account_parsed,
            is_default_organization=True,
        )

        self.logger.info('Got account: {}'.format(account_scraped))
        self.basic_upload_accounts_scraped([account_scraped])
        self.basic_log_time_spent('GET BALANCES')

        movs_parsed = parse_helpers.get_movements_parsed(resp_movs.text)

        movs_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movs_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_upload_movements_scraped(
            account_scraped,
            movs_scraped,
            date_from_str=date_from_str
        )
        self.basic_log_process_account(fin_ent_account_id, date_from_str, movs_scraped)

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

        self.process_access(s, resp_logged_in)

        self.basic_log_time_spent("GET MOVEMENTS")
        return self.basic_result_success()
