import re
from custom_libs.norma43parser import Norma43Parser, DateFormat
from unittest import TestCase

__version__ = '2.0.0'
__changelog__ = """
2.0.0
validate_n43_structure
"""


def _validate_by_re(n43_content: bytes) -> bool:
    """
    General contentvalidation by regexp patterns.
    Detects non-N43 data by regexp

    >>> _validate_by_re(b'11007531 56464')
    True
    >>> _validate_by_re(b'0025000000000000000  2301TRANSFERENCIA')
    True
    >>> _validate_by_re(b'wrong data')
    False
    """

    if not n43_content:
        return False
    if not re.match(rb'^\d+', n43_content):  # must start from digits
        return False
    return True


def _validate_by_parser(n43_text: str) -> bool:
    """If n43 contains critical errors, the parser fails and returns False"""
    # ENGLISH dates (usual): YMD; SPANISH dates: DMY.
    try:
        _n43 = Norma43Parser(DateFormat.ENGLISH).parse(n43_text)
        return True
    except Exception as _e1:
        try:
            _n43 = Norma43Parser(DateFormat.SPANISH).parse(n43_text)
            return True
        except Exception as _e2:
            return False


def validate(n43_content: bytes) -> bool:
    """Checks is it N43 or not.
    Basic validation to detect that N43 file was downloaded
    """
    ok = _validate_by_re(n43_content)
    return ok


def validate_n43_structure(n43_text: str) -> bool:
    """Checks for N43 errors.
    Deep validation to check N43 file structure correctness when backend generates broken N43 files.
    Example:
        -a 22940, account ...4022, 15.06.2021-15.06.2021
    """
    ok = _validate_by_parser(n43_text)
    return ok


class Test(TestCase):
    def test_parser1(self):
        # -a 22940, account ...4022, 15.06.2021-15.06.2021
        # /mnt/descargas/N43Python-pro/TES-RURALVIA-22940-20210616-055316-2.N43
        t = ('113067014121880640222106152106152000000000577499783MADERAS MORAL BLANCA S.L.-\n'   
             '22    0000000000000000000000000000000000000000000000000000000000\n'                
             '3330670141218806402200000000000000000000000000000000000000200000000057749978\n'    
             '88999999999999999999000003  ')
        self.assertFalse(_validate_by_parser(t))

    def test_parser2(self):
        t = ('110182232501080000382106112106111000000145733199783LAGUARDIA Y MOREIRA S.A.\n'
             '2201824041210611210611020092000000002200000000000000INGRESO EN EFECT\n'
             '23019724000491356610 RODRIGUEZ ES         RODRIGUEZ ESPIGA CAJA EMB\n'
             '2201827013210611210611040072000000002276540365161281TRANSFERENCIAS\n'
             '2301DELIA FLORINDA CALVO ARIAS            PEDIDOS  403000475 Y 403000477\n'
             '2302                                      01820365\n'
             '3301822325010800003800003000000000911140000700000001695391100000012969042978\n'
             '110182232502015208282106112106112000000000033269783LAGUARDIA Y MOREIRA S.A.\n'
             '3301822325020152082800000000000000000000000000000000000000200000000003326978\n'
             '88999999999999999999000032  ')
        self.assertTrue(_validate_by_parser(t))

