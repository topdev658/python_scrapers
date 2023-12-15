import re
import time
import traceback
from collections import OrderedDict
from typing import List, Tuple, Optional

from custom_libs import pdf_funcs, extract
from custom_libs.myrequests import MySession, Response
from project.custom_types import (
    CorrespondenceDocParsed, DBOrganization, PDF_UNKNOWN_ACCOUNT_NO,
    AccountScraped, MovementParsed, MovementScraped,
)
from project.custom_types import CorrespondenceDocScraped
from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS, SCRAPER_DATE_FMT
from . import parse_helpers_receipts, parse_helpers
from .unicaja_scraper import UnicajaScraper

__version__ = '1.3.0'

__changelog__ = """
1.3.0 2023.05.25
download_receipts and download_movement_receipt
_product_to_fin_ent_id: fixed to return product_id
1.2.0
process_correspondence_document: use PDF_UNKNOWN_ACCOUNT_NO as fin_ent_account_id
1.1.0
fixed duplicate PDFs:
    deleted line with datetime of issue
1.0.0
init
"""


def account_no_to_fin_ent_acc_id(account_no: str):
    """
    >>> account_no_to_fin_ent_acc_id('ES9221034749170034711977')
    'ES92 2103 4749 1700 3471 1977'
    """
    return ' '.join(account_no[i: i + 4] for i in range(0, len(account_no), 4))


class UnicajaReceiptsScraper(UnicajaScraper):

    def _product_to_fin_ent_id(self, product_id: str) -> str:
        return product_id

    def download_correspondence(
            self,
            s: MySession,
            csrf_token: str,
            org_title: str) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Implements the documents downloading from corr mailbox.
        It gets the pdf files, saves them to the "receipts folder"
        and inserts the documents data in _TesoraliaDocuments table.

        Redefines download_documents method to provide real results
        """

        if not self.basic_should_download_correspondence():
            return False, []

        self.logger.info('Download correspondence')
        self.process_contract_for_correspondence(s, csrf_token, org_title)
        return True, []  # no correspondence required in the main scraper

    def process_contract_for_correspondence(
            self,
            s: MySession,
            csrf_token: str,
            org_title: str) -> bool:
        organization = self.basic_get_organization(org_title)  # type: Optional[DBOrganization]
        if not organization:
            self.logger.error(
                "process_company_for_correspondence: no organization_saved with title '{}'. "
                "Can't continue. Abort".format(org_title)
            )
            return False
        organization_name = organization.Name

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=85  # 3 months w/ padding
        )

        self.logger.info("{}: download correspondence from {} to {}".format(
            organization_name,
            date_from_str,
            self.date_to_str
        ))

        req_corr_filtered_params = OrderedDict([
            ('tipoCorrespondencia', ''),
            ('papelera', 'N'),
            ('leido', ''),
            ('fechaDesde', date_from.strftime('%Y-%m-%d')),  # '2022-06-01'
            ('fechaHasta', self.date_to.strftime('%Y-%m-%d')),
            ('concepto', '')
        ])

        corrs_parsed_desc = []  # type: List[CorrespondenceDocParsed]
        for page_ix in range(1, 100):
            self.logger.info('{}: page #{}: get correspondence'.format(org_title, page_ix))
            resp_corresp_filtered_i = s.get(
                'https://univia.unicajabanco.es/services/rest/api/notificaciones/correspondencias',
                params=req_corr_filtered_params,
                headers=self.basic_req_headers_updated({
                    'tokenCSRF': csrf_token,
                }),
                proxies=self.req_proxies
            )
            ok, resp_corresp_filtered_i_json = self.basic_get_resp_json(
                resp_corresp_filtered_i,
                "{}: page #{}: can't get resp_corresp_filtered_i. Skip".format(org_title, page_ix)
            )
            if not ok:
                break  # already reported

            # 50 per page
            corrs_parsed_desc_i = parse_helpers_receipts.get_correspondence_from_list(
                resp_corresp_filtered_i_json
            )

            corrs_parsed_desc.extend(corrs_parsed_desc_i)

            has_next_page = resp_corresp_filtered_i_json.get('masDatos', '') == 'S'
            if not has_next_page:
                self.logger.warning('{}: no more pages with correspondence'.format(org_title))
                break
            # next page param
            req_corr_filtered_params['idComunicadoDesde'] = corrs_parsed_desc_i[-1].extra['pdf_param']
            ...

        self.logger.info('{}: got {} correspondence docs for accounts: {}'.format(
            organization.Name,
            len(corrs_parsed_desc),
            sorted(list({acc.account_no for acc in corrs_parsed_desc}))
        ))

        # Download in ASC
        for corr_parsed in reversed(corrs_parsed_desc):
            _ok, s = self.process_correspondence_document(
                s,
                csrf_token,
                organization,
                corr_parsed
            )

        return True

    def _download_correspondence_pdf(
            self,
            s: MySession,
            csrf_token: str,
            corr_parsed: CorrespondenceDocParsed) -> Tuple[bool, MySession, bytes]:

        corr_str = "Corr '{}...' ({}) @ {} of {}".format(
            corr_parsed.descr[:10],
            corr_parsed.amount,
            corr_parsed.operation_date.strftime(SCRAPER_DATE_FMT),
            corr_parsed.account_no
        )
        try:
            resp_maybe_pdf = Response()
            for i in range(1, 4):
                self.logger.info('{}: att #{}: download'.format(
                    corr_str,
                    i,
                ))
                resp_maybe_pdf = s.get(
                    'https://univia.unicajabanco.es/services/rest/api/notificaciones/'
                    'correspondencias/detalleCorrespondencia?idCorrespondencia={}'.format(
                        corr_parsed.extra['pdf_param']
                    ),
                    headers=self.basic_req_headers_updated({
                        'tokenCSRF': csrf_token,
                    }),
                    proxies=self.req_proxies
                )
                # Check: is it PDF or HTML resp
                if b'!DOCTYPE' in resp_maybe_pdf.content:
                    time.sleep(3)
                    continue
                break
            else:
                self.logger.error(
                    "{}: couldn't download correspondence PDF after several attempts".format(
                        corr_str
                    )
                )
                return False, s, b''

            pdf_content = resp_maybe_pdf.content
            return True, s, pdf_content

        except:
            self.logger.error("{}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                corr_str,
                traceback.format_exc()
            ))

        return False, s, b''

    def process_correspondence_document(
            self,
            s: MySession,
            csrf_token: str,
            organization: DBOrganization,
            corr_parsed: CorrespondenceDocParsed) -> Tuple[bool, MySession]:

        if corr_parsed.account_no != PDF_UNKNOWN_ACCOUNT_NO:
            fin_ent_account_id = account_no_to_fin_ent_acc_id(corr_parsed.account_no)
        else:
            fin_ent_account_id = corr_parsed.account_no
        if not self.basic_should_download_correspondence_for_account(fin_ent_account_id):
            return True, s

        self.logger.info('Process correspondence {}'.format(corr_parsed))
        ok, s, doc_pdf_content = self._download_correspondence_pdf(s, csrf_token, corr_parsed)
        if not ok:
            return False, s

        document_text = pdf_funcs.get_text(doc_pdf_content)
        product_id = corr_parsed.account_no  # 'ES7020482178763400008898' / 'Sin cuenta asociada'
        #The UNICAJA bank is generating each document with a datetime of issue, which generates a checksum for each downloaded document
        #This caused duplicates in DB and we have implemented a control to generate the checksum avoiding the datetime of issue
        document_text_lines = re.split('\d{2}-\d{2}-\d{4}.*\d{2}:\d{2}:\d{2}',document_text)
        if len(document_text_lines) == 2:
            document_text = document_text_lines[0]

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
            Checksum=pdf_funcs.calc_checksum(bytes(document_text, 'utf-8')),
            AccountId=None,  # Account DB Id
            StatementId=None,
            Amount=corr_parsed.amount,
            Currency=corr_parsed.currency,
        )

        corr_scraped_upd, should_save = self.basic_check_correspondence_doc_to_add(
            corr_parsed,
            corr_scraped,
            product_to_fin_ent_fn=account_no_to_fin_ent_acc_id
        )
        if should_save:
            self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)

        return True, s

    def download_receipts(
            self, s: MySession,
            token,
            account_scraped: AccountScraped,
            movements_scraped: List[MovementScraped],
            movements_parsed: List[MovementParsed]) -> Tuple[bool, List[MovementScraped]]:
        """Redefines stub method to provide real results"""

        self.token = token

        return self.basic_download_receipts_common(
            s,
            account_scraped,
            movements_scraped,
            movements_parsed
        )

    def download_movement_receipt(self,
                                  s: MySession,
                                  account_scraped: AccountScraped,
                                  movement_scraped: MovementScraped,
                                  movement_parsed: MovementParsed,
                                  meta: dict) -> str:
        """Saves receipt, updates DB and returns its text (description)"""

        mov_receipt_params = movement_parsed['receipt_params']  # type: ReceiptReqParams

        if mov_receipt_params['recibo'] == 'S':
            self.logger.info('{}: download receipt for mov {}'.format(
                account_scraped.FinancialEntityAccountId,
                mov_receipt_params['nummov']
            ))
            try:
                req_pdf_url = 'https://univia.unicajabanco.es/services/rest/api/cuentas/movimientos/recibomovimiento'

                pdf_req_params = {
                    'ppp': mov_receipt_params['ppp_param'],
                    'nummov': mov_receipt_params['nummov']
                }

                resp_pdf = s.post(
                    req_pdf_url,
                    headers=self.basic_req_headers_updated({
                        'tokenCSRF': self.token
                    }),
                    proxies=self.req_proxies,
                    data=pdf_req_params,
                    stream=True
                )

                if 'ses-caducada' in resp_pdf.text:
                    s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()
                    self.token = parse_helpers.get_csrf_token(resp_logged_in_json)
                    resp_pdf = s.post(
                        req_pdf_url,
                        headers=self.basic_req_headers_updated({
                            'tokenCSRF': self.token
                        }),
                        proxies=self.req_proxies,
                        data=pdf_req_params,
                        stream=True
                    )

                # Expected PDF, but got HTML
                if b'PDF-' not in resp_pdf.content:
                    self.logger.error(
                        "{}: {}: can't download pdf. resp_pdf is not a valid PDF. Skip. "
                        "RESPONSE\n{}".format(
                            account_scraped.FinancialEntityAccountId,
                            mov_receipt_params['nummov'],
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
                    mov_receipt_params['nummov'],
                    traceback.format_exc()
                ))
                return ''
        else:
            self.logger.info('{}: No receipt attached for mov {}'.format(
                account_scraped.FinancialEntityAccountId,
                mov_receipt_params['nummov']
            ))
            return ''