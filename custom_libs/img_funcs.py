import io
import os
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from custom_libs import log

__version__ = '1.4.1'

__changelog__ = """
1.4.1
fixes for type checker
1.4.0
find_positions: speed optimization for ordered search (3x-4x)
1.3.0
find_tiles, find_positions (3x-4x speed optimization to find_pos)
1.2.0
find_tile, find_pos
1.1.0
split_with_margin: don't split if x_to > x_max or y_to > y_max to avoid blank tiles
"""


def _get_img_bytes(img: Image, extension='png') -> bytes:
    """Saves Image obj to in-memory file and returns its bytes"""
    fileobj = io.BytesIO()
    img.save(fileobj, format=extension)
    return fileobj.getvalue()


def split(img_path: Optional[str], img_bytes: bytes, height: int, width: int, is_save=False) -> List[bytes]:
    """
    Splits image to several tiles with given width and height

    :param img_path: path to image in fs
    :param img_bytes: bytes of downloaded image. Will be used if img_path is None or ''
    :param height: cropped height
    :param width: cropped width
    :param is_save: save or not
    :return: list of split images as bytes
    """
    if img_path:
        im = Image.open(img_path)
    else:
        # img_bytesio = io.StringIO(base64.b64decode(img_str))
        img_bytesio = io.BytesIO(img_bytes)
        im = Image.open(img_bytesio)

    imw, imh = im.size
    tiles = []  # type: List[bytes]
    idx = 0

    for i in range(0, imh, height):
        for j in range(0, imw, width):
            box = (j, i, j + width, i + height)
            tile = im.crop(box)  # type: Image
            tiles.append(_get_img_bytes(tile))
            if is_save:
                tile.save(os.path.join("TILE-%s.png" % idx))
            idx += 1

    return tiles


def _convert_to_png(img):
    fileobj = io.BytesIO()
    img.save(fileobj, format='png')
    return Image.open(fileobj)


def split_with_margin(img_path: Optional[str],
                      img_bytes: Optional[bytes],
                      height: int,
                      width: int,
                      margin_left: int,
                      margin_top: int,
                      extension='png',
                      is_bw=False,
                      is_save=False) -> List[bytes]:
    """
    Extended version of 'split' function
    Splits image to several tiles with given width, height and margins
    Outer margins should be 0

    :param img_path: path to image in fs
    :param img_bytes: bytes of downloaded image. Will be used if img_path is None or ''
    :param height: cropped height
    :param width: cropped width
    :param margin_left: margin BETWEEN tiles
    :param margin_top: margin BETWEEN tiles
    :param extension: necessary format to save/convert, 'png' or 'gif'
    :param is_bw: if True - will convert img to b/w img without gray
    :param is_save: save or not
    :return: list of split images as bytes

    """
    if img_path:
        im = Image.open(img_path)
    elif img_bytes:
        img_bytesio = io.BytesIO(img_bytes)
        im = Image.open(img_bytesio)
    else:
        log.log_err('No enough args to split: no img_path, no img_bytes')
        return []

    if is_bw:
        im = im.convert('1')

    x_max, y_max = im.size
    tiles = []  # type: List[bytes]
    idx = 0

    for y in range(0, y_max, height + margin_top):
        for x in range(0, x_max, width + margin_left):
            x_to = x + width
            y_to = y + height
            # handle case with 'white' unused right border margin
            # avoid blank tiles
            if x_to > x_max or y_to > y_max:
                continue
            box = (x, y, x_to, y_to)
            tile = im.crop(box)  # type: Image
            tiles.append(_get_img_bytes(tile, extension))
            if is_save:
                tile.save(os.path.join("TILE-{}.{}".format(idx, extension)))
            idx += 1

    return tiles


def _common_find_position(img_large: Image.Image,
                          imgs_small_to_search: Dict[str, Image.Image],
                          imgs_small_names_to_data: Dict[str, List[int]],
                          imgs_names_to_pos: Dict[str, Tuple[int, int]],
                          total_found: int,
                          total_to_find: int) -> Dict[str, Tuple[int, int]]:
    """subfunction for better code organization"""
    x_max, y_max = img_large.size
    w_small, h_small = imgs_small_to_search[list(imgs_small_to_search.keys())[0]].size

    should_stop = False
    for y in range(0, y_max - h_small):
        if should_stop:
            break
        for x in range(0, x_max - w_small):
            if should_stop:
                break
            box = (x, y, x + w_small, y + h_small)
            cropped = img_large.crop(box)
            for img_name in imgs_small_to_search.keys():
                if list(cropped.getdata()) == imgs_small_names_to_data[img_name]:
                    imgs_names_to_pos[img_name] = (x, y)
                    # speed optimization
                    imgs_small_to_search.pop(img_name)
                    total_found += 1
                    if total_to_find == total_found:
                        should_stop = True
                    break

    return imgs_names_to_pos


def find_positions(img_large_path: Optional[str] = None,
                   img_large_bytes: Optional[bytes] = None,
                   imgs_small_names_to_paths: Dict[Any, str] = None,
                   is_bw=True,
                   is_ordered_search=False) -> Tuple[Dict[str, Tuple[int, int]], Tuple[int, int]]:
    """
    Algorithm:
        for each x_position, y_position in img_large:
            if img_small == crop_img_large_to_img_small_in_position:
                imgs[img_name] = x_position, y_position

    With speed optimizations:
        compare each imgs_small_to_search with each img_large.crop() at each iteration
        caches:
            imgs_small_names_to_data
            total_found
            pop found img from imgs_small_to_search

    :param imgs_small_names_to_paths: dict{img_name: img_path}
    :param is_ordered_search: for optimization purposes.
        If True, the func starts to search next img_name only if found previous.
        Useful for digits if img_name == digit
        (they should be ordered in tiles, check bnp_paribas)
    :returns:
        Positions on img_large where found matched block with img_small
        and size of img_large
        {img_small_name: (pos_x, pos_y)}, (img_large_size_x, img_large_size_y))
    """
    if not imgs_small_names_to_paths:
        imgs_small_names_to_paths = {}
    if img_large_path:
        img_large = Image.open(img_large_path)
    elif img_large_bytes:
        img_large_bytesio = io.BytesIO(img_large_bytes)
        img_large = Image.open(img_large_bytesio)
    else:
        log.log_err('No enough args to find: no img_large_path, no img_large_bytes')
        return {}, (0, 0)

    imgs_small = {img_name: Image.open(img_path)
                  for img_name, img_path
                  in imgs_small_names_to_paths.items()}

    if is_bw:
        img_large = img_large.convert('1')
        imgs_small = {img_path: img.convert('1') for img_path, img in imgs_small.items()}

    # defaults
    imgs_names_to_pos = {img_name: (-1, -1)
                         for img_name
                         in imgs_small_names_to_paths.keys()}  # type: Dict[str, Tuple[int, int]]

    # for speed optimization - cache img data
    imgs_small_names_to_data = {img_name: list(img.getdata())
                                for img_name, img
                                in imgs_small.items()}

    imgs_small_to_search = imgs_small.copy()
    total_found = 0
    total_to_find = len(imgs_small)
    # / for speed optimization
    if not is_ordered_search:
        # common search
        imgs_names_to_pos = _common_find_position(
            img_large,
            imgs_small_to_search,
            imgs_small_names_to_data,
            imgs_names_to_pos,
            total_found,
            total_to_find
        )
    else:
        # Additional optimization (up to 4x to common search)
        # only if ordered_search
        # that means that we expect to find ordered imgs_small in same ordering
        # as we iterate boxes over img_large
        img_small_names_ordered = sorted(list(imgs_small.keys()))
        search_for_img_name_ix_if_ordered_search = 0
        img_name = img_small_names_ordered[search_for_img_name_ix_if_ordered_search]
        img_data = imgs_small_names_to_data[img_name]
        x_max, y_max = img_large.size
        w_small, h_small = imgs_small[0].size
        should_stop = False
        for y in range(0, y_max - h_small):
            if should_stop:
                break
            for x in range(0, x_max - w_small):
                box = (x, y, x + w_small, y + h_small)
                cropped = img_large.crop(box)
                # additionally optimized search for ordered search
                if list(cropped.getdata()) == img_data:
                    imgs_names_to_pos[img_name] = (x, y)
                    # common speed optimization
                    imgs_small_to_search.pop(img_name)
                    total_found += 1
                    if total_to_find == total_found:
                        should_stop = True
                        break
                    # next item
                    search_for_img_name_ix_if_ordered_search += 1
                    img_name = img_small_names_ordered[search_for_img_name_ix_if_ordered_search]
                    img_data = imgs_small_names_to_data[img_name]
        else:
            # bad news: search loop not interrupted. need to continue as common search for the rest
            print('Found only up to {} in ordered search. Continue with unordered'.format(
                search_for_img_name_ix_if_ordered_search
            ))
            imgs_names_to_pos = _common_find_position(
                img_large,
                imgs_small_to_search,
                imgs_small_names_to_data,
                imgs_names_to_pos,
                total_found,
                total_to_find
            )

    return imgs_names_to_pos, img_large.size


def find_tiles(img_large_path: Optional[str] = None,
               img_large_bytes: Optional[bytes] = None,
               img_small_names_to_paths: Optional[Dict[Any, str]] = None,
               tiles_x: int = 0,
               tiles_y: int = 0,
               is_bw=True,
               is_ordered_search=False) -> Tuple[Dict[Any, Tuple[int, int]], bool]:
    """Searches img_small position in tiles
    when img_small has 'float' position inside a tile.
    Provides it for all imgs in img_small_names_to_paths.

    Note: size(img_small) should be < size(tile) for correct search
    Used by bnp_paribas

    :param img_small_names_to_paths: dict {img_name: img_path}
    :returns:
        {img_name: (tile_pos_x, tile_pos_y), ...}, is_success
        Note: pos index starts from 0
    """

    imgs_names_to_pos, (size_x, size_y) = find_positions(
        img_large_path=img_large_path,
        img_large_bytes=img_large_bytes,
        imgs_small_names_to_paths=img_small_names_to_paths,
        is_bw=is_bw,
        is_ordered_search=is_ordered_search
    )

    imgs_names_to_tiles = {}  # type: Dict[Any, Tuple[int, int]]

    for img_name, (pos_x, pos_y) in imgs_names_to_pos.items():

        if (pos_x, pos_y) == (-1, -1):
            return {}, False

        tile_step_x = size_x / tiles_x
        tile_step_y = size_y / tiles_y

        tile_x = int(pos_x // tile_step_x)
        tile_y = int(pos_y // tile_step_y)
        imgs_names_to_tiles[img_name] = (tile_x, tile_y)

    return imgs_names_to_tiles, True
