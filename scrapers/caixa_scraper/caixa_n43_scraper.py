import traceback
from collections import OrderedDict
from datetime import datetime, time
from typing import List, Tuple, Set

from custom_libs import n43_funcs
from custom_libs.extract import splitquery
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from . import parse_helpers_n43
from .caixa_regular_scraper import CaixaScraper
from .custom_types import Company, N43FromList

__version__ = '1.3.0'
__changelog__ = """
1.3.0
scraper_name as class prop
1.2.0
ASC order for n43s_to_download
1.1.0 
parse_helpers_n43: upd DOWNLOAD_FILES_CONTAINING (more file types to download)
1.0.0
init
"""

# Don't download automatically created files during dev mode (IS_DEPLOYED=False or IS_PROD_DB=False)
# Usually, those files have 'created_at' < 10:00
DOWNLOAD_IF_NOT_DEPLOYED_ONLY_FILES_CREATED_AFTER = time(hour=9)
# Skip explicitly when need
SKIP_N43_DOWNLOADING_BY_CREATION_DATETIME = {
    21402: ['18/04/2021 17:09:00'],
}

MAX_N43S_PER_PAGE = 10


class CaixaN43Scraper(CaixaScraper):
    """Opposite to web browser, the scraper doesn't mark
    already downloaded files as 'downloaded',
    thus they are still 'pending' all the time.
    """

    fin_entity_name = 'CAIXA'
    scraper_name = 'CaixaN43Scraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.is_success = True
        self._skip_created_by_datetime = set(
            datetime.strptime(dt, '%d/%m/%Y %H:%M:%S')
            for dt in SKIP_N43_DOWNLOADING_BY_CREATION_DATETIME.get(self.db_financial_entity_access_id, [])
        )  # type: Set[datetime]

    def __skip_prod_n43s_if_not_deployed(self, n43s_from_list: List[N43FromList]) -> List[N43FromList]:
        """Important to avoid downloading
        for automatically generated but downloaded by prod scraper yet
        """
        if project_settings.IS_DEPLOYED and project_settings.IS_PRODUCTION_DB:
            return n43s_from_list
        n43s_to_process = [
            f for f in n43s_from_list
            if (f.file_created_at.time() > DOWNLOAD_IF_NOT_DEPLOYED_ONLY_FILES_CREATED_AFTER
                and f.file_created_at not in self._skip_created_by_datetime)
        ]
        return n43s_to_process

    def _open_ficheros_page(self, s: MySession, resp_company_home: Response, company: Company) -> Response:
        """'Files' page"""
        self.logger.info("{}: open 'Ficheros' page".format(company.title))
        req_ficheros_params = OrderedDict([
            ('PN', "FTX"),
            ('PE', "12"),
            ('REMOVE_REFVAL', "1"),
            ('VOLVER_PE', ""),
            ('VOLVER_PN', ""),
            ('ORIGEN_PE', ""),
            ('ORIGEN_PN', ""),
            ('BAJA', ""),
            ('MODIFICAR', ""),
            ('CLICK_ORIG', "MNU_EMP_9"),
        ])
        req_ficheros_url = splitquery(resp_company_home.url)[0]
        resp_ficheros = s.post(
            req_ficheros_url,
            data=req_ficheros_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_company_home.url
            }),
            proxies=self.req_proxies
        )
        return resp_ficheros

    def _open_descargar_ficheros_page(
            self,
            s: MySession,
            resp_ficheros_page: Response,
            company: Company) -> Response:
        """'Download files' page"""
        self.logger.info("{}: open 'Descargar ficheros' page".format(company.title))
        req_descargar_ficheros_params = OrderedDict([
            ('PN', 'FTR'),
            ('PE', '70'),
            ('CLICK_ORIG', 'MNU_EMP_9.2'),
            ('REMOVE_REFVAL', ''),
            ('NUMERO_PESTANYA', '9'),
        ])
        req_descargar_ficheros_url = splitquery(resp_ficheros_page.url)[0]
        resp_descargar_ficheros_page = s.post(
            req_descargar_ficheros_url,
            data=req_descargar_ficheros_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_ficheros_page.url
            }),
            proxies=self.req_proxies
        )
        return resp_descargar_ficheros_page

    def _open_next_ficheros_page(
            self,
            s: MySession,
            resp_prev: Response,
            company: Company,
            page_ix: int) -> Tuple[bool, Response]:
        self.logger.info("{}: open 'Descargar ficheros' page #{}".format(company.title, page_ix))
        clave_continuation_param = parse_helpers_n43.get_clave_continuacion_param(resp_prev.text)
        if not clave_continuation_param:
            self.basic_log_wrong_layout(
                resp_prev,
                "{}: can't extract clave_continuation_param".format(company.title)
            )
            return False, Response()

        req_next_ficheros_params = OrderedDict([
            ('operacionesDescarga', ''),
            ('PN', 'FTR'),
            ('PE', '70'),
            ('PN_VOLVER', 'FTR'),
            ('PE_VOLVER', '70'),
            ('CLAVE_ITR', ''),
            ('SITUA', ''),
            ('NOMBRE_FICH_HP', ''),
            ('NOMBRE_FICH_PC', ''),
            ('CLAU_REC', ''),
            # 'n12yZQ7FA9efXbJlDsUD1wAAAXkDTADUG2s4E~ml6V4'
            ('CLAVE_CONTINUACION', clave_continuation_param),
            ('LISTA_FICHEROS_DESCARGA', ''),
            ('LISTA_FICHEROS_DESCARGA_HP', ''),
            ('LISTA_CLAVE_ITR', ''),
            ('LISTA_CLAU_REC', ''),
            ('NUM_DESCARGAS', ''),
            ('ALIASPETICION', ''),
            ('PRIMERA_PAGINA_FTR70', 'N'),
            ('SEGUNDA_VUELTA', ''),
            ('FLUJO', ''),
            ('CLICK_ORIG', 'PAG_FTR_70')
        ])
        req_next_ficheros_url = splitquery(resp_prev.url)[0]
        resp_next_ficheros_page = s.post(
            req_next_ficheros_url,
            data=req_next_ficheros_params,
            headers=self.basic_req_headers_updated({
                'Referer': resp_prev.url
            }),
            proxies=self.req_proxies
        )
        return True, resp_next_ficheros_page

    def process_company(self,
                        s: MySession,
                        resp_logged_in: Response,
                        company_ix: int,
                        subdomain: str) -> bool:
        """Overrides parent's process_company"""
        self.logger.info("{}: process company #{} for N43".format(subdomain, company_ix))
        ok, company, resp_company_home = self._switch_to_company(s, resp_logged_in, company_ix, subdomain)
        if not ok:
            return False
        assert company  # for mypy

        self.logger.info('Get N43 for company {}'.format(company.title))
        resp_ficheros = self._open_ficheros_page(s, resp_company_home, company)
        resp_descargar_ficheros = self._open_descargar_ficheros_page(s, resp_ficheros, company)
        # DESC
        number_of_files, n43s_from_list = parse_helpers_n43.get_n43s_from_list(resp_descargar_ficheros.text)

        # Pagination
        resp_prev = resp_descargar_ficheros
        n43s_from_list_i = n43s_from_list  # type: List[N43FromList]
        for page_ix in range(2, 100):  # avoid inf loop
            if number_of_files < MAX_N43S_PER_PAGE:
                self.logger.info('{}: no more pages with N43s'.format(company.title))
                break
            if (self.last_successful_n43_download_dt
                    and n43s_from_list_i
                    and n43s_from_list_i[-1].file_created_at < self.last_successful_n43_download_dt):
                self.logger.info('{}: reached earlier downloaded N43s'.format(company.title))
                break

            ok, resp_descargar_ficheros_i = self._open_next_ficheros_page(s, resp_prev, company, page_ix)
            if not ok:
                break  # already reported
            number_of_files, n43s_from_list_i = parse_helpers_n43.get_n43s_from_list(resp_descargar_ficheros_i.text)
            n43s_from_list.extend(n43s_from_list_i)
            # Prepare next iter
            resp_prev = resp_descargar_ficheros_i

        n43s_to_download = self.__skip_prod_n43s_if_not_deployed(n43s_from_list)
        if self.last_successful_n43_download_dt:
            n43s_to_download = [
                f for f in n43s_to_download
                # both file_created_at and last_successful_n43_download_dt use Spanish time zone
                if f.file_created_at > self.last_successful_n43_download_dt
            ]
        self.logger.info('{}: got N43 file(s): total {}, to download {}'.format(
            company.title,
            len(n43s_from_list),
            len(n43s_to_download)
        ))

        n43s_to_download.reverse()  # ASC

        for file_ix, n43_from_list in enumerate(n43s_to_download):
            ok = self.download_n43_file(s, resp_prev, company, n43_from_list, file_ix)
            if not ok:
                self.is_success = False
                return False  # already reported
        return True

    def download_n43_file(
            self,
            s: MySession,
            resp_prev: Response,
            company: Company,
            n43_from_list: N43FromList,
            file_ix: int) -> bool:
        file_str = 'file #{} (created {})'.format(
            file_ix,
            n43_from_list.file_created_at.strftime('%d/%m %H:%M:%S')
        )
        try:
            req_url = splitquery(resp_prev.url)[0]

            nom_fich_hp_param = n43_from_list.nom_fich_hp_param
            clave_itr_param = n43_from_list.clave_itr_param
            clau_rec_param = n43_from_list.clau_rec_param
            nom_fich_pc_param = n43_from_list.nom_fich_hp_param
            tipo_fichero_param = n43_from_list.tipo_fichero_param

            self.logger.info('{}: download N43 {}'.format(company.title, file_str))

            # Step 1
            req_43_step1_param = OrderedDict([
                ('PN', 'FTR'),
                ('PE', '23'),
                ('CLICK_ORIG', 'RED_FTR_70'),
                ('FLAG_LIGHTBOX_DESCARGA', 'S'),
                ('NOM_FICH_HP', nom_fich_hp_param),  # 'L_NvdQ2wgWIv8291DbCBYgAAAXiaKQf_opVGY14omXE'
                ('CLAVE_ITR', clave_itr_param),  # 'L_NvdQ55pt8v8291Dnmm3wAAAXiaKQf_1GIhWW9A5gA'
                ('SITUA', 'RU'),
                ('CLAU_REC', clau_rec_param),  # '00001MHC99973'
                ('NOM_FICH_PC', nom_fich_pc_param),  # 'TT100421.755'
                ('TIPO_FICHERO', tipo_fichero_param)  # 'Ext.C43/3 SEPA'
            ])

            resp_n43_step1 = s.post(
                req_url,
                data=req_43_step1_param,
                headers=self.basic_req_headers_updated({
                    'Referer': resp_prev.url
                }),
                proxies=self.req_proxies,
            )

            format_param, estilo_param = parse_helpers_n43.get_format_and_estilo_params(resp_n43_step1.text)
            usuari_sau_param = parse_helpers_n43.get_n43_form_param_by_name(resp_n43_step1.text, 'USUARI_SAU')

            # Step 2
            req_n43_step2_params = OrderedDict([
                ('FORMAT', format_param),  # 'RMHC9997302002'
                ('ESTILO', estilo_param),  # 'RMHC999730200201'
                ('CLAU_REC', clau_rec_param),  # '00001MHC99973'
                ('NOM_FICH_PC', nom_fich_pc_param),  # 'TT100421.755'
                ('NOM_FICH_HP', nom_fich_hp_param),  # 'L_NvdQ2wgWIv8291DbCBYgAAAXiaKQf_opVGY14omXE'
                ('CLAVE_PRODUCTO', ''),
                ('CLAVE_ITR', clave_itr_param),  # 'L_NvdQ55pt8v8291Dnmm3wAAAXiaKQf_1GIhWW9A5gA'
                ('USUARI_SAU', usuari_sau_param),  # '0003751317'
                ('LITERAL_TEXTO', ''),
                ('IDIOMA', '02'),
                ('SITUA', 'RU'),
                ('presentacion',
                 '/jsp/prometeus/popupdescargafichero/web/FTRPopupDescargaFichero.jsp'),
                ('CLICK_ORIG', 'RED_FTR_70'),
                ('FLAG_LIGHTBOX_DESCARGA', 'S'),
                ('PN', 'FTR'),
                ('PE', '23'),
                ('FLAG_PDF', 'NO')
            ])

            resp_n43_step2 = s.post(
                req_url,
                data=req_n43_step2_params,
                headers=self.basic_req_headers_updated({
                    'Referer': resp_prev.url
                }),
                proxies=self.req_proxies,
            )

            ruta_fich_hp_param = parse_helpers_n43.get_n43_form_param_by_name(resp_n43_step2.text, 'RUTA_FICH_HP')

            # Step 3
            req_n43_file_params = OrderedDict([
                ('PN', 'FTR'),
                ('PE', '91'),
                ('PE_ORIGEN', '23'),
                ('NOM_FICH_PC', nom_fich_pc_param),  # 'TT090421.978'
                ('RUTA_FICH_HP', ruta_fich_hp_param),  # 'Edx_uDN_TGsR3H~4M39MawAAAXidyZdj5hgxs_jYr9U'
                ('EXTENS', 'TXT'),
                ('CLAU_REC', '00001MHC99973'),
                ('MULTIDESCARGA', 'N'),
                ('CLICK_ORIG', 'FLX_FTR_23')
            ])

            resp_n43_file = s.post(
                req_url,
                data=req_n43_file_params,
                headers=self.basic_req_headers_updated({
                    'Referer': resp_prev.url
                }),
                proxies=self.req_proxies,
            )

            if not n43_funcs.validate(resp_n43_file.content):
                self.basic_log_wrong_layout(
                    resp_n43_file,
                    "{}: {}: got invalid resp_n43. Abort".format(
                        company.title,
                        file_str
                    )
                )
                return False

            self.n43_contents.append(resp_n43_file.text.encode('UTF-8'))
            return True
        except Exception as _e:
            self.logger.error(
                "{}: {}: can't download. Abort. HANDLED EXCEPTION: {}".format(
                    company.title,
                    file_str,
                    traceback.format_exc()
                )
            )
            return False

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, reason, subdomains = self.login_to_subdomain()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        # Concurrent processing for subdomains was disabled in caixa_regular_scraper
        for ix, subdomain in enumerate(subdomains):
            self.process_subdomain(s, resp_logged_in, subdomain, ix)

        self.basic_log_time_spent('GET N43')

        if not self.is_success:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        # Can upload only after successful scraping job
        # because the scraper doesn't move downloaded N43s to 'archived' area
        # (it's different to web behavior)
        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
