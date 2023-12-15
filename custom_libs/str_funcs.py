import math
import re

__version__ = '1.3.0'
__changelog__ = """
1.3.0
fuzzy_equal, fuzzy_matching: drop extra spaces
1.2.0
fuzzy_matching
fuzzy_equal: param check_fst_in_snd
1.1.0
upd doctests
"""

LETTERS_REX = re.compile(r'[\w. ]')
DIGITS_REX = re.compile(r'\d')


def fuzzy_equal(text1: str, text2: str, stricter=True, drop_symbols_re=r'''[.,'"]''',
                check_fst_in_snd=False) -> bool:
    """
    :param text1: unchanging str1 str
    :param text2: the string to aplpy fuzzy equal
    :param stricter:  if True then will be comparing str2==str1
                      else 'str2 in str1' (only str2 in str1)
    :param drop_symbols_re: to use in re.sub(drop_symbols_re, '', str1/str2)
    :param check_fst_in_snd: by default, it check only snd in fst, this param also allows fst in snd
    >>> fuzzy_equal('CONSTRUCTORA DE ESPACIOS AEREOS S.A.', 'CONSTRUCTORA DE ESPACIOS AE', stricter=False)
    True
    >>> fuzzy_equal('INMO, S.L.', 'INMO S.L', stricter=False)
    True
    >>> fuzzy_equal('INMO, S.L.', 'INMO S.', stricter=True)
    False
    """
    text1 = re.sub(r'(?s)\s+', ' ', text1)
    text2 = re.sub(r'(?s)\s+', ' ', text2)

    text1_clean = re.sub(drop_symbols_re, '', text1).strip()
    text2_clean = re.sub(drop_symbols_re, '', text2).strip()
    if not stricter:
        if not check_fst_in_snd:
            return text2_clean in text1_clean
        else:
            return (text2_clean in text1_clean) or (text1_clean in text2_clean)

    return text1_clean == text2_clean


def fuzzy_matching(text1: str, text2: str) -> float:
    """:returns [0;1.0] with precision 1. Use 0.9 to consider as matched
    Digits are important
    >>> fuzzy_matching('a  bc\\n  d', 'a bc d')
    1.0

    >>> fuzzy_matching('x y 123', 'x a b 123')  # same digits
    0.9

    >>> fuzzy_matching('INMO, S.L.', 'INMO S.')
    1.0

    >>> fuzzy_matching('TED-TRANSF ELET DISPONREMT.LUCIANO T. ALVES', 'TED-TRANSF ELET DISPONREMT.LUCIANO TEIXERIA ALV')
    0.9

    >>> fuzzy_matching('x y 123', 'x z 123')  # same digits
    0.9

    >>> fuzzy_matching('x y 123', 'x z 12')  # diferent digits
    0.2

    >>> fuzzy_matching('x y', 'x z')
    0.7

    >>> fuzzy_matching('a b c', 'a b d')
    0.9

    >>> fuzzy_matching('a b c', 'a x y')
    0.5
    """
    text1 = re.sub(r'(?s)\s+', ' ', text1)
    text2 = re.sub(r'(?s)\s+', ' ', text2)

    if fuzzy_equal(text1, text2, stricter=False, check_fst_in_snd=True):
        return 1.0

    words1 = set(x for x in re.split('[ .]', ''.join(LETTERS_REX.findall(text1)).lower()) if x)
    words2 = set(x for x in re.split('[ .]', ''.join(LETTERS_REX.findall(text2)).lower()) if x)

    words_max_len = max(len(words1), len(words2))

    weight_words = 0.0
    weight_words_max = 0.5
    words_diff_len = max(len(words1.difference(words2)), len(words2.difference(words1)))
    if not words1:
        weight_words_max = 0.0
    elif len(words1) < 2:
        weight_words_max = 0.3
    diff_factor = (words_max_len - words_diff_len) / words_max_len  # 0 <=  diff_factor <= 1.0
    # matched grows faster than linear
    weight_words = math.sin(0.5 * math.pi * diff_factor) * weight_words_max

    digits1 = ''.join(DIGITS_REX.findall(text1))
    digits2 = ''.join(DIGITS_REX.findall(text2))
    weight_digits = 0.0
    weight_digits_max = 0.5
    if not digits1:
        weight_digits_max = 0.0
    elif len(digits1) < 3:
        weight_digits_max = 0.3
    if digits1 == digits2:
        weight_digits = weight_digits_max

    # normalization due to changing _max
    matched = (weight_words + weight_digits) / (weight_words_max + weight_digits_max)

    return round(matched, 1)
