import os
from typing import Dict

from custom_libs import img_funcs
from .custom_types import Tile


def get_digits_to_tiles(gridpass_img_bytes: bytes) -> Dict[int, Tile]:
    folder = os.path.join(os.path.dirname(__file__), 'saved_images')

    digits_to_imgs_paths = {
        num: os.path.abspath(os.path.join(folder, '{}.png').format(num))
        for num in range(10)
    }

    digits_to_tiles_raw, is_success = img_funcs.find_tiles(
        img_large_bytes=gridpass_img_bytes,
        img_small_names_to_paths=digits_to_imgs_paths,
        tiles_x=6,
        tiles_y=4,
        is_bw=True,
        is_ordered_search=True
    )

    assert is_success
    digits_to_tiles = {name: Tile(tile_tuple)
                       for name, tile_tuple in digits_to_tiles_raw.items()}

    return digits_to_tiles


def get_digits_to_codes(gridpass_img_bytes: bytes,
                        tile_to_val: Dict[Tile, str]) -> Dict[int, str]:
    digits_to_tiles = get_digits_to_tiles(gridpass_img_bytes)

    digits_to_codes = {}  # type: Dict[int, str]
    for digit, tile in digits_to_tiles.items():
        val = tile_to_val[tile]
        digits_to_codes[digit] = val
    return digits_to_codes
