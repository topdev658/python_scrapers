import re
import traceback
from collections import OrderedDict
from datetime import datetime
from typing import List, Tuple, Optional

from custom_libs import date_funcs
from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, MovementParsed, MovementScraped,
    ScraperParamsCommon, CorrespondenceDocScraped, CorrespondenceDocParsed,
    DBOrganization
)
from scrapers.bbva_scraper.bbva_netcash_scraper import BBVANetcashScraper
from . import parse_helpers_netcash_receipts
from .custom_types import AccountForCorrespondence

__version__ = '6.7.0'
__changelog__ = """
6.7.0 2023.06.19
_get_resp_w_mov_details_pdf_req_params: fixed parameters to get PDF link from movement details
download_movement_receipt: deleted hardcoded with access to download PDF from movement details
6.6.0 2023.06.06
download_correspondence: added call to _open_corr_filter_form to reload filter on each account correspondence iteration
_open_corr_filter_form: removed resp_logged_in as it's not being used
6.5.0
removed call to basic_save_receipt_pdf_and_update_db 
(only basic_save_receipt_pdf_as_correspondence is needed now) 
6.4.0
check for ok after basic_save_receipt_pdf_as_correspondence
6.3.0
save receipt metadata with checksum
6.2.0
save receipt as correspondence
6.1.0
use basic_should_download_correspondence_for_account
6.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
5.2.2
download_company_documents: use basic_should_download_company_documents
5.2.1
parse_helpers_netcash_receipts: use convert.to_currency_code
5.2.0
correspondence: currency field support
5.1.2
download_account_correspondence: fixed log msg
5.1.1
DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS = 4 (many corrs for -a 18014)
5.1.0
download_account_correspondence: 
  more log msgs, long timeout for resp_corr_filtered_i 
5.0.0
download correspondence
4.1.1
upd type hints
4.1.0
moved ACCESSES_TO_GET_MOV_DETAILS_PDF to a distinct file
4.0.0
download PDF from correspondence (envelopes) and/or from mov details (descargar)
ACCESSES_TO_GET_MOV_DETAILS_PDF
parse_helpers_netcash: get_movements_parsed_from_json: mov_raw
handle cases with AMBIGIOUS_RESULT_ERR_MARKER for envelopes - download PDFs from details
3.1.0
is_receipts_scraper property
3.0.0
download_receipts: use basic_download_receipts_common
download_movement_receipt: use new basic_save_receipt_pdf_and_update_db
2.0.0
checks scraper (formerly named as 'receipts scraper') was moved to BBVANetcashChecksScraper
real receipts scraper implemented
1.0.1
download_checks: fixed type hints and returning vals
check_parsed: fixed log arg check_parsed
log msgs: removed redundant leading colons
1.0.0
init
"""

# Movements correspondence not available with Chrome... - only Firefox allowed
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0'

# Some movements generate such err for correspondence req
AMBIGUOUS_RESULT_ERR_MARKER = 'No se envia respuesta al no poder validar de manera univoca el resultado'

DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS = 4  # many docs for Small world


class BBVANetcashReceiptsScraper(BBVANetcashScraper):
    CONCURRENT_PDF_SCRAPING_EXECUTORS = 1  # TODO increase after test period

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BBVANetcashReceiptsScraper') -> None:

        super().__init__(scraper_params_common, proxies, scraper_name)
        self.req_headers = {'User-Agent': USER_AGENT}
        self.is_receipts_scraper = True

    def download_receipts(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            movements_scraped: List[MovementScraped],
            movements_parsed: List[MovementParsed]) -> Tuple[bool, List[MovementScraped]]:
        """Redefines stub method to provide real results"""

        return self.basic_download_receipts_common(
            s,
            account_scraped,
            movements_scraped,
            movements_parsed
        )

    def _get_resp_w_mov_details_pdf_req_params(
            self,
            s: MySession,
            movement_parsed: MovementParsed) -> Response:
        """Some movements have no real receipt,
        but the website provides possibility to download
        all extra info as a PDF, using btn "Descargar"
        - all movements w/o envelopes
        """

        req_url = 'https://www.bbvanetcash.com/SESEYOZ/eyoz_mult_web_posicioncuentas_01/descargarDetalleMovimiento'

        # importe=-144,16
        # pais=ES
        # banco=BANCO+BILBAO+VIZCAYA+ARGENTARIA+S.A.
        # divisa=EUR
        # cuenta=ES2401825651010201512169
        # oficina
        # infAdicional=5996
        # fechaContable=14/11/2019
        # fechaValor=14/11/2019
        # codigo=0612+-+CHEQUE+CARGADO+EN+SU+CUENTA+++++
        # concepto=CHEQUE+N.+80382054
        # conceptoTx=CHEQUE+CARGADO+EN+SU+CUENTA+++++
        # codRmsoperS=140000034405384883
        # descargar=true
        # iuc=ES2401825651010201512169
        # detalle
        # parameroFiltro=null
        # parametroId=null
        # tipoDetalleMovimiento=null
        # saldoContable=1.902,94

        mov_raw = movement_parsed['mov_raw']
        req_params = OrderedDict([
            ('importe', mov_raw['importe']),
            ('pais', mov_raw['pais']),
            ('banco', mov_raw['banco']),
            ('divisa', mov_raw['divisa']),
            ('cuenta', mov_raw['cuenta']),
            ('oficina', mov_raw['oficina'] or 'null'),
            ('infAdicional', mov_raw['infAdicional']),
            ('fechaContable', mov_raw['fechaContable']),
            ('fechaValor', mov_raw['fechaValor']),
            ('codigo', mov_raw['codigo'] + '+-+' + mov_raw['descConcepto']),#.replace(' ', '+')),
            ('concepto', mov_raw['concepto']),  # CHEQUE+N.+80382054
            ('conceptoTx', ''),  # CHEQUE+CARGADO+EN+SU+CUENTA+++++
            ('codRmsoperS', mov_raw['codRmsoperS']),
            ('descargar', 'true'),
            ('iuc', mov_raw['cuenta']),
            ('detalle', ''),
            ('parameroFiltro', mov_raw['detalleMovimientoParametroFiltro'] or 'null'),
            ('parametroId', mov_raw['detalleMovimientoParametroId'] or 'null'),
            ('tipoDetalleMovimiento', mov_raw['tipoDetalleMovimiento'] or 'null'),
            ('saldoContable', mov_raw['saldoContable']),
        ])

        resp = s.post(
            req_url,
            headers=self.basic_req_headers_updated({'X-Requested-With': 'XMLHttpRequest'}),
            data=req_params,
            proxies=self.req_proxies,
            timeout=30
        )

        return resp

    def _get_resp_w_receipt_req_params(self,
                                       s: MySession,
                                       account_scraped: AccountScraped,
                                       movement_scraped: MovementScraped,
                                       movement_parsed: MovementParsed,
                                       meta: dict) -> Response:

        req_url = ('https://www.bbvanetcash.com/SESEYOZ/'
                   'eyoz_mult_web_posicioncuentas_01/obtenerCorrespondenciaVirtual')

        # expect
        # OrderedDict([('codigo', '0007'),
        #              ('cuenta', 'ES2601822355260208000593'),
        #              ('divisa', 'EUR'),
        #              ('fechaContable', '30/04/2019'),
        #              ('fechaValor', '30/04/2019'),
        #              ('importe', '30.000,00'),
        #              ('observaciones', 'TRASPASO IEN LBK A IEN BBVA'),
        #              ('claveAppOrigen', '2019120102602040609037049')])
        req_params = OrderedDict([
            ('codigo', movement_parsed['codigo_param']),
            ('cuenta', account_scraped.AccountNo),
            ('divisa', account_scraped.Currency),
            ('fechaContable', movement_parsed['operation_date']),
            ('fechaValor', movement_parsed['value_date']),
            ('importe', movement_parsed['amount_str']),
            ('observaciones', movement_parsed['observaciones_param']),
            ('claveAppOrigen', movement_parsed['clave_aplicacion_origen_param'])
        ])

        resp = s.post(
            req_url,
            headers=self.basic_req_headers_updated({'X-Requested-With': 'XMLHttpRequest'}),
            data=req_params,
            proxies=self.req_proxies
        )
        return resp

    def download_movement_receipt(self,
                                  s: MySession,
                                  account_scraped: AccountScraped,
                                  movement_scraped: MovementScraped,
                                  movement_parsed: MovementParsed,
                                  meta: dict) -> str:
        """Download receipts from movements's 'correspondecia' link
        Saves receipt, updates DB and returns its text (description)
        """

        mov_str = self.basic_mov_parsed_str(movement_parsed)

        resp_w_pdf_params = Response()
        got_correspondence_pdf = False
        pdf_req_datos_param = ''

        try:
            if movement_parsed['may_have_receipt']:
                self.logger.info('{}: download receipt PDF for: {}'.format(
                    account_scraped.FinancialEntityAccountId,
                    mov_str
                ))
                resp_w_pdf_params = self._get_resp_w_receipt_req_params(
                    s,
                    account_scraped,
                    movement_scraped,
                    movement_parsed,
                    meta
                )

                if '"success":true' in resp_w_pdf_params.text:
                    got_correspondence_pdf = True
                    pdf_req_datos_param = resp_w_pdf_params.json().get('data', {}).get('contenido')

                # Some movements have correspondence with a receipt (envelope mark), but
                # it can't be downloaded due to 5005 err (ambiguous results).
                # This logic will be applied for all accesses
                elif AMBIGUOUS_RESULT_ERR_MARKER in resp_w_pdf_params.text:
                    self.logger.info(
                        "{}: {}: can't download PDF from correspondence due to err 'ambiguous results' (errCode 5005). "
                        "Will try to download PDF from details. RESPONSE: {}".format(
                            account_scraped.AccountNo,
                            mov_str,
                            resp_w_pdf_params.text)
                    )
                else:
                    self.logger.error(
                        "{}: {}: can't download PDF from correspondence. "
                        "Skip mov. RESPONSE:\n{}. ".format(
                            account_scraped.AccountNo,
                            mov_str,
                            resp_w_pdf_params.text
                        )
                    )
                    return ''

            if not got_correspondence_pdf:
                self.logger.info('{}: download mov details PDF for: {}'.format(
                    account_scraped.FinancialEntityAccountId,
                    mov_str
                ))

                resp_w_pdf_params = self._get_resp_w_mov_details_pdf_req_params(
                    s,
                    movement_parsed,
                )

                if '"success":true' not in resp_w_pdf_params.text:
                    self.logger.error("{}: {}: can't download receipt PDF: RESPONSE:\n{}".format(
                        account_scraped.AccountNo,
                        mov_str,
                        resp_w_pdf_params.text
                    ))
                    return ''

                pdf_req_datos_param = resp_w_pdf_params.json().get('data', {}).get('datos')

            if not pdf_req_datos_param:
                self.logger.error("{}: {}: empty pdf_req_datos_param. Skip".format(
                    account_scraped.AccountNo,
                    mov_str
                ))
                return ''

            req_pdf_url = ('https://www.bbvanetcash.com/SESEYOZ/'
                           'eyoz_mult_web_posicioncuentas_01/descargarFichero')

            req_pdf_params = OrderedDict([
                ('datos', pdf_req_datos_param),
                ('titulo', 'pdf'),
                # ('descargar', 'false') # not necessary
            ])

            resp_pdf = s.post(
                req_pdf_url,
                headers=self.req_headers,
                data=req_pdf_params,
                proxies=self.req_proxies,
                stream=True,
            )

            ok, receipt_parsed_text, checksum = self.basic_save_receipt_pdf_as_correspondence(
                account_scraped,
                movement_scraped,
                resp_pdf.content,
            )

            return receipt_parsed_text

        except:
            self.logger.error("{}: {}: can't download receipt PDF: HANDLED EXCEPTION\n{}".format(
                account_scraped.FinancialEntityAccountId,
                mov_str,
                traceback.format_exc()
            ))
            return ''

    def _open_corr_filter_form(
            self,
            s: MySession) -> Tuple[bool, MySession, Response]:
        # Constant, avalable in 008_resp_getnewmasterrequest.json
        req_params = OrderedDict([
            ('pb_cod_prod', '201'),
            ('pb_cod_serv', '8125'),
            ('pb_cod_proc', '20020059'),
            ('LOCALE', 'es_ES'),
            ('pb_cod_ffecha', 'dd/MM/yyyy'),
            ('pb_cod_fimporte', '0.000,00'),
            ('pb_husohora', '(GMT+01:00)'),
            ('pb_xti_comprper', 'S'),
            ('pb_url', '?proceso=TLBHPrCVConsultaAvanzada'
                       '&operacion=TLBHOpCVCriteriosSeleccionCA'
                       '&accion=execute'
                       '&codigoServicio=8125'),
            ('pb_segmento', '10'),
            ('xtiTipoProd', 'C'),
            ('pb_isPortalKyop', 'true'),
            ('cod_emp', self.username),
            ('pb_cod_prod_p', '201'),
            ('kyop-process-id', '')
        ])

        resp_filter_form = s.post(
            'https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/PIBEE'
            '?proceso=TLBHPrCVConsultaAvanzada'
            '&operacion=TLBHOpCVCriteriosSeleccionCA'
            '&accion=execute'
            '&codigoServicio=8125'
            '&isInformationalArchitecture=true',
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        return True, s, resp_filter_form

    def download_correspondence(
            self,
            s: MySession,
            resp_logged_in: Response) -> Tuple[bool, List[CorrespondenceDocScraped]]:

        if not self.basic_should_download_correspondence():
            return False, []

        ok, s, resp_filter_form = self._open_corr_filter_form(s)
        if not ok:
            return False, []  # already reported

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=85  # 3 months with padding
        )

        accs_for_corr = parse_helpers_netcash_receipts.get_accounts_for_corr(resp_filter_form.text)

        self.logger.info('Got {} accounts to download correspondence: {}'.format(
            len(accs_for_corr),
            [acc.account_no for acc in accs_for_corr]
        ))

        for acc in accs_for_corr:
            # Reload filter form to get account correspondence PDF
            ok = self._open_corr_filter_form(s)
            if not ok:
                return False, []
            self.download_account_correspondence(s, acc, date_from, self.date_to)
        return True, []  # result is unused

    def _get_organization(
            self,
            fin_ent_account_id: str,
            resp_corr_filtered: Response) -> Optional[DBOrganization]:
        organization_title = parse_helpers_netcash_receipts.get_corr_organization_title(
            resp_corr_filtered.text
        )
        if not organization_title:
            self.logger.error("Can't get organization_title. RESPONSE:\n{}".format(resp_corr_filtered.text))
            return None

        organization = self.basic_get_organization(organization_title)  # type: Optional[DBOrganization]

        if not organization:
            self.logger.error("{}: download_correspondence: no organization_saved with title '{}'. "
                              "Can't continue. Skip".format(fin_ent_account_id, organization_title))
            return None

        return organization

    def download_account_correspondence(
            self,
            s: MySession,
            acc_for_corr: AccountForCorrespondence,
            date_from: datetime,
            date_to: datetime) -> List[CorrespondenceDocScraped]:

        fin_ent_account_id = acc_for_corr.account_no

        if not self.basic_should_download_correspondence_for_account(fin_ent_account_id):
            return []

        yf, mf, df = date_from.strftime('%Y/%m/%d').split('/')
        yt, mt, dt = date_to.strftime('%Y/%m/%d').split('/')
        ytd, mtd, dtd = date_funcs.today_str('%Y/%m/%d').split('/')
        # ASC
        # 1st page has other params
        req_corr_filtered_params_i = OrderedDict([
            ('proceso', 'TLBHPrCVConsultaAvanzada'),
            ('operacion', 'TLBHOpCVListaDocumentosCA'),
            ('accion', 'ejecutar'),
            ('codigoGrupo', 'TODOS'),
            ('indiceGrupo', ''),
            ('fechaDesde', date_from.strftime('%Y%m%d')),  # '20200801'
            ('fechaHasta', date_to.strftime('%Y%m%d')),  # '20200925
            ('fechaAnterior', ''),
            ('aux', ''),
            ('diaHoy', ytd),
            ('mesHoy', mtd),
            ('anioHoy', ytd),  # '2020'
            ('importeDesde', '-9999999999999'),
            ('importeHasta', '99999999999999'),
            ('listaAsuntos', '{}#'.format(acc_for_corr.ix)),  # 0# 1#
            ('listaCodigosDocumento', '4#'),
            ('listaAsuntosSelected', ''),
            ('okRangoCompletoImportes', 'S'),
            ('tipoVersion', ''),
            ('fechaAnt', date_to.strftime('%Y%m%d')),  # '20200925'
            ('op', 'R'),
            ('diaDesde', df),
            ('mesDesde', mf),
            ('anioDesde', yf),
            ('diaHasta', dt),
            ('mesHasta', mt),
            ('anioHasta', yt),
            ('imported', ''),
            ('importeh', ''),
            ('producto', 'TODOS'),
            ('tipoDocumento', '4'),
            ('cBanc', ''),
            ('cOfic', ''),
            ('cCont', ''),
            ('cFoli', ''),
            ('cuentaNuevaIBAN', ''),
            ('listaCuentas', acc_for_corr.req_param),  # '2@USD0182 2351 48 2012008039'
            ('ordenacion1', 'FEC-DOCUM'),
            ('ordenacion2', 'DES-FORMUL')
        ])
        req_corr_filtered_url = 'https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/OperacionCBTFServlet'

        corrs_scraped = []  # type: List[CorrespondenceDocScraped]

        # Will get from resp_corr_filtered, no data at filter form page
        organization = None  # type: Optional[DBOrganization]

        for page_ix in range(1, 100):  # avoid inf loop
            self.logger.info('{}: {}: page {}: wait for resp_corr_filtered_i (may take awhile)'.format(
                '' if not organization else organization.Name,
                fin_ent_account_id,
                page_ix
            ))
            resp_corr_filtered_i = s.post(
                req_corr_filtered_url,
                data=req_corr_filtered_params_i,
                headers=self.req_headers,
                proxies=self.req_proxies,
                timeout=300,  # could be very slow (-a 18014: >3 min)
            )

            # Get it 1 time
            if not organization:
                organization = self._get_organization(fin_ent_account_id, resp_corr_filtered_i)
                if not organization:  # already reported
                    return []

            self.logger.info('{}: {}: page {}: download correspondence'.format(
                organization.Name,
                fin_ent_account_id,
                page_ix
            ))

            corrs_parsed_asc = parse_helpers_netcash_receipts.get_correspondence_from_list(
                self.logger,
                resp_corr_filtered_i.text,
                acc_for_corr.account_no,
            )  # type: List[CorrespondenceDocParsed]

            for i, corr_parsed in enumerate(corrs_parsed_asc):
                corr_scraped_opt = self.download_correspondence_one_doc(
                    s,
                    acc_for_corr,
                    organization,
                    i,
                    corr_parsed
                )
                if corr_scraped_opt:
                    corrs_scraped.append(corr_scraped_opt)

            # from <a href="javascript:paginarMvtosCuenta('2');">Cuenta Siguiente</a></li>
            if 'Cuenta Siguiente' not in resp_corr_filtered_i.text:
                break

            req_corr_filtered_params_i = OrderedDict([(
                'proceso', 'TLBHPrCVConsultaAvanzada'),
                ('operacion', 'TLBHOpCVListaDocumentosCA'),
                ('accion', 'paginarCuenta'),
                ('codigoServicio', '8125'),
                ('cuentaInicio', str(page_ix)),
                ('paginaActual', ''),
                ('guardarMultiplesPDF', ''),
                ('xtiTipocta', ''),
                ('tipoOperacion', ''),
                ('msgErrMax50Docu', 'No se pueden descargar más de 50 documentos a la vez.')
            ])

        return corrs_scraped

    def download_correspondence_one_doc(
            self,
            s: MySession,
            acc_for_corr: AccountForCorrespondence,
            organization: DBOrganization,
            ix: int,
            corr_parsed: CorrespondenceDocParsed) -> Optional[CorrespondenceDocScraped]:
        fin_ent_account_id = acc_for_corr.account_no

        self.logger.info('{}: download correspondence document with ix: {}'.format(
            fin_ent_account_id,
            ix
        ))

        try:
            resp_pdf = s.get(
                'https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/OperacionCBTFServlet',
                params=corr_parsed.extra['req_pdf_params'],
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            doc_pdf_content = resp_pdf.content
            if b'<html' in doc_pdf_content or b'<HTML' in doc_pdf_content:
                self.logger.error("{}: {}: can't download correspondence PDF. Skip. RESPONSE:\n{}".format(
                    fin_ent_account_id,
                    corr_parsed,
                    resp_pdf.text
                ))
                return None

            doc_pdf_text = pdf_funcs.get_text(doc_pdf_content)
            # drop last line with 'system info'
            doc_pdf_checksum = pdf_funcs.calc_checksum(bytes(re.sub('\n.*?$', '', doc_pdf_text), 'utf8'))

            document_text = pdf_funcs.get_text(doc_pdf_content)
            product_id = fin_ent_account_id  # 'ES7020482178763400008898'

            corr_scraped = CorrespondenceDocScraped(
                CustomerId=self.db_customer_id,
                OrganizationId=organization.Id,
                FinancialEntityId=self.db_financial_entity_id,
                ProductId=product_id,
                ProductType='',
                DocumentDate=corr_parsed.operation_date,
                Description=corr_parsed.descr,
                DocumentType=corr_parsed.type,
                DocumentText=document_text,
                # Need to use Checksum to compare with PDFs from receipts
                Checksum=doc_pdf_checksum,
                AccountId=None,  # Account DB Id
                StatementId=None,
                Amount=corr_parsed.amount,
                Currency=corr_parsed.currency,
            )

            corr_scraped_upd, should_add = self.basic_check_correspondence_doc_to_add(
                corr_parsed,
                corr_scraped
            )

            if should_add:
                self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)
                return corr_scraped_upd
            return None
        except:
            self.logger.error("{}: {}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                fin_ent_account_id,
                corr_parsed,
                traceback.format_exc()
            ))
            return None
