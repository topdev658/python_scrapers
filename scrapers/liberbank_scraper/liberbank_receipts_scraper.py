import random
import time
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import List, Tuple
from urllib.parse import urljoin

from custom_libs import extract
from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession, Response
from project.custom_types import (
    CorrespondenceDocScraped, CorrespondenceDocParsed,
    AccountScraped, MovementScraped, MovementParsed,
    ScraperParamsCommon
)
from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS, DEFAULT_PROXIES
from . import parse_helpers
from . import parse_helpers_receipts
from . import req_helpers
from .custom_types import CorrespondenceAccountOption
from .liberbank_scraper import LiberbankScraper

__version__ = '4.5.0'

__changelog__ = """
4.6.0
removed call to basic_save_receipt_pdf_and_update_db 
(only basic_save_receipt_pdf_as_correspondence is needed now) 
4.5.0
check for ok after basic_save_receipt_pdf_as_correspondence
4.4.0
save receipt metadata
always calc receipt_checksum (was only by flag save_checksum)
4.3.0
renamed to _receipt_checksum()
4.2.0
save receipt as correspondence
4.1.0
use basic_should_download_correspondence_for_account
upd log msg
4.1.0
use basic_should_download_correspondence_for_access
4.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
3.2.0
set self.is_receipts_scraper=True (for serial processing from parent)
download_movement_receipt: several attempts to get valid resps
3.1.0
_calc_checksum_wo_export_date: handle several timestamps in a doc 
3.0.0
movement receipt downloading
2.2.0
correspondence: currency field support
2.1.0
use project-level offset for corr
2.0.0
use basic funcs for correspondence
use project types
DocumentScraped: upd field (DocumentDate: datetime)
1.1.0
_calc_checksum_wo_export_date
DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS = 7
1.0.0
impl correspondence downloading
"""


class LiberbankReceiptsScraper(LiberbankScraper):
    scraper_name = 'LiberbankReceiptsScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        # Inform parent scraper, it will process accounts in serial mode
        # (or it fail on receipt downloading, -a 24432)
        self.is_receipts_scraper = True

    def _product_to_fin_ent_id_suffix(self, product_id: str) -> str:
        """
        Need ES5020482179183400001768 -> 20480121790000183400001768,
        but it's can't be built this way,
        so let's use suffix 183400001768, it is acceptable for the needed db_funcs
        """
        return product_id[-12:]

    def _receipt_checksum(self, document_text: str) -> str:
        """Drops trailing 'export date' before hashing:
            '200604 13.46',
            '200604 15.47'
            '200605 03.47'
        to get equal checksums each time
        """
        # timestamp_info placed in the end of the doc (mandatory),
        # but also can be placed somewhere else
        # '\n12-11-2020 20:50:59 0442 2048088593 0063-5-10'
        timestamp_info = extract.re_first_or_blank(r'(?s)\n[^\n]+$', document_text)
        # Backward compat:
        # delete: 1. last as is, 2. stripped included
        document_text_clean = document_text.replace(timestamp_info, '').replace(timestamp_info.strip(), '')
        checksum = pdf_funcs.calc_checksum(bytes(document_text_clean, 'utf-8'))
        return checksum

    def download_receipts(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            movements_scraped: List[MovementScraped],
            movements_parsed: List[MovementParsed],
            resp_mov_filtered: Response,
            caja_param: str) -> Tuple[bool, List[MovementScraped]]:
        """Redefines download_receipts method to provide real results

        If correspondence downloading is active for the client, then
        receiptchecksum field is used to avoid duplicated files downloading.
        """

        save_checksum = self.basic_should_download_correspondence_for_access()

        return self.basic_download_receipts_common(
            s,
            account_scraped,
            movements_scraped,
            movements_parsed,
            meta={
                'save_checksum': save_checksum,
                'resp_mov_filtered': resp_mov_filtered,
                'caja_param': caja_param,
            }
        )

    def download_movement_receipt(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            movement_scraped: MovementScraped,
            movement_parsed: MovementParsed,
            meta: dict) -> str:

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        save_checksum = meta['save_checksum']  # type: bool
        resp_movs_filtered = meta['resp_mov_filtered']  # type: Response
        caja_param = meta['caja_param']  # type: str

        mov_str = "'{}'@{}".format(movement_parsed['description'], movement_parsed['operation_date'])
        if not movement_parsed['has_receipt']:
            return ''

        self.logger.info('{}: {}: download receipt'.format(fin_ent_account_id, mov_str))
        try:
            llamada_param = parse_helpers.get_llamada_param(resp_movs_filtered.text)
            # '2048099385'
            cliente_param = parse_helpers.get_cliente_param(resp_movs_filtered.text)
            # '0121780000763400008898'
            gcuenta_param = extract.form_param(resp_movs_filtered.text, 'GCUENTA')

            camino_param = '5485'  # hardcoded to get correct resp_filter_form

            # Step 1
            req_pre_pdf_url = 'https://bancaadistancia.liberbank.es/BEWeb/{}/{}/vrsnot6578_d_CMO_COMUN.action'.format(
                caja_param,
                camino_param
            )

            # Calc dates
            mov_date = datetime.strptime(movement_parsed['operation_date'], '%d/%m/%Y')
            fecini_param = (mov_date - timedelta(days=1)).strftime('%d-%m-%Y')
            fecfin_param = (mov_date + timedelta(days=3)).strftime('%d-%m-%Y')

            req_pre_pdf_params = OrderedDict([
                ('LLAMADA', llamada_param),
                ('CLIENTE', cliente_param),
                ('IDIOMA', '01'),
                ('CAJA', caja_param),
                ('OPERAC', '6578'),  # '9692'?
                ('CTASEL', ''),
                ('CTAFOR', ''),
                ('GCUENTA', movement_parsed['gcuenta_param']),  # '0121780000763400008898'
                ('FECINI', fecini_param),  # '28-10-2020'
                ('FECFIN', fecfin_param),  # "01-11-2020"
                # '20482178763400008898'
                ('CUENTAENVIA', movement_parsed['cuentaenvia_param'] or account_scraped.AccountNo[-20:]),
                ('CADENABUSCAR', movement_parsed['cadenabuscar_param']),  # DB82EA2836618836
                ('SEGMENTO', 'HASH'),
                ('CONFECHAS', 'SI'),
                ('CUALMOSTRAR_6578', '0')
            ])

            # resp_pre_pdf may fail during concurrent scraping
            resp_pre_pdf = Response()
            for att in range(1, 4):
                resp_pre_pdf = s.post(
                    req_pre_pdf_url,
                    data=req_pre_pdf_params,
                    headers=self.req_headers,
                    proxies=self.req_proxies
                )
                if 'muestrapdf' in resp_pre_pdf.text:
                    break
                self.logger.warning("{}: {}: wrong resp_pre_pdf. Retry #{}".format(
                    fin_ent_account_id,
                    mov_str,
                    att
                ))
                time.sleep(1 + random.random())
            else:
                self.basic_log_wrong_layout(
                    resp_pre_pdf,
                    "{}: {}: can't download receipt PDF. Wrong resp_pre_pdf".format(
                        fin_ent_account_id,
                        mov_str
                    )
                )
                return ''

            req_pdf_link, req_pdf_params = extract.build_req_params_from_form_html_patched(
                resp_pre_pdf.text,
                'muestrapdf',
                is_ordered=True
            )

            # Expect
            # LLAMADA=E3D1F2H0R1C0A0A1R0F2
            # CLIENTE=2048099385
            # IDIOMA=01
            # CAJA=2048
            # OPERAC=6578
            # CTASEL
            # CTAFOR
            # GCUENTA=20480121780000763400008898
            # FECHA=05-11-2020
            # CUENTA=20482178763400008898
            # DESDE_REGISTRO=3671752
            # HASTA_REGISTRO=3671752
            # FORMATO_INICIAL=0021
            req_pdf_extra_params = req_helpers.receipt_extra_req_params_from_pre_receipt(resp_pre_pdf.text)
            req_pdf_params.update(req_pdf_extra_params)

            # resp_receipt_pdf may fail during concurrent scraping
            resp_receipt_pdf = Response()
            for att in range(1, 4):
                resp_receipt_pdf = s.post(
                    urljoin(resp_pre_pdf.url, req_pdf_link),
                    data=req_pdf_params,
                    headers=self.req_headers,
                    proxies=self.req_proxies,
                )
                receipt_pdf_content = resp_receipt_pdf.content
                if receipt_pdf_content and not receipt_pdf_content.startswith(b'<!DOCTYPE'):
                    break
                if not receipt_pdf_content:
                    self.logger.warning("{}: {}: empty receipt_pdf_content. Retry #{}".format(
                            fin_ent_account_id,
                            mov_str,
                            att
                        ))
                if receipt_pdf_content.startswith(b'<!DOCTYPE'):
                    self.logger.warning("{}: {}: wrong resp_receipt_pdf: not a PDF. Retry #{}".format(
                        fin_ent_account_id,
                        mov_str,
                        att
                    ))
                time.sleep(1 + random.random())
            else:
                self.basic_log_wrong_layout(
                    resp_pre_pdf,
                    "{}: {}: can't download receipt PDF. Wrong resp_receipt_pdf".format(
                        fin_ent_account_id,
                        mov_str
                    )
                )
                return ''

            receipt_parsed_text = pdf_funcs.get_text(receipt_pdf_content)
            receipt_checksum = self._receipt_checksum(receipt_parsed_text)

            ok, _, _ = self.basic_save_receipt_pdf_as_correspondence(
                account_scraped,
                movement_scraped,
                receipt_pdf_content,
                pdf_parsed_text=receipt_parsed_text,
                account_to_fin_ent_fn=self._product_to_fin_ent_id_suffix,
                checksum=receipt_checksum
            )

            return receipt_parsed_text
        except:
            self.logger.error("{}: {}: can't download receipt PDF: HANDLED EXCEPTION\n{}".format(
                account_scraped.FinancialEntityAccountId,
                movement_parsed['operation_date'],
                traceback.format_exc()
            ))

            return ''

    def _get_correspondences(
            self,
            s: MySession,
            resp_prev: Response,
            organization_title: str,
            date_from_str: str,
            date_to_str: str,
            caja_param: str,
            camino_param: str) -> List[CorrespondenceDocParsed]:

        camino_param = '5485'  # hardcoded to get correct resp_filter_form

        req_filter_form_url = 'https://bancaadistancia.liberbank.es/BEWeb/{}/{}/psFASTm_COMUN.action'.format(
            caja_param,
            camino_param,
        )

        llamada_param = parse_helpers.get_llamada_param(resp_prev.text)
        # '2048099385'
        cliente_param = parse_helpers.get_cliente_param(resp_prev.text)

        req_filter_form_params = OrderedDict([
            ('OPERACION', 'psFASTm_COMUN'),
            ('IDIOMA', '01'),
            ('OPERAC', '1004'),
            ('LLAMADA', llamada_param),
            ('CLIENTE', cliente_param),
            ('CAJA', caja_param),
            ('CAMINO', camino_param)
        ])

        resp_filter_form = s.get(
            req_filter_form_url,
            params=req_filter_form_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # params already with LLAMADA, CLIENTE
        req_corresp_filtered_link, req_corresp_filtered_params = extract.build_req_params_from_form_html_patched(
            resp_filter_form.text,
            form_name='Cliente'
        )
        date_from_param = date_from_str.replace('/', '-')  # 01-04-2020
        date_to_param = date_to_str.replace('/', '-')
        req_corresp_filtered_params['FECINI'] = date_from_param
        req_corresp_filtered_params['FECFIN'] = date_to_param
        req_corresp_filtered_params['select_fecha_desde'] = date_from_param
        req_corresp_filtered_params['select_fecha_hasta'] = date_to_param

        correspondence_account_options = parse_helpers_receipts.get_correspondence_account_options(
            resp_filter_form.text
        )  # type: List[CorrespondenceAccountOption]

        corr_parsed_desc = []  # type: List[CorrespondenceDocParsed]
        for acc_option in correspondence_account_options:
            # Expected:
            # req_corresp_filtered_params['CUENTAENVIA'] = '20482178763400008898' # iban[4:]
            # req_corresp_filtered_params['IBANORIGEN'] = 'IBAN ES70 2048 2178 7634 0000 8898 - CUENTA CORRIENTE'
            # req_corresp_filtered_params['GCUENTA'] = '0121780000763400008898'

            req_corresp_filtered_params['CUENTAENVIA'] = acc_option.cuentaenvia_param
            req_corresp_filtered_params['IBANORIGEN'] = acc_option.ibanorigen_param
            req_corresp_filtered_params['GCUENTA'] = acc_option.gcuenta_param

            req_corresp_filtered_params['tp_cta'] = 'tp_cta4'

            resp_corresp_filtered = s.post(
                urljoin(resp_filter_form.url, 'not6578_d_FST.action'),
                data=req_corresp_filtered_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            self.logger.info(
                '{}: get correspondence from list for account {}'.format(organization_title, acc_option.account_no))

            corr_parsed_desc_for_acc = parse_helpers_receipts.get_correspondence_from_list(
                self.logger,
                resp_corresp_filtered.text,
                acc_option.account_no
            )  # type: List[CorrespondenceDocParsed]
            corr_parsed_desc.extend(corr_parsed_desc_for_acc)

        corr_parsed_asc = corr_parsed_desc[::-1]
        return corr_parsed_asc

    def _download_correspondence_pdf(
            self,
            s: MySession,
            corr: CorrespondenceDocParsed) -> Tuple[bool, MySession, bytes]:

        req_base_url = 'https://bancaadistancia.liberbank.es/'

        resp_pdf = s.get(
            urljoin(req_base_url, corr.extra['req_link']),
            headers=self.req_headers,
            proxies=self.req_proxies,
            stream=True
        )

        resp_pdf_content = resp_pdf.content
        if not resp_pdf_content:
            self.basic_log_wrong_layout(resp_pdf, "{}: can't download PDF (empty content)".format(corr))
            return False, s, b''

        return True, s, resp_pdf_content

    def download_correspondence(
            self,
            s: MySession,
            resp_prev: Response,
            organization_title: str,
            caja_param: str,
            camino_param: str) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Implements the documents downloading from corr mailbox.
        It gets the pdf files, saves them to the "receipts folder"
        and inserts the documents data in _TesoraliaDocuments table.

        Redefines download_documents method to provide real results
        """

        if not self.basic_should_download_correspondence():
            return False, []

        organization = self.basic_get_organization(organization_title)

        if not organization:
            self.logger.error("download_correspondence: no organization_saved with title '{}'. "
                              "Can't continue. Abort".format(organization_title))
            return False, []

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=85  # 3 months with padding
        )

        self.logger.info("{}: download correspondence from {} to {}".format(
            organization.Name,
            date_from_str,
            self.date_to_str
        ))

        corrs_parsed = self._get_correspondences(
            s,
            resp_prev,
            organization_title,
            date_from_str,
            self.date_to_str,
            caja_param,
            camino_param
        )  # type: List[CorrespondenceDocParsed]

        self.logger.info('{}: got {} correspondence docs for accounts: {}'.format(
            organization.Name,
            len(corrs_parsed),
            sorted(list({acc.account_no for acc in corrs_parsed}))
        ))

        corrs_scraped = []  # type: List[CorrespondenceDocScraped]

        for i, corr_parsed in enumerate(corrs_parsed):

            fin_ent_account_id_suffix = self._product_to_fin_ent_id_suffix(corr_parsed.account_no)
            # TODO check with suffix
            if not self.basic_should_download_correspondence_for_account(fin_ent_account_id_suffix):
                continue

            try:
                ok, s, doc_pdf_content = self._download_correspondence_pdf(s, corr_parsed)
                if not ok:
                    self.logger.error("{}: {}: can't download correspondence PDF. Skip".format(
                        organization_title,
                        corr_parsed,
                    ))
                    continue

                document_text = pdf_funcs.get_text(doc_pdf_content)
                product_id = corr_parsed.account_no  # 'ES7020482178763400008898'

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
                    Checksum=self._receipt_checksum(document_text),
                    AccountId=None,  # Account DB Id
                    StatementId=None,
                    Amount=corr_parsed.amount,
                    Currency=corr_parsed.currency,
                )

                corr_scraped_upd, should_add = self.basic_check_correspondence_doc_to_add(
                    corr_parsed,
                    corr_scraped,
                    product_to_fin_ent_fn=self._product_to_fin_ent_id_suffix
                )

                if should_add:
                    corrs_scraped.append(corr_scraped_upd)
                    self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)

            except:
                self.logger.error("{}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                    corr_parsed,
                    traceback.format_exc()
                ))

        return True, corrs_scraped
