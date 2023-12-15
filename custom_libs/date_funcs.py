import datetime
from typing import Optional, Union, List

from project.settings import (
    DB_DATE_FMT,
    DB_TIMESTAMP_FMT,
    SCRAPER_DATE_FMT,
    SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_BEFORE_LAST_SCRAPED_MOV,
    SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_INITIALLY,
)

__version__ = '2.24.0'

__changelog__ = """
2.24.0
limit_date_to_max_offset
2.23.0
offset_dt
2.22.0
month_esp_to_num_str_short: more variants
2.21.1
get_date_range: fixed range date to return 2 days in consecutive dates param
2.21.0
get_date_range
2.20.0
now_str, today_str with param
2.19.1
convert_date_to_db_format: fixed for provided date_fmt arg
2.19.0
convert_date_str
fmt
2.18.1
convert_date_to_db_format: default exc to pass type checker
2.18.0
more flexible convert_date_to_db_format (more formats, extra params)
2.17.0
use DB_TIMESTAMP_FMT
2.16.0
today
limit_date_max_offset
2.15.0
DAF: convert_to_ymd_type2
2.14.2
DAF: month_esp_to_num_str_short
2.14.1
fmt
get_date_from_str: renamed par (it was not used as named arg yet)
2.14.0
get_date_from_str
2.13.0
convert_to_ymd
2.12.0
month_esp_to_num_str
2.11.0
get_date_from_ts
2.10.0
scrape_dates_before_on_rescraping_str: offset parameter
2.9.0
scrape_dates_before_on_rescraping_str
scrape_dates_before_initially_str
2.8.0
convert_db_fmt_date_str_to_dt
2.7.0
correct_year_if_new_year
2.6.0
convert_dt_to_scraper_date_type...
2.5.0
convert_date_to_db_format: strip() date_str
2.4.0
convert_date_to_db_format: allow empty str as 'empty' date
2.3.0
get_date_from_with_offset_of_working_dates_str
2.2.1
fixed type annotations
2.2.0
scrape_dates_before
2.1.0
convert_dt_to_db_ts_str
2.0.1
optimize imports
2.0.0
unused functions are removed
%Y%m%d fmt usage implemented 
1.7.0
get_datetime_from_db_date_str
1.6.0
get_datetime_from_date_str
1.5.0
get_date_using_td_days_since_epoch
1.4.0
now_time_hour
1.3.0
is_enough_time_interval handle None datetime_from
1.2.0
is_enough_timedelta -> is_enough_time_interval
1.1.0
is_enough_timedelta
"""


def now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def now_str(fmt=SCRAPER_DATE_FMT) -> str:
    return now().strftime(fmt)


def today() -> datetime.datetime:
    """Today start at 00:00"""
    now_ = now()
    return datetime.datetime(year=now_.year, month=now_.month, day=now_.day)


def today_str(fmt=SCRAPER_DATE_FMT) -> str:
    """
    :return: str '18/01/2017'
    """
    return today().strftime(fmt)


def now_time_hour() -> float:
    t = datetime.datetime.time(datetime.datetime.utcnow())
    return t.hour + t.minute / 60


def now_ts() -> int:
    """
    :return: int timestamp of now
    """
    return int(datetime.datetime.timestamp(datetime.datetime.utcnow()))


def now_for_db() -> str:
    """
    :return: str '20170118 02:56:03.638'
    """
    return datetime.datetime.utcnow().strftime(DB_TIMESTAMP_FMT)[:-3]


def convert_dt_to_db_ts_str(dt: datetime.datetime) -> str:
    """
    >>> convert_dt_to_db_ts_str(datetime.datetime(2017, 6, 10, 23, 55, 59, 987654))
    '20170610 23:55:59.987'
    """
    return dt.strftime(DB_TIMESTAMP_FMT)[:-3]


def convert_dt_to_scraper_date_type1(dt: datetime.datetime) -> str:
    """
    >>> convert_dt_to_scraper_date_type1(datetime.datetime(2017, 6, 30, 23, 55, 59, 999999))
    '30/06/2017'

    Converts to basic SCRAPER_DATE_FMT
    Check convert_date_to_db_format() to see date format
    """
    return dt.strftime(SCRAPER_DATE_FMT)


def convert_dt_to_scraper_date_type2(dt: datetime.datetime) -> str:
    """
    >>> convert_dt_to_scraper_date_type2(datetime.datetime(2017, 6, 30, 23, 55, 59, 999999))
    '2017-06-30'

    Converts to additional DATE_FMT which upload func expects from scraper
    Check convert_date_to_db_format() to see date format
    """
    date_fmt = '%Y-%m-%d'
    return dt.strftime(date_fmt)


def convert_to_ymd(date_str: str, from_fmt='%d/%m/%Y') -> str:
    """
    >>> convert_to_ymd('31/12/2018')
    '20181231'

    Converts date str in common scraper firmat to Ymd format
    """
    to_fmt = '%Y%m%d'
    return datetime.datetime.strptime(date_str, from_fmt).strftime(to_fmt)


def convert_to_ymd_type2(date_str: str, from_fmt='%d/%m/%y') -> str:
    """
    >>> convert_to_ymd('31/12/18')
    '20181231'

    Converts date str in common scraper format to Ymd format
    """
    to_fmt = '%Y%m%d'
    return datetime.datetime.strptime(date_str, from_fmt).strftime(to_fmt)


def convert_dt_to_scraper_date_type3(dt: datetime.datetime) -> str:
    """
    >>> convert_dt_to_scraper_date_type3(datetime.datetime(2017, 6, 30, 23, 55, 59, 999999))
    '20170630'

    Converts to additional DB_DATE_FMT which upload func expects from scraper
    Check convert_date_to_db_format() to see date format
    """
    return dt.strftime(DB_DATE_FMT)


def first_day_of_the_month_str() -> str:
    now_dt = datetime.datetime.utcnow()
    date_one = datetime.datetime(year=now_dt.year, month=now_dt.month, day=1)
    return date_one.strftime(SCRAPER_DATE_FMT)


def _get_date_with_offset_of_working_dates_dt(date_init: datetime.datetime,
                                              days_before: int) -> datetime.datetime:
    """Date to rescrape from.
    Calculates date with offset to overwrite movements.
    If got Sunday or Saturday - scrape from Friday"""
    while True:
        date_from = date_init - datetime.timedelta(days=days_before)
        weekday = date_from.weekday()
        # 5 - Saturday, 6- Sunday
        if weekday in [5, 6]:
            days_before += 1
        else:
            return date_from


def scrape_dates_before_on_rescraping_str(
        date_last_mov: datetime.datetime,
        offset=SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_BEFORE_LAST_SCRAPED_MOV) -> str:
    """Date to scrape from (if re-scraping)"""
    date_from_dt = _get_date_with_offset_of_working_dates_dt(
        date_last_mov,
        offset
    )
    return date_from_dt.strftime(SCRAPER_DATE_FMT)


def scrape_dates_before_initially_str() -> str:
    """Date to scrape from (if initial scraping of an account)"""
    now_dt = now()
    date_from_dt = _get_date_with_offset_of_working_dates_dt(
        now_dt,
        SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_INITIALLY
    )
    return date_from_dt.strftime(SCRAPER_DATE_FMT)


# todo DEPREACTED. duplicates convert ...type1
def convert_db_timestamp_dt_to_scraper_date_str(dt: datetime.datetime) -> str:
    timestamp_scraper_str = dt.strftime(SCRAPER_DATE_FMT)
    return timestamp_scraper_str


def convert_date_str(date_str: str, to_fmt: str) -> str:
    """Converts from standard SCRAPER_DATE_FMT to `to_fmt`"""
    return datetime.datetime.strptime(date_str, SCRAPER_DATE_FMT).strftime(to_fmt)


def convert_date_to_db_format(date_str: str, date_fmt='') -> str:
    """
    Converts date_str as any known date format into DB_DATE_FMT
    Raises an exn if can't convert due to unknown format/bad data

    :param date_str: 30/01/2017 or 2017-01-30 or any supported
    :param date_fmt: if provided, then it is used instead of default supported formats
    :return: 20170130

    >>> convert_date_to_db_format('20170102')
    '20170102'

    >>> convert_date_to_db_format('20170201', date_fmt='%Y%d%m')
    '20170102'

    >>> convert_date_to_db_format('2017-01-30')
    '20170130'

    >>> convert_date_to_db_format('30/01/2017')
    '20170130'

    >>> convert_date_to_db_format('')
    ''

    >>> convert_date_to_db_format('29-05-2019')
    '20190529'

    >>> convert_date_to_db_format('29.05.2019', '%d.%m.%Y')
    '20190529'

    # Suppress the EXPECTED exception and check for None
    >>> from contextlib import suppress
    >>> with suppress(ValueError): convert_date_to_db_format('29.05.2019');

    """

    # Allow empty str as 'empty' date
    if date_str == '':
        return date_str

    date_str = date_str.strip()

    # date_fmt or default list
    formats = [date_fmt] if date_fmt else [DB_DATE_FMT, SCRAPER_DATE_FMT, '%Y-%m-%d', '%d-%m-%Y']

    exc = Exception()  # correct default for a linter
    for f in formats:
        try:
            date_str = datetime.datetime.strptime(date_str, f).strftime(DB_DATE_FMT)
            return date_str
        except ValueError as e:
            exc = e
    # If we reached this line, then re-raise the last exception
    raise exc


def convert_db_fmt_date_str_to_dt(date_str: str) -> datetime.datetime:
    """
    :param date_str: expects 20170130 format

    >>> convert_db_fmt_date_str_to_dt('20170130')
    datetime.datetime(2017, 1, 30, 0, 0)
    """
    dt = datetime.datetime.strptime(date_str, DB_DATE_FMT)
    return dt


def is_enough_time_interval(datetime_from: Union[datetime.datetime, None], necessary_interval_seconds: int) -> bool:
    """
    predicate to check is enough timedelta from datetime_from to now
    :param: necessary_interval_seconds: in seconds
    """
    if not datetime_from:
        return True

    now_utc = now()  # type: datetime.datetime
    current_timedelta = now_utc - datetime_from
    return current_timedelta > datetime.timedelta(seconds=necessary_interval_seconds)


def get_date_using_td_days_since_epoch(td_days: int) -> str:
    """
    >>> get_date_using_td_days_since_epoch(42430)
    '01/03/2016'

    :param td_days: int since 01/01/1900
    :return: '30/01/2017' format
    NOTE: error 2 days+, correct manually
    """

    CORRECTION = -2  # fix date detection error

    date0 = datetime.datetime(year=1900, month=1, day=1)
    td = datetime.timedelta(days=td_days + CORRECTION)

    date_target = date0 + td
    return date_target.strftime(SCRAPER_DATE_FMT)


def get_date_from_ts(ts: int) -> str:
    """
    >>> get_date_from_ts(1525996800)
    '11/05/2018'
    >>> get_date_from_ts(1525996800000)
     '11/05/2018'

    :param ts: 10- or 13- digits (seconds or miliseconds) unix timestamp
    :return: date str in SCRAPER_DATE_FMT
    """

    # 1525996800000
    # 1525996800
    ts_str = str(ts)
    if len(ts_str) == 13:
        ts_to_convert = int(ts_str[:10])
    elif len(ts_str) == 10:
        ts_to_convert = ts
    else:
        raise Exception("Can't convert timestamp {}".format(ts))
    return datetime.datetime.utcfromtimestamp(ts_to_convert).strftime(SCRAPER_DATE_FMT)


def get_date_from_str(date_str: str, date_format=SCRAPER_DATE_FMT) -> datetime.datetime:
    return datetime.datetime.strptime(date_str, date_format)


def correct_year_if_new_year(basic_date: datetime.datetime,
                             processing_date: datetime.datetime,
                             max_timedelta: datetime.timedelta) -> datetime.datetime:
    """
    Correct year of processing_date basic on year of basic date and max_timedelta
    It is necessary when one of mov dates created with year from another date
    In this case need to check and correct the year to handle new year dates changes
    :return: new processing_date with correct year

    >>> allowed_td = datetime.timedelta(days=15)

    >>> op_date1 = datetime.datetime(2017, 12, 31, 0, 0)
    >>> val_date1 = datetime.datetime(2017, 1, 1, 0, 0)
    >>> correct_year_if_new_year(op_date1, val_date1, allowed_td)
    datetime.datetime(2018, 1, 1, 0, 0)

    >>> op_date2 = datetime.datetime(2017, 1, 1, 0, 0)
    >>> val_date2 = datetime.datetime(2017, 12, 31, 0, 0)
    >>> correct_year_if_new_year(op_date2, val_date2, allowed_td)
    datetime.datetime(2016, 12, 31, 0, 0)

    >>> op_date3 = datetime.datetime(2017, 1, 1, 0, 0)
    >>> val_date3 = datetime.datetime(2017, 1, 2, 0, 0)
    >>> correct_year_if_new_year(op_date3, val_date3, allowed_td)
    datetime.datetime(2017, 1, 2, 0, 0)
    """

    for year_correction in [-1, 0, 1]:
        date_corrected = datetime.datetime(
            processing_date.year + year_correction,
            processing_date.month,
            processing_date.day
        )

        td = date_corrected - basic_date

        if abs(td) <= max_timedelta:
            return date_corrected

    # not returned date? error
    assert False


def month_esp_to_num_str(esp_month: str) -> str:
    """
    >>> month_esp_to_num_str('Julio')
    '07'

    Returns corresponding month position in str or '' if no month found

    :param esp_month: 'julio'
    :return: '07'
    """
    m_to_n = {
        'enero': '01',
        'febrero': '02',
        'marzo': '03',
        'abril': '04',
        'mayo': '05',
        'junio': '06',
        'julio': '07',
        'agosto': '08',
        'septiembre': '09',
        'octubre': '10',
        'noviembre': '11',
        'diciembre': '12',
    }

    return m_to_n.get(esp_month.lower(), '')


def month_esp_to_num_str_short(esp_month: str) -> str:
    """
    >>> month_esp_to_num_str('Jul')
    '07'

    Returns corresponding month position in str or '' if no month found

    :param esp_month: 'jul'
    :return: '07'
    """
    m_to_n = {
        'ene': '01',
        'feb': '02',
        'mar': '03',
        'abr': '04',
        'may': '05',
        'jun': '06',
        'jul': '07',
        'ago': '08',
        'sep': '09',
        'oct': '10',
        'novi': '11',
        'nov': '11',
        'dic': '12',
    }

    return m_to_n.get(esp_month.lower(), '')


def offset_dt(offset: int) -> datetime.datetime:
    """Calculates date of offset from today"""
    return today() - datetime.timedelta(days=offset)


def limit_date_max_offset(
        date_from_str: str,
        max_offset: Optional[int]) -> str:
    """
    IF date_from > (today - max_offset)
    THEN return date_from
    ELSE return (today - max_offset)

    :param date_from_str: date str in SCRAPER_DATE_FMT (dd/mm/yyyy)
    :param max_offset: max offset in days
    :return date_from_str in SCRAPER_DATE_FMT

    >>> import datetime as dt
    >>> from project import settings
    >>> result = limit_date_max_offset('01/01/2017', 1)
    >>> # expect changed date_from_str
    >>> dt.datetime.strptime(result, settings.SCRAPER_DATE_FMT) == today() - dt.timedelta(days=1)
    True
    >>> # expect given date_from_str
    >>> limit_date_max_offset('01/01/2030', 10)
    '01/01/2030'
    """

    if not max_offset:
        return date_from_str

    date_from = get_date_from_str(date_from_str)
    min_date = offset_dt(max_offset)
    if date_from < min_date:
        return convert_dt_to_scraper_date_type1(min_date)

    return date_from_str


def limit_date_to_max_offset(
        date_to_str: str,
        offset: Optional[int]) -> str:
    """
    IF date_to > (today - offset)
    THEN return (today - offset)
    ELSE return date_to

    :param date_to_str: date str in SCRAPER_DATE_FMT (dd/mm/yyyy)
    :param offset: offset in days
    :return date_to_str in SCRAPER_DATE_FMT

    >>> import datetime as dt
    >>> from project import settings
    >>> result = limit_date_to_max_offset('01/01/2017', 1)
    >>> # expect changed date_from_str
    >>> dt.datetime.strptime(result, settings.SCRAPER_DATE_FMT) == today() - dt.timedelta(days=1)
    True
    >>> # expect given date_from_str
    >>> limit_date_to_max_offset('01/01/2020', 10)
    '01/01/2020'
    """

    if not offset:
        return date_to_str

    date_to = get_date_from_str(date_to_str)
    max_date = offset_dt(offset)
    if date_to > max_date:
        return convert_dt_to_scraper_date_type1(max_date)

    return date_to_str


def get_date_range(
        start_date: datetime.datetime,
        end_date: datetime.datetime) -> List[datetime.datetime]:
    """
    >>> start_date = datetime.datetime(year=1900, month=1, day=1)
    >>> end_date = datetime.datetime(year=1900, month=1, day=2)
    >>> get_date_range(start_date, end_date)
    [datetime.datetime(1900, 1, 1, 0, 0), datetime.datetime(1900, 1, 2, 0, 0)]

    >>> start_date = datetime.datetime(year=1900, month=1, day=1, hour=18)
    >>> end_date = datetime.datetime(year=1900, month=1, day=2)
    >>> get_date_range(start_date, end_date)
    [datetime.datetime(1900, 1, 1, 18, 0), datetime.datetime(1900, 1, 2, 18, 0)]
    """
    date_range = [
        start_date + datetime.timedelta(days=delta)
        for delta in range((end_date.date() - start_date.date()).days + 1)
    ]
    return date_range

def is_weekend_day(
        day_param: Optional[datetime.datetime] = None) -> bool:
    """
    Returns if the weekday is Saturday or Sunday (weekend)
    :return bool
    """
    day = day_param
    if not day:
        day = datetime.datetime(year=now().year, month=now().month, day=now().day)
    # Saturday = 5 / Sunday - 6
    if day.weekday() == 5 or day.weekday() == 6:
        return True

    return False

