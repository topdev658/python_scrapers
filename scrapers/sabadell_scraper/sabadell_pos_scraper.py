import os
import random
import time
from collections import OrderedDict
from datetime import timedelta, date
from typing import List, Tuple, Set

from custom_libs import date_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import POSTradePoint, POSCollection, ScraperParamsCommon
from . import parse_helpers_pos
from .sabadell_scraper import SabadellScraper

__version__ = '1.3.0'

__changelog__ = """
1.3.0
POS_IDS from env
process_pos_trade_point: filter by id when it's necessary
1.2.0
POSTradePoint: DownloadTimeStamp field
1.1.0
POS_RESCRAPING_OFFSET from env
1.0.0
stable
RESCRAPING_OFFSET_DAYS
MAX_OFFSET
more delays
"""

# Days before LastDownloadedOperationalDate
POS_RESCRAPING_OFFSET = int(os.getenv('POS_RESCRAPING_OFFSET', '3'))
MAX_OFFSET = 85  # days before today
# POSTradePoint IDs to process, all if empty
POS_IDS_TO_PROCESS = os.getenv('POS_IDS').split(',') if os.getenv('POS_IDS') else []  # type: List[str]


class SabadellPOSScraper(SabadellScraper):
    """Extracts POS movements and saves into ...POS.. tables
    See dev_pos/ docs
    """
    scraper_name = 'SabadellPOSScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.logger.info('POSTradePoint IDs (IdComercio) to process: {}'.format(POS_IDS_TO_PROCESS or 'ALL'))
        self.pos_tp_ids_to_process = {int(p) for p in POS_IDS_TO_PROCESS}  # type: Set[int]

    def _open_filter_form(self, s: MySession) -> Tuple[bool, MySession, Response]:
        # Inicio -> Operaciones TPV
        # In web https://www.bancsabadell.com/txempbs/TJLiqOpTradeQuery.init.bs?key=E71DB0015924537541630760023187
        req_url = 'https://www.bancsabadell.com/txempbs/TJLiqOpTradeQuery.init.bs'
        resp_filter_form = s.get(
            req_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        is_aborted_session, s, is_relogined = self.relogin_if_lost_session(
            s,
            resp_filter_form,
            msg_prefix='_open_filter_form'
        )
        if is_aborted_session:
            False, s, Response()

        if is_relogined:
            return self._open_filter_form(s)

        return True, s, resp_filter_form

    def process_company(self, s: MySession, resp_logged_in: Response) -> bool:
        """overrides"""
        self.logger.info('PROCESS COMPANY/CONTRACT: {}'.format(self._current_company_param))
        trade_points = self.basic_get_pos_trade_points()  # type: List[POSTradePoint]
        for trade_point in trade_points:
            self.process_pos_trade_point(s, trade_point)
        return True

    def process_pos_trade_point(self, s: MySession, trade_point: POSTradePoint) -> bool:
        if self.pos_tp_ids_to_process and trade_point.CommercialId not in self.pos_tp_ids_to_process:
            self.logger.info('Trade point {} not in the list to process. Skip'.format(trade_point.CommercialId))
            return True

        today = date_funcs.today().date()
        date_from = max(
            trade_point.LastDownloadedOperationalDate - timedelta(days=POS_RESCRAPING_OFFSET),
            today - timedelta(days=MAX_OFFSET)
        )
        date_to = today
        self.logger.info('Process trade point {}, dates from {} to {}'.format(
            trade_point.CommercialId,
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT),
        ))
        delta_days = (date_to - date_from).days
        # download day by day, since the last_downloaded_date up to today
        # (allow overlaps of already downloaded movs, will handle it later)
        for diff in range(delta_days + 1):
            download_date = date_from + timedelta(days=diff)
            ok = self.process_pos_trade_point_date_excel(s, trade_point, download_date)
            if not ok:  # already reported
                return False

        return True

    def _check_no_movs(self, resp_text: str) -> bool:
        return 'Z23011: No existen movimientos en el periodo de fechas seleccionado.' in resp_text

    def _check_unsupported_trade_point(self, resp_text: str) -> bool:
        return 'Lo sentimos, algo no ha ido bien.' in resp_text

    def _save_trade_point_upd_date_downloaded(
            self,
            trade_point: POSTradePoint,
            downloaded_operational_date: date) -> bool:
        trade_point_upd = POSTradePoint(
            Id=trade_point.Id,
            AccessId=trade_point.AccessId,
            CommercialId=trade_point.CommercialId,
            Active=trade_point.Active,
            CreateTimeStamp=trade_point.CreateTimeStamp,
            DownloadTimeStamp=trade_point.DownloadTimeStamp,  # will be upd on save in DB
            LastDownloadedOperationalDate=downloaded_operational_date,  # upd
        )

        self.basic_update_pos_trade_point(trade_point_upd)
        return True

    def process_pos_trade_point_date_excel(
            self,
            s: MySession,
            trade_point: POSTradePoint,
            filter_date: date) -> bool:
        time.sleep(0.5 * (1 + random.random()))

        # Need to open each time
        ok, s, _resp_filter_form = self._open_filter_form(s)
        if not ok:
            # already reported
            return False

        trade_point_commercial_id = trade_point.CommercialId
        download_date_str = filter_date.strftime('%d/%m/%Y')
        self.logger.info('{}: {}: download POS collections of movements'.format(
            trade_point_commercial_id,
            download_date_str
        ))

        d, m, y = download_date_str.split('/')
        req_params = OrderedDict([
            ('noPag', '0'),
            ('r0', '1'),
            ('trade', trade_point_commercial_id),  # '33743493'
            ('account.bank', ''),
            ('account.branch', ''),
            ('account.checkDigit', ''),
            ('account.accountNumber', ''),
            ('combo1', '-1'),
            ('r1', '1'),
            ('startDate.day', d),  # '03'
            ('startDate.month', m),  # '09'
            ('startDate.year', y),  # '2021'
            ('endDate.day', d),  # '03'
            ('endDate.month', m),  # '09'
            ('endDate.year', y),  # '2021'
            ('r2', '1')
        ])
        resp_excel_step1 = s.post(
            'https://www.bancsabadell.com/txempbs/TJLiqOpTradeQuery.invoke.bs?excel&',
            data=req_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if self._check_no_movs(resp_excel_step1.text):
            self.logger.info("{}: {}: 'no movements' marker detected. Update downloaded date".format(
                trade_point_commercial_id,
                download_date_str
            ))
            self._save_trade_point_upd_date_downloaded(trade_point, filter_date)
            return True

        if self._check_unsupported_trade_point(resp_excel_step1.text):
            self.logger.warning(
                "{}: {}: 'something wrong' marker detected. "
                "It seems like this trade point is unavailable. Skip".format(
                    trade_point_commercial_id,
                    download_date_str
                )
            )
            return False

        resp_excel = s.get(
            'https://www.bancsabadell.com/txempbs/TJLiqOpTradeQuery.excelAttach.bs',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        ok = parse_helpers_pos.validate_excel(resp_excel.content)
        if not ok:
            self.basic_log_wrong_layout(
                resp_excel,
                "{}: {}: can't get valid excel. Skip the trade point".format(
                    trade_point.CommercialId,
                    download_date_str
                )
            )
            return False

        self.basic_save_excel_with_movs_pos(
            trade_point_id=trade_point_commercial_id,
            filter_date=filter_date,
            downloaded_at=date_funcs.now(),
            file_content=resp_excel.content
        )

        pos_collections = parse_helpers_pos.get_pos_collections(
            resp_excel.content,
            trade_point_id=trade_point_commercial_id,
            logger=self.logger
        )  # type: List[POSCollection]

        n_pos_colls = len(pos_collections)
        self.logger.info('{}: {}: downloaded {} POS collections of movements: {}'.format(
            trade_point_commercial_id,
            download_date_str,
            n_pos_colls,
            pos_collections
        ))

        self.basic_save_pos_collections(pos_collections)

        self.logger.info('{}: {}: saved {} POS collections'.format(
            trade_point_commercial_id,
            download_date_str,
            n_pos_colls
        ))

        self._save_trade_point_upd_date_downloaded(trade_point, filter_date)
        return True
