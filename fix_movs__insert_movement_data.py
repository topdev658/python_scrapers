"""Insert new movement on DB without scraping

Expects args: data movement
(operational_date, value_data, amount, temp_balance, operational_date_position, account_id, description)

Example:
-------
`$ python3 fix_movs__insert_movement_data.py 20/03/2023 20/03/2023 33.06 110000.00 1 17055 REMESA TPV 0

***** START *****
Processing movement data
Getting key value with the movement data passed as arguments
Keyvalue = dc6a4b44bf85021e21bb2dcade494c3ddddaafcb100d3cc891daaba7b0007722
Start queue thread
DB query from queue afe21203-6509-4acf-bfe1-4bb814322a82: "-- add_new_movement for account 17055..."
To update initialId: 0
All movements filled initialId: DONE
**** FINISH INSERT in 0:00:25.784325 *****


This command will insert the movement data passed on DB _TesoraliaStatements
and will update the account on _TesoraliaAccounts (TempBalance and update dates)

"""

import argparse
import datetime
import hashlib
import sys
import traceback
from typing import List

import fix_movs__fill_initialid_for_all_movs
from custom_libs import date_funcs
from collections import OrderedDict

from custom_libs.db import queue_simple
from custom_libs.db.db_funcs import process_query
from project import settings


def get_keyvalue_from_haslib(movement_data: OrderedDict) -> str:
    print('Getting key value with the movement data passed as arguments')
    try:
        hashbase = '{}{}{}{}{}'.format(
            movement_data['operational_date'],
            movement_data['value_date'],
            movement_data['amount'],
            movement_data['temp_balance'],
            movement_data['operational_date_position']
        )
        # print('Movement data: {} {} {} {} {} ').format(
        #     movement_data['operational_date'],
        #     movement_data['value_date'],
        #     movement_data['amount'],
        #     movement_data['temp_balance'],
        #     movement_data['operational_date_position']
        # )
        key_value = hashlib.sha256(hashbase.encode()).hexdigest().strip()

        return key_value
    except:
        print("Can\'t get keyvalue. Please check the process")
        exit()


def parse_movement_data(args: List[str]):
    try:
        print('Processing movement data')
        movement_data = OrderedDict([
            ('operational_date', date_funcs.convert_date_to_db_format(args.movement_data[0])),  # dyn
            ('value_date', date_funcs.convert_date_to_db_format(args.movement_data[1])),
            ('amount', round(float(args.movement_data[2]), 2)),
            ('temp_balance', round(float(args.movement_data[3]), 2)),
            ('operational_date_position', int(args.movement_data[4])),
            ('account_id', int(args.movement_data[5])),
            ('statement_description', ' '.join(args.movement_data[6:])),
        ])

        return movement_data
    except:
        print("Can\'t process movement data. Please, check the arguments")
        exit()


def insert_statement_on_db(movement_data: OrderedDict, keyvalue: str) -> str:
    try:
        q = """
        -- add_new_movement for account {account_id}

        INSERT INTO dbo._TesoraliaStatements (
            OperationalDate,
            ValueDate,
            StatementDescription,
            Amount,
            TempBalance,
            AccountId,
            CreateTimeStamp,
            OperationalDatePosition,
            KeyValue,
            StatementExtendedDescription,
            CurrentCreateTimeStamp,
            BankOffice,
            Payer
        ) VALUES (
            '{operational_date}',
            '{value_date}',
            '{statement_description}',
            {amount},
            {temp_balance},
            {account_id},
            GETUTCDATE(),
            {operational_date_position},
            '{KeyValue}',
            '{statement_description}',
            GETUTCDATE(),
            '',
            ''
        )
        
        UPDATE dbo._TesoraliaAccounts
        SET Balance = {temp_balance},
            UpdateTimeStamp = GETUTCDATE(),
            LastBalancesScrapingStartedTimeStamp = GETUTCDATE(),
            LastBalancesScrapingFinishedTimeStamp = GETUTCDATE(),
            LastMovementsScrapingStartedTimeStamp = GETUTCDATE(),
            LastMovementsScrapingFinishedTimeStamp = GETUTCDATE(),      
            LastSuccessDownload = GETUTCDATE(),
            LastScrapingAttemptFinishedTimeStamp = GETUTCDATE()
        WHERE 
            Id = {account_id}
        """.format(
            **movement_data,
            KeyValue=keyvalue
        )

        process_query(q)
        print('Movement inserted on DB _TesoraliaStatements and updated account on _TesoraliaAccounts:')
        print('QUERY: {}'.format(q))
    except:
        print("Can\'t insert the data. Please check the query")
        exit()


def main():
    movement_data_parsed = parse_movement_data(args)
    keyvalue = get_keyvalue_from_haslib(movement_data_parsed)
    print('Keyvalue = {}'.format(keyvalue))
    insert_statement_on_db(movement_data_parsed, keyvalue)
    fix_movs__fill_initialid_for_all_movs.fill_initialid_for_all()


if __name__ == '__main__':

    if not settings.IS_UPDATE_DB:
        print('SETTINGS ERROR: The scraper will not insert the statement data'
              'The data will be lost. '
              'Check the project settings IS_UPDATE_DB. Abort.')
        exit(1)

    print('IS_PRODUCTION_DB: {}'.format(settings.IS_PRODUCTION_DB))
    print('IS_UPDATE_DB: {}'.format(settings.IS_UPDATE_DB))

    parser = argparse.ArgumentParser()
    parser.add_argument('movement_data', metavar='movement_data', nargs='+',
                        help='The data of the movement that we want to insert in db')

    args = parser.parse_args()

    print('***** START *****')
    start = datetime.datetime.now()
    try:
        main()
    except Exception as exc:
        traceback.print_exc()
        sys.exit(1)
    finally:
        finish = datetime.datetime.now()
        print('**** FINISH INSERT in {} *****'.format(finish - start))
        queue_simple.wait_finishing()
