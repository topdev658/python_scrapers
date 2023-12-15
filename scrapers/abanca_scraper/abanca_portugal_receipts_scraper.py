from .abanca_beabanca_receipts_scraper import AbancaBeAbancaReceiptsScraper
from .abanca_portugal_scraper import AbancaPortugalScraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""


class AbancaPortugalReceiptsScraper(AbancaPortugalScraper, AbancaBeAbancaReceiptsScraper):
    """
    Correspondence download into AbancaBeAbancaReceiptsScraper
    """
    scraper_name = 'AbancaPortugalReceiptsScraper'
    iban_country_code = 'PT'
    base_url = 'https://be.abanca.pt/'

