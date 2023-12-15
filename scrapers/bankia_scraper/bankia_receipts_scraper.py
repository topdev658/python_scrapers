import json
import random
import time
import traceback
from collections import OrderedDict
from typing import List, Optional, Tuple
from urllib.parse import urljoin

from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, CorrespondenceDocScraped, MovementParsed, MovementScraped,
    ScraperParamsCommon, CorrespondenceDocParsed
)
from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
from scrapers.bankia_scraper import parse_helpers_receipts
from scrapers.bankia_scraper.bankia_scraper import BankiaScraper

__version__ = '4.7.0'
__changelog__ = """
4.7.0
removed call to basic_save_receipt_pdf_and_update_db 
(only basic_save_receipt_pdf_as_correspondence is needed now) 
4.6.0
check for ok after basic_save_receipt_pdf_as_correspondence
4.5.0
save receipt metadata with checksum
4.4.0
always use regular receipt_checksum (due to saving as corr)
4.3.0
save receipt as correspondence
4.2.0
use basic_should_download_correspondence_for_account
4.1.0
use basic_should_download_correspondence_for_access
4.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
3.6.0
basic_should_download_company_documents_for_customer to set 'save_checksum' flag
3.5.0
correspondence: 
  handle changing event_number (get from resp)
  impl pagination
3.4.0
correspondence: currency field support
3.3.0
use project-level corr offset
3.2.0
correct product_to_fin_ent_id
3.1.0
fixed receipt/correspondence downloading (new urls and req args)
3.0.0
use basic funcs for correspondence
use project types
DocumentScraped: upd field (DocumentDate: datetime)
2.7.1
upd log msg
2.7.0
download_company_documents:
  DocumentScraped: new fields (Amount) 
  use DocumentChecked
_get_document_movement_id:
  upd type hints
parse_helpers: actual DocumentTextInfo fields 
2.6.0
_get_correspondence_documents: 
  better err handling
  correct event_number
2.5.0 InitialId support for documents
upd type hints
2.4.1
upd type hints
2.4.0
download_company_documents: check for None organization
2.3.0
use pdf_funcs.calc_checksum instead of parse_helpers
_get_document_movement_id: 
  receives exactly Optional[int] from db_connector, no need for additional processing
parse_helpers: removed unused funcs
2.2.0
DAF: the method get_checksum_from_expedient_key doesn't work: the expedient key data to download the document are 
different in each execution. Specifically the "encrypted" values are changed in each execution.
The rest of the parameters associated to a correspondence document or the rest of the parameters of the expedient key 
are repeated for different documents. Therefore, they are not enough to generate a unique checksum for the document.
For this reason, to avoid duplicities between the receipt associated with a movement and a correspondence document. 
As between the correspondence documents themselves, we are forced on this occasion to always 
download the pdf and get the checksum from it.
New method parse_helpers.get_checksum_from_pdf_file_content is used. 
2.1.0
download_company_documents: UPD clave_expediente: use encrypted params
_download_pdf_from_expedient_key: UPD req urls
_get_correspondence_documents: new req_correspondencia_url, more attempts
parse_helpers: get_documents_parsed: put the rest into req_args
2.0.0
download_receipts: use basic_download_receipts_common
impl download_movement_receipt
download_movement_receipt: use new basic_save_receipt_pdf_and_update_db
parse_helpers: removed unused get_receipt_text_faster_fitz
parse_helpers: removed earlier unused get_receipt_text_fitz, get_checksum
1.3.2
DAF: _get_document_movement_id: modified to handle the rare case of several possible movement ids fr a company document
1.3.1
fmt
download_company_documents: if not document_check['IsToAdd'] then: `continue` instead of `return False`  
1.3.0
DAF:
renamed _download_pdf_from_clave_expediente -> _download_pdf_from_expedient_key
renamed _get_expediente_data -> _get_expedient_data
changed download_documents(request, DBOrganization, opt str) -> download_company_documents(request, str, opt str)
download_company_documents: check if the document is already downloaded before do it. check that using the
value returned by get_checksum_from_expedient_key
download_receipts: now save the receiptchecksum field with value returned by get_checksum_from_expedient_key
1.2.1
fmt
upd docs
1.2.0
DAF:
download_receipts: save the receiptchecksum field in the movements table if document downloading is active 
download_documents
_get_correspondence_documents
_download_pdf_from_clave_expediente
_get_expediente_data
1.1.0
download_receipts: changed return types to provide compat with BasicScraper
1.0.0
init
"""

INT_DATE_FMT = '%Y-%m-%d'


def product_to_fin_ent_id(product_id: str):
    """
    Handle different cases: for currrent and other accounts.
    When not used erlier, then product id '541205' was '%05'
    in db select statements
    (see db_funcs.check_add_document historical convering),
    and, for -u 395518,
    it led to wrong matching with 'ES3920801206383040017505'.
    When using this func, it's ok (no false-positive matches)

    >>> product_to_fin_ent_id('ES7620389466916000002136')
    '6000002136'
    >>> product_to_fin_ent_id('94666000002136')
    '6000002136'
    >>> product_to_fin_ent_id('541205')
    '541205'
    """
    return product_id[-10:]


class BankiaReceiptsScraper(BankiaScraper):
    CONCURRENT_PDF_SCRAPING_EXECUTORS = 1

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BankiaReceiptsScraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)

    def download_receipts(
            self, s: MySession,
            account_scraped: AccountScraped,
            movements_scraped: List[MovementScraped],
            movements_parsed: List[MovementParsed]) -> Tuple[bool, List[MovementScraped]]:
        """Redefines download_receipts method to provide real results

        If document downloading is active for the client, then
        receiptchecksum field is used to avoid downloading duplicated files.

        NO StatementDescription added to MovementScraped data (because it's
        not used in BankiaScraper), can be added
        """

        save_checksum = self.basic_should_download_correspondence_for_access()

        return self.basic_download_receipts_common(
            s,
            account_scraped,
            movements_scraped,
            movements_parsed,
            meta={'save_checksum': save_checksum}
        )

    def _get_movement_expedient_data(self,
                                     s: MySession,
                                     movement: MovementParsed,
                                     account_scraped: AccountScraped) -> dict:
        """Now is used by download_receipts
        to get the correspondence keys to get the movement receipt"""

        # Step 1: check that the receipt exists
        req1_url = (
            'https://oficinaempresas.bankia.es/api/1.0/servicios/'
            'comunes.movimientos.consultarexistenciacorrespondenciamovimientos/'
            '2.0/comunes/movimientos/consultarexistenciacorrespondenciamovimientos'
            '?request={}&_ts{}'.format(
                json.dumps(movement['receipt_req_args']),
                int(time.time() * 1000)
            )
        )

        resp1 = self._req_json_get_with_retry(
            s,
            req1_url,
            self.basic_req_headers_updated({'x-j_gid_cod_app': 'o2'}),
            self.req_proxies
        )

        # Exists (has)
        # <<<< {"indicadorCorrespondencia":"S",
        # "localizadorDocumento":{
        # "baseDatos":"IPLCORRESP",
        # "expediente":"CORRESPOND","clavesCorrespondencia":[
        # {"valor":"00000","tipo":"int"},{"valor":"10600","tipo":"int"},
        # {"valor":"00041236000013510","tipo":"int"},
        # {"valor":"01.08.2018","tipo":"string"},
        # {"valor":"00000048","tipo":"int"},{"valor":"00001","tipo":"int"}]}}
        #
        # No
        # <<<< {"indicadorCorrespondencia":"N",
        # "localizadorDocumento":{"baseDatos":"IPLCORRESP",
        # "expediente":"CORRESPOND","clavesCorrespondencia":[
        # {"valor":"","tipo":"int"},{"valor":"","tipo":"int"},
        # {"valor":"","tipo":"int"},{"valor":"","tipo":"string"},
        # {"valor":"","tipo":"int"},{"valor":"","tipo":"int"}]}}
        resp1_data = resp1.json()
        if resp1_data['indicadorCorrespondencia'] == 'N':
            self.logger.info(
                "{}: no receipt: {}/{}".format(
                    account_scraped.AccountNo,
                    movement['operation_date'],
                    movement['amount']
                )
            )
            return {}

        # Step 2. Get the receipt id
        exp_data = OrderedDict([
            ('base_datos', resp1_data['localizadorDocumento']['baseDatos']),
            ('expediente', resp1_data['localizadorDocumento']['expediente'])
        ])

        claves_corr = resp1_data['localizadorDocumento']['clavesCorrespondencia']

        exp_data['clave_expediente'] = {
            "claveExpediente": [
                # "00000"
                OrderedDict([("identificadorClave", "1"), ("valorClave", claves_corr[0]['valorEncr'])]),
                # "10600"
                OrderedDict([("identificadorClave", "2"), ("valorClave", claves_corr[1]['valorEncr'])]),
                # "00041236000013510"
                OrderedDict([("identificadorClave", "3"), ("valorClave", claves_corr[2]['valorEncr'])]),
                # "01.08.2018"
                OrderedDict([("identificadorClave", "4"), ("valorClave", claves_corr[3]['valorEncr'])]),
                # "00000048"
                OrderedDict([("identificadorClave", "5"), ("valorClave", claves_corr[4]['valorEncr'])]),
                # "00001"
                OrderedDict([("identificadorClave", "6"), ("valorClave", claves_corr[5]['valorEncr'])]),
            ]
        }

        return exp_data

    def download_movement_receipt(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            movement_scraped: MovementScraped,
            movement_parsed: MovementParsed,
            meta: dict) -> str:

        save_checksum = meta['save_checksum']  # type: bool

        if not movement_parsed['may_have_receipt']:
            return ''
        try:
            exp_data = self._get_movement_expedient_data(s, movement_parsed, account_scraped)
            if not exp_data:
                return ''

            pdf_file_content = self._download_pdf_from_expedient_key(
                s,
                exp_data['base_datos'],
                exp_data['expediente'],
                exp_data['clave_expediente']
            )

            ok, receipt_parsed_text, checksum = self.basic_save_receipt_pdf_as_correspondence(
                account_scraped,
                movement_scraped,
                pdf_file_content,
                account_to_fin_ent_fn=product_to_fin_ent_id,
            )

            return receipt_parsed_text

        except:
            self.logger.error("{}: {}: can't download pdf: HANDLED EXCEPTION\n{}".format(
                account_scraped.FinancialEntityAccountId,
                movement_parsed['operation_date'],
                traceback.format_exc()
            ))

            return ''

    def _get_req_correspondence_url(self, event_number: int, num_page: int) -> str:
        return (
            'https://oficinaempresas.bankia.es/api/1.0/servicios/buzonpersonal.gestionarcomunicaciones/'
            '2.0/buzonpersonal/gestionarcomunicaciones?_eventId=consultar&execution=e{}s{}'.format(
                event_number,
                num_page
            )
        )

    def _get_correspondence_docs_parsed(
            self,
            s: MySession,
            event_number: int,
            organization_title: str,
            company_param: Optional[str] = None) -> List[CorrespondenceDocParsed]:

        """DAF: here starts the Correspondence Scraping:
        The good news: No searching results pagination
        Our approach: we search **ALL** the company documents to download them.
        The pros:
        - We can download all the PDFs
        - It's easy to clasify or to FILTER by the product "account" from the whole results.
        ...and also by other products: "cards", "credits", "avales", etc.
        The cons:
        - Without choosing product and cetegory 1 month date range is allowed.
        If you configure the searching filtering by product and category you don't have date range limitations

        Used by download_documents to get the correspondence documents data.
        """
        # event_number = 1
        num_page = 1

        req_correspondence_url = self._get_req_correspondence_url(event_number, num_page)

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=30
        )

        req_data = OrderedDict([
            ("codigoGrupoComunicacion", None),
            ("codigoProductoUrsus", None),
            ("codigoTipoComunicacion", None),
            ("fechaDesde", {"valor": date_from.strftime(INT_DATE_FMT)}),
            ("fechaHasta", {"valor": self.date_to.strftime(INT_DATE_FMT)}),
            ("identificadorProducto", None), ("tipoComunicaciones", "LF")
        ])

        req_headers = self.req_headers.copy()
        if company_param:
            req_headers['j_gid_indice'] = company_param

        # The response to the first call never include the "list of documents".
        # But if you repeat the  call, It works...
        resp_corr = Response()  # avoid false positive mypy warnings
        resp_corr_json = {}  # type: dict
        corrs_asc = []  # type: List[CorrespondenceDocParsed]

        # Several attempts for the 1st page
        for i in range(5):
            time.sleep(0.2 + 0.2 * random.random())
            resp_corr = self._req_json_post_with_retry(
                s,
                req_correspondence_url,
                req_data,
                req_headers,
                self.req_proxies
            )
            try:
                resp_corr_json = resp_corr.json()
                # Handle wrong event_number, see dev_corr/resp_corr_wrong_eventnumber.json
                if (resp_corr_json.get('stateData', {}).get('viewId', '')
                        == 'SolicitarCriteriosBusquedaComunicacionesIU'):
                    self.logger.warning(
                        '{}: get new req_correspondence_url due to initial wrong event_number'.format(
                            organization_title
                        )
                    )
                    req_correspondence_link = resp_corr_json['stateData']['availableTransitions']['consultar']
                    req_correspondence_url = urljoin(req_correspondence_url, req_correspondence_link)
                    continue
                if resp_corr_json.get('data', {}).get('comunicaciones') is None:
                    self.logger.warning(
                        "{}: _get_correspondence_documents: data not ready. Retry".format(organization_title))
                    continue
                corrs_asc = parse_helpers_receipts.get_correspondence_from_list(resp_corr_json)
                break  # got 1st page
            except Exception as e:
                self.logger.warning("{}: can't parse correspondence. Retry. HANDLED EXCEPTION: {}\nRESPONSE\n{}".format(
                    organization_title,
                    e,
                    resp_corr.text,
                ))
                continue
        else:
            self.logger.error(
                "{}: can't parse documents. RESPONSE\n{}\n"
                "Skip.".format(
                    organization_title,
                    resp_corr.text
                )
            )
            return []

        # Pagination, see dev_corr/resp_corr_paginataion.json
        resp_prev_json = resp_corr_json
        resp_prev = resp_corr
        for page_ix in range(2, 32):  # 30 pages * 50 docs = 1500, avoid inf loop
            try:
                time.sleep(0.2 + random.random() * 0.2)
                if not resp_prev_json['data']['indicadorMasComunicaciones']:
                    self.logger.info('{}: no more pages with correspondence'.format(organization_title))
                    break
                self.logger.info('{}: get correspondence from page #{}'.format(organization_title, page_ix))
                req_corr_link_i = resp_prev_json['stateData']['availableTransitions']['consultarMas']
                req_corr_url_i = urljoin(resp_prev.url, req_corr_link_i)
                resp_corr_i = self._req_json_get_with_retry(
                    s,
                    req_corr_url_i,
                    req_headers,
                    self.req_proxies
                )
                resp_data_i = resp_corr_i.json()
                corrs_i = parse_helpers_receipts.get_correspondence_from_list(resp_data_i)
                corrs_asc.extend(corrs_i)
                resp_prev = resp_corr_i
                resp_prev_json = resp_data_i
            except Exception as e:
                self.logger.error(
                    "{}: correspondence page #{}. Abort pagination. "
                    "HANDLED EXCEPTION: {}\nRESPONSE\n{}".format(
                        organization_title,
                        page_ix,
                        e,
                        resp_corr.text,
                    )
                )

        return corrs_asc

    def download_correspondence(
            self,
            s: MySession,
            event_number: int,
            organization_title: str,
            company_param: Optional[str] = None) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Implements the documents downloading from each company (i.e. contract) correspondence mailbox.
        It gets the pdf files, saves them to the "receipts folder"
        and inserts the documents data in _TesoraliaDocuments table.

        Redefines download_documents method to provide real results
        """

        if not self.basic_should_download_correspondence():
            return False, []

        organization = self.basic_get_organization(organization_title)
        if not organization:
            self.logger.error("No organization_saved with title {}. Can't continue. Abort".format(
                organization_title
            ))
            return False, []
        self.logger.info("{}: download correspondence".format(organization.Name))

        corrs_parsed = self._get_correspondence_docs_parsed(
            s,
            event_number,
            organization.Name,
            company_param
        )  # type: List[CorrespondenceDocParsed]

        self.logger.info('{}: got {} correspondence docs for accounts: {}'.format(
            organization.Name,
            len(corrs_parsed),
            sorted(list({acc.account_no for acc in corrs_parsed}))
        ))

        for i, corr_parsed in enumerate(corrs_parsed):

            fin_ent_account_id = product_to_fin_ent_id(corr_parsed.account_no)
            if not self.basic_should_download_correspondence_for_account(fin_ent_account_id):
                continue

            try:
                clave_expediente = {
                    "claveExpediente": [
                        # "00000" -> encrypted 'CDYAxWdVvT/I2PldPSGiQO....CKtHCaeEh9xw1WQ=='
                        OrderedDict([
                            ("identificadorClave", "1"),
                            ("valorClave", corr_parsed.extra['req_args']['claveIPLUS'])
                        ]),
                        # "10600" -> encrypted
                        OrderedDict([
                            ("identificadorClave", "2"),
                            ("valorClave", corr_parsed.extra['req_args']['codigoProductoUrsusEncr'])
                        ]),
                        # "00041236000013510" -> encrypted
                        OrderedDict([
                            ("identificadorClave", "3"),
                            ("valorClave", corr_parsed.extra['req_args']['identificadorProductoEncr'])
                        ]),
                        # "01.08.2018" -> encrypted
                        OrderedDict([
                            ("identificadorClave", "4"),
                            ("valorClave", corr_parsed.extra['req_args']['fechaComunicacionEncr']['valor'])
                        ]),
                        # "00000048" -> encrypted
                        OrderedDict([
                            ("identificadorClave", "5"),
                            ("valorClave", corr_parsed.extra['req_args']['codigoTipoDocumentoEncr'])
                        ]),
                        # "00001" -> encrypted
                        OrderedDict([
                            ("identificadorClave", "6"),
                            ("valorClave", corr_parsed.extra['req_args']['claveDocumentoComunicacionEncr'])
                        ]),
                    ]
                }

                doc_pdf_content = self._download_pdf_from_expedient_key(
                    s,
                    "IPLCORRESP",
                    "CORRESPOND",
                    clave_expediente
                )

                corr_scraped = CorrespondenceDocScraped(
                    CustomerId=self.db_customer_id,
                    OrganizationId=organization.Id,
                    FinancialEntityId=self.db_financial_entity_id,
                    ProductId=corr_parsed.account_no,
                    ProductType=corr_parsed.extra['product_type'],
                    DocumentDate=corr_parsed.operation_date,
                    Description=corr_parsed.descr,
                    DocumentType=corr_parsed.type,
                    DocumentText=pdf_funcs.get_text(doc_pdf_content),
                    Checksum=pdf_funcs.calc_checksum(doc_pdf_content),
                    AccountId=None,
                    StatementId=None,
                    Amount=corr_parsed.amount,
                    Currency=corr_parsed.currency,
                )

                # Get useful data from PDF
                document_text_info = parse_helpers_receipts.get_document_text_info(
                    pdf_funcs.get_text(doc_pdf_content)
                )

                corr_scraped_upd, should_save = self.basic_check_correspondence_doc_to_add(
                    corr_parsed,
                    corr_scraped,
                    product_to_fin_ent_fn=product_to_fin_ent_id,
                    corr_document_text_info=document_text_info
                )
                if should_save:
                    self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)

            except:
                self.logger.error("{}: can't download correspondence PDF: EXCEPTION\n{}".format(
                    corr_parsed,
                    traceback.format_exc()
                ))

        return True, []

    def _download_pdf_from_expedient_key(self,
                                         s: MySession,
                                         base_datos: str,
                                         expediente: str,
                                         clave_expediente: dict) -> bytes:
        """Implements pdf download procedure to be used by both
        download_receipts (of the movements) and
        download_documents (from the companies correspondence mailboxes)
        """

        req_headers = self.basic_req_headers_updated({
            'x-j_gid_cod_app': 'o2',
        })

        # Step 1. Get the receipt/correspondence id
        req1_params = {
            "entradaConsultaExpediente": OrderedDict([
                ("baseDatos", base_datos),  # "IPLCORRESP" for correspondence
                ("expediente", expediente),  # "CORRESPOND" for correspondence
                ("ordenDocumento", "1"),
                ("claves", clave_expediente)
            ])
        }

        req1_url = (
            'https://oficinaempresas.bankia.es/api/1.0/servicios/obtenerdocumentos/2.0/'
            'comunes/iplus/obtenerdocumentos?request={}&_ts{}'.format(
                json.dumps(req1_params),
                int(time.time() * 1000)
            )
        )

        # <<<< {"documentos":[
        # {"codigoEstado":"M","identificadorUsuario":"CORRESP","extensionDocumento":"PDF",
        # "fechaAlta":{"microsegundos":"000000","date":"Aug 2, 2018 12:00:00 AM",
        # "timeZone":"Europe/Madrid","codigo":"2018-08-02-00.00.00.000000","fecha":{
        # "codigo":"2018-08-02","año":2018,"mes":8,"diaDelMes":2,"diaDeLaSemana":4,
        # "diasDesdeUnoDeEnero":214,"fechaGregorianCalendar":"Aug 2, 2018 1:01:01 AM",
        # "literalDiaDeLaSemana":"Jueves","literalMesDelAño":"Agosto","ultimoDiaDelMes":31,
        # "bisiesto":false},"rfc822TimeZone":"+0200","horas":"00","minutos":"00","segundos":"00",
        # "timestampSQL":"Aug 2, 2018 12:00:00 AM"},"metadatosDocumento":[],
        # "identificadorDocumento":"UHOMDFNEUQBLIM5RN1M54285H6MONF83UT8EDB95","nombreDocumento":"
        #  ","numeroOrden":1,"numeroOrdenPresentacion":0}],"clavePaginacionOut":"0"}
        resp1 = self._req_json_get_with_retry(
            s,
            req1_url,
            req_headers,
            self.req_proxies
        )

        receipt_id = resp1.json().get('documentos', [{}])[0].get('identificadorDocumento')
        if not receipt_id:
            self.logger.warning("{}".format('No receipt_id. RESPONSE:\n{}\n'
                                            'Skip'.format(resp1.text)))
            return b''

        # Step 2. Get the receipt/correspondence download url

        req2_url = ('https://oficinaempresas.bankia.es/api/1.0/saps/comunes/iplus/documentos'
                    '/{}?x-j_gid_cod_app=o2&_ts{}'.format(receipt_id, int(time.time() * 1000)))

        # <<<< {"codigoEstado":" ","codigoUsuario":"CORRESP",
        # "extensionDocumento":"PDF",
        # "fechaAlta":"2018-08-02-00.00.00.000000","metadatosDocumento":[],
        # "numeroOrdenPresentacion":0,
        # "localizadorDocumento":
        # "generica/A153676_7118507408111634344___552018-09-0120.08.1198351148/00001/00001/001/1.PDF",
        # "nombreDocumento":" ",
        # "numeroOrden":0}
        resp2 = self._req_json_get_with_retry(s, req2_url, req_headers, self.req_proxies)
        receipt_url = resp2.json()['localizadorDocumento']

        # Step 3. Download PDF

        req3_url = ('https://oficinaempresas.bankia.es/api/1.0/sap/commons/transmission/'
                    'get/EWDCZZZG/{}?x-j_gid_cod_app=o2'.format(receipt_url))
        resp3 = s.get(
            req3_url,
            headers=req_headers,
            proxies=self.req_proxies,
            stream=True
        )
        pdf_file_content = resp3.content

        return pdf_file_content
