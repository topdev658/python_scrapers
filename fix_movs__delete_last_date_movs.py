"""Deletes movements OF LAST DATE ONLY of list of accounts

Uses current DB from project.settings (check IS_PRODUCTION_DB)

Expects args: list of ids of accounts to fix
Non-int arguments will be filtered

Example:
-------
`$ cut logs/santander_accounts.csv -d, -f1 | xargs python movements_fixer__delete_last_date_movs.py`

This command will extract first column from santander_accounts.csv
and will feed its output as list to the movements_fixer__delete_last_date_movs.py


Helpers
-------

Select accounts, which belong to specific financial entity
```
SELECT accountsTable.Id, accountsTable.CustomerFinancialEntityAccessId, CustomerId FROM
(
  -- accounts by fin end id
  SELECT Id, CustomerFinancialEntityAccessId, CustomerId
  FROM _TesoraliaAccounts
    INNER JOIN
    (
      -- accesses by fin ent id
      SELECT accesosClienteId
      FROM accesos_AccClientes
      WHERE accesoId = 201 -- <--- set here Santander
    ) AS accessesTable
  ON _TesoraliaAccounts.CustomerFinancialEntityAccessId = accessesTable.accesosClienteId
) AS accountsTable
INNER JOIN _TesoraliaStatements
ON _TesoraliaStatements.AccountId = accountsTable.Id
GROUP BY accountsTable.Id,  accountsTable.CustomerFinancialEntityAccessId, CustomerId
```

"""

import argparse
import datetime
from typing import List, Optional

from custom_libs.db.db_funcs import process_query
from custom_libs import date_funcs
from project import settings


def _toint(text):
    try:
        return int(text)
    except:
        return


def _delete_account_movements(account_id: str, delete_movs_from_date: str):
    q = """
        DELETE _TesoraliaStatements 
        WHERE 
            AccountId={}
            AND OperationalDate >= '{}'
    """.format(
        account_id,
        delete_movs_from_date
    )
    process_query(q)


def _get_last_date(account_id: str) -> Optional[str]:

    q = """
        SELECT TOP 1 OperationalDate 
        FROM dbo._TesoraliaStatements
        WHERE AccountId = {}
        ORDER BY Id DESC;
    """.format(
        account_id
    )

    op_date = process_query(q)
    if not op_date:
        return

    return date_funcs.convert_dt_to_scraper_date_type3(op_date[0]['OperationalDate'])


def delete_movements_of_last_mov_date(accounts_ids: List[str]):

    for account_id in accounts_ids:
        print('{}: process account'.format(account_id))
        movs_last_date = _get_last_date(account_id)
        print('{}: last mov date {}'.format(account_id, movs_last_date))
        if not movs_last_date:
            continue
        _delete_account_movements(account_id, movs_last_date)
        print('{}: deleted movs since last date'.format(account_id))


if __name__ == '__main__':

    if not settings.IS_UPDATE_DB:
        print('SETTINGS ERROR: The scrapers will not update the DB after the movements being deleted. '
              'The data will be lost. '
              'Check the project settings IS_UPDATE_DB. Abort.')
        exit(1)

    print('IS_PRODUCTION_DB: {}'.format(settings.IS_PRODUCTION_DB))
    print('IS_UPDATE_DB: {}'.format(settings.IS_UPDATE_DB))

    parser = argparse.ArgumentParser()
    parser.add_argument('accounts_ids', metavar='account_id', nargs='+',
                        help='Id (or the list of Ids) of account(s) with balance integrity error')

    args = parser.parse_args()

    accounts_ids = [account_id for account_id in args.accounts_ids if _toint(account_id)]  # type: List[str]
    print('Number of accounts to process: {}'.format(len(accounts_ids)))

    print('***** MOVEMENTS FIXER: DELETE LAST DATE MOVEMENTS: START *****')
    start = datetime.datetime.now()
    delete_movements_of_last_mov_date(accounts_ids)
    finish = datetime.datetime.now()
    print('**** MOVEMENTS FIXER: DELETE LAST DATE MOVEMENTS: DONE in {} *****'.format(finish - start))
