"""This module provides functions to obtain
all necessary information in the DB after changing the schema

Desn't update KeyValue because there is a risk to operate with different values
from scraper and from DB
"""

import datetime
from concurrent import futures

from custom_libs.db.db_funcs import process_query


def process_account(account_id):
    # Extract movements of last date
    q_last_date_movs = """
    DECLARE @LastOperationalDate DATETIME;

    SELECT TOP 1 @LastOperationalDate = OperationalDate
    FROM dbo._TesoraliaStatements
    WHERE AccountId = {account_id}
    ORDER BY OperationalDate DESC, Id DESC;

    SELECT *
    FROM dbo._TesoraliaStatements
    WHERE 
        AccountId = {account_id}
        AND OperationalDate =  @LastOperationalDate
    ORDER BY Id ASC;
    """.format(
        account_id=account_id
    )
    movements_dicts = process_query(q_last_date_movs)

    if not movements_dicts:
        return '{}: no movements'.format(account_id)

    if all(mov_dict['OperationalDatePosition'] for mov_dict in movements_dicts):
        return '{}: no need to update'.format(account_id)

    # Generate query with updated OperationalDatePosition
    q_mov_data_to_update = ''
    for i, mov_dict in enumerate(movements_dicts):
        operational_date_position = i + 1

        mov_id = mov_dict['Id']
        q_mov_data_to_update += """
        UPDATE dbo._TesoraliaStatements
        SET 
          OperationalDatePosition = {}
        WHERE Id = {};
        """.format(operational_date_position, mov_id)

    # Update DB
    process_query(q_mov_data_to_update)
    return '{}: UPDATED now'.format(account_id)


def set_operational_date_position_for_last_date_movements():
    """Updates only movements of accounts
    If there are no any OperationalDatePosition of the movements of the last date
    """

    # Get all accounts
    q_all_accs = """SELECT Id FROM dbo._TesoraliaAccounts;"""
    accs_dicts = process_query(q_all_accs)  # [{'Id': 1234}, ...]

    # Process each account
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures_dict = {
            executor.submit(process_account, acc_dict['Id']): acc_dict['Id']
            for acc_dict in accs_dicts
        }
        for future in futures.as_completed(futures_dict):
            future_id = futures_dict[future]
            try:
                print(future.result())
            except Exception as exc:
                print('{}: {}'.format(future_id, exc))

    # Serial processing
    # for acc_dict in accs_dicts:
    #     process_account(acc_dict)

    print('All accounts: DONE')
    return True


if __name__ == '__main__':

    print('***** START *****')
    start = datetime.datetime.now()
    set_operational_date_position_for_last_date_movements()
    finish = datetime.datetime.now()
    print('**** DONE in {} *****'.format(finish - start))
