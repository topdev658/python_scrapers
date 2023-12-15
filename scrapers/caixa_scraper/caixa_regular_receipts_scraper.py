import random
import re
import time
import traceback
from collections import OrderedDict
from typing import List, Tuple
# splitquery is hidden but can be imported
from urllib.parse import urljoin

from custom_libs import extract
from custom_libs import pdf_funcs
from custom_libs.extract import splitquery
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, MovementParsed, MovementScraped,
    ScraperParamsCommon, CorrespondenceDocScraped, CorrespondenceDocParsed
)
# from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
from scrapers.caixa_scraper.caixa_regular_scraper import CaixaScraper
from . import parse_helpers_regular as parse_helpers

__version__ = '5.19.0'

__changelog__ = """
5.19.0 2023.08.24
download_correspondence: deleted unnecessary method call to basic_get_organization
5.18.0 2023.06.26
modified INVALID_PDF_MARKERS
5.17.0
added _get_pdf_document_from_correspondence_parsed:
_get_correspondence_documents: changed pdf download just after each pagination step
5.16.0
_pdf_text_wo_export_date: drops leading 'export date' before hashing
5.15.0
removed call to basic_save_receipt_pdf_and_update_db 
(only basic_save_receipt_pdf_as_correspondence is needed now) 
5.14.0
check for ok after basic_save_receipt_pdf_as_correspondence
5.13.0
CONCURRENT_PDF_SCRAPING_EXECUTORS = 1 (or downloads same PDFs for different movs)
5.12.0
save receipt metadata
always calc receipt_checksum
5.11.0
renamed to _receipt_checksum()
5.10.0
save receipt as correspondence
5.9.0
_product_to_fin_ent_id to use in children
scraper_name as class prop
5.8.0
download_movement_receipt: handle unexpected resps, download receipts w/o stream
5.7.1
upd log: mov_str
5.7.0
use basic_should_download_correspondence_for_account
5.6.0
_open_correspondence_page_ix: different parsing if exist paginacionComunicadosNew
_get_correspondence_documents: different parsing if exists tablacorresp or tablaComunicado
_open_corr_details_and_download_pdf: different parsing if exists refval_complejo_param or ref_parametros_comunicado
5.5.0
use splitquery from custom_libs.extract
5.4.1
fixed _pdf_checksum_wo_export_date
5.4.0
text from all pages of multi-PDF correspondence  
5.3.0
multi-PDF correspondence
5.2.0
INVALID_PDF_MARKERS
5.1.1
upd log msgs 
5.1.0
use basic_should_download_correspondence_for_access
5.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
4.4.0
basic_should_download_company_documents_for_customer to set 'save_checksum' flag
4.3.1
TEMP: use custom temporary DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS = 14 
to re-scrape missed during correspondence down period  
4.3.0
correspondence: upd reqs
parse_helpers_regular: get_corespondence_from_list: extract currency 
4.2.0
correspondence: currency field support
4.1.0
use project-level offset for corr
4.0.0
use basic funcs for correspondence
use project types
DocumentScraped: upd field (DocumentDate: datetime)
3.7.1
DOWNLOAD_CORRESPONDENCE_DAYS_BEFORE_DATE_TO=4
3.7.0
handle 'no correspondence'
several attempts to get correct resp with correspondence
3.6.2
upd log msg
3.6.1
upd ACCESSES_TO_DOWNLOAD_ONLY_CORRESPONDENCE
3.6.0
documents_parsed_asc
3.5.0
_calc_checksum_wo_export_date
ACCESSES_TO_DOWNLOAD_ONLY_CORRESPONDENCE
3.4.0
aligned pdf_checksum implementation (for receipts and correspondence)
3.3.0
can do pagination for company correspondence
3.2.1
handle absent receipt_params 
3.2.0
_open_document_page_and_download_pdf, parse_helpers: handle more cases for account_iban
3.1.0
more 'wrong layout' checks
upd log msgs
removed unnecessary reqs
3.0.0
download_company_documents implemented
2.1.1
upd type hints
2.1.0
is_receipts_scraper property
2.0.0
download_receipts: use basic_download_receipts_common
download_movement_receipt: use new basic_save_receipt_pdf_and_update_db
parse_helpers_regular: removed unused get_receipt_text_faster_fitz
parse_helpers_regular: removed unused get_receipt_text_fitz
call basic_update_db_with_receipt_pdf_info with text as is (no replacement for quotes needed)
1.0.1
fmt
1.0.0
init
"""

USER_AGENT = ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.22 '
              '(KHTML, like Gecko) Chrome/25.0.1364.97 Safari/537.22')

DOCS_PER_PAGE = 15
MAX_PDF_PAGES_PER_FILE = 12

# The list with accesses
# to skip receipt downloading from movement list
# in favor of mailbox correspondence downloading.
# This is to skip receipts downloading in favor of mailbox correspondence downloading,
# but only for specific accesses to prevent duplicates
# at movement-list-receipts level,
# (because some movements have shared receipts and fin entity provide them
# for all movements which share the same receipt)
ACCESSES_TO_DOWNLOAD_ONLY_CORRESPONDENCE = [
    22952,  # -u 395518 (GAMBAFRESH)
    23006,  # -u 398774 (LANTEGI BATUAK)
    17715,  # -u 305424 (GRUPO CONTROL)
]

DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS = 8

# HTML instead of desired PDF
INVALID_PDF_MARKERS = [
    b'<script type=',
    b'<HTML',
    b'<html',
    b'<!DOCTYPE html'
]

KEY_CORRESPONDENCE_DOCUMENT_ACCOUNT_IBAN = 'document_account_iban'
KEY_CORRESPONDENCE_DOCUMENT_PDF_CONTENT = 'document_pdf_content'


class CaixaReceiptsScraper(CaixaScraper):
    CONCURRENT_PDF_SCRAPING_EXECUTORS = 1

    scraper_name = 'CaixaReceiptsScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        # important field for movements processing optimization
        self.is_receipts_scraper = True

    def _pdf_text_wo_export_date(self, document_text: str) -> str:
        """For receipts and correspondence
        Drops trailing 'export date' before hashing:
            '200604 13.46',
            '200604 15.47'
            '200605 03.47'
        to get equal checksums each time

        Drops leading 'export date' before hashing:
            '8 Dic 2022'
            '12 Dic 2022'
        to get equal checksums each time
        """
        document_text_clean = re.sub(r'(?s)\n\d{6}\s\d{2}\.\d{2}$', '', document_text)
        document_text_clean = re.sub(r'(?s)^\d{1,2}\s[a-zA-Z]{3}\s\d{4}\n', '', document_text_clean)
        return document_text_clean

    def _receipt_checksum(self, document_text: str) -> str:
        """Without export date"""
        document_text_clean = self._pdf_text_wo_export_date(document_text)
        checksum = pdf_funcs.calc_checksum(bytes(document_text_clean, 'utf-8'))
        return checksum

    def _is_valid_pdf(self, resp_pdf_content: bytes) -> bool:
        """Detects by explicit 'invalid' markers"""
        is_valid = (resp_pdf_content.startswith(b'%PDF')
                    and not any(m in resp_pdf_content for m in INVALID_PDF_MARKERS))
        return is_valid

    @staticmethod
    def _product_to_fin_ent_id(product_id: str) -> str:
        """Can redefine in children (Bankia)"""
        return product_id

    def download_receipts(
            self, s: MySession,
            resp_movs: Response,
            account_scraped: AccountScraped,
            movements_scraped: List[MovementScraped],
            movements_parsed: List[MovementParsed]) -> Tuple[bool, List[MovementScraped]]:
        """Redefines stub method to provide real results"""

        # Skip receipts downloading in favor of mailbox correspondence downloading
        # to prevent duplicates, but only for specific accesses
        # (NOT TESTED AS A GENERAL APPROACH FOR ALL ACCESSES)
        if self.db_financial_entity_access_id in ACCESSES_TO_DOWNLOAD_ONLY_CORRESPONDENCE:
            return True, movements_scraped

        # DAF: For CAIXA receipt downloading depends on
        # the extended_descriptions scraping is activated
        # bcs receipt params are in the same page than the extended description params.
        if not self.basic_should_scrape_extended_descriptions():
            return False, movements_scraped

        save_checksum = self.basic_should_download_correspondence_for_access()

        return self.basic_download_receipts_common(
            s,
            account_scraped,
            movements_scraped,
            movements_parsed,
            meta={'req_url': resp_movs.url, 'save_checksum': save_checksum}
        )

    def download_movement_receipt(self,
                                  s: MySession,
                                  account_scraped: AccountScraped,
                                  movement_scraped: MovementScraped,
                                  movement_parsed: MovementParsed,
                                  meta: dict) -> str:

        """Downloads, saves receipt and returns its text (description)"""

        req_url = meta['req_url']  # type: str
        save_checksum = meta['save_checksum']  # type: bool

        if not movement_parsed.get('receipt_params'):
            return ''

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        mov_str = self.basic_mov_parsed_str(movement_parsed)

        self.logger.info('Download receipts for {}'.format(mov_str))
        try:
            for att in range(1, 3):

                resp_pdf = s.post(
                    req_url,
                    data=movement_parsed['receipt_params'],
                    headers=self.req_headers,
                    proxies=self.req_proxies
                )
                if resp_pdf.headers['Content-Type'] != 'application/x-download':
                    self.logger.error("{}: {}: can't download pdf: BAD Content-Type\n{}".format(
                        account_scraped.FinancialEntityAccountId,
                        movement_parsed['operation_date'],
                        resp_pdf.headers['Content-Type']
                    ))
                    return ''  # -6931, ROTONDA GRUPO EMPRESARIAL, due to many movs?

                # To calc checksums only for receipts if should_download_company_documents
                # (to avoid duplicates from company correspondence)
                # Difference to Bankia: we use text because backend returns
                # always slightly different PDFs for the same movements
                time.sleep(0.1)
                receipt_parsed_text = pdf_funcs.get_text(resp_pdf.content)

                if not receipt_parsed_text.startswith('FlateDecode>>stream'):
                    # expected description
                    break
                # unwanted description
                self.logger.warning("{}: {}: att #{}: got wrong receipt PDF. Retry".format(
                    fin_ent_account_id,
                    mov_str,
                    att,
                ))
                time.sleep(1 + random.random())
                continue
            else:
                self.logger.warning("{}: {}: can't download valid receipt PDF. Skip".format(
                    fin_ent_account_id,
                    mov_str
                ))
                return ''

            receipt_checksum = self._receipt_checksum(receipt_parsed_text)

            ok, _, _ = self.basic_save_receipt_pdf_as_correspondence(
                account_scraped,
                movement_scraped,
                resp_pdf.content,
                pdf_parsed_text=receipt_parsed_text,
                checksum=receipt_checksum,
                account_to_fin_ent_fn=self._product_to_fin_ent_id
            )

            return receipt_parsed_text

        except Exception as _e:
            self.logger.error("{}: {}: can't download receipt PDF: EXCEPTION\n{}".format(
                fin_ent_account_id,
                mov_str,
                traceback.format_exc()
            ))
            return ''

    def _open_company_recent_correspondence(
            self,
            s: MySession,
            resp_prev: Response) -> Tuple[MySession, Response]:

        req_url = splitquery(resp_prev.url)[0]
        req_mailbox_params = OrderedDict([
            ('PN', 'MBX'),
            ('PE', '1'),
            ('CLICK_ORIG', ''),
            ('REMOVE_REFVAL', '0'),
            ('VOLVER_PE', ''),
            ('VOLVER_PN', ''),
            ('ORIGEN_PE', ''),
            ('ORIGEN_PN', ''),
            ('BAJA', ''),
            ('MODIFICAR', ''),
            ('CLICK_ORIG', ''),
        ])

        _resp_mailbox = s.post(
            req_url,
            data=req_mailbox_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # MailBox - Mis documentos: Correspondencia (0) foldable
        req_correspondence_widget_params = OrderedDict([
            ('PN', 'COX'),
            ('PE', '1'),
            ('CLICK_ORIG', 'AJX_MBX_1'),
            ('FLAG_OPERATIVA_CORRESPONDENCIA', 'DASHBOARD_MAILBOX')
        ])

        _resp_corespondence_widget = s.post(
            req_url,
            data=req_correspondence_widget_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # Click on right bottom 'Toda la correspondencia'
        req_corrs_all_params = OrderedDict([
            ('PN', 'COX'),
            ('PE', '1'),
            ('PAGINAR_CUENTA', 'S'),
            ('CLICK_ORIG', 'EOC_MBX_1')
        ])

        resp_corrs_all = s.get(
            req_url,
            params=req_corrs_all_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return s, resp_corrs_all

    def _open_correspondence_filtered_first_page(
            self,
            s: MySession,
            resp_prev: Response,
            date_from_str: str,
            date_to_str: str) -> Tuple[MySession, Response]:
        """:param date_from_str: date like 20200526
           :param date_to_str:  date like 20200531
        """
        req_url = splitquery(resp_prev.url)[0]

        req_params = OrderedDict([
            ('PN', 'COX'),
            ('PE', '1'),
            ('TIPO_LISTA_CUENTAS', 'V'),
            ('CAMPO_ORDENACION', 'FD'),
            ('SELECTOR_FECHA', ''),
            ('CLICK_ORIG', 'AJX_COX_1'),
            ('REFVAL_SIMPLE_NUMERO_CUENTA', ''),
            ('IND_CTA_FORZADA', 'N'),
            ('FECHA_DESDE', date_from_str),  # 20200526
            ('FECHA_HASTA', date_to_str),  # 20200531
            ('CON_FILTRO', 'true'),
            ('PETICION_AJAX', 'S'),
        ])

        time.sleep(0.1 + 0.1 * random.random())
        resp_docs_filtered = s.post(
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return s, resp_docs_filtered

    def _open_correspondence_page_ix(
            self,
            s: MySession,
            resp_prev: Response,
            organization_title: str,
            date_from_str: str,
            date_to_str: str,
            n_docs_total: int,
            page_num: int) -> Tuple[bool, MySession, Response]:
        """:param date_from_str: date like 20200526
           :param date_to_str:  date like 20200531
           :param page_num: page num [1,2..]
        """
        req_url = splitquery(resp_prev.url)[0]
        # b3mb6TfY6X9veZvpN9jpfwAAAXJsY9B1hXIeYy0e2qw
        refval_param = parse_helpers.get_docs_next_page_refval_param(resp_prev.text)
        if not refval_param:
            self.basic_log_wrong_layout(
                resp_prev,
                "{}: page {}: can't parse refval_param for the next page with correspondence".format(
                    organization_title,
                    page_num
                )
            )
            return False, s, resp_prev
        req_params = OrderedDict([
            ('PN', 'COX'),
            ('PE', '1'),
            ('TIPO_LISTA_CUENTAS', 'V'),
            ('CAMPO_ORDENACION', 'FD'),
            ('SELECTOR_FECHA', ''),
            ('CLICK_ORIG', 'AJX_COX_1'),
            ('REFVAL_SIMPLE_NUMERO_CUENTA', ''),
            ('IND_CTA_FORZADA', 'N'),
            ('FECHA_DESDE', date_from_str),  # 20200526
            ('FECHA_HASTA', date_to_str),  # 20200531
            ('CON_FILTRO', 'true'),
            ('REFVAL_SIMPLE_CLAVE_CONTINUACION_LISTA_COMUNICADOS', refval_param),
            ('TOTAL_LISTA_COMUNICADOS', str(n_docs_total)),
            ('TOTAL_LISTA_COMUNICADOS_VISUALIZADOS', str(DOCS_PER_PAGE * (page_num - 1))),  # skip prev docs
            ('PAGINACION', 'ACUMULATIVA'),
            ('PETICION_AJAX', 'S')
        ])

        if 'paginacionComunicadosNew' in resp_prev.text:
            req_params = OrderedDict([
                ('PN', 'COX'),
                ('PE', '1'),
                ('CAMPO_ORDENACION', 'FD'),
                ('SELECTOR_FECHA', ''),
                ('TIPO_LISTA_CUENTAS', 'V'),
                ('FECHA_DESDE', date_from_str),  # 20200526
                ('FECHA_HASTA', date_to_str),  # 20200531
                ('LISTA_CATEGORIAS', ''),
                ('IND_CTA_FORZADA', ''),
                ('CLICK_ORIG', 'PAG_COX_1'),
                ('REFVAL_SIMPLE_CLAVE_CONTINUACION_LISTA_COMUNICADOS', refval_param),
                ('TOTAL_LISTA_COMUNICADOS', str(n_docs_total)),
                ('TOTAL_LISTA_COMUNICADOS_VISUALIZADOS', str(DOCS_PER_PAGE * (page_num - 1))),  # skip prev docs
                ('PAGINACION', 'ACUMULATIVA'),
                ('PETICION_AJAX', 'S')
            ])

        resp_docs_filtered_i = s.post(
            req_url,
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return True, s, resp_docs_filtered_i

    def _get_pdf_document_from_correspondence_parsed(
            self,
            s: MySession,
            resp_company_home: Response,
            organization_title: str,
            corrs_parsed: List[CorrespondenceDocParsed],
            page_num) -> List[CorrespondenceDocParsed]:
        for i, corr_parsed in enumerate(corrs_parsed):
            try:
                self.logger.info("{} page {} document {}: Download corresponcence for doc parsed: {}, {}, {}".format(
                    organization_title,
                    page_num,
                    i+1,
                    corr_parsed.operation_date,
                    corr_parsed.amount,
                    corr_parsed.descr,
                ))
                ok, s, account_iban, doc_pdf_contents = self._open_corr_details_and_download_pdf(
                    s,
                    resp_company_home,
                    organization_title,
                    corr_parsed
                )
                if not ok:
                    continue  # already reported
                corrs_parsed[i].extra[KEY_CORRESPONDENCE_DOCUMENT_PDF_CONTENT] = doc_pdf_contents
                corrs_parsed[i].extra[KEY_CORRESPONDENCE_DOCUMENT_ACCOUNT_IBAN] = account_iban
            except Exception as _e:
                self.logger.error("{}: {}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                    organization_title,
                    corr_parsed,
                    traceback.format_exc()))

        return s, corrs_parsed

    def _get_correspondence_documents(
            self,
            s: MySession,
            resp_company_home: Response,
            organization_title: str) -> Tuple[MySession, List[CorrespondenceDocParsed]]:

        date_from, _ = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
        )

        date_from_str = date_from.strftime('%Y%m%d')
        date_to_str = self.date_to.strftime('%Y%m%d')

        self.logger.info('{}: get correspondence documents from {} to {}'.format(
            organization_title,
            date_from_str,
            date_to_str
        ))

        s, resp_docs_recent = self._open_company_recent_correspondence(
            s,
            resp_company_home
        )

        corrs_desc = []  # type: List[CorrespondenceDocParsed]
        try:
            resp_docs_filtered = Response()
            for att in range(1, 4):
                self.logger.info('{}: get resp_docs_filtered: attempt #{}'.format(organization_title, att))
                s, resp_docs_filtered = self._open_correspondence_filtered_first_page(
                    s,
                    resp_docs_recent,
                    date_from_str,
                    date_to_str
                )
                # Check for failed request
                if (('Sentimos comunicarle que su petición no se ha realizado' in resp_docs_filtered.text)
                        or 'EN ESTOS MOMENTOS NO ESTA DISPONIBLE' in resp_docs_filtered.text):
                    self.logger.warning("{}: can't get correct resp_docs_filtered. Retry".format(
                        organization_title,
                    ))
                    time.sleep(1 + random.random())
                    continue
                break
            else:
                self.basic_log_wrong_layout(
                    resp_docs_filtered,
                    "{}: can't get correct resp_docs_filtered. Abort".format(organization_title)
                )
                return s, []

            corrs_desc = parse_helpers.get_corespondence_from_list(resp_docs_filtered.text)
            ok, n_docs_total = parse_helpers.get_number_of_correspondence_documents(resp_docs_filtered.text)
            self.logger.info('{}: total {} correspondence document(s)'.format(organization_title, n_docs_total))
            if not n_docs_total:
                return s, []

            if n_docs_total > 0:
                self.logger.info('{}: get correspondence from page {}'.format(
                        organization_title,
                        1
                    ))

            s, corrs_desc = self._get_pdf_document_from_correspondence_parsed(s, resp_company_home, organization_title, corrs_desc, 1)

            if not ok:
                self.basic_log_wrong_layout(
                    resp_docs_filtered,
                    "{}: can't get total number of correspondence. Abort".format(organization_title)
                )
                return s, []

            resp_prev = resp_docs_filtered
            for page_num in range(2, 30):  # up to 450 docs total

                if 'tablacorresp' in resp_prev.text:
                    has_next_page = bool(extract.get_link_by_text(resp_prev.text, '', 'Siguientes'))
                if 'tablaComunicadosNew' in resp_prev.text:
                    has_next_page = bool(extract.get_link_by_text(resp_prev.text, '', 'Ver siguientes'))

                if not has_next_page:
                    break
                self.logger.info('{}: get correspondence from page {}'.format(
                    organization_title,
                    page_num
                ))
                ok, s, resp_docs_i = self._open_correspondence_page_ix(
                    s,
                    resp_prev,
                    organization_title,
                    date_from_str,
                    date_to_str,
                    n_docs_total,
                    page_num
                )
                # Early stop, already logged
                if not ok:
                    return s, corrs_desc
                corrs_i = parse_helpers.get_corespondence_from_list(resp_docs_i.text)
                s, corrs_i = self._get_pdf_document_from_correspondence_parsed(s, resp_company_home, organization_title, corrs_i, page_num)

                corrs_desc.extend(corrs_i)
                resp_prev = resp_docs_i
                time.sleep(0.2 + 0.2 * random.random())
        except Exception as e:
            self.logger.warning("{}: can't parse documents from resp {}.\nGOT EXCEPTION:\n{}\nABORT".format(
                organization_title,
                resp_docs_recent.text,
                e
            ))

        documents_parsed_asc = corrs_desc[::-1]
        return s, documents_parsed_asc

    def _download_multi_pdf(
            self,
            s: MySession,
            resp_prev: Response,
            org_title: str,
            corr_parsed: CorrespondenceDocParsed) -> Tuple[bool, List[bytes]]:
        # Expect, see req-resp_corr_multipdf, 030_resp_multi-file-corr_instead_of_pdf.html
        # PNalBody=COX
        # PAGINA_SOLICITADA=00001
        # DIVISA_IMPORTE_COMUNICADO=200
        # TIPO_COMUNICADO=01523
        # TORNA_PN=COX
        # INDICADOR_DUPLICADO_COMUNICADO=S
        # CLICK_ORIG
        # DESCRIPCION_COMUNICADO=Liquidaci%C3%B3n+cuenta+de+cr%C3%A9dito
        # PEalBody=12
        # OPCION
        # TIPO_CUENTA_COMUNICADO=ES
        # FLUJO=COX,2,:COX,1,:GFI,7,''
        # FORMATO_COMUNICADO=G
        # RESOLUCION=300
        # CANAL_MOVIMIENTO=INT
        # CATEGORIA_COMUNICADO=6
        # TORNA_PE=1
        # FAVORITO_COMUNICADO=N
        # CLAVE_COMUNICADO=20210101002850000327
        # FLAG_JURIDICA=J
        # NUMERO_MAXIMO_PAGINAS_PDF=12  <--- !!
        # REFVAL_SIMPLE_CLAVE_COMUNICADO=xg~84PrnmD3GD7zg~ueYPQAAAXcRHOVRSA7ktLVwjKk
        # NUMERO_PAGINAS=00015  <--- TOTAL PDF PAGES
        # REFCLAVECOMUNICADO=xg~84PkHyfLGD7zg~QfJ8gAAAXcRHOVBCXFRsrQqb~Y:COX:2
        # RefInformacionComunicado=xg~84PkMCIfGD7zg~QwIhwAAAXcRHOlK3HkeYJZVkTY:COX:2
        # CODIGO_CUENTA_COMUNICADO=0012100381020020600000030647
        # IMPORTE_COMUNICADO=2.639,60
        # presentacion=/jsp/elocoxp001300.jsp
        # PN=COX
        # PE=12  <-- (== BLOQUE_PAGINAS_FINAL? / )
        # IS_INICIO_DOCUMENTOS
        # PAGINA_DOCUMENTOS_SOLICITADA
        # BLOQUE_PAGINAS_INICIAL=1  <-- pdf pages from
        # BLOQUE_PAGINAS_FINAL=12   <-- pdf pages to
        # CLICK_ORIG
        # Page 1
        req_corr_link_pdf1, req_corr_params_pdf1 = extract.build_req_params_from_form_html_patched(
            resp_prev.text,
            'formAbrirPDF',
            is_ordered=True
        )

        # '00015' -> 15
        # Number of pdf pages of the document
        # It is possible to get max 12 pdf pages at one file
        num_pdf_pages_str = req_corr_params_pdf1.get('NUMERO_PAGINAS', '')
        if not num_pdf_pages_str:
            self.basic_log_wrong_layout(
                resp_prev,
                "{}: {}: can't get param NUMERO_PAGINAS".format(org_title, corr_parsed)
            )
            return False, []
        num_pdf_pages = int(num_pdf_pages_str)
        if num_pdf_pages > MAX_PDF_PAGES_PER_FILE * 2:
            self.logger.error('{}: {}: UNIMPLEMENTED: more than 2 PDF files per doc. '
                              'Pls, implement this case'.format(org_title, corr_parsed))
            return False, []

        req_corr_params_pdf1['PN'] = 'COX'
        req_corr_params_pdf1['PE'] = '12'
        req_corr_params_pdf1['BLOQUE_PAGINAS_INICIAL'] = '1'
        req_corr_params_pdf1['BLOQUE_PAGINAS_FINAL'] = str(MAX_PDF_PAGES_PER_FILE)  # max number of pdf pages

        req_corr_url_pdf1 = urljoin(resp_prev.url, req_corr_link_pdf1)
        resp_corr_pdf1 = s.post(
            req_corr_url_pdf1,
            data=req_corr_params_pdf1,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if not self._is_valid_pdf(resp_corr_pdf1.content):
            self.basic_log_wrong_layout(
                resp_corr_pdf1,
                "{}: {}: pdf file #1: can't download multi-file correspondence".format(org_title, corr_parsed)
            )
            return False, []
        time.sleep(0.1)
        # Page 2
        req_corr_link_i, req_corr_params_i_raw = extract.build_req_params_from_form_html_patched(
            resp_prev.text,
            'formPaginacionPDFs',
            is_ordered=True
        )
        req_corr_url_i = urljoin(resp_prev.url, req_corr_link_i)
        req_corr_params_i = req_corr_params_pdf1.copy()
        req_corr_params_i.update(req_corr_params_i_raw)  # fill many params from
        req_corr_params_i['PN'] = 'COX'
        req_corr_params_i['PE'] = '12'
        req_corr_params_i['BLOQUE_PAGINAS_INICIAL'] = str(MAX_PDF_PAGES_PER_FILE + 1)
        req_corr_params_i['BLOQUE_PAGINAS_FINAL'] = str(num_pdf_pages)
        resp_corr_pdf_i = s.post(
            req_corr_url_i,
            data=req_corr_params_i,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if not self._is_valid_pdf(resp_corr_pdf_i.content):
            self.basic_log_wrong_layout(
                resp_corr_pdf_i,
                "{}: {}: pdf file #2: can't download multi-file correspondence".format(org_title, corr_parsed)
            )
            return False, []

        return True, [resp_corr_pdf1.content, resp_corr_pdf_i.content]

    def _open_corr_details_and_download_pdf(
            self,
            s: MySession,
            resp_prev: Response,
            org_title: str,
            corr_parsed: CorrespondenceDocParsed) -> Tuple[bool, MySession, str, List[bytes]]:
        """:returns (ok, session, account_iban, [pdf_content1, pdf_content_2])"""
        req_url = splitquery(resp_prev.url)[0]
        if 'refval_complejo_param' in corr_parsed.extra:
            # ['REFVAL_COMPLEJO_1474', 'HD2pjRqG1Z0cPamNGobVnQAAAXJgFjLgIzasWNFQoIM']
            custom_params = corr_parsed.extra['refval_complejo_param'].split('=')
            req_doc_params = OrderedDict([
                ('PN', 'COX'),
                ('PE', '2'),
                ('TORNA_PN', 'MBX'),
                ('TORNA_PE', '1'),
                ('TORNA_PN_BACKUP', 'MBX'),
                ('TORNA_PE_BACKUP', '1'),
                ('CLICK_ORIG', 'FLX_MBX_1'),
                (custom_params[0], custom_params[1]),
                ('FECHA_DESDE', ''),  # 20190501
                ('FECHA_HASTA', ''),  # 20200529
                ('REFVAL_SIMPLE_NUMERO_CUENTA', ''),
                ('IND_CTA_FORZADA', 'N'),
            ])
        if 'ref_parametros_comunicado' in corr_parsed.extra:
            # 'REFPARAMETROSCOMUNICADO=8U7Jm9U6aGnxTsmb1TpoaQAAAXpc6azqEuSf56aOkv8'
            custom_params = corr_parsed.extra['ref_parametros_comunicado'].split('=')
            req_doc_params = OrderedDict([
                ('PN', 'COX'),
                ('PE', '2'),
                ('TORNA_PN_BACKUP', 'SCP'),
                ('TORNA_PE_BACKUP', '0'),
                ('TORNA_PN', 'COX'),
                ('TORNA_PE', '1'),
                ('CLICK_ORIG', 'FLX_COX_1'),
                (custom_params[0], custom_params[1]),
                ('FECHA_DESDE', ''),  # 20190501
                ('FECHA_HASTA', ''),  # 20200529
            ])

        resp_corr_details = s.post(
            req_url,
            data=req_doc_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        ok, account_iban = parse_helpers.get_account_iban_for_correspondence_document(resp_corr_details.text)

        if not (ok and account_iban):
            self.basic_log_wrong_layout(
                resp_corr_details,
                "{}: {}: can't download PDF: no account_iban. Skip".format(
                    org_title,
                    corr_parsed
                )
            )
            return False, s, '', []

        if not self.basic_should_download_correspondence_for_account(account_iban):
            return False, s, account_iban, []

        req_pdf_link, req_pdf_params = extract.build_req_params_from_form_html_patched(
            resp_corr_details.text,
            form_name='formAbrirPDF_COX2',
            is_ordered=True
        )
        if not (req_pdf_link and req_pdf_params):
            self.basic_log_wrong_layout(
                resp_corr_details,
                "{}: {}: can't download PDF: no req_pdf_link/req_pdf_params. Skip".format(
                    org_title,
                    corr_parsed
                )
            )
            return False, s, '', []

        resp_pdf = s.post(
            urljoin(resp_corr_details.url, req_pdf_link),
            data=req_pdf_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            stream=True
        )

        resp_pdf_content = resp_pdf.content
        if not resp_pdf_content:
            self.basic_log_wrong_layout(
                resp_corr_details,
                "{}: {}: can't download PDF (empty content). Skip".format(
                    org_title,
                    corr_parsed
                )
            )
            return False, s, '', []

        if not self._is_valid_pdf(resp_pdf_content):
            if parse_helpers.is_multi_pdf_correspondence(resp_pdf.text):
                # Multi-file correspondence
                self.logger.info('{}: {}: download multi-PDF correspondence'.format(org_title, corr_parsed))
                ok, resp_pdf_contents = self._download_multi_pdf(
                    s,
                    resp_pdf,  # it's multi-pdf preload html page here
                    org_title,
                    corr_parsed
                )
                if not ok:
                    return False, s, '', []  # already reported
                return True, s, account_iban, resp_pdf_contents

            self.basic_log_wrong_layout(
                resp_pdf,
                "{}: {}: can't download PDF (HTML content). Skip".format(
                    org_title,
                    corr_parsed
                )
            )
            return False, s, '', []

        return True, s, account_iban, [resp_pdf_content]

    def download_correspondence(
            self,
            s: MySession,
            resp_company_home: Response,
            org_title: str) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Implements the documents downloading from each company (i.e. contract) correspondence mailbox.
        It gets the pdf files, saves them to the "receipts folder"
        and inserts the documents data in _TesoraliaDocuments table.

        Redefines download_documents method to provide real results
        """
        if not self.basic_should_download_correspondence():
            return False, []

        self.logger.info("{}: download correspondence".format(org_title))

        s, corrs_parsed = self._get_correspondence_documents(s, resp_company_home, org_title)
        corrs_scraped = []  # type: List[CorrespondenceDocScraped]
        for i, corr_parsed in enumerate(corrs_parsed):
            try:

                if not KEY_CORRESPONDENCE_DOCUMENT_PDF_CONTENT in corr_parsed.extra:
                    continue
                doc_pdf_contents = corr_parsed.extra[KEY_CORRESPONDENCE_DOCUMENT_PDF_CONTENT]
                account_iban = corr_parsed.extra[KEY_CORRESPONDENCE_DOCUMENT_ACCOUNT_IBAN]

                # Update corr_parsed: fill account_no.
                # Use explicit assignment for linting
                # Basically, account_no of CorrespondenceDocParsed is not used in upper funcs,
                # but need to keep it aligned for possible further changes
                corr_parsed = CorrespondenceDocParsed(
                    type=corr_parsed.type,
                    account_no=account_iban,  # fill
                    operation_date=corr_parsed.operation_date,
                    value_date=corr_parsed.value_date,
                    amount=corr_parsed.amount,
                    currency=corr_parsed.currency,
                    descr=corr_parsed.descr,
                    extra=corr_parsed.extra
                )

                document_texts_all_pages = pdf_funcs.get_text_all_pages(doc_pdf_contents)

                # Merge doc_pdf_contents,
                # trim export date at this step (otherwise func will trim only last one)
                document_text = '\n'.join(
                    self._pdf_text_wo_export_date(page_text)
                    for page_text
                    in document_texts_all_pages
                )

                # For checksum, document_texts_all_pages always >= 1 page ('no text' already handled above)
                document_text_1st_page = self._pdf_text_wo_export_date(document_texts_all_pages[0])

                corr_scraped = CorrespondenceDocScraped(
                    CustomerId=self.db_customer_id,
                    OrganizationId=None,
                    FinancialEntityId=self.db_financial_entity_id,
                    ProductId=account_iban,
                    ProductType='',
                    DocumentDate=corr_parsed.operation_date,
                    Description=corr_parsed.descr,
                    DocumentType=corr_parsed.type,
                    DocumentText=document_text,
                    # Need to use Checksum to compare with PDFs from receipts
                    Checksum=pdf_funcs.calc_checksum(bytes(document_text_1st_page, 'utf-8')),
                    AccountId=None,  # Account DB Id
                    StatementId=None,
                    Amount=corr_parsed.amount,
                    Currency=corr_parsed.currency,
                )

                corr_scraped_upd, should_save = self.basic_check_correspondence_doc_to_add(
                    corr_parsed,
                    corr_scraped,
                    product_to_fin_ent_fn=self._product_to_fin_ent_id
                )
                if should_save:
                    corrs_scraped.append(corr_scraped_upd)
                    if len(doc_pdf_contents) == 1:
                        # Single-PDF correspondence (regular case)
                        self.basic_save_correspondence_doc_pdf_and_update_db(
                            corr_scraped_upd,
                            doc_pdf_contents[0]
                        )
                    else:
                        # Multi-PDF correpondence (rare case)
                        self.basic_save_correspondence_doc_zip_and_update_db(
                            corr_scraped_upd,
                            doc_pdf_contents
                        )

            except Exception as _e:
                self.logger.error("{}: {}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                    org_title,
                    corr_parsed,
                    traceback.format_exc()
                ))

        return True, corrs_scraped
