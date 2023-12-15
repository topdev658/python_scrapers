import threading
import traceback
import urllib.parse
from collections import OrderedDict
from datetime import datetime
from typing import List, Optional, Tuple, Set

from custom_libs import extract
from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession
from project import settings as project_settings
from project.custom_types import (
    AccountScraped, MovementParsed, MovementScraped,
    ScraperParamsCommon, CorrespondenceDocScraped, DBOrganization, CorrespondenceDocParsed, INVALID_PDF_MARKER
)
from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
from scrapers.bankinter_scraper.bankinter_scraper import BankinterScraper
from . import parse_helpers_receipts
from .custom_types import ReceiptOption, ReceiptReqParams, AccountForCorrespondence

__version__ = '4.9.0'

__changelog__ = """
4.9.0 2023.06.23
download_movement_receipt: replaced currency on FinancialAccountId to validate check and download receipts
_download_correspondence_pdf: fixed check 'can't download PDF' with INVALID_PDF_MARKER
4.8.0 2023.05.23
download_movement_receipt: added log when the movement_parsed has not receipt to download
4.7.0
download_movement_receipt: check possible 'unhandled_receipt_params'
4.6.0
removed call to basic_save_receipt_pdf_and_update_db 
(only basic_save_receipt_pdf_as_correspondence is needed now) 
4.5.0
check for ok after basic_save_receipt_pdf_as_correspondence
4.4.0
_product_to_fin_ent_id: handle different formats of product_id
4.3.1 (temp)
CONCURRENT_PDF_SCRAPING_EXECUTORS = 1 to exclude possible duplicates for correspondence
4.3.0
save receipt metadata with checksum
4.2.0
save receipt as correspondence
_product_to_fin_ent_id
4.1.0
use basic_should_download_correspondence_for_account
4.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
3.2.0
correspondence: currency field support
3.1.0
use project-level corr offset
3.0.0
correspondence downloading
2.1.2
upd type hints, MySession
2.1.1
error -> warning if can't download receipt due to detected reason
2.1.0
_handle_various_receipts_selection
_get_download_pdf_url: use ReceiptReqParams
parse_helpers: movement_parsed['receipt_params'] now has type ReceiptReqParams
handle ambiguous receipts
2.0.0
download_receipts: use basic_download_receipts_common
download_movement_receipt: use new basic_save_receipt_pdf_and_update_db
1.2.0
download_receipts: changed return types to provide compat with BasicScraper
1.1.0
CONCURRENT_PDF_SCRAPING_EXECUTORS as const
download_receipts: movements_scraped[i].KeyValue
download_movement_receipt: return True/False (useful for futures)
_get_download_pdf_url: removed redundant transformations, upd
1.0.1
reformatted
1.0.0
init
"""

USER_AGENT = ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.22 '
              '(KHTML, like Gecko) Chrome/25.0.1364.97 Safari/537.22')


class BankinterReceiptsScraper(BankinterScraper):
    # DAF: downloading 200 PDFs from one account,
    # with CONCURRENT_PDF_SCRAPING_EXECUTORS=0 (no concurrence) lasts 124 sec
    # with CONCURRENT_PDF_SCRAPING_EXECUTORS=4 lasts 54 sec (too hard)
    CONCURRENT_PDF_SCRAPING_EXECUTORS = 1

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BankinterReceiptsScraper') -> None:

        super().__init__(scraper_params_common, proxies, scraper_name)
        self.receipts_lock = threading.Lock()

        # Special set to notify only one time for a set of ambiguous_receipts.
        # Example: -u 198549 -a 6918, acc ES8801287712680500001871, 06/06/19
        #  - all receipts for movements with amount 37,56 D
        #  have description "LIQUIDACION DE AVAL".
        # key is fin_ent_account_id__descr_part
        self.ambiguous_receipts = set()  # type: Set[str]

    def _add_to_ambiguous_receipts(self, ambiguous_receipt_key: str) -> None:
        with self.receipts_lock:
            self.ambiguous_receipts.add(ambiguous_receipt_key)

    def _is_in_ambiguous_receipts(self, ambiguous_receipt_key: str) -> bool:
        with self.receipts_lock:
            return ambiguous_receipt_key in self.ambiguous_receipts

    def _mov_str(self, movement_scraped: MovementScraped):
        return "{} ({}/{})".format(movement_scraped.KeyValue[:6],
                                   movement_scraped.Amount,
                                   movement_scraped.OperationalDate)

    def _product_to_fin_ent_id(self, product_id: str) -> str:
        """
        Doc from receipt area usually has product_id like IBAN,
           but doc from correspondence area usually has product id like FinEntAccountId
        So:
           ES2201287712690510000412 -> 01287712510000412
           01287712510000412 -> 01287712510000412
        """
        fin_ent_account_id = product_id
        if len(product_id) == 24:
            fin_ent_account_id = '{}{}'.format(product_id[4:12], product_id[-9:])
        return fin_ent_account_id

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

    def _get_download_pdf_url(self, req_params: ReceiptReqParams) -> str:
        # 'https://empresas.bankinter.com/www/es-es/cgi/empresas+cuentas+vis_pdf
        # ?semana=50&persona=null
        # &envio=1548091&cuenta=01287712500001871&fecha=20181213&fecha_valor=20181213
        # &num_pag=006&ind_csf=1&ind_anyo=A'
        url = (
            'https://empresas.bankinter.com/'
            'www/es-es/cgi/empresas+cuentas+vis_pdf?'
            'semana={semana}&persona=null&envio={envio}&cuenta={cuenta}&fecha={fecha}'
            '&fecha_valor={fecha_valor}&num_pag=006&ind_csf=1&ind_anyo=A'.format(
                **req_params._asdict()
            )
        )

        return url

    def _handle_various_receipts_selection(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            movement_scraped: MovementScraped,
            movement_parsed: MovementParsed) -> Tuple[bool, ReceiptReqParams]:
        """Handles case:
        Some movements return pages with receipt selection if there are
        several movements w/ the same amount during one day
        -u 198549 -a 6921 acc ES9101287712680100000395, 20190605
        :returns  (is_success, ReceiptReqParams)
        """

        mov_receipt_params = movement_parsed['receipt_params']  # type: ReceiptReqParams
        mov_str = self._mov_str(movement_scraped)

        req_various_url = ('https://empresas.bankinter.com/www/es-es/cgi/'
                           'empresas+cuentas+varios_documentos')

        req_various_params = {
            'cuenta': account_scraped.FinancialEntityAccountId,  # 01287712100000395
            'aplicacion': mov_receipt_params.semana,  # 'A04'
            'formulario': mov_receipt_params.envio,  # 'F008'
            'importe': abs(movement_scraped.Amount),  # 1020.00, only abs val
            'fecha_contable': movement_scraped.OperationalDate,  # '20190605'
            'fecha_valor': movement_scraped.ValueDate  # '20190605'

        }

        resp_receipts_selection = s.post(
            req_various_url,
            data=req_various_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        receipts_options = parse_helpers_receipts.get_receipts_options(
            resp_receipts_selection.text
        )

        receipt_option = None  # type: Optional[ReceiptOption]
        for ro in receipts_options:
            # Looking for
            # `AB 2015, S.L.`  in  `OTRAS EN /AB 2015, S.L.`
            # `Renovables Rotonda,`  in  `/Renovables Rotonda, S.L`
            # That means receipt_option.descr_part
            #  is always a part of correct movement_scraped.StatementDescription
            if ro.descr_part in movement_scraped.StatementDescription:
                if receipt_option is None:
                    receipt_option = ro
                    # Do not interrupt the loop to be sure
                    # that this is unique receipt_option with such appropriate
                    # descr_part for the movement
                else:
                    # Handle ambiguous receipts - skip downloading with
                    # one time err notification.
                    # Example: -u 198549 -a 6918, acc ES8801287712680500001871, 06/06/19
                    ambiguous_receipt_key = '{}__{}'.format(
                        account_scraped.FinancialEntityAccountId,
                        ro.descr_part
                    )
                    if self._is_in_ambiguous_receipts(ambiguous_receipt_key):
                        self.logger.info(
                            "{}: {}: previously detected ambiguous receipt. "
                            "Skip without additional err notification".format(
                                account_scraped.FinancialEntityAccountId,
                                mov_str
                            )
                        )
                        return False, mov_receipt_params

                    # First-time ambiguous receipt detected
                    self._add_to_ambiguous_receipts(ambiguous_receipt_key)
                    self.logger.warning(
                        "{}: {}: "
                        "bank-level ambiguity: found several receipt links with the same descr_part `{}` "
                        "at the receipt selection page. "
                        "SKIP receipt downloading.".format(
                            account_scraped.FinancialEntityAccountId,
                            mov_str,
                            ro.descr_part
                        )
                    )
                    return False, mov_receipt_params

        if not receipt_option:
            self.logger.warning(
                "{}: {}: can't find a specific receipt for descr `{}`. Skip. "
                "RESPONSE TEXT:\n{}".format(
                    account_scraped.FinancialEntityAccountId,
                    mov_str,
                    movement_scraped.StatementDescription,
                    extract.text_wo_scripts_and_tags(resp_receipts_selection.text)
                )
            )
            return False, mov_receipt_params

        mov_receipt_params_correct = receipt_option.req_params  # type: ReceiptReqParams
        self.logger.info(
            "{}: {}: got correct mov_receipt_params".format(
                account_scraped.FinancialEntityAccountId,
                mov_str,
            )
        )
        return True, mov_receipt_params_correct

    def download_movement_receipt(self,
                                  s: MySession,
                                  account_scraped: AccountScraped,
                                  movement_scraped: MovementScraped,
                                  movement_parsed: MovementParsed,
                                  meta: dict) -> str:
        """Saves receipt, updates DB and returns its text (description)"""

        if not movement_parsed['may_have_receipt']:
            self.logger.info('{}: the movement has not receipt to download: date {}, pos #{}, amount {}. Skip'.format(
                account_scraped.FinancialEntityAccountId,
                movement_scraped.OperationalDate,
                movement_scraped.OperationalDatePosition,
                movement_scraped.Amount
            ))
            return ''

        # Log possible 'unhandled_receipt_params'
        if 'unhandled_receipt_params' in movement_parsed:
            self.logger.warning(
                'Unhandled receipt_params html response -> {}'.format(movement_parsed['unhandled_receipt_params']))

        mov_receipt_params = movement_parsed['receipt_params']  # type: ReceiptReqParams
        mov_str = self._mov_str(movement_scraped)

        self.logger.info('{}: download receipt for mov {}'.format(
            account_scraped.FinancialEntityAccountId,
            mov_str
        ))
        try:
            fin_entity_account_id_wo_currency = str(account_scraped.FinancialEntityAccountId)\
                .replace('EUR', '').replace('USD', '')
            if mov_receipt_params.cuenta != fin_entity_account_id_wo_currency:
                self.logger.info(
                    "{}: {}: various receipts selection page detected. Processing".format(
                        account_scraped.FinancialEntityAccountId,
                        mov_str
                    )
                )

                ok, mov_receipt_params = self._handle_various_receipts_selection(
                    s,
                    account_scraped,
                    movement_scraped,
                    movement_parsed
                )

                if not ok:
                    # already logged
                    return ''

            req_pdf_url = self._get_download_pdf_url(mov_receipt_params)

            resp_pdf = s.get(
                req_pdf_url,
                headers=self.req_headers,
                proxies=self.req_proxies,
                stream=True
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

            ok, receipt_parsed_text, checksum = self.basic_save_receipt_pdf_as_correspondence(
                account_scraped,
                movement_scraped,
                resp_pdf.content,
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

    def download_correspondence(
            self,
            s: MySession,
            organization_title: str) -> Tuple[bool, List[CorrespondenceDocScraped]]:

        if not self.basic_should_download_correspondence():
            return False, []

        organization = self.basic_get_organization(organization_title)

        if not organization:
            self.logger.warning("download_correspondence: no organization_saved with title '{}'. "
                                "Can't continue. Skip organization".format(organization_title))
            return False, []

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=360  # 1 year with padding
        )

        self.logger.info("{}: download correspondence from {} to {}".format(
            organization.Name,
            date_from_str,
            self.date_to_str
        ))

        resp_corr_form = s.get(
            'https://empresas.bankinter.com/www/es-es/cgi/empresas+cuentas+extractos_docu_selcta',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_for_corr = parse_helpers_receipts.get_accounts_for_correspondence(
            resp_corr_form.text
        )  # type: List[AccountForCorrespondence]

        self.logger.info('{}: got {} accounts to download correspondence: {}'.format(
            organization.Name,
            len(accounts_for_corr),
            [acc.fin_ent_account_id for acc in accounts_for_corr]
        ))

        for acc in accounts_for_corr:
            # Only serial processing is possible
            # Need to download PDFs while filtered correspondence for the account
            self.download_account_correspondence(
                s,
                organization,
                acc,
                date_from,
                self.date_to,
            )
        return True, []  # results are not used

    def _download_correspondence_pdf(
            self,
            s: MySession,
            corr_parsed: CorrespondenceDocParsed) -> Tuple[bool, MySession, bytes]:
        # Full req_link leads to popup pdf container, let's get only query part
        req_pdf_query = urllib.parse.urlsplit(corr_parsed.extra['req_link']).query
        req_pdf_url = 'https://empresas.bankinter.com/www/es-es/cgi/empresas+cuentas+vis_pdf?{}'.format(
            req_pdf_query
        )
        resp_pdf = s.get(
            req_pdf_url,
            headers=self.req_headers,
            proxies=self.req_proxies,
            stream=True
        )
        pdf_content = resp_pdf.content
        if INVALID_PDF_MARKER in pdf_content:
            self.logger.error("{}: can't download PDF. Skip. RESPONSE:\v{}".format(
                corr_parsed,
                resp_pdf.text
            ))
            return False, s, pdf_content
        return True, s, pdf_content

    def download_account_correspondence(
            self,
            s: MySession,
            organization: DBOrganization,
            account_for_corr: AccountForCorrespondence,
            date_from: datetime,
            date_to: datetime) -> Tuple[bool, List[CorrespondenceDocScraped]]:

        fin_ent_account_id = account_for_corr.fin_ent_account_id

        if not self.basic_should_download_correspondence_for_account(fin_ent_account_id):
            return True, []

        df, mf, yf = date_from.strftime('%d/%m/%Y').split('/')
        dt, mt, yt = date_to.strftime('%d/%m/%Y').split('/')
        req_params = OrderedDict([
            ('tipo_documento', ''),
            ('tipo_documento_desc', ''),
            ('grupo_sel', 'CTA'),
            ('producto_sel', 'EYR'),
            ('paso_ejec', '3'),
            ('anio', ''),
            ('tipoCons', 'M'),
            ('dia_desde', df),
            ('mes_desde', mf),
            ('anyo_desde', yf),
            ('dia_hasta', dt),
            ('mes_hasta', mt),
            ('anyo_hasta', yt),
            ('CUENTA', account_for_corr.fin_ent_account_id),  # '01289426510002287'
            ('importeMayor', ''),
            ('importeMenor', ''),
            ('importeIgual', '')
        ])

        resp_corrs_filtered = s.post(
            'https://empresas.bankinter.com/www/es-es/cgi/empresas+cuentas+extractos_docu',
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        self.logger.info('{}: get correspondence from list for account {}'.format(
            organization.Name,
            account_for_corr.account_displayed
        ))

        # All correspondence documents at once, pagination is not required
        corrs_parsed_desc = parse_helpers_receipts.get_correspondence_from_list(
            resp_corrs_filtered.text,
            fin_ent_account_id
        )  # type: List[CorrespondenceDocParsed]

        corrs_parsed_asc = corrs_parsed_desc[::-1]

        corrs_scraped = []  # type: List[CorrespondenceDocScraped]
        for i, corr_parsed in enumerate(corrs_parsed_asc):
            try:
                ok, s, doc_pdf_content = self._download_correspondence_pdf(s, corr_parsed)
                if not ok:
                    self.logger.error("{}: {}: can't download correspondence PDF. Skip".format(
                        organization.Name,
                        corr_parsed,
                    ))
                    continue

                document_text = pdf_funcs.get_text(doc_pdf_content)

                corr_scraped = CorrespondenceDocScraped(
                    CustomerId=self.db_customer_id,
                    OrganizationId=organization.Id,
                    FinancialEntityId=self.db_financial_entity_id,
                    ProductId=corr_parsed.account_no,
                    ProductType='',
                    DocumentDate=corr_parsed.operation_date,
                    Description=corr_parsed.descr,
                    DocumentType=corr_parsed.type,
                    DocumentText=document_text,
                    # Need to use Checksum to compare with PDFs from receipts
                    Checksum=pdf_funcs.calc_checksum(bytes(document_text, 'utf-8')),
                    AccountId=None,  # Account DB Id
                    StatementId=None,
                    Amount=corr_parsed.amount,
                    Currency=corr_parsed.currency,
                )

                corr_scraped_upd, should_add = self.basic_check_correspondence_doc_to_add(
                    corr_parsed,
                    corr_scraped,
                    product_to_fin_ent_fn=self._product_to_fin_ent_id
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
