"""This module provides functions to obtain
all necessary information in the DB after changing the schema

Desn't update KeyValue because there is a risk to operate with different values
from scraper and from DB

Launch it with or without list of accounts ids
"""

import datetime
import argparse

from custom_libs.db.db_funcs import process_query


def _toint(text):
    try:
        return int(text)
    except:
        return


def process_account(account_id):
    # Extract movements of last date
    q_last_date_movs = """
    SELECT *
    FROM dbo._TesoraliaStatements
    WHERE 
        AccountId = {account_id}
    ORDER BY Id ASC;
    """.format(
        account_id=account_id
    )
    movements_dicts = process_query(q_last_date_movs)

    if not movements_dicts:
        # return
        return '{}: no movements'.format(account_id)

    if all(mov_dict['OperationalDatePosition'] for mov_dict in movements_dicts):
        # return
        return '{}: no need to update'.format(account_id)

    # Generate query with updated OperationalDatePosition
    q_mov_data_to_update = ''
    prev_date = None
    pos = 1
    temp_balance_prev = float('inf')
    for i, mov_dict in enumerate(movements_dicts):
        curr_date = mov_dict['OperationalDate']
        if curr_date != prev_date:
           pos = 1

        operational_date_position_calculated = pos
        operational_date_position_current = mov_dict['OperationalDatePosition']

        temp_balance_calculated = round(temp_balance_prev + float(mov_dict['Amount']), 2)
        temp_balance_current = round(float(mov_dict['TempBalance']), 2)

        if temp_balance_prev != float('inf') and temp_balance_calculated != temp_balance_current:
            return ('{}: mov {}: calculated temp_bal {} != current temp_bal {}. Curr: {}. Prev {}'.format(
                account_id,
                mov_dict['Id'],
                temp_balance_calculated,
                temp_balance_current,
                mov_dict,
                movements_dicts[i - 1]
            ))

        # for next iter
        pos += 1
        prev_date = curr_date
        temp_balance_prev = temp_balance_current

        if operational_date_position_current:
            if operational_date_position_current == operational_date_position_calculated:
                continue

            return ('{}: mov {}: calculated pos {} != current pos {}. Curr: {}. Prev {}'.format(
                account_id,
                mov_dict['Id'],
                operational_date_position_calculated,
                operational_date_position_current,
                mov_dict,
                movements_dicts[i-1]
            ))

        mov_id = mov_dict['Id']
        q_mov_data_to_update += """
        UPDATE dbo._TesoraliaStatements
        SET 
          OperationalDatePosition = {}
        WHERE Id = {};
        """.format(operational_date_position_calculated, mov_id)

    # Update DB
    # queue.add(process_query, q_mov_data_to_update)

    try:
        process_query(q_mov_data_to_update)
    except Exception as exc:
        return '{}: {}'.format(account_id, exc)

    return '{}: UPDATED now'.format(account_id)


def set_operational_date_position_for_last_date_movements(accounts_ids):
    """Updates only movements of accounts
    If there are no any OperationalDatePosition of the movements of the last date
    """

    # Get accounts
    # All
    if not accounts_ids:
        q_all_accs = """SELECT Id FROM dbo._TesoraliaAccounts;"""
    # From the listaccounts_ids
    else:
        q_all_accs = """SELECT Id FROM dbo._TesoraliaAccounts WHERE Id IN ({})""".format(','.join(accounts_ids))

    accs_dicts = process_query(q_all_accs)  # [{'Id': 1234}, ...]

    # Process each account
    # with futures.ThreadPoolExecutor(max_workers=2) as executor:
    #     futures_dict = {
    #         executor.submit(process_account, acc_dict['Id']): acc_dict['Id']
    #         for acc_dict in accs_dicts
    #     }
    #     for future in futures.as_completed(futures_dict):
    #         future_id = futures_dict[future]
    #         try:
    #             result = future.result()
    #             if result:
    #                 print(result)
    #         except Exception as exc:
    #             print('{}: {}'.format(future_id, exc))

    # Serial processing
    for acc_dict in accs_dicts:
        result = process_account(acc_dict['Id'])
        if result:
            print(result)

    print('All accounts: DONE')
    return True


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('accounts_ids', metavar='account_id', nargs='*',
                        help='Id (or the list of Ids) of account(s) with balance integrity error')

    args = parser.parse_args()

    accounts_ids_raw = args.accounts_ids
    if accounts_ids_raw:

        accounts_ids = [account_id for account_id in args.accounts_ids if _toint(account_id)]
    else:
        accounts_ids = []

    print('***** START *****')
    start = datetime.datetime.now()
    set_operational_date_position_for_last_date_movements(accounts_ids)
    finish = datetime.datetime.now()
    print('**** DONE in {} *****'.format(finish - start))
