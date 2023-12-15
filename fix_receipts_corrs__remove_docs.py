"""
Deletes correspondence documents from _TesoraliaDocuments table and their related PDFs from Disk.
Uses command line arguments to select (and then delete) documents with AND operator
(i.e. for given "-u 123 -d 01/01/2020" will select by "CustomerId=123 AND DocumentDate='01/01/2020'").
Asks for manual confirmation before deleting.
"""

import argparse
import os
import shutil
import re
import sys
import time
from datetime import datetime
from typing import Optional, List, Union

from custom_libs.db import queue_simple, db_funcs
from custom_libs.db.db_funcs import process_query
from custom_libs.log import log, log_err, prepare_fixer_logging
from project import settings as project_settings
from scrapers._basic_scraper.basic_scraper import BasicScraper

__version__ = '2.1.0'
__changelog__ = """
2.1.0
delete folders after deleting pdfs
2.0.0
renamed from fix_corrs__remove_docs.py
main: log call arguments
call to prepare_fixer_logging in order to have log to file besides console
1.1.0
more confirmations
1.0.0
init
"""


class NullRec:
    """Distinct type for filtering"""

    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        return None

    def __repr__(self):
        return 'NullRec'


def _escape(text: str) -> str:
    return re.sub('''[!=`;'"-]''', '', text.strip())


def _wrap_str(text: str) -> str:
    return db_funcs._str_or_null_for_db(text)


def has_null_rec(els: list) -> bool:
    return any(isinstance(el, NullRec) for el in els)


def str_to_str_or_nullrec(val: str) -> Union[str, NullRec]:
    """Cleans string and converts 'null' to None"""
    val_clean = _escape(val)
    if val_clean == 'null':
        return NullRec()
    return val_clean


def str_to_int_or_nullrec(val: str) -> Union[int, NullRec]:
    """Cleans string and converts 'null' to None or digits to int"""
    val_clean = _escape(val)
    if val_clean == 'null':
        return NullRec()
    return int(val_clean)


def confirm() -> bool:
    inp = input("CONTINUE? (y/N)")
    return inp.lower() == 'y'


def confirm_no_rollback() -> bool:
    inp = input("ATTENTION: you won't be able to rollback it. CONTINUE? (y/N)")
    return inp.lower() == 'y'


def get_access_account_ids(access_id: int) -> List[int]:
    q = "SELECT Id, AccountNo FROM _TesoraliaAccounts WHERE CustomerFinancialEntityAccessId={}".format(
        access_id
    )
    results = process_query(q)
    log('Accounts by CustomerFinancialEntityAccessId: {}'.format(results))
    account_ids = [a['Id'] for a in results]
    return account_ids


def build_where(
        customer_id: Optional[int],
        access_id: Optional[int],
        fin_entity_id: Optional[int],
        account_ids: Optional[List[Union[int, NullRec]]],
        product_ids: Optional[List[Union[str, NullRec]]],
        delete_date: Optional[datetime]) -> str:
    log('*** Building WHERE stmt ***')

    if access_id:
        accounts_ids_by_access = get_access_account_ids(access_id)
        account_ids.extend(accounts_ids_by_access) if account_ids else accounts_ids_by_access

    where_cust = " AND CustomerId = {} ".format(customer_id) if customer_id is not None else ''
    where_date = (" AND DocumentDate = '{}' ".format(delete_date.strftime(project_settings.DB_DATE_FMT))
                  if delete_date is not None else '')
    where_fin_ent = " AND FinancialEntityId = {}".format(fin_entity_id) if fin_entity_id is not None else ''

    where_prods = ''
    if product_ids and has_null_rec(product_ids) and len(product_ids) == 1:
        # only null
        where_prods = " AND ProductId is NULL "
    elif product_ids and not has_null_rec(product_ids):
        # only ids
        where_prods = " AND ProductId in ({}) ".format(
            ",".join([_wrap_str(el) for el in product_ids]).strip(',')
        )
    elif product_ids and has_null_rec(product_ids) and len(product_ids) > 1:
        # ids and null
        where_prods = " AND (ProductId is NULL OR ProductId in ({})) ".format(
            ",".join([_wrap_str(el) for el in product_ids if not isinstance(el, NullRec)]).strip(',')
        )

    where_accounts = ''
    if account_ids and has_null_rec(account_ids) and len(account_ids) == 1:
        # only null
        where_accounts = " AND AccountId is NULL "
    elif account_ids and not has_null_rec(account_ids):
        # only ids
        where_accounts = " AND AccountId in ({}) ".format(
            ",".join([str(el) for el in account_ids]).strip(',')
        )
    elif account_ids and has_null_rec(account_ids) and len(account_ids) > 1:
        # ids and null
        where_accounts = " AND (AccountId is NULL OR AccountId in ({})) ".format(
            ",".join([str(el) for el in account_ids if not isinstance(el, NullRec)]).strip(',')
        )

    where_alltogether = re.sub('^ AND', '', '{}{}{}{}{}'.format(
        where_cust,
        where_fin_ent,
        where_date,
        where_prods,
        where_accounts
    ))

    log('WHERE stmt: {}'.format(where_alltogether))

    return where_alltogether


def delete_files(where_str: str) -> bool:
    log('*** Getting documents to delete ***')
    q = 'SELECT ProductId, Checksum from _TesoraliaDocuments WHERE {};'.format(where_str)
    results = process_query(q)

    folders_product_ids = [(r['ProductId']) for r in results]
    folders_product_ids = list(set(folders_product_ids))

    product_ids_and_checksums = [(r['ProductId'], r['Checksum'].strip()) for r in results]
    checksums = [pc[1] for pc in product_ids_and_checksums]
    log('                  ')
    log('*** Total {} documents to delete: checksums {}'.format(len(checksums), checksums))
    log('                  ')

    if not confirm_no_rollback():
        log("Abort")
        return False

    file_paths_wo_ext = []  # type: List[str]
    for pc in product_ids_and_checksums:
        folder_path = BasicScraper.correspondence_folder_path(pc[0])
        file_path = BasicScraper.correspondence_file_path(
            folder_path=folder_path,
            file_id=pc[1],
            file_extension=''  # 'pdf' or 'zip' will be used then
        )
        file_paths_wo_ext.append(file_path)

    log('*** Deleting files ***')
    for fpath_wo_ext in file_paths_wo_ext:
        for ext in ['pdf', 'zip']:
            fpath = fpath_wo_ext + ext
            if os.path.isfile(fpath):
                os.remove(fpath)
                log('Deleted {}'.format(fpath))
                break
            else:
                log('Not found {}'.format(fpath_wo_ext + '[pdf|zip]'))

    for folder in folders_product_ids:
        folder_path = BasicScraper.correspondence_folder_path(folder)
        if os.path.isdir(folder_path):
            try:
                shutil.rmtree(folder_path, ignore_errors=True)
            except:
                print("The system cannot find the folder specified")

            log('Folder deleted {}'.format(folder_path))
        else:
            log('Not found {}'.format(folder_path))
    return True


def delete_db_entries(where_str: str) -> bool:
    log('*** Deleting DB entries ***')
    q = 'DELETE FROM _TesoraliaDocuments WHERE {};'.format(where_str)
    _res = process_query(q)
    return True


def parse_cmdline_args():
    log(sys.argv[0:])
    parser = argparse.ArgumentParser(
        description=('DESCRIPTION: {}'.format(__doc__))
    )

    parser.add_argument(
        '--user-id',
        '-u',
        help='Delete docs for this CustomerId (user Id). '
             'If not passed: will not be used in filtering operations',
        type=int,
        default=None
    )

    parser.add_argument(
        '--access-id',
        '-a',
        help='Delete docs for this AccessId. '
             'If not passed: will not be used in filtering operations',
        type=int,
        default=None
    )

    parser.add_argument(
        '--product-ids',
        '-p',
        help='Delete docs for this list of ProductId. '
             'Use "," as the delimiter. '
             'Pass "null" to filter by <null>. '
             'If not passed: will not be used in filtering operations',
        type=str,
        default=None
    )

    parser.add_argument(
        '--account-ids',
        help='Delete docs for this list of AccountId. '
             'Use "," as the delimiter. '
             'Pass "null" to filter by <null>. '
             'If not passed: will not be used in filtering operations',
        type=str,
        default=None
    )

    parser.add_argument(
        '--entity-id',
        '-e',
        help='Delete docs for this FinancialEntityId. '
             'If not passed: will not be used in filtering operations',
        type=int,
        default=None
    )

    parser.add_argument(
        '--date',
        '-d',
        help='Delete docs for this DocumentDate in dd/mm/yyyy format. '
             'If not passed: will not be used in filtering operations',
        type=str,
        default=None
    )

    args = parser.parse_args()
    log(args)
    return parser, args



def main():
    try:
        log(sys.argv[0:])
        parser, args = parse_cmdline_args()
        log(args)
        customer_id = args.user_id  # type: Optional[int]
        access_id = args.access_id  # type: Optional[int]
        fin_entity_id = args.entity_id  # type: Optional[int]

        account_ids = ([str_to_int_or_nullrec(v) for v in args.account_ids.split(",")]
                       if args.account_ids else None)  # type: Optional[List[Union[int, NullRec]]]

        product_ids = ([str_to_str_or_nullrec(v) for v in args.product_ids.split(",")]
                       if args.product_ids else None)  # type: Optional[List[Union[str, NullRec]]]

        delete_date = (datetime.strptime(args.date, project_settings.SCRAPER_DATE_FMT)
                       if args.date else None)  # type: Optional[str]

        mandatory_one_of = [
            customer_id,
            access_id,
            fin_entity_id,
            account_ids,
            product_ids,
        ]

        if not any(mandatory_one_of):
            log('\nPLEASE, SPECIFY AT LEAST ONE COMMAND LINE ARGUMENT of -u/-a/-p/-e/--account-ids. '
                  'Abort\n')
            time.sleep(2)
            parser.print_help()
            exit(0)

        where_str = build_where(
            customer_id=customer_id,
            access_id=access_id,
            fin_entity_id=fin_entity_id,
            account_ids=account_ids,
            product_ids=product_ids,
            delete_date=delete_date
        )

        if not confirm():
            log("Abort")
            return

        log("OK, deleting...")

        ok = delete_files(where_str)
        if not ok:
            return
        ok = delete_db_entries(where_str)
        log("*** DELETED ***")
    finally:
        log('==== queue.wait_finishing and close db connection ====')
        queue_simple.wait_finishing()
        # Mostly to allow sentry client send all pending msgs
        time.sleep(1)

if __name__ == '__main__':
    prepare_fixer_logging(os.path.basename(__file__))
    log('IS_DEPLOYED = {}'.format(project_settings.IS_DEPLOYED))
    log('IS_PRODUCTION_DB = {}'.format(project_settings.IS_PRODUCTION_DB))
    main()
