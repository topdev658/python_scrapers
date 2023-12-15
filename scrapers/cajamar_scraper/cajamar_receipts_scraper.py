import traceback
from collections import OrderedDict
from datetime import datetime
from typing import List, Tuple, Optional

from custom_libs import extract
from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession, Response
from project.custom_types import CorrespondenceDocParsed
from project.custom_types import CorrespondenceDocScraped, DBOrganization
from project.settings import DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS
from . import parse_helpers
from . import parse_helpers_receipts
from .cajamar_scraper import CajamarScraper
from .custom_types import AccountForCorrespondence

__version__ = '3.3.0'

__changelog__ = """
3.3.1
download_account_correspondence: log trace change when 'no correspondence' message is detected
3.3.0
download_account_correspondence: 'no correspondence' detection
3.2.0
use basic_should_download_correspondence_for_account
upd log msg
3.1.0
download_account_correspondence: upd req params, validate selected account
parse_helpers_receipts: upd get_accounts_nos_for_correspondence
3.0.0
new web
2.0.0
renamed to download_correspondence(), CorrespondenceDocParsed, CorrespondenceDocScraped
1.2.0
correspondence: currency field support
1.1.0
use project-level offset for corr
1.0.0
init 
"""


class CajamarReceiptsScraper(CajamarScraper):
    scraper_name = 'CajamarReceiptsScraper'

    def _get_op_code_param(
            self,
            s: MySession,
            resp_filter_form: Response,
            org_title: str) -> Tuple[bool, str]:
        dtid_param = parse_helpers.get_dt_param(resp_filter_form.text)

        req_op_code_params = {
            'dtid': dtid_param,
            'cmd_0': 'onSubmit',
            'uuid_0': 'formulario',
            'data_0': '{"":"true|ACEPTAR|true|_self"}',
        }
        resp_op_code = s.post(
            self._url('BE/zkau'),
            data=req_op_code_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        op_code = parse_helpers.get_op_code(resp_op_code.text)
        if not op_code:
            self.basic_log_wrong_layout(resp_op_code, "{}: can't get op_code_param".format(org_title))
            return False, ''

        return True, op_code

    def download_correspondence(
            self,
            s: MySession,
            organization_title: str) -> Tuple[bool, List[CorrespondenceDocScraped]]:

        if not self.basic_should_download_correspondence():
            return False, []

        organization = (
                self.basic_get_organization(organization_title)
                or self.basic_get_organization(organization_title.upper())  # back compat with orgs from oldweb
        )  # type: Optional[DBOrganization]

        if not organization:
            self.logger.error("download_correspondence: no organization_saved with title '{}'. "
                              "Can't continue. Abort".format(organization_title))
            return False, []

        date_from, date_from_str = self.basic_get_date_from_for_correspondence(
            offset=DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS,
            max_offset=55  # 2 months with padding
        )

        self.logger.info('{}: download correspondence from {} to {}'.format(
            organization.Name,
            date_from_str,
            self.date_to_str
        ))

        req_params = {
            'CHANNEL': 'WEB',
            'MODEL': 'FullModel',
            'OP_CODE': 'O_C_BUZON_VIRTUAL_BIZTOL_v1',
            'SERV': '17',
            'NOMBRE_OPERACION': 'O_C_BUZON_VIRTUAL_BIZTOL_v1'
        }

        resp_filter_form = s.post(
            self._url('BE/ServletOperation'),
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_nos = parse_helpers_receipts.get_accounts_nos_for_correspondence(
            resp_filter_form.text
        )
        accounts_for_corr = [
            AccountForCorrespondence(
                account_no=acc_no,
                req_param=self._acc_alias_param(acc_no),
                ix=ix
            )
            for ix, acc_no in enumerate(accounts_nos)
        ]
        self.logger.info('{}: got {} accounts to download correspondence:: {}'.format(
            organization.Name,
            len(accounts_for_corr),
            accounts_for_corr
        ))

        ok, op_code_param = self._get_op_code_param(s, resp_filter_form, organization_title)
        if not ok:
            return False, []  # already reported

        for acc in accounts_for_corr:
            self.download_account_correspondence(
                s,
                organization,
                acc,
                date_from,
                self.date_to,
                op_code_param
            )
        return True, []  # results are not used

    def _download_correspondence_pdf(
            self,
            s: MySession,
            dtid_param: str,
            account_no: str,
            corr: CorrespondenceDocParsed) -> Tuple[bool, MySession, bytes]:

        corr_ix = corr.extra['corr_ix']

        req_pre_pdf_params = OrderedDict([
            ('dtid', dtid_param),
            ('cmd_0', 'onSubmitGrid'),
            ('uuid_0', 'formulario'),
            ('data_0', '{{"":"true|PDF|true|_self|{}|TAB_DOCU_row_{}"}}'.format(corr_ix, corr_ix))
        ])
        resp_pre_pdf = s.post(
            self._url('BE/zkau'),
            data=req_pre_pdf_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        req_pdf_params = OrderedDict([
            ('CHANNEL', 'WEB'),
            ('MODEL', 'FullModel'),
            ('OP_CODE', parse_helpers.get_op_code(resp_pre_pdf.text)),
            ('CURRENT_NODE', 'W_C_DOCUMENTOS_BUZON_UNIR_PDF'),
            ('REACTION_CODE', 'PDF'),
            ('TAB_DOCU[{}].ZKCHECKBOX1'.format(corr_ix), '0'),
            ('INSTANCIA_CONSULTA', ''),
            ('NCTA', parse_helpers.get_zkau_form_param(resp_pre_pdf.text, 'NCTA')),  # '000009810210800058'
            ('SRCE', parse_helpers.get_zkau_form_param(resp_pre_pdf.text, 'SRCE')),  # 'CORE'/'SF-CORE'
            ('OFICINA', parse_helpers.get_zkau_form_param(resp_pre_pdf.text, 'OFICINA')),  # '3058'
            ('ENLACE_FICHERO', ''),
            ('VENTCODI', ''),
            ('SOBRE', parse_helpers.get_zkau_form_param(resp_pre_pdf.text, 'SOBRE')),  # S/N
            ('ESTADO', ''),
            ('SECUENCIA', parse_helpers.get_zkau_form_param(resp_pre_pdf.text, 'SECUENCIA')),  # '972278273'
            ('CORRESPONSALIA', ''),
            ('TIPODOCU', parse_helpers.get_zkau_form_param(resp_pre_pdf.text, 'TIPODOCU')),  # 0F004A
            ('IMPO_HISTO', ''),
            ('ID_DR', parse_helpers.get_zkau_form_param(resp_pre_pdf.text, 'ID_DR')),  # '972278273
            ('ENTIDAD_LOGO', ''),
            ('DOMINIO', '')
        ])

        ok = all(req_pdf_params[key] for key in ['OP_CODE', 'NCTA', 'SRCE', 'SOBRE', 'SECUENCIA', 'ID_DR'])
        if not ok:
            self.basic_log_wrong_layout(
                resp_pre_pdf,
                "{}: {}: can't get valid req_pdf_params. Got {}".format(
                    account_no,
                    corr,
                    req_pdf_params
                )
            )
            return False, s, b''

        resp_pdf = s.post(
            self._url('BE/ServletOperation'),
            data=req_pdf_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            stream=True,
        )

        pdf_content = resp_pdf.content
        if b'<html' in pdf_content:
            self.basic_log_wrong_layout(
                resp_pdf,
                "{}: {}: can't download correspondence PDF. Skip".format(
                    account_no,
                    corr,
                )
            )
            return False, s, pdf_content

        return True, s, pdf_content

    def download_account_correspondence(
            self,
            s: MySession,
            organization: DBOrganization,
            account_for_corr: AccountForCorrespondence,
            date_from: datetime,
            date_to: datetime,
            op_code_param) -> Tuple[bool, List[CorrespondenceDocScraped]]:

        fin_ent_account_id = account_for_corr.account_no  # same
        if not self.basic_should_download_correspondence_for_account(fin_ent_account_id):
            return True, []

        # self.logger.info('Download account correspondence for {}'.format(account_for_corr))

        req_params = {
            'CHANNEL': 'WEB',
            'MODEL': 'FullModel',
            'OP_CODE': op_code_param,
            'CURRENT_NODE': 'W_C_BUZON_VIRTUAL_NUEVO',
            'REACTION_CODE': 'ACEPTAR',
            'NCTA_LISTA': str(account_for_corr.ix),  # '560127200001859', # NCTA_LISTA - 0
            'TIPO_DOCUS': '0',
            'MOVIMIENTOS': '0',
            'TIPO_CONSUL': '1',
            'MOVIMIENTOS3': '0',
            'FINI': date_from.strftime('%d%m%Y'),  # '01082020'
            'FFIN': date_to.strftime('%d%m%Y'),  # '15092020'
            'TIPODOCUMENTO': '00',
            'TIPODOCUMENTO2': 'TODOS',
            'CHECKCONSULTA': '0',
            'CONFIGURAR_BUZON': '0'
        }

        resp_corr_filtered = s.post(
            self._url('BE/ServletOperation'),
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        # Validate selected account
        # ['zul.mesh.Auxheader','vMxPi',{id:'ZKHEADER1',label:'CUENTA: ES92 3058 0098 6110 2180 0058',...],
        if not (extract.re_first_or_blank("CUENTA: ([^']+)", resp_corr_filtered.text).replace(' ', '')
                == account_for_corr.account_no):
            if 'No hay ningún documento en el periodo seleccionado' in resp_corr_filtered.text:
                self.logger.info("{}: 'no correspondence' message (possible bank inconsistency). Review manually or launch download with a more recent date".format(fin_ent_account_id))
                return True, []
            else:
                self.basic_log_wrong_layout(
                    resp_corr_filtered,
                    "{}: can't validate selected account".format(account_for_corr.account_no)
                )
                return False, []

        # All docs at 1 page, no pagination required
        corrs_parsed_asc = parse_helpers_receipts.get_correspondence_from_list(
            resp_corr_filtered.text,
            account_for_corr.account_no
        )  # type: List[CorrespondenceDocParsed]
        corrs_scraped = []  # type: List[CorrespondenceDocScraped]

        dtid_param = parse_helpers.get_dt_param(resp_corr_filtered.text)
        for i, corr_parsed in enumerate(corrs_parsed_asc):
            try:
                ok, s, doc_pdf_content = self._download_correspondence_pdf(
                    s,
                    dtid_param,
                    account_for_corr.account_no,
                    corr_parsed
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
                    corr_scraped
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
