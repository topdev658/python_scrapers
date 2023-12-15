"""
El algoritmo es el siguiente:

Primero, se considera el alfabeto dándole un número de 10 a 35 a cada letra: A=10, B=11, ..., Y=34, Z=35 (no se toma
en cuenta la letra Ñ).
Se toma el número de cuenta con formato 1111 2222 33 4444444444 (4, 4, 2, y 10 cifras) y se le añade el código del
país (ES para España, por ejemplo), y 00. Se obtiene 11112222334444444444ES00.
Se reemplazan las letras del país por los números correspondientes del alfabeto del punto 1. En nuestro ejemplo: E=14
y S=28. Obtenemos: 11112222334444444444142800.
Se calcula: 98 - (11112222334444444444142800 módulo 97). En este ejemplo, se obtiene 71. Si se obtuviera un número
menor que 10, habría que formatearlo con 2 dígitos.
Finalmente, el código IBAN de nuestro ejemplo es ES71 1111 2222 3344 4444 4444

FOR DC

To calculate DC (control digit):
The control digits of the bank accounts are calculated from an algorithm that will provide us with two digits. The first is calculated from the entity and branch number data and the second from the account number.
(I attached an example at the end)

-First digit:

1. The four digits of the entity are taken and listing from left to right:
The first number of the entity is multiplied by 4.
The second number of the entity is multiplied by 8.
The third figure of the entity is multiplied by 5.
The fourth figure of the entity is multiplied by 10.

2. The four digits of the branch are taken and listing from left to right:

The first number of the branch is multiplied by 9.
The second number of the branch is multiplied by 7.
The third number of the branch  is multiplied by 3.
The fourth number of the branch is multiplied by 6.

3. All the results obtained are added.

4. It is divided by 11 and we are left with the rest of the division.

5. To 11 we removed the previous rest, and that the first digit of control,
with the proviso that if it gives us 10, the digit is 1

-Second digit

1. The ten digits of the account number are taken and listing from left to right:
The first number of the account is multiplied by 1.
The second number of the account is multiplied by 2.
The third number of the account is multiplied by 4.
The fourth number of the account is multiplied by 8.
The fifth number of the account is multiplied by 5.
The sixth number of the account is multiplied by 10.
The seventh number of the account is multiplied by 9.
The eighth number of the account is multiplied by 7.
The ninth number of the account is multiplied by 3.
The tenth number of the account is multiplied by 6.

2. All the results obtained are added.

3. It is divided by 11 and we are left with the rest of the division.
4. To 11 we removed the previous rest, and that the second digit of control,
with the exception of that if it gives us 10, the digit is 1.
"""

import string
import unittest

from typing import *

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# https://github.com/juan70/iban
# https://github.com/joWeiss/simple_iban_calculator/blob/master/main.py

__version__ = '3.0.1'

__changelog__ = """
3.0.1
correct dc if mod == 0
3.0.0
build_iban_complex
2.1.0
account_no_str_clean better cleaning
2.0.1
type declarations
2.0.0
correct is_valid for French IBAN 
unittest instead of simple asserts
"""


def _letters2numbers(letters):
    """
    >>> _letters2numbers('ES')
    '1428'

    Converts a letters to the corresponding numbers string,
    e.g. A = 10, B = 11, ... Z = 35
    """
    numbers = ''.join(str(ALPHABET.find(l.capitalize()) + 10) for l in letters)
    return numbers


def _is_valid(iban_str):
    if iban_str.startswith('FR'):
        return len(iban_str) == 27
    return len(iban_str) == 24


def build_iban(country_prefix: str, account_no: Union[str, int]) -> str:
    """
    :returns: valid IBAN (with country prefix) :type: str

    >>> build_iban('ES', '1480-0010-98-0400123575')
    'ES2314800010980400123575'

    >>> build_iban('FR', '41189 00001 16010160904 28EUR')
    'FR7641189000011601016090428'
    """
    assert len(country_prefix) == 2

    # account_no_str = str(account_no).replace(' ', '').strip()
    account_no_str_clean = ''.join(l for l in str(account_no) if l in string.digits)
    account_no_str_processing = account_no_str_clean + _letters2numbers(country_prefix) + '00'

    iban_leading_digits_str = '%02d' % (98 - int(account_no_str_processing) % 97)

    iban_str = country_prefix + iban_leading_digits_str + account_no_str_clean

    if not _is_valid(iban_str):
        msg = "IBAN not validated: {}: length={}".format(iban_str, len(iban_str))
        raise Exception(msg)
    return iban_str


def _dc(entity: str, branch: str, account_no: str) -> str:
    # mults for first and second dc digit
    basics = [(entity + branch, [4, 8, 5, 10, 9, 7, 3, 6]),
              (account_no, [1, 2, 4, 8, 5, 10, 9, 7, 3, 6])]
    dc = ['', '']
    for dc_ix, (digits_str, mults) in enumerate(basics):
        acc = 0
        for digit_str, mult in zip(digits_str, mults):
            acc += int(digit_str) * mult
        mod = acc % 11
        if mod == 0:
            dc[dc_ix] = '0'  # explicit 0
        else:
            dc[dc_ix] = str(11 - mod)[0]  # ix [0] converts 10 -> 1
    dc_str = ''.join(dc)
    return dc_str


def build_iban_complex(country_prefix: str,
                       entity: str,
                       branch: str,
                       account_no: str) -> str:
    assert len(entity) == 4
    assert len(branch) == 4
    assert len(account_no) == 10
    dc = _dc(entity, branch, account_no)
    assert len(dc) == 2
    iban = build_iban(country_prefix, entity + branch + dc + account_no)
    return iban


class TestIBANBuilder(unittest.TestCase):
    def test1(self):
        self.assertEqual(
            build_iban('ES', '2095 5519 28 3900277274'),
            'ES4920955519283900277274'
        )

    def test2(self):
        self.assertEqual(
            build_iban('ES', '1111 2222 3344 4444 4444'),
            'ES7111112222334444444444'
        )

    def test3(self):
        self.assertEqual(
            build_iban('ES', '00491893002010391697'),
            'ES1900491893002010391697'
        )

    def test_french(self):
        self.assertEqual(
            build_iban('FR', '41189 00001 16010160904 28'),
            'FR7641189000011601016090428'
        )

    def test_french2(self):
        self.assertEqual(
            build_iban('FR', '41189 00001 16010160904 28EUR'),
            'FR7641189000011601016090428'
        )

    def test_vwb(self):
        self.assertEqual(
            build_iban('ES', '1480-0010-98-0400123575'),
            'ES2314800010980400123575'
        )

    def test_complex(self):
        self.assertEqual(
            build_iban_complex('ES', '0216', '4739', '8700148996'),
            'ES9202164739218700148996'
        )

    def test_dc(self):
        self.assertEqual(
            _dc('1432', '0154', '7422504551'),
            '49'
        )

    def test_dc2(self):
        self.assertEqual(
            _dc('0216', '4739', '8700148996'),
            '21'
        )

    def test_dc3(self):
        self.assertEqual(
            _dc('0216', '1083', '0600325906'),
            '07'
        )


if __name__ == "__main__":
    unittest.main()
