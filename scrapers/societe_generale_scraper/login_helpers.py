import os
from typing import Dict
from typing import List

from custom_libs import img_funcs


def read_saved_images_with_digits() -> Dict[int, bytes]:
    """Read saved images with digits to use them to detect place at the page of each digit"""
    folder = os.path.join(os.path.curdir, 'scrapers', 'societe_generale_scraper', 'saved_images')
    nums_bytes_dict = {}
    for num in range(0, 10):
        with open(os.path.abspath(os.path.join(folder, '{}.gif').format(num)), 'rb') as f:
            num_bytes = f.read()
            nums_bytes_dict[num] = num_bytes
    return nums_bytes_dict


def get_digit_from_img(saved_images: Dict[int, bytes], pinpad_img: bytes) -> int:
    for num, num_bytes in saved_images.items():
        if num_bytes == pinpad_img:
            return num
    return -1


def get_pinpad_digits(pinpad_img: bytes) -> List[int]:
    """Extracts list of digits (0-9) from pinpad image"""
    saved_imgs = read_saved_images_with_digits()
    pinpad_tiles = img_funcs.split_with_margin(None, pinpad_img, 124, 134, 0, 0,
                                               extension='gif', is_save=False, is_bw=True)
    digits = []  # type: List[int]
    for tile_img in pinpad_tiles:
        tile_number = get_digit_from_img(saved_imgs, tile_img)
        digits.append(tile_number)
    return digits


def pass_digits_to_letters(password_digits: str, pinpad_digits: List[int]) -> str:
    """Returns user password as corresponding letters (ordered as digits on pinpad)
    :param password_digits: real user password
    :param pinpad_digits: recognized digits from pinpad

    >>> pass_digits_to_letters('021172', [2, 0, 1, 5, 4, 3, 7, 9, 6, 8])
    'baccga'
    """

    alfabet = 'abcdefghij'  # 0-9 to letters

    digit_to_letter = {}  # type: Dict[str, str]
    for digit_pos, digit_val in enumerate(pinpad_digits):
        assert digit_val != -1  # will raise exception if recognition error occur
        digit_to_letter[str(digit_val)] = alfabet[digit_pos]

    password_as_letters = ''
    for password_digit in str(password_digits):
        password_as_letters += digit_to_letter[password_digit]

    return password_as_letters
