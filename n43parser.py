"""Parses and prints N43 file"""

import sys

from custom_libs.norma43parser import Norma43Parser, DateFormat


def pp_dict(d: dict):
    [print('\t{}\t{}'.format(k, v)) for k, v in d.items()]


def parse(n43_text: str):
    # SPANISH reads dates in DMY format, for YMD use DateFormat.ENGLISH
    parser = Norma43Parser(DateFormat.ENGLISH)

    n43 = parser.parse(n43_text)
    for acc in n43.accounts:
        print('=== ACCOUNT ===')
        pp_dict(acc.header.__dict__)
        if acc.movement_lines:
            print('--- MOVEMENTS ---')
        for i, mov in enumerate(acc.movement_lines):
            print(i + 1)
            pp_dict(mov.__dict__)
        print()


def parse_file(file_path: str):
    print("Parse {}".format(file_path))
    with open(file_path, 'r') as f:
        n43_content = f.read()
    parse(n43_content)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        print("USAGE: n43parser.py <file_path>")
        sys.exit(1)
    parse_file(file_path)
