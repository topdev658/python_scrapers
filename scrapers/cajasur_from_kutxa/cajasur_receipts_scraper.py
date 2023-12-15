from .cajasur_scraper import CajasurScraper
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.kutxabank_scraper.kutxa_receipts_scraper import KutxaReceiptsScraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""


class CajasurReceiptsScraper(CajasurScraper, KutxaReceiptsScraper):
    scraper_name = 'CajasurReceiptsScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

        self._open_correspondence_page_params = {
            'ice.submit.partial': "false",
            'ice.event.target': "formMenuLateral:lateralCorrespondencia",
            'ice.event.captured': "formMenuLateral:lateralCorrespondencia",
            'formMenuLateral': "formMenuLateral",
            'javax.faces.RenderKitId': "ICEfacesRenderKit",
            'formMenuLateral:_idcl': 'formMenuLateral:lateralCorrespondencia',
            'ice.focus': 'formMenuLateral:lateralCorrespondencia',
        }
