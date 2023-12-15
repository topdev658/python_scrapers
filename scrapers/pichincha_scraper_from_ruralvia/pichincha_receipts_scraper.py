import re
import traceback
from datetime import datetime
from typing import List, Tuple, Dict

from custom_libs import pdf_funcs
from custom_libs.myrequests import MySession
from project.custom_types import (
    AccountScraped, MovementParsed, MovementScraped, CorrespondenceDocScraped, CorrespondenceDocParsed
)
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.ruralvia_scraper.ruralvia_receipts_scraper import RuralviaReceiptsScraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0 2023.06.14
init
"""


class PichinchaReceiptsScraper(RuralviaReceiptsScraper):

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='PichinchaReceiptsScraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)
        self.login_init_url = 'https://www.bancopichincha.es/'
        self.domain = 'https://clientes.bancopichincha.es/'
        self.ssl_cert_init = False  # 'bancopichincha-es-chain.pem' brings err [X509] PEM lib (_ssl.c:3053)
        self.ssl_cert = True  # 'clientes-bancopichincha-es-chain.pem' brings err
        self.logger.info('Scraper started')

