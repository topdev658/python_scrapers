from datetime import datetime
from typing import List

from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from .custom_types import N43FromList


__version__ = '1.1.0'
__changelog__ = """
1.1.0
_get_file_date_from_name
"""


def _get_file_date_from_name(file_name: str, file_date: datetime) -> datetime:
    """
    Extracts correct date from file_name name using year provided by file_date arg
    :param file_name: given file name like  F0811192.Q43 (contains only date and month)
    :param file_date: extracte file date from FECHA field
    :return: file_date_from_name with year from file_date

    >>> dt = _get_file_date_from_name('F0811192.Q43', datetime.strptime('12/08/2022', '%d/%m/%Y'))
    >>> dt == datetime(day=11, month=8, year=2022)
    True

    >>> dt = _get_file_date_from_name('F1231192.Q43', datetime.strptime('01/01/2022', '%d/%m/%Y'))
    >>> dt == datetime(day=31, month=12, year=2021)
    True

    >>> dt = _get_file_date_from_name('F0101192.Q43', datetime.strptime('31/12/2021', '%d/%m/%Y'))
    >>> dt == datetime(day=1, month=1, year=2022)
    True
    """
    file_name_digits = extract.re_first_or_blank(r'\d+', file_name)
    mm, dd = int(file_name_digits[:2]), int(file_name_digits[2:4])
    file_date_from_name = datetime(day=dd, month=mm, year=file_date.year)
    # Handle new year, in this case timedelta will be
    # mm, dd = 12, 31
    # while file_date=01/01/next_year
    if (file_date_from_name - file_date).days > 150:
        file_date_from_name = datetime(day=dd, month=mm, year=file_date.year - 1)
    # OR mm, dd = 01, 01
    # while file_date=31/12/prev_year
    if (file_date_from_name - file_date).days < -150:
        file_date_from_name = datetime(day=dd, month=mm, year=file_date.year + 1)
    return file_date_from_name


def get_n43s_from_list(resp_json: dict, logger: ScrapeLogger) -> List[N43FromList]:
    """
    {
      "FICHERO":"F0811192.Q43",
      "EXTENSION":"Q43",
      "LONGITUD":"0000410",
      "FECHA":"12/08/2021"
    }
    """
    n43s_from_list = []  # type: List[N43FromList]
    for n43_dict in resp_json['PAGINA']:
        if n43_dict['EXTENSION'] != 'Q43':
            logger.warning('Non-N43 file extension: {}. Skip'.format(
                n43_dict
            ))
            continue
        file_name = n43_dict['FICHERO']
        file_date = datetime.strptime(n43_dict['FECHA'], '%d/%m/%Y')
        file_date_from_file_name = _get_file_date_from_name(file_name, file_date)
        n43_from_list = N43FromList(
            longitud=n43_dict['LONGITUD'],
            fichero=file_name,
            date=file_date_from_file_name.date(),
        )
        n43s_from_list.append(n43_from_list)
    return n43s_from_list
