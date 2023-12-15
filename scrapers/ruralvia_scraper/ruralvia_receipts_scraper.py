import random
import re
import time
import traceback
from collections import OrderedDict
from typing import List, Tuple, Optional, Dict
from urllib.parse import urljoin

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession, Response
from project.custom_types import (
    CorrespondenceDocScraped, DBOrganization,
    CorrespondenceDocParsed, ScraperParamsCommon, PDF_UNKNOWN_ACCOUNT_NO, AccountScraped, MovementScraped,
    MovementParsed
)
from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS, DEFAULT_PROXIES, SCRAPER_DATE_FMT
from . import parse_helpers_receipts
from .ruralvia_scraper import RuralviaScraper

__version__ = '2.5.0'
__changelog__ = """
2.5.0 2023.06.14
added PDF download from movement
download_movement_receipt:
download_receipts:
2.4.0
N_COMPANY_PROCESSING_WORKERS set to 1 to avoid concurrent contracts processing
2.3.0
set empty 'ProductId' as PDF_UNKNOWN_ACCOUNT_NO
2.2.0
download_correspondence: per day filter on request to avoid pagination error in bank
2.1.0
use basic_should_download_correspondence_for_account
upd log msg 
2.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
1.1.0
N_COMPANY_PROCESSING_WORKERS = 2 (decreased for better stability)
fixed scraper name
1.0.0
init
"""

RESP_ERR_MARKERS = [
    'En estos momentos no es posible realizar la opera',
    'Error de la aplicaci'
]

CORRS_PER_PAGE = 100  # 25 by default


class RuralviaReceiptsScraper(RuralviaScraper):
    N_COMPANY_PROCESSING_WORKERS = 1  # for better stability

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=DEFAULT_PROXIES,
                 scraper_name='RuralviaReceiptsScraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)

    def _sleep(self):
        time.sleep(0.1 + random.random() * 0.1)


    def _product_to_fin_ent_id(self, product_id: str) -> str:
        return product_id

    def _mov_str(self, movement_scraped: MovementScraped):
        return "{} ({}/{})".format(movement_scraped.KeyValue[:6],
                                   movement_scraped.Amount,
                                   movement_scraped.OperationalDate)

    def download_receipts(
            self, s: MySession,
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

    def _get_download_pdf_url(self, pdf_link) -> str:
        url = urljoin(self.domain, pdf_link)
        return url

    def _document_checksum(self, document_text: str, doc_id: Optional[str] = '') -> str:
        # Drop all lines with changing technical info
        # 'EXT0EXA1A01' -> '~EXT~0EXA1A01~'
        #doc_id = corr_parsed.extra['pdf_params']['codigoFormulario']
        #doc_mark = '~{}~{}~'.format(doc_id[:3], doc_id[3:])
        # drop lines with doc mark
        #doc_text_for_checksum = re.sub('.*{}.*'.format(doc_mark), '', document_text)
        # also, tech line by pattern
        # '3060 09320 A002 01   0012968 01/01 20201015 OO F-HOA-1A 00'
        doc_text_for_checksum = re.sub(
            r'\d{4} \d{5} \w\d{3} \d{2}\s{3}\d{7} \d{2}/\d{2} \d{8} [A-Z]{2} [A-Z]-[A-Z]{3}-\d\w \d{2}',
            '',
            document_text
        )
        # '3060~01~N~MAIMULTIC01~   ~20' - only for 'MAILING MULTICANAL' doc type, drop 1st line
        doc_text_for_checksum = re.sub(
            r'^.*~MAIMULTIC.*', '', doc_text_for_checksum
        )

        checksum = pdf_funcs.calc_checksum(bytes(doc_text_for_checksum, 'utf-8'))
        return checksum

    def download_movement_receipt(self,
                                  s: MySession,
                                  account_scraped: AccountScraped,
                                  movement_scraped: MovementScraped,
                                  movement_parsed: MovementParsed,
                                  meta: dict) -> str:
        """Saves receipt, updates DB and returns its text (description)"""

        if 'receipt_params' not in movement_parsed:
            return ''

        mov_receipt_params = movement_parsed['receipt_params']
        mov_str = self._mov_str(movement_scraped)

        self.logger.info('{}: download receipt for mov {}'.format(
            account_scraped.FinancialEntityAccountId,
            mov_str
        ))
        try:
            req_pdf_url = self._get_download_pdf_url(mov_receipt_params['action_url'])
            resp_pdf = s.post(
                req_pdf_url,
                headers=self.req_headers,
                proxies=self.req_proxies,
                data=mov_receipt_params['req_params']
            )

            # Expected PDF, but got HTML
            if b'PDF-' not in resp_pdf.content:
                self.logger.error(
                    "{}: {}: can't download pdf. resp_pdf is not a valid PDF. Skip. "
                    "RESPONSE\n{}".format(
                        account_scraped.FinancialEntityAccountId,
                        mov_str,
                        resp_pdf.text
                    )
                )
                return ''
            document_text = pdf_funcs.get_text(resp_pdf.content)

            ok, receipt_parsed_text, checksum = self.basic_save_receipt_pdf_as_correspondence(
                account_scraped,
                movement_scraped,
                resp_pdf.content,
                pdf_parsed_text=document_text,
                checksum=self._document_checksum(document_text),
                account_to_fin_ent_fn=self._product_to_fin_ent_id
            )

            return receipt_parsed_text

        except:
            self.logger.error("{}: {}: can't download pdf: EXCEPTION\n{}".format(
                account_scraped.FinancialEntityAccountId,
                mov_str,
                traceback.format_exc()
            ))
            return ''


    def _download_correspondence_pdf(
            self,
            s: MySession,
            corr_parsed: CorrespondenceDocParsed,
            resp_corrs: Response,
            page_form_link: str,
            page_form_params: Dict[str, str]) -> Tuple[MySession, bytes, str]:
        """:returns (session, resp_content, err)"""

        corr_ = corr_parsed._replace(extra={})  # for logging
        self.logger.info('{}: download PDF'.format(corr_))

        req_pdf_params = page_form_params.copy()
        req_pdf_params['clavePagina'] = 'BDP_BZVIRTUAL_DETALLE_DOCUMENTO'
        req_pdf_params.update(corr_parsed.extra['pdf_params'])

        resp_pdf = s.post(
            urljoin(resp_corrs.url, page_form_link),
            data=req_pdf_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=60,
        )
        resp_pdf_content = resp_pdf.content
        if not resp_pdf_content:
            return s, b'', "empty content"
        if not resp_pdf_content.startswith(b'%PDF'):
            err = 'not a PDF resp. RESPONSE:\n{}'.format(resp_pdf.text)
            return s, b'', err

        return s, resp_pdf_content, ''

    def download_correspondence(
            self,
            s: MySession,
            resp_company: Response,
            organization_title: str) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        if not self.basic_should_download_correspondence():
            return False, []

        organization = self.basic_get_organization(organization_title)  # type: Optional[DBOrganization]

        if not organization:
            self.logger.error("download_correspondence: no organization_saved with title '{}'. "
                              "Can't continue. Abort".format(organization_title))
            return False, []

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=360  # 1 yr with padding
        )

        self.logger.info("{}: download correspondence from {} to {}".format(
            organization.Name,
            date_from_str,
            self.date_to_str
        ))

        dates = date_funcs.get_date_range(date_from, self.date_to)
        corrs_with_content_desc = []  # type: List[Tuple[CorrespondenceDocParsed, bytes]]
        for single_date in dates:
            single_date_str = single_date.strftime(SCRAPER_DATE_FMT)
            self.logger.info("{}: download correspondence for {}".format(
                organization.Name,
                single_date_str
            ))
            day_corrs_with_content = 0

            req_corr_filter_form_url = parse_helpers_receipts.get_correspondence_menu_url(
                resp_company.text,
                resp_company.url
            )

            self._sleep()
            resp_corr_filter_form = s.get(
                req_corr_filter_form_url,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            req_corr_filtered_all_accs_param = parse_helpers_receipts.get_corr_all_accounts_param(
                resp_corr_filter_form.text
            )

            req_corr_filtered_link, _ = extract.build_req_params_from_form_html_patched(
                resp_corr_filter_form.text,
                'FORM_RVIA_0'
            )
            validation_token = extract.re_first_or_blank('<div data-token="(.*?)" id="tokenValid">', resp_corr_filter_form.text)
            req_corr_filtered_params = OrderedDict([
                ('ISUM_OLD_METHOD', 'POST'),
                ('ISUM_ISFORM', 'true'),
                ('TIPO', '0'),
                ('SELCTA', '0'),
                ('listaSituaciones', '*'),
                ('listaCategorias', '0'),
                ('fechaDesde', single_date.strftime('%d-%m-%Y')),  # 01-09-2020
                ('fechaHasta', single_date.strftime('%d-%m-%Y')),
                ('clavePagina', 'BDP_BZVIRTUAL_LISTA'),
                ('cuenta', ''),
                ('cuentaSeleccionada', '0'),
                # '30603001212070456427|30603001242317022925|30603001222279261925|'
                ('listaCuentas', req_corr_filtered_all_accs_param),
                ('sVisualizado', ''),
                ('categoria', '0'),
                ('primeraVez', '1'),
                ('paginaActual', '0'),
                ('tamanioPagina', CORRS_PER_PAGE),  # 25 by default, 100 - OK
                ('campoPaginacion', 'ListaCorrespondencia'),
                ('validationToken', validation_token)

            ])

            self._sleep()
            resp_corr_filtered = Response()
            # Several attempts
            for i in range(3):
                resp_corr_filtered = s.post(
                    urljoin(resp_corr_filter_form.url, req_corr_filtered_link),
                    data=req_corr_filtered_params,
                    headers=self.basic_req_headers_updated({
                        'Referer': resp_corr_filter_form.url
                    }),
                    proxies=self.req_proxies
                )
                if not any(m in resp_corr_filtered.text for m in RESP_ERR_MARKERS):
                    break
                self.logger.warning("{}: can't open correct resp_corr_filtered. Retry".format(
                    organization_title
                ))
                time.sleep(2 * i + random.random())
            else:
                self.logger.error(
                    "{}: can't open correct resp_corr_filtered after several attempts. Abort. "
                    "RESPONSE: \n{}".format(organization_title, resp_corr_filtered.text)
                )
                return False, []

            resp_corr_i = resp_corr_filtered
            for page_ix in range(0, 30):  # 30*100=3000 docs
                # Page #1 has page_ix=0
                self.logger.info('{}: get correspondence from page #{}'.format(organization_title, page_ix + 1))

                corrs_parsed_desc_i = parse_helpers_receipts.get_correspondence_from_list(resp_corr_i.text)

                self.logger.info('{}: page #{}: got {} correspondence docs for accounts: {}'.format(
                    organization.Name,
                    page_ix + 1,
                    len(corrs_parsed_desc_i),
                    sorted(list({acc.account_no for acc in corrs_parsed_desc_i}))
                ))

                # Need to get it here to use for doc downloading,
                # bcs many params are the same.
                # page_form_link and page_form_params are used for different reqs (for pdfs an pagination)
                page_form_link, page_form_params = \
                    parse_helpers_receipts.get_corr_page_form_link_and_req_params(
                        resp_corr_i.text,
                        CORRS_PER_PAGE
                    )

                # Download docs from the page (just when the page in open)
                for i, corr_parsed in enumerate(corrs_parsed_desc_i):

                    fin_ent_account_id = corr_parsed.account_no  # same
                    if not self.basic_should_download_correspondence_for_account(fin_ent_account_id):
                        continue

                    try:
                        self._sleep()
                        s, doc_pdf_content, err = self._download_correspondence_pdf(
                            s,
                            corr_parsed,
                            resp_corr_i,
                            page_form_link,
                            page_form_params
                        )
                        if err:
                            self.logger.error("{}: {}: can't download correspondence PDF. Skip. ERR: {}".format(
                                organization_title,
                                corr_parsed,
                                err
                            ))
                            continue

                        corrs_with_content_desc.append((corr_parsed, doc_pdf_content))
                        day_corrs_with_content += 1
                    except Exception as _e:
                        self.logger.error("{}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                            corr_parsed,
                            traceback.format_exc()
                        ))
                # / end of for i, corr in enumerate(corrs_desc_i)
                self.logger.info('{}: day scraped correspondence: {} total {} docs'.format(
                    organization_title,
                    single_date_str,
                    day_corrs_with_content
                ))

                next_page_ix = page_ix + 1
                has_next_page = bool(parse_helpers_receipts.check_corr_pagination_next_page(
                    resp_corr_i.text,
                    next_page_ix,
                ))
                if not has_next_page:
                    self.logger.info('{}: no more correspondence pages'.format(organization_title))
                    break

                self.logger.info('{}: open correspondence page {}'.format(organization_title, next_page_ix))
                resp_prev = resp_corr_i
                page_form_params['paginaActual'] = str(next_page_ix)
                page_form_params['pagXpag'] = '5'
                # Drop unwanted keys
                page_form_params_clean = OrderedDict([])
                for k, v in page_form_params.items():
                    if 'seleccion' not in k and k != 'checkCabecera':
                        page_form_params_clean[k] = v

                self._sleep()
                for i in range(3):
                    resp_corr_i = s.post(
                        urljoin(resp_prev.url, page_form_link),
                        data=page_form_params_clean,
                        headers=self.basic_req_headers_updated({
                            'Referer': resp_prev.url
                        }),
                        proxies=self.req_proxies
                    )
                    if not any(m in resp_corr_i.text for m in RESP_ERR_MARKERS):
                        break
                    self.logger.warning("{}: can't open correct resp_corr_i for next_page_ix={}. Retry".format(
                        organization_title,
                        next_page_ix
                    ))
                    time.sleep(2 * i + random.random())
                else:
                    self.logger.error(
                        "{}: can't open correct resp_corr_i for next_page_ix={} after several attempts. "
                        "Abort pagination. RESPONSE: \n{}".format(
                            organization_title,
                            next_page_ix,
                            resp_corr_filtered.text
                        )
                    )
                    break  # abort 'for page_ix in ...'
                continue
            # / end of for page_ix in ...

        self.logger.info('{}: insert scraped correspondence: total {} docs'.format(
            organization_title,
            len(corrs_with_content_desc)
        ))

        # Insert all docs in ASC order
        corrs_with_contents_asc = list(reversed(corrs_with_content_desc))
        for corr_parsed, doc_pdf_content in corrs_with_contents_asc:
            document_text = pdf_funcs.get_text(doc_pdf_content)
            # When there is no account associated to the PDF, set 'product_id' as PDF_UNKNOWN_ACCOUNT_NO
            product_id = corr_parsed.account_no if corr_parsed.account_no != '' else PDF_UNKNOWN_ACCOUNT_NO
            doc_id = corr_parsed.extra['pdf_params']['codigoFormulario']

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
                Checksum=self._document_checksum(document_text, doc_id),
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
                # documents_scraped.append(corr_scraped_upd)  # not used
                self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)

        return True, []
