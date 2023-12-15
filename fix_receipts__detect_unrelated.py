"""Check all receipts recursively and searches for related movement by KeyValue.
If no movement found for a specific receipts, then it prints its path.
Feed it to `rm` utility to remove orphaned receipts:
# search for orphans
$ time python3 fix_receipts__detect_unrelated > receipts_orphans.txt
# check and modify if need
$ vim receipts_orphans.txt
# remove orphans
$ cat receipts_orphans.txt | xargs rm
"""

import argparse
import os
import sys
import traceback


from custom_libs.db import queue_simple
from custom_libs import extract
from custom_libs.db.db_funcs import _execute_query as process_query


def get_mov_id(mov_kv: str) -> str:
    if not mov_kv:
        return ''

    q_mov_data_to_update = """
    SELECT Id from dbo._TesoraliaStatements
    WHERE KeyValue = '{}';
    """.format(mov_kv)

    try:
        result = process_query(q_mov_data_to_update)
        if result:
            return str(result[0]['Id'])
    except Exception as exc:
        print(exc, file=sys.stderr)
    return ''


def main(receipts_folder_root: str):
    print("Search for receipts recursively in {}".format(receipts_folder_root),
          file=sys.stderr)
    if not os.path.exists(receipts_folder_root):
        print("No folder found. Check the args!", file=sys.stderr)

    # todo check for
    # /mnt/tesoralia/prod/files/receipts/all
    # /mnt/tesoralia/prod/files/receipts/busca.sh
    # /mnt/tesoralia/prod/files/receipts/elcp.sh
    # /mnt/tesoralia/prod/files/receipts/ES0320382823876000212897/doc-0157a954196683b407287a070fad0e4a.pdf
    # /mnt/tesoralia/prod/files/receipts/ES0320382823876000212897/doc-02d75c8533d1e48f52c2965fda6938cb.pdf
    # /mnt/tesoralia/prod/files/receipts/ES0320382823876000212897/doc-036ad932e965b7c8152ee31e9775aa84.pdf
    # /mnt/tesoralia/prod/files/receipts/ES0320382823876000212897/doc-0606f9ce92dfe66379a21acd619e5eb9.pdf
    # /mnt/tesoralia/prod/files/receipts/rep_ES2200810250970001844891_2
    # /mnt/tesoralia/prod/files/receipts/rep_ES2200810250970001844891_ULTIMO
    # /mnt/tesoralia/prod/files/receipts/rep_ULTIMO
    for dirpath, _, fnames in os.walk(receipts_folder_root):  # dirpath, subdirs, fnames
        for fname in fnames:
            mov_kv = extract.re_first_or_blank('receipt-(.*?)[.]pdf', fname)
            if not mov_kv:
                continue
            mov_id = get_mov_id(mov_kv)
            # not found
            if not mov_id:
                # todo filter if got /...doc-2e19b40e96d04c990d4874714f6a8331.pdf - not a receipt
                print(os.path.join(dirpath, fname))  # stdout, feed it then to rm


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--dir',
            '-d',
            help="The (root) directory with receipts",
        )

        args = parser.parse_args()

        receipts_folder = args.dir
        if not receipts_folder:
            print(parser.format_help(), file=sys.stderr)
            sys.exit(1)

        main(os.path.abspath(receipts_folder))

    except Exception as exc:
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)
    finally:
        queue_simple.wait_finishing()
