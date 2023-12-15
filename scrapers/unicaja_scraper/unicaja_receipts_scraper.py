import random
import time
import traceback
from collections import OrderedDict
from typing import List, Tuple, Optional

from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession, Response
from project.custom_types import (
    CorrespondenceDocParsed, DBOrganization
)
from project.custom_types import CorrespondenceDocScraped
from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
from . import parse_helpers_receipts
from .unicaja_scraper import UnicajaScraper

__version__ = '3.1.0'

__changelog__ = """
3.1.0
use basic_should_download_correspondence_for_account
upd log msgs
3.0.0
renamed from caja_espana_scraper to unicaja_scraper
2.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
1.3.0
correspondence: currency field support
1.2.0
use project-level offset for corr
1.1.0
DocumentScraped: upd field (DocumentDate: datetime)
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

    def download_correspondence(
            self,
            s: MySession,
            resp_logged_in: Response,
            organization_title: str) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Implements the documents downloading from corr mailbox.
        It gets the pdf files, saves them to the "receipts folder"
        and inserts the documents data in _TesoraliaDocuments table.

        Redefines download_documents method to provide real results
        """

        if not self.basic_should_download_correspondence():
            return False, []

        self.logger.info('Download correspondence')
        self.process_company_for_correspondence(s, resp_logged_in, organization_title)
        return True, []  # no correspondence required in the main scraper

    def _open_filter_form(self, s: MySession) -> Tuple[MySession, Response]:
        req_url = (
            '{}/univia/servlet/ControlServlet?'
            'o=gesCom'
            '&p=8'
            '&M1=empr-servicios'
            '&M2=correspondencia'
            '&M3=servicio-unibuzon'
            '&M4=buscador-correo-empr'.format(
                self._get_host(),
            )
        )
        resp_filter_form = s.get(
            req_url,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        return s, resp_filter_form

    def process_company_for_correspondence(
            self,
            s: MySession,
            resp_logged_in: Response,
            organization_title: str) -> bool:
        organization = self.basic_get_organization(organization_title)  # type: Optional[DBOrganization]
        if not organization:
            self.logger.error(
                "process_company_for_correspondence: no organization_saved with title '{}'. "
                "Can't continue. Abort".format(organization_title)
            )
            return False
        organization_name = organization.Name

        s, resp_filter_form = self._open_filter_form(s)

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=360  # 1 year w/ padding
        )

        self.logger.info("{}: download correspondence from {} to {}".format(
            organization_name,
            date_from_str,
            self.date_to_str
        ))

        req_url = '{}/univia/servlet/ControlServlet'.format(self._get_host())

        y_from, m_from, d_from = date_from_str.split('/')
        y_to, m_to, d_to = self.date_to_str.split('/')

        req_params = OrderedDict([
            ('o', 'gesCom'),
            ('p', '8r'),
            ('idComunicado', ''),
            ('fechaDesde', date_from_str),  # '01/08/2020'
            ('fechaHasta', self.date_to_str),  # '22/08/2020'
            ('referencia', '000'),
            ('diaDesde', d_from),
            ('mesDesde', m_from),
            ('anoDesde', y_from),
            ('diaHasta', d_to),
            ('mesHasta', m_to),
            ('anoHasta', y_to),
            ('importeDesdeEnt', '0'),
            ('importeDesdeDec', '00'),
            ('importeHastaEnt', '0'),
            ('importeHastaDec', '00'),
            ('concepto', ''),
            ('orden', 'O'),  # O=DESC, ?=ASC (not F, 1, A, T)
            ('x', str(random.randrange(51, 59))),  # '57'
            ('y', str(random.randrange(5, 9))),  # '9'
        ])

        corrs_parsed_desc = []  # type: List[CorrespondenceDocParsed]
        for page_ix in range(1, 100):
            self.logger.info('Get correspondence from page #{}'.format(page_ix))
            resp_corresp_filtered_i = s.post(
                req_url,
                data=req_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
            )
            # 50 per page
            corrs_parsed_desc_i = parse_helpers_receipts.get_correspondence_from_list(
                resp_corresp_filtered_i.text
            )

            corrs_parsed_desc.extend(corrs_parsed_desc_i)

            has_next_page = '/images/univia/btnsiguiente.gif' in resp_corresp_filtered_i.text
            if not has_next_page:
                break
            # Other req params for next pages
            req_params = OrderedDict([
                ('o', 'gesCom'),
                ('p', '8rs')
            ])

        self.logger.info('{}: got {} correspondence docs for accounts: {}'.format(
            organization.Name,
            len(corrs_parsed_desc),
            sorted(list({acc.account_no for acc in corrs_parsed_desc}))
        ))

        # Download in ASC
        for corr_parsed in reversed(corrs_parsed_desc):
            _ok, s = self.process_correspondence_document(
                s,
                organization,
                corr_parsed
            )

        return True

    def _download_correspondence_pdf(
            self,
            s: MySession,
            corr: CorrespondenceDocParsed) -> Tuple[bool, MySession, bytes]:

        try:
            resp_maybe_pdf = Response()
            req_url = (
                '{}/univia/servlet/ControlServlet?o=gesCom&p=2l&idComunicado={}'.format(
                    self._get_host(),
                    corr.extra['pdf_param']
                )
            )
            for i in range(1, 4):
                self.logger.info('att #{}: download corr {}'.format(
                    i,
                    corr
                ))
                resp_maybe_pdf = s.get(
                    req_url,
                    headers=self.req_headers,
                    proxies=self.req_proxies,
                )
                # Check: is it PDF or HTML resp
                if b'!DOCTYPE' in resp_maybe_pdf.content:
                    time.sleep(3)
                    continue
                break
            else:
                self.logger.error(
                    "corr {}: couldn't download correspondence PDF after several attempts".format(
                        corr
                    )
                )
                return False, s, b''

            pdf_content = resp_maybe_pdf.content

            return True, s, pdf_content
        except:
            self.logger.error("{}: can't download correspondence PDF: HANDLED EXCEPTION\n{}".format(
                corr,
                traceback.format_exc()
            ))
        return False, s, b''

    def process_correspondence_document(
            self,
            s: MySession,
            organization: DBOrganization,
            corr_parsed: CorrespondenceDocParsed) -> Tuple[bool, MySession]:

        fin_ent_account_id = account_no_to_fin_ent_acc_id(corr_parsed.account_no)
        if not self.basic_should_download_correspondence_for_account(fin_ent_account_id):
            return True, s

        self.logger.info('Process correspondence {}'.format(corr_parsed))
        ok, s, doc_pdf_content = self._download_correspondence_pdf(s, corr_parsed)
        if not ok:
            return False, s

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

        corr_scraped_upd, should_save = self.basic_check_correspondence_doc_to_add(
            corr_parsed,
            corr_scraped,
            product_to_fin_ent_fn=account_no_to_fin_ent_acc_id
        )
        if should_save:
            self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)

        return True, s
