import time
import traceback
from collections import OrderedDict
from typing import List, Tuple, Optional

from custom_libs import extract
from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession, Response
from project.custom_types import (
    CorrespondenceDocScraped, CorrespondenceDocParsed, DBOrganization
)
from project import settings
from . import parse_helpers
from . import parse_helpers_receipts
from .iber_caja_scraper import IberCajaScraper, DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS

__version__ = '2.0.0'

__changelog__ = """
2.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
1.4.0
parse_helpers_receipts: get_correspondence_from_list: extract currency
custom DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
1.3.0
correspondence: currency field support
1.2.0
use project-level offset for corr
1.1.0
DocumentScraped: upd field (DocumentDate: datetime)
1.0.0
init
"""

# Extra offset bcs IberCaja's date_to is a future date
DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS = (
    settings.DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
    + DATE_TO_OFFSET_TO_SCRAPE_FUTURE_MOVS
)


class IberCajaReceiptsScraper(IberCajaScraper):
    scraper_name = 'IberCajaReceiptsScraper'

    def download_correspondence(
            self,
            s: MySession,
            resp_logged_in: Response) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Implements the documents downloading from corr mailbox.
        It gets the pdf files, saves them to the "receipts folder"
        and inserts the documents data in _TesoraliaDocuments table.

        Redefines download_documents method to provide real results
        """

        if not self.basic_should_download_correspondence():
            return False, []

        self.logger.info('Download correspondence')
        self.process_company_for_correspondence(s, resp_logged_in)
        return True, []  # no correspondence required in the main scraper

    def _open_filter_form(
            self,
            s: MySession,
            auth_param: str) -> Tuple[MySession, Response]:
        req_url = 'https://www1.ibercajadirecto.com/ibercaja/asp/modulodirector.asp?MSCSAuth={}'.format(auth_param)
        req_params = OrderedDict([
            ('idoperacion', '527_0'),
            ('Entidad', '2085'),
            ('Idioma', 'ES'),
            ('Dispositivo', 'INTR'),
            ('Canal', 'IBE'),
            ('Entorno', 'IN')
        ])
        resp_filter_form = s.post(
            req_url,
            data=req_params,
            headers=self.basic_req_headers_updated({
                'Content-Type': 'application/x-www-form-urlencoded'
            }),
            proxies=self.req_proxies,
        )

        return s, resp_filter_form

    def process_company_for_correspondence(self, s, resp_logged_in) -> bool:
        organization_title = self.db_customer_name  # default organization only
        organization = self.basic_get_organization(organization_title)  # type: Optional[DBOrganization]

        if not organization:
            self.logger.error("process_company_for_correspondence: no organization_saved with title '{}'. "
                              "Can't continue. Abort".format(organization_title))
            return False
        organization_name = organization.Name

        auth_param = parse_helpers.get_auth_param(resp_logged_in.text)
        s, resp_filter_form = self._open_filter_form(s, auth_param)

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=120  # tested up to 4 months
        )

        self.logger.info("{}: download correspondence from {} to {}".format(
            organization_name,
            date_from_str,
            self.date_to_str
        ))

        req_url = 'https://www1.ibercajadirecto.com/ibercaja/asp/modulodirector.asp?MSCSAUTH={}'.format(auth_param)

        # Can download pdf only from the current page
        for page_ix in range(1, 100):
            self.logger.info('{}: download correspondence from page #{}'.format(organization_name, page_ix))

            req_params = OrderedDict([
                ('idoperacion', '527_1'),
                ('dispositivo', 'INTR'),
                ('Idioma', 'ES'),
                ('canal', 'IBE'),
                ('entidad', '2085'),
                ('entorno', 'IN'),
                ('claf_entrada', ''),
                ('tipo_busq', 'sitodas'),
                ('cuentas', parse_helpers_receipts.get_all_cuentas_param_for_corr(resp_filter_form.text)),
                ('fecha_ini', date_from.strftime('%Y/%m/%d')),  # '2020/05/01'
                ('fecha_fin', self.date_to.strftime('%Y/%m/%d')),  # '2020/08/12'
                ('importe_min', '0'),
                ('importe_max', '9999999999'),
                ('indconsultado', ''),
                ('agrupacion', ''),
                ('pagina_a_mostrar', str(page_ix)),
                ('orden', '0'),  # 1 DESC, 0 ASC
                ('columna_orden', '1'),
                ('pestanas', '00#04#05#07#08#09#11#13#14#15#16'),  # todo ?
                # '20859660310330231072-AH#20859660388300470098-AH#96605800048835-DX#6001753272-MP#'
                ('ctas_ec', extract.form_param(resp_filter_form.text, 'ctas_ec')),
                ('guardar', 'N'),
                ('ctas_guardadas', ''),
                ('vistaSel', '')
            ])

            resp_corresp_filtered_i = s.post(
                req_url,
                data=req_params,
                headers=self.basic_req_headers_updated({
                    'Content-Type': 'application/x-www-form-urlencoded'
                }),
                proxies=self.req_proxies,
            )

            ok, corrs_parsed_asc_i = parse_helpers_receipts.get_correspondence_from_list(
                resp_corresp_filtered_i.text,
                self.logger
            )
            if not ok:
                # Already logged
                return False
            n_corrs = len(corrs_parsed_asc_i)

            self.logger.info('{}: page #{}: download PDFs ({} from the page)'.format(
                organization_name,
                page_ix,
                n_corrs
            ))

            # ASC order allows to download PDF and save the document in one step
            # (no need to reorder downloaded ones  and save them then)
            for corr_parsed in corrs_parsed_asc_i:
                _ok, s = self.process_correspondence_document(
                    s,
                    page_ix,
                    organization,
                    corr_parsed,
                    auth_param,
                )

            has_next_page = (
                    parse_helpers_receipts.get_num_pages_with_corr(resp_corresp_filtered_i.text)
                    > page_ix
            )
            if not has_next_page:
                break
            pass
        return True

    def _download_correspondence_pdf(
            self,
            s: MySession,
            page_ix: int,
            corr: CorrespondenceDocParsed,
            auth_param: str) -> Tuple[bool, MySession, bytes]:

        try:
            # another re than in get_auth_param
            # auth_param_upd = extract.re_first_or_blank("""(?si)MSCSAUTH=(.*?)[&'"]""", resp_vis.text)
            corr_ix = corr.extra['ix']
            resp_maybe_pdf = Response()
            req_url = 'https://www1.ibercajadirecto.com/ibercaja/asp/modulodirector.asp?MSCSAUTH={}'.format(auth_param)
            req_params = OrderedDict([
                ('idoperacion', '502_0'),
                ('Entidad', '2085'),
                ('Canal', 'IBE'),
                ('Dispositivo', 'INTR'),
                ('Idioma', ''),
                # Finally, the position (correct corr_ix) is not critical
                # and can by any
                # pdf_param examples:
                # 'S#200625002400000153#1 B09417932  00# #LF599 #2#1#DX#20859660315800582518#  #                         #0#ESP#2020/06/25#S#01'
                # 'S#200625002400000153#1 B09417932  00# #LF599 #2#1#DX#20859660315800582518#  #                         #0#ESP#2020/06/25#S#01'
                # 'S#200518000350001242#1 B09417932  00# #I0552 #2#1#AH#20859660310330231072#  #                         #72.6#EUR#2020/05/18#S#01'
                # 'S#200617001860040377#1 B09417932  00# #I5197A#4#1#AH#20859660310330231072#  #                         #9#EUR#2020/06/16#S#01'
                ('param{}'.format(corr_ix), corr.extra['pdf_param']),
                # Not critical
                # extract.form_param(resp_prev.text, 'Op_origen')),
                ('Op_origen', '525_1'),
            ])

            for i in range(1, 4):
                self.logger.info('page #{}: att #{}: download corr with ix={}'.format(
                    page_ix,
                    i,
                    corr.extra['ix']
                ))
                resp_maybe_pdf = s.post(
                    req_url,
                    data=req_params,
                    headers=self.basic_req_headers_updated({
                        'Content-Type': 'application/x-www-form-urlencoded',
                    }),
                    proxies=self.req_proxies,
                )
                # Check: is it PDF or HTML resp
                if b'<HTML>' in resp_maybe_pdf.content:
                    time.sleep(3)
                    continue
                break
            else:
                self.logger.error(
                    "{}: corr ix={}: couldn't download correspondence PDF after several attempts".format(
                        corr.account_no,
                        corr_ix
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
            page_ix: int,
            organization: DBOrganization,
            corr_parsed: CorrespondenceDocParsed,
            auth_param: str) -> Tuple[bool, MySession]:

        self.logger.info('Process correspondence {}'.format(corr_parsed))
        ok, s, doc_pdf_content = self._download_correspondence_pdf(s, page_ix, corr_parsed, auth_param)
        if not ok:
            return False, s  # already reported

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

        corr_scraped_upd, should_save = self.basic_check_correspondence_doc_to_add(corr_parsed, corr_scraped)
        if should_save:
            self.basic_save_correspondence_doc_pdf_and_update_db(corr_scraped_upd, doc_pdf_content)

        return True, s
