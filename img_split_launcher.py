from custom_libs.img_funcs import split_with_margin


if __name__ == '__main__':
    tiles = split_with_margin(
        img_path='/home/vladimirb/_upwork/_upwork_raul/Gestor.gif',
        img_bytes=None,
        height=23,
        width=23,
        margin_left=5,
        margin_top=5,
        is_save=True
    )
    pass