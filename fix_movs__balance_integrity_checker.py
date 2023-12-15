import csv
import datetime

from concurrent import futures

from custom_libs.db.db_funcs import process_query
from custom_libs import date_funcs
from project.custom_types import MovementScraped

ts = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')

PASSED_PATH = 'logs/balance_integrity_passed_accounts__{}.csv'.format(ts)
FAILED_PATH = 'logs/balance_integrity_failed_accounts__{}.csv'.format(ts)


def _mov_scraped_by_dt_format(mov_dict, datetime_convert_func) -> MovementScraped:
    movement_scraped = MovementScraped(
        Amount=float(mov_dict['Amount']),  # from Decimal
        TempBalance=float(mov_dict['TempBalance']),  # from Decimal
        OperationalDate=datetime_convert_func(mov_dict['OperationalDate']),
        ValueDate=datetime_convert_func(mov_dict['ValueDate']),
        StatementDescription=mov_dict['StatementDescription'],
        StatementExtendedDescription=mov_dict['StatementExtendedDescription'],
        OperationalDatePosition=mov_dict['OperationalDatePosition'],
        KeyValue=(mov_dict['KeyValue'] or '').strip()
    )

    return movement_scraped


def delete_and_recreate_output_files():
    for path in [FAILED_PATH, PASSED_PATH]:
        with open(path, 'w') as f:
            w = csv.writer(f)
            w.writerow([
                'AccountId',
                'CustomerId',
                'FinEntAccountId',
                'AccessId',
                'AccessUrl',
                'Msg'
            ])


def save_result(acc, msg, path):
    with open(path, 'a') as f:
        w = csv.writer(f)
        w.writerow(
            [
                acc['Id'],
                acc['CustomerId'],
                str(acc['FinancialEntityAccountId']),
                acc['accessId'],
                acc['accessUrl'],
                msg
            ]
        )
        return True


def _process_account(acc, index, accs_to_check_len):
    acc_id = acc['Id']

    # Extract all movements
    q_movs = """
    SELECT *
    FROM dbo._TesoraliaStatements
    WHERE 
        AccountId = {account_id}
    ORDER BY Id ASC;
    """.format(
        account_id=acc_id
    )

    movs = process_query(q_movs)

    # Balance of last movement should be equals to account balance
    if movs and movs[-1]['TempBalance'] != acc['Balance']:
        msg = 'FAILED'

        msg_export = ('FAILED: DIFFERENT BALANCES: ACC BALANCE {} IS NOT EQUAL TO {}'.format(
            acc['Balance'],
            movs[-1]
        ))

        save_result(acc, msg_export, FAILED_PATH)

        print('Process #{}/{}: {} ({}): {}'.format(
            index + 1,
            accs_to_check_len,
            acc['Id'],
            acc['FinancialEntityAccountId'],
            msg
        ))

        return

    # Check consistency of all movements
    prev_mov_scraped = None  # type: MovementScraped
    # Check all movements
    for mov in movs:

        mov_scraped = _mov_scraped_by_dt_format(
            mov,
            date_funcs.convert_dt_to_scraper_date_type3
        )  # date fmt 20170130

        if not prev_mov_scraped:
            prev_mov_scraped = mov_scraped
            continue

        temp_balance_calc = round(prev_mov_scraped.TempBalance + mov_scraped.Amount, 2)
        if temp_balance_calc == mov_scraped.TempBalance:
            prev_mov_scraped = mov_scraped
            continue
        else:
            msg = 'FAILED'

            msg_export = ('FAILED: INCONSISTENT MOVEMENTS:  {}  IS NOT AFTER  {}'.format(
                mov_scraped,
                prev_mov_scraped
            ))

            save_result(acc, msg_export, FAILED_PATH)
            break
    else:
        msg = 'PASSED'
        save_result(acc, msg, PASSED_PATH)

    print('Process #{}/{}: {} ({}): {}'.format(
        index + 1,
        accs_to_check_len,
        acc['Id'],
        acc['FinancialEntityAccountId'],
        msg
    ))


def check_balance_integrity_for_all_movements():
    """
    We expect movements in ascending ordering by id
    """

    # passed_accounts_ids = set(_read_list_accounts())
    delete_and_recreate_output_files()

    q_all_accounts = """
        SELECT Id, CustomerId, FinancialEntityAccountId, Balance, t.accessId, t.accessUrl
        FROM _TesoraliaAccounts
        LEFT JOIN (
          SELECT accesosClienteId as accessId, accesos_AccEntidades.accessUrl as accessUrl
          FROM accesos_AccClientes
          LEFT JOIN accesos_AccEntidades on accesos_AccClientes.accesoId = accesos_AccEntidades.accesoId
        ) as t
        ON _TesoraliaAccounts.CustomerFinancialEntityAccessId = t.accessId
    """

    # [{'Id', 'CustomerId', 'FinancialEntityAccountId', 'accessId', 'accessUrl'}, ...]
    all_accounts = process_query(q_all_accounts)

    accs_to_check_len = len(all_accounts)

    # Process each account

    # for i, acc in enumerate(all_accounts):
    #     _process_account(acc, i, accs_to_check_len)

    with futures.ThreadPoolExecutor(max_workers=12) as executor:
        futures_dict = {
            executor.submit(_process_account, acc, i, accs_to_check_len): acc
            for i, acc in enumerate(all_accounts)
        }
        for future in futures.as_completed(futures_dict):
            future_id = futures_dict[future]
            try:
                future.result()
            except Exception as exc:
                print('EXCEPTION IN THE FUTURE: {}: {}'.format(future_id,  exc))


if __name__ == '__main__':
    print('START')
    start = datetime.datetime.now()
    check_balance_integrity_for_all_movements()
    finish = datetime.datetime.now()
    print('DONE in {}'.format(finish - start))
    print('Check the output files for details')
