"""Contains the list of users/customers (by DB customer Id) required future movements.

Note: the 'future movement scraping' feature must also be supported by a specific scraper.
For now (06/2020) CAIXA and BBVANetcash are supporting future movements.

It's easy to add support of 'future movements scraping' to a specific scraper:
just need to call self.set_date_to_for_future_movs() in __init__ method of the scraper
"""

from typing import List

USERS_ALLOW_FUTURE_MOVS = [
    # 290483,
    # 304902,
    # 308997,
    # 340332,
]  # type: List[int]
