import re
import traceback
from datetime import datetime
from typing import List, Tuple, Dict

from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession
from project.custom_types import (
    AccountScraped, MovementParsed, MovementScraped, CorrespondenceDocScraped, CorrespondenceDocParsed
)
from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
from scrapers.caja_ingenieros_scraper_from_caixa_geral import parse_helpers_receipts
from scrapers.caja_ingenieros_scraper_from_caixa_geral.caja_ingenieros_scraper import CajaIngenierosScraper

__version__ = '1.5.0'

__changelog__ = """
1.5.0 2023.04.28
_product_to_fin_ent_id: fixed to return same product_id received as parameter
1.4.0 2023.04.25
download_all_accounts_correspondence: refactored from download_account_correspondence
1.3.0 2023.04.17
download_account_correspondence:
    deleted call to basic_should_download_correspondence_for_account as all PDF should be download from correspondence
added _pdf_text_wo_export_date
added _receipt_checksum
download_account_correspondence, download_movement_receipt:
    deleted creation date from PDF document text to callculate checksum and avoid same files being considered the same
removed unused imports
1.2.0 download_movement_receipt
1.1.0 download_correspondence with _download_correspondence_pdf
1.0.0
Inherits CajaIngenierosScraper
"""


class CajaIngenierosReceiptsScraper(CajaIngenierosScraper):

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
        url = 'https://be.caja-ingenieros.es' + pdf_link
        return url

    def _pdf_text_wo_export_date(self, document_text: str) -> str:
        """For receipts and correspondence
        Drops trailing 'export date' before hashing:
            '14-04-2023 11:19:58 9999 USUARI�WEB 0121-004-01'
        to get equal checksums each time
        """
        document_text_clean = re.sub(r'(?s)\n\d{2}-\d{2}-\d{4}\s\d{2}\:\d{2}:\d{2}\s.*?$', '', document_text)
        return document_text_clean

    def _receipt_checksum(self, document_text: str) -> str:
        """Without export date"""
        document_text_clean = self._pdf_text_wo_export_date(document_text)
        checksum = pdf_funcs.calc_checksum(bytes(document_text_clean, 'utf-8'))
        return checksum

    def download_movement_receipt(self,
                                  s: MySession,
                                  account_scraped: AccountScraped,
                                  movement_scraped: MovementScraped,
                                  movement_parsed: MovementParsed,
                                  meta: dict) -> str:
        """Saves receipt, updates DB and returns its text (description)"""

        if not movement_parsed['receipt_params']['pdf_link']:
            return ''

        mov_receipt_params = movement_parsed['receipt_params']
        mov_str = self._mov_str(movement_scraped)

        self.logger.info('{}: download receipt for mov {}'.format(
            account_scraped.FinancialEntityAccountId,
            mov_str
        ))
        try:
            req_pdf_url = self._get_download_pdf_url(mov_receipt_params['pdf_link'])
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
            receipt_parsed_text = pdf_funcs.get_text(resp_pdf.content)
            receipt_parsed_text_wo_export_date = self._pdf_text_wo_export_date(receipt_parsed_text)

            ok, receipt_parsed_text, checksum = self.basic_save_receipt_pdf_as_correspondence(
                account_scraped,
                movement_scraped,
                resp_pdf.content,
                pdf_parsed_text=receipt_parsed_text_wo_export_date,
                checksum=self._receipt_checksum(receipt_parsed_text),
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
            corr_parsed: CorrespondenceDocParsed) -> Tuple[bool, MySession, bytes]:
        req_pdf_url = 'https://be.caja-ingenieros.es{}'.format(
            corr_parsed.extra['req_link']
        )
        resp_pdf = s.get(
            req_pdf_url,
            headers=self.req_headers,
            proxies=self.req_proxies,
            stream=True
        )
        pdf_content = resp_pdf.content
        if b'<HTML' in pdf_content:
            self.logger.error("{}: can't download PDF. Skip. RESPONSE:\v{}".format(
                corr_parsed,
                resp_pdf.text
            ))
            return False, s, pdf_content
        return True, s, pdf_content

    def download_correspondence(
            self,
            s: MySession,
    ):

        if not self.basic_should_download_correspondence():
            return False, []

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=360  # 1 year with padding
        )

        req_params = {
            "OPERACION": "not0000_m_0TRE",
            "IDIOMA": "01",
            "OPERAC": "1004",
            "LLAMADA": self.llamada_param,
            "CLIENTE": self.cliente_param,
            "CAJA": "3025",
            "CAMINO": "6025",
            "DATOPEINI2": "",
            "DATOSOPEINI": "",
            "DESCGENE": "",
            "DEDONDE": "GENE",
            "OPGENERICA": "",
            "ACCSS": "FUSION",
            "APN": "no",
            "REFDESDE": "",
            "certBody": "",
            "INILOGIN": "S",
            "IGNORA_TEST": "",
        }

        resp_corr_gnp2 = s.post(
            'https://be.caja-ingenieros.es/BEWeb/3025/6025/not0000_m_0TRE.action',
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        self.gnp2 = parse_helpers_receipts.get_access_gnp2(str(resp_corr_gnp2.content))

        reg_params_corr_form = {
            "LLAMADA": self.llamada_param,
            "CLIENTE": self.cliente_param,
            "IDIOMA": "01",
            "CAJA": "3025",
            "OPERAC": "9837",
            "CTASEL": "",
            "CTAFOR": "",
            "GNP2": self.gnp2
        }

        resp_corr_form = s.post(
            'https://be.caja-ingenieros.es/BEWeb/3025/6025/not6578_m_0GNRL.action',
            data=reg_params_corr_form,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts = parse_helpers_receipts.get_gcuenta_numbers(str(resp_corr_form.content))

        self.download_all_accounts_correspondence(s, accounts, date_from)

        return True, []  # results are not used


    def download_all_accounts_correspondence(
            self,
            s: MySession,
            accounts_for_corr: List[Dict[str, str]],
            date_from: datetime):

        req_params_corr_dict = {
            "MENUDER": "",
            "LLAMADA": self.llamada_param,
            "CLIENTE": self.cliente_param,
            "IDIOMA": "01",
            "CAJA": "3025",
            "OPERAC": "6578",
            "CTASEL": "",
            "CTAFOR": "",
            "datosEnvioSeleccion": "",
            "CODAVANCE": "",
            "CODRETROCESO": "",
            "PAGINAACTUAL": "",
            "PAGINAANTERIOR": "",
            "COMBOTIPO": "0",
            "GCUENTAAUX": "T",
            "CCC1": "T",
            "cuentaFormateadaGCUENTAAUX": "Todas",
            "fecha-ini": date_from.strftime("%d/%m/%Y"),
            "FECHAINI": date_from.strftime("%d%m%Y"),
            "fecha-fin": self.date_to.strftime("%d/%m/%Y"),
            "FECHAFIN": self.date_to.strftime("%d%m%Y"),
            "FAMILIA": "1999",
            "descripcionComboFAMILIA": "",
            "CADENA_BUSCAR": "",
            "TXTERROR": "",
            "PLANTILLA": "",
            "PLANTILLA_ERROR": "",
            "FECHA_INICIO": date_from.strftime("%d-%m-%Y"),
            "FECHA_FIN": self.date_to.strftime("%d-%m-%Y"),
            "CUENTA": "",
            "TIPO1": "",
            "NCUENTAS": "",
            "MENU": "",
            "VRS": "CED",
        }

        req_params_corr_list = [i for i in req_params_corr_dict.items()]
        for account in accounts_for_corr:
            req_params_corr_list.append(("GCUENTA", account['gcuenta']))

        resp_corr_list = s.post(
            'https://be.caja-ingenieros.es/BEWeb/3025/6025/not6578_d_0CORR.action',
            data=req_params_corr_list,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        corrs_parsed_desc = parse_helpers_receipts.get_correspondence_from_list(
            accounts_for_corr,
            resp_corr_list.text,
        )  # type: List[CorrespondenceDocParsed]

        corrs_parsed_asc = corrs_parsed_desc[::-1]

        corrs_scraped = []  # type: List[CorrespondenceDocScraped]
        for i, corr_parsed in enumerate(corrs_parsed_asc):
            try:
                ok, s, doc_pdf_content = self._download_correspondence_pdf(s, corr_parsed)
                if not ok:
                    self.logger.error("{}: {}: can't download correspondence PDF. Skip".format(
                        corr_parsed,
                    ))
                    continue

                document_text = pdf_funcs.get_text(doc_pdf_content)
                document_text_wo_export_date = self._pdf_text_wo_export_date(document_text)

                corr_scraped = CorrespondenceDocScraped(
                    CustomerId=self.db_customer_id,
                    OrganizationId=None,
                    FinancialEntityId=self.db_financial_entity_id,
                    ProductId=corr_parsed.account_no,
                    ProductType='',
                    DocumentDate=corr_parsed.operation_date,
                    Description=corr_parsed.descr,
                    DocumentType=corr_parsed.type,
                    DocumentText=document_text,
                    # Need to use Checksum to compare with PDFs from receipts
                    Checksum=pdf_funcs.calc_checksum(bytes(document_text_wo_export_date, 'utf-8')),
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