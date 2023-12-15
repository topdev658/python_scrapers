import os
from typing import Dict
from typing import List

from custom_libs import img_funcs


def read_saved_images_with_digits() -> Dict[int, bytes]:
    """Read saved images with digits to use them to detect place at the page of each digit"""
    folder = os.path.join(os.path.curdir, 'scrapers', 'kutxabank_scraper', 'saved_images')
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
    pinpad_tiles = img_funcs.split_with_margin(None, pinpad_img, 23, 23, 5, 5, 'gif', is_bw=True, is_save=False)
    digits = []  # type: List[int]
    for tile_img in pinpad_tiles:
        tile_number = get_digit_from_img(saved_imgs, tile_img)
        digits.append(tile_number)
    return digits
