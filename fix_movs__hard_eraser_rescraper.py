"""Deletes all movements of broken account
And re-scrape necessary fin ent accesses again

Uses current DB from project.settings (check IS_PRODUCTION_DB)

Expects args: list of ids of accounts to fix
Non-int arguments will be filtered

Example:
-------
`$ cut logs/balance_integrity_failed_accounts.csv -d, -f1 | xargs python movements_hard_fixer.py`

This command will extract first column from balance_integrity_failed_accounts.csv
and will feed its output as list to the movements_hard_fixer.py


Helpers
-------

Detect which accounts were processed 100% (with corresponding AccountId)
and probably not processed (without corresponding AccountId)
```
SELECT Id
FROM _TesoraliaAccounts
LEFT JOIN
(
  SELECT AccountId FROM _TesoraliaStatements
  WHERE AccountId IN (
    2096   <---------------- put list here
    ,2095
    ,2097
    ,2080
  )
  GROUP BY AccountId
) as t ON _TesoraliaAccounts.Id = t.AccountId
WHERE Id IN (
    2096   <---------------- same list
    ,2095
    ,2097
    ,2080
)
```

"""

import argparse
import datetime
import subprocess
import time
from typing import List

from custom_libs.db.db_funcs import process_query
from project import settings


def _toint(text):
    try:
        return int(text)
    except:
        return


def _get_accesses(accounts_ids: List[str]):
    """
    :return: [{'CustomerId', 'accessId'}, ...]
    """
    q = """
        SELECT _TesoraliaAccounts.CustomerId, t.accessId
        FROM _TesoraliaAccounts
        INNER JOIN (
          SELECT accesosClienteId as accessId
          FROM accesos_AccClientes
          INNER JOIN accesos_AccEntidades on accesos_AccClientes.accesoId = accesos_AccEntidades.accesoId
        ) as t
        ON _TesoraliaAccounts.CustomerFinancialEntityAccessId = t.accessId
        WHERE _TesoraliaAccounts.Id IN ({})
        GROUP BY _TesoraliaAccounts.CustomerId ,t.accessId
    """.format(','.join(accounts_ids))

    accesses = process_query(q)
    return accesses


def _delete_movements(accounts_ids: List[str]):
    q = """DELETE _TesoraliaStatements WHERE AccountId IN ({})""".format(','.join(accounts_ids))
    process_query(q)


def _rescrape_movements(customer_id: int, access_id: int):
    cmd = 'python3 main_launcher.py -u {} -a {}'.format(customer_id, access_id)
    # async run
    # result = subprocess.Popen(cmd, shell=True)

    # synced run
    result = subprocess.run(cmd, shell=True)
    return result


def delete_movements_and_scrape_again(accounts_ids: List[str]):
    accesses = _get_accesses(accounts_ids)
    print('Need to re-scrape accesses:')
    for access in accesses:
        print(access)

    print('Delete movements')
    _delete_movements(accounts_ids)

    for access in accesses:
        customer_id = access['CustomerId']
        access_id = access['accessId']
        print('Scrape customer {} access {}'.format(customer_id, access_id))
        result = _rescrape_movements(customer_id, access_id)
        print(result)


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

    # Final countdown
    print("!!! DON'T INTERRUPT THE PROCESS WHEN IT STARTS !!!")
    for i in range(3, 0, -1):
        time.sleep(1)
        print('{}...'.format(i))
    time.sleep(1)

    print('***** MOVEMENTS HARD FIXER: START *****')
    start = datetime.datetime.now()
    delete_movements_and_scrape_again(accounts_ids)
    finish = datetime.datetime.now()
    print('**** MOVEMENTS HARD FIXER: DONE in {} *****'.format(finish - start))
