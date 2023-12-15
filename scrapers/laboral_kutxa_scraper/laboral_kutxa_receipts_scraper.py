import random
import re
import time
import traceback
from datetime import datetime
from typing import List, Tuple, Optional

from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession
from project.custom_types import CorrespondenceDocParsed
from project.custom_types import CorrespondenceDocScraped, DBOrganization
from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
from . import parse_helpers_receipts
from .custom_types import AccountForCorrespondence, Contract
from .laboral_kutxa__banca_online_scraper import LaboralKutxaBancaOnlineScraper

__version__ = '4.1.0'

__changelog__ = """
4.1.0
Fixed import LaboralKutxaBancaOnlineScraper from 
laboral_kutxa__banca_online_scraper instead laboral_kutxa_scraper__newweb
4.0.0 
multi-contract support
3.2.0
inherits LaboralKutxaNewWebScraper
download_correspondence: use parent's _get_organization_title 
3.1.0
use basic_should_download_correspondence_for_account
upd log msg
renamed methods/params
3.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
2.5.0
corr: early detection of server err
upd log msgs
2.4.0
parse_helpers_receipts: get_correspondence_from_list: extract currency
2.3.0
correspondence: currency field support
2.2.1
_download_correspondence_pdf: fixed wrn msgs
2.2.0
use project-level offset for corr
2.1.0
_download_correspondence_pdf: several attempts to get valid PDF
DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS = 7
2.0.0
use basic funcs for correspondence
use project types
DocumentScraped: upd field (DocumentDate: datetime)
1.0.0
init
"""


def account_no_to_fin_ent_acc_id(account_no: str) -> str:
    """
    ES6030350238612380020003 ->
       238.0.02000.3
    OR 456.41.0300.1
    OR 691.002305.8
    10 digits, different places for dots
    wild cards for SQL queries
    """
    return '{}%{}%{}%{}%{}'.format(
        account_no[-10:-7],
        account_no[-7:-6],
        account_no[-6:-5],
        account_no[-4:-1],
        account_no[-1:]
    )


def account_no_to_fin_ent_acc_id__for_early_detection(account_no: str) -> str:
    """ES6030350238612380020003 -> 2380020003"""
    return account_no[-10:]


class LaboralKutxaReceiptsScraper(LaboralKutxaBancaOnlineScraper):
    scraper_name = 'LaboralKutxaReceiptsScraper'

    def download_correspondence(
            self,
            s: MySession,
            contract: Contract,
            lkid_param: str) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Implements the documents downloading from corr mailbox.
        It gets the pdf files, saves them to the "receipts folder"
        and inserts the documents data in _TesoraliaDocuments table.

        Redefines download_documents method to provide real results
        """

        if not self.basic_should_download_correspondence():
            return False, []

        # To use fuzzy matching in basic_should_download_correspondence_for_account
        # early detection (points can be placed on different positions, so only digits can be matched)
        self._accounts_to_download_corr = {
            db_acc_id: re.sub(r'[^\d]', '', fin_ent_acc_id)  # keep only digits
            for db_acc_id, fin_ent_acc_id in self._accounts_to_download_corr.items()
        }

        org_title = contract.org_title
        organization = self.basic_get_organization(org_title)  # type: Optional[DBOrganization]

        if not organization:
            self.logger.error("download_correspondence: no organization_saved with title '{}'. "
                              "Can't continue. Abort".format(org_title))
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

        # accounts
        resp_accounts = s.get(
            'https://lkweb.laboralkutxa.com/srv/api/documentos/postanet/cuentas',
            headers=self.basic_req_headers_updated({
                # 'Accept': 'application/json, text/plain, */*',
                'lkid': lkid_param,
            }),
            proxies=self.req_proxies
        )

        try:
            resp_accounts_json = resp_accounts.json()
        except Exception as e:
            self.logger.error("{}: can't parse resp_accounts_json: RESPONSE\n{}\nAbort".format(
                org_title,
                resp_accounts.text
            ))
            return False, []

        accounts_for_corr = parse_helpers_receipts.get_accounts_for_correspondence(
            resp_accounts_json
        )  # type: List[AccountForCorrespondence]

        self.logger.info('{}: got {} accounts to download correspondence:: {}'.format(
            organization.Name,
            len(accounts_for_corr),
            accounts_for_corr
        ))

        for acc in accounts_for_corr:
            # Only serial processing is possible
            # Need to download PDFs while filtered correspondence for the account
            self.process_account_for_correspondence(
                s,
                organization,
                acc,
                lkid_param,
                date_from,
                self.date_to,
            )
        return True, []  # results are not used

    def _download_correspondence_pdf(
            self,
            s: MySession,
            organization_name: str,
            corr: CorrespondenceDocParsed,
            lkid_param: str) -> Tuple[bool, MySession, bytes]:

        # GET https://lkweb.laboralkutxa.com/srv/api/documentos/5?lkId=122df470-4b16-4f43-ae49-2f7bd7af405b&document=pdf
        # <<< {"MensajeIdioma":null,"TipoError":null,"Resultado":0,"Mensaje":"x2nOfcj0b0akF6Si4Oo9qQ","MensajeRaw":null}
        # GET https://objectstorage.laboralkutxa.com/api/ObjectStorage/file/x2nOfcj0b0akF6Si4Oo9qQ
        # <<< PDF
        req_pre_pdf_url = 'https://lkweb.laboralkutxa.com/srv/api/documentos/{}'.format(
            corr.extra['docid_param']
        )
        req_pre_pdf_params = {
            'lkId': lkid_param,
            'document': 'pdf'
        }
        err = ''
        resp_codes_bad_for_proxies_cache = s.resp_codes_bad_for_proxies.copy()
        # Several attempts, bsc err resp often occurs - it disappears after retries
        for i in range(1, 4):
            s.resp_codes_bad_for_proxies = [502, 503, 504, 403, None]  # drop 500
            resp_pre_pdf = s.get(
                req_pre_pdf_url,
                params=req_pre_pdf_params,
                headers=self.basic_req_headers_updated({
                    'lkid': lkid_param
                }),
                proxies=self.req_proxies
            )

            if resp_pre_pdf.text == '{"message":"An error has occurred."}':
                err = '{}: {}: SERVER ERROR. RESPONSE:\n{}'.format(
                    organization_name,
                    corr,
                    resp_pre_pdf.text
                )
                continue

            try:
                resp_pre_pdf_json = resp_pre_pdf.json()
            except Exception as _e:
                err = "{}: {}: can't parse resp_pre_pdf_json. RESPONSE:\n{}".format(
                    organization_name,
                    corr,
                    resp_pre_pdf.text
                )
                self.logger.warning(err.split(' RESPONSE', maxsplit=1)[0])  # short report
                time.sleep(i * 3 + random.random())
                continue

            if 'Mensaje' not in resp_pre_pdf_json:
                err = "{}: {}: no 'Mensaje' code in resp_pre_pdf_json. RESPONSE:\n{}".format(
                    organization_name,
                    corr,
                    resp_pre_pdf.text
                )
                self.logger.warning(err.split(' RESPONSE', maxsplit=1)[0])  # short report
                time.sleep(i * 3 + random.random())
                continue

            pdf_id = resp_pre_pdf_json['Mensaje']  # 'x2nOfcj0b0akF6Si4Oo9qQ'
            time.sleep(0.1)
            resp_pdf = s.get(
                'https://objectstorage.laboralkutxa.com/api/ObjectStorage/file/{}'.format(pdf_id),
                headers=self.req_headers,
                proxies=self.req_proxies,
                stream=True,
            )

            pdf_content = resp_pdf.content

            if b'<!DOCTYPE' in pdf_content:
                err = "{}: {}: not a PDF. RESPONSE:\n{}".format(
                    organization_name,
                    corr,
                    resp_pdf.text
                )
                self.logger.warning(err.split(' RESPONSE', maxsplit=1)[0])  # short report
                time.sleep(i * 3 + random.random())
                continue

            # All OK
            break
        else:
            s.resp_codes_bad_for_proxies = resp_codes_bad_for_proxies_cache
            self.logger.error("{}\nCan't download correspondence PDF. Skip".format(err))
            return False, s, b''
        # end of for i in range(1, 4)

        s.resp_codes_bad_for_proxies = resp_codes_bad_for_proxies_cache

        return True, s, pdf_content

    def process_account_for_correspondence(
            self,
            s: MySession,
            organization: DBOrganization,
            account_for_corr: AccountForCorrespondence,
            lkid_param: str,
            date_from: datetime,
            date_to: datetime) -> Tuple[bool, List[CorrespondenceDocScraped]]:

        fin_ent_account_id_for_corr = account_no_to_fin_ent_acc_id__for_early_detection(
            account_for_corr.account_no
        )
        if not self.basic_should_download_correspondence_for_account(fin_ent_account_id_for_corr):
            return True, []

        req_params = {
            # ?producto=0&tipo=*&visto=todos&fechaDesde=2020-05-01&fechaHasta=2020-07-16
            'producto': account_for_corr.position_id_param,
            'tipo': '*',
            'visto': 'todos',
            'fechaDesde': date_from.strftime('%Y-%m-%d'),
            'fechaHasta': date_to.strftime('%Y-%m-%d')

        }
        # Retrieves all correspondence for these dates at once
        resp_corresp_filtered = s.get(
            'https://lkweb.laboralkutxa.com/srv/api/documentos/postanet',
            params=req_params,
            headers=self.basic_req_headers_updated({
                'lkid': lkid_param,
            }),
            proxies=self.req_proxies
        )

        try:
            resp_corresp_filtered_json = resp_corresp_filtered.json()
        except:
            self.logger.error("{}: {}: can't parse resp_corresp_filtered_json. Skip. RESPONSE:\n{}. ".format(
                organization.Name,
                account_for_corr.account_no,
                resp_corresp_filtered.text
            ))
            return False, []

        if 'documentos' not in resp_corresp_filtered_json:
            self.basic_log_wrong_layout(resp_corresp_filtered, "{}: {}: no 'documentos' in the response".format(
                organization.Name,
                account_for_corr.account_no
            ))
            return False, []

        self.logger.info('{}: {}: get correspondence from list'.format(
            organization.Name,
            account_for_corr.account_no
        ))

        corrs_parsed_desc = parse_helpers_receipts.get_correspondence_from_list(
            resp_corresp_filtered_json,
            account_for_corr.account_no
        )  # type: List[CorrespondenceDocParsed]

        corrs_parsed_asc = corrs_parsed_desc[::-1]

        corrs_scraped = []  # type: List[CorrespondenceDocScraped]
        for i, corr_parsed in enumerate(corrs_parsed_asc):
            try:
                ok, s, doc_pdf_content = self._download_correspondence_pdf(
                    s,
                    organization.Name,
                    corr_parsed,
                    lkid_param
                )
                if not ok:
                    continue  # already reported

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
                    Checksum=pdf_funcs.calc_checksum(bytes(document_text, 'utf-8')),
                    AccountId=None,  # Account DB Id
                    StatementId=None,
                    Amount=corr_parsed.amount,
                    Currency=corr_parsed.currency,
                )

                corr_scraped_upd, should_add = self.basic_check_correspondence_doc_to_add(
                    corr_parsed,
                    corr_scraped,
                    product_to_fin_ent_fn=account_no_to_fin_ent_acc_id
                )

                if should_add:
                    corrs_scraped.append(corr_scraped_upd)
                    self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)

            except Exception as _e:
                self.logger.error("{}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                    corr_parsed,
                    traceback.format_exc()
                ))

        return True, corrs_scraped
