#! any
# coding: utf-8

"""
Python-style pseudo-code
You can wrap this functions with classes if necessary
You can divide these functions to several during development to build more clean code
"""

__version__ = '1.0'

# CONSTANTS

STATUS_RESULT_FAILED = False    # necessary result is not reached
STATUS_RESULT_SUCCESS = True    # got necessary result

# MAIN FUNCTIONS

def instantScrapingGetScrapedData(req, resp):
    """
    This function returns new scraped data (between this and previous call) while scraping is in progress

    """

    # validate user and get id from http request
    customerId = getCustomerIdFromReqSession(req)
    if not customerId:
        return resp(HttpUnauthorizedErrorCode,
                    {'data': None,
                     'status': STATUS_RESULT_FAILED,
                     'meta': {'code': 401, 'system_msg': 'Wrong credentials'}})

    # get customer object (ORM or struct or tuple or similar) with access to all fields
    customer = getCustomerFields(customerId)

    # DB queries

    # get all data which hasn't been sent before
    accounts = getDBAccountsWhereFlagSentIsFalse(customerId)  # to display balances
    movements = getDBMovementsWhereFlagSentIsFalse(customerId)

    # set flag 'sent' for retrieved data
    # Note: need additional field 'InstantlySent' (bool, default=False) for accounts and movements to use with this function
    # Don't do this field available for the scraper by default (don't include in stored procedures and table types)
    # Because these fields for server-side usage only
    # Update these 'InstantlySent' fields and filter by them only from 'instant-scraping-related' functions
    setDBAccountsFlagSentToTrue(accounts)
    setDBMovementsFlagSentToTrue(movements)

    # the scraping is finished or not
    isScrapingFinished = not customer.ScrapingInProgress
    system_msg = 'The scraping is finished' if isScrapingFinished else 'Scraping is in progress'

    return {'data': {'accounts': accounts,
                     'movements': movements,
                     'isScrapingFinished': isScrapingFinished,},
            'status': STATUS_RESULT_SUCCESS,
            'meta': {'code': 200, 'system_msg': system_msg}}

