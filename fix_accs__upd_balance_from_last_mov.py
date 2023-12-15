"""This module sets the account balance from the last movement
If there is no last movement, id doesn't perform any changes.
Example:
    python fix_accs__upd_balance_from_last_mov.py -u 173943 --acc-fid "0049 1668 40 2710172398"
"""

import argparse
import sys
import traceback
from typing import Optional

from custom_libs.db import queue_simple
from custom_libs.db.db_connector_for_scraper import DBConnector
from custom_libs.db.db_funcs import _execute_query as process_query
from project.custom_types import MovementSaved


def process_acc(acc_dict: dict, mov_saved: MovementSaved) -> bool:
    print('Last {}'.format(mov_saved))
    print("{}: Id={}: Balance was {:.2f} => will be {}".format(
        acc_dict['FinancialEntityAccountId'],
        acc_dict['Id'],
        acc_dict['Balance'],
        mov_saved.TempBalance
    ))
    q_upd_balance = """
    UPDATE dbo._TesoraliaAccounts
    SET
      Balance = {}
    WHERE Id = {};
    """.format(mov_saved.TempBalance, acc_dict['Id'])
    process_query(q_upd_balance)
    return True


def get_acc(db_customer_id: int, fin_ent_account_id: str) -> dict:
    q_accs = """
    SELECT * FROM dbo._TesoraliaAccounts 
    WHERE CustomerId={}
    AND FinancialEntityAccountId='{}'""".format(
        db_customer_id,
        fin_ent_account_id
    )
    accs_dicts, msg = process_query(q_accs)
    assert len(accs_dicts) == 1
    return accs_dicts[0]


def get_mov(db_connector: DBConnector, fin_ent_acc_id: str) -> Optional[MovementSaved]:
    mov = db_connector.get_last_movement_of_account(fin_ent_acc_id)
    return mov


def parse_cli_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--user-id',
        '-u',
        help='User (customer) Id',
        type=int
    )
    parser.add_argument(
        '--acc-fid',
        help='FinancialEntityAccountId (NOT DB Id!)'
    )

    return parser, parser.parse_args()


def main():
    parser, args = parse_cli_args()
    fin_ent_account_id = args.acc_fid
    db_customer_id = args.user_id
    if not (fin_ent_account_id and db_customer_id):
        parser.print_help()
        exit(1)
    db_connector = DBConnector(db_customer_id, '')  # for mov_saved
    mov_saved = get_mov(db_connector, fin_ent_account_id)
    assert mov_saved
    acc_dict = get_acc(db_customer_id, fin_ent_account_id)
    process_acc(acc_dict, mov_saved)


if __name__ == '__main__':
    print('***** START *****')
    try:
        main()
    except Exception as exc:
        traceback.print_exc()
        sys.exit(1)
    finally:
        queue_simple.wait_finishing()
    print('***** DONE *****')
