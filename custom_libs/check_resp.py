from typing import List

from custom_libs.myrequests import Response
from custom_libs.scrape_logger import ScrapeLogger

__version__ = '1.1.0'
__changelog__ = """
1.1.0
err_markers
upd log msg
"""


def is_error_msg_in_resp(err_markers: List[str],
                         resp: Response,
                         logger: ScrapeLogger,
                         from_place: str) -> bool:
    """
    :param err_markers: markers in html text to detect error
    :param resp: response
    :param logger: logger
    :param from_place: text to add in err msg
    :return: has_err/no_err
    """
    for marker in err_markers:
        if marker in resp.text:
            logger.error("Error marker '{}' in response from {}".format(marker, from_place))
            return True
    return False
