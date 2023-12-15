"""
Access-specific cookies to emulate
scraping from the 'confirmed' environment (web browser).
Usually, these cookies require SMS confirmation and cannot be obtained
without extra customer-provided efforts.

Add once here the necessary cookies for every access after the SMS confirmation.
"""

from typing import Dict

# {access_id_int: cookies_str}
# Note: the cookies_str is used to provide forward compat with DB-integrated environ cookies
ENVIRON_COOKIES = {
    35550: 'uid-login=20220629103750403095056841',
    17733: 'uid-login=20220629103750403095056841',
    28152: 'uid-login=20220629103750403095056841',
    35555: 'uid-login=20220629103750403095056841',
    30032: 'uid-login=20220614101834232759642937',
    30606: 'uid-login=20220614101834232759642937',
    22304: 'uid-login=20220629103750403095056841',
    21305: 'uid-login=20220629103750403095056841',
    31307: 'uid-login=20220629103750403095056841',
    31503: 'uid-login=20220629103750403095056841',
    35011: 'uid-login=20220629103750403095056841',
    34004: 'uid-login=20220629103750403095056841',
    35208: 'uid-login=20220912113729924183328076',
    18914: 'uid-login=20220912113729924183328076',
    35549: 'uid-login=20220912113729924183328076',
    17710: 'uid-login=20220912113729924183328076',
    35704: 'uid-login=20220912113729924183328076',
    32505: 'uid-login=20220912113729924183328076',
    26911: 'uid-login=20220912113729924183328076',
    31037: 'uid-login=20220912113729924183328076',
    37333: 'uid-login=20220912113729924183328076',
    31308: 'uid-login=20220912113729924183328076',
    26311: 'uid-login=20220912113729924183328076',
    23405: 'uid-login=20220912113729924183328076',
    31703: 'uid-login=20220912113729924183328076',
    26004: 'uid-login=20220912113729924183328076',
    11449: 'uid-login=20220912113729924183328076',
    31306: 'uid-login=20220912113729924183328076',
    18103: 'uid-login=20220912113729924183328076',
    20960: 'uid-login=20220912113729924183328076',
    36010: 'uid-login=20220912113729924183328076',
    24902: 'uid-login=20220912113729924183328076',
    23511: 'uid-login=20220912113729924183328076',
    37047: 'uid-login=20220912113729924183328076',
    35174: 'uid-login=20230123092637822534196728',
    24440: 'uid-login=20230123092637822534196728',
    35469: 'uid-login=20230123092637822534196728',
    30947: 'uid-login=20230123092637822534196728',
    38251: 'uid-login=20230123092637822534196728',
    32833: 'uid-login=20230123092637822534196728',
    38546: 'uid-login=20230123092637822534196728',
    14510: 'uid-login=20230123092637822534196728',
    28213: 'uid-login=20230123092637822534196728',
    36305: 'uid-login=20230320104518858276283416',
    36306: 'uid-login=20230320104518858276283416',
    35530: 'uid-login=20230123092637822534196728',
    35554: 'uid-login=20230123092637822534196728',
    17720: 'uid-login=20230123092637822534196728',
    38931: 'uid-login=20230123092637822534196728',
    39044: 'uid-login=20230123092637822534196728',
    39085: 'uid-login=20230123092637822534196728',
    39079: 'uid-login=20230123092637822534196728',
    16543: 'uid-login=20230123092637822534196728',
    35551: 'uid-login=20230123092637822534196728',
    32103: 'uid-login=20230123092637822534196728',
    28238: 'uid-login=20230123092637822534196728',
    39108: 'uid-login=20230123092637822534196728',
    39097: 'uid-login=20230123092637822534196728',
    16803: 'uid-login=20230123092637822534196728',
    39006: 'uid-login=20230123092637822534196728',
     2306: 'uid-login=20230123092637822534196728',
    38747: 'uid-login=20230123092637822534196728',
    39090: 'uid-login=20230123092637822534196728',
    35188: 'uid-login=20230123092637822534196728',
    26003: 'uid-login=20230123092637822534196728',
    38813: 'uid-login=20230123092637822534196728',
    39217: 'uid-login=20230123092637822534196728',
    10409: 'uid-login=20230123092637822534196728',
    26005: 'uid-login=20230123092637822534196728',
    32111: 'uid-login=20230123092637822534196728',
    22921: 'uid-login=20230123092637822534196728',
    30920: 'uid-login=20230123092637822534196728',
    30029: 'uid-login=20230123092637822534196728',
    16515: 'uid-login=20230123092637822534196728',
    31605: 'uid-login=20230123092637822534196728',
    30758: 'uid-login=20230123092637822534196728',
    13802: 'uid-login=20230123092637822534196728',
    19510: 'uid-login=20230123092637822534196728',
    16829: 'uid-login=20230123092637822534196728',
    36907: 'uid-login=20230123092637822534196728',
    24712: 'uid-login=20230123092637822534196728',
    35455: 'uid-login=20230123092637822534196728',
    38723: 'uid-login=20230123092637822534196728',
    33801: 'uid-login=20230123092637822534196728',
    20523: 'uid-login=20230123092637822534196728',
    22485: 'uid-login=20230123092637822534196728',
    31010: 'uid-login=20230123092637822534196728',
    11825: 'uid-login=20230123092637822534196728',
    38554: 'uid-login=20230123092637822534196728',
    35548: 'uid-login=20230123092637822534196728',
    27820: 'uid-login=20230123092637822534196728',
    38912: 'uid-login=20230123092637822534196728',
    20202: 'uid-login=20230123092637822534196728',
    36040: 'uid-login=20230123092637822534196728',
    35301: 'uid-login=20230123092637822534196728',
    30030: 'uid-login=20230123092637822534196728',
    39814: 'uid-login=20230123092637822534196728',
    31001: 'uid-login=20230123092637822534196728',
    33330: 'uid-login=20230123092637822534196728',
    32817: 'uid-login=20230123092637822534196728',
    40121: 'uid-login=20230123092637822534196728',
    40138: 'uid-login=20230123092637822534196728',
    36804: 'uid-login=20230123092637822534196728',
    22937: 'uid-login=20230123092637822534196728',
    40202: 'uid-login=20230123092637822534196728',
    16518: 'uid-login=20230123092637822534196728',
    31322: 'uid-login=20230123092637822534196728',
    40102: 'uid-login=20230123092637822534196728',
    32744: 'uid-login=20230123092637822534196728',
    32816: 'uid-login=20230123092637822534196728',
    40507: 'uid-login=20230123092637822534196728',
    40508: 'uid-login=20230123092637822534196728',
    40505: 'uid-login=20230123092637822534196728',
    40506: 'uid-login=20230123092637822534196728',
    40604: 'uid-login=20230123092637822534196728',
    40714: 'uid-login=20230123092637822534196728',
    40811: 'uid-login=20230123092637822534196728',
    40945: 'uid-login=20230123092637822534196728',
    38925: 'uid-login=20230123092637822534196728',
    37049: 'uid-login=20230123092637822534196728',
    28224: 'uid-login=20230123092637822534196728',
    40968: 'uid-login=20230123092637822534196728',
     9502: 'uid-login=20230123092637822534196728',
    11804: 'uid-login=20230123092637822534196728',
    40725: 'uid-login=20230123092637822534196728',
    35553: 'uid-login=20230123092637822534196728',
    17719: 'uid-login=20230123092637822534196728',
     4615: 'uid-login=20230123092637822534196728',
    39016: 'uid-login=20230123092637822534196728',
    26811: 'uid-login=20230123092637822534196728',
     9432: 'uid-login=20230123092637822534196728',
    32809: 'uid-login=20230123092637822534196728',
    41326: 'uid-login=20230123092637822534196728',
    41339: 'uid-login=20230123092637822534196728',
    41355: 'uid-login=20230123092637822534196728',
}  # type: Dict[int, str]
