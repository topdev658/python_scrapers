from custom_libs import img_funcs
from os import path


def find_positions(img_large_path):
    img_small_path_pattern = 'scrapers/bnp_paribas_scraper/saved_images/{}.png'
    imgs_small_names_to_paths = {
        name: path.abspath(img_small_path_pattern.format(name))
        for name in range(10)
    }

    tiles_pos, is_success = img_funcs.find_tiles(
        img_large_path=img_large_path,
        img_small_names_to_paths=imgs_small_names_to_paths,
        tiles_x=6,
        tiles_y=4,
        is_bw=True,
        is_ordered_search=True
    )

    for name, pos in tiles_pos.items():
        print("{}: {}".format(name, pos))


def main():
    img_large_path = 'scrapers/bnp_paribas_scraper/saved_images/generateImg4.png'
    find_positions(path.abspath(img_large_path))


if __name__ == '__main__':
    main()


