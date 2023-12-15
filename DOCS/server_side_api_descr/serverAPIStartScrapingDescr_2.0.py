#! any
# coding: utf-8

"""
Python-style pseudo-code
You can wrap this functions with classes if necessary
You can divide these functions to several during development to build more clean code
"""

__version__ = '2.0'

# Changelog
# 2.0
# some functions were moved to scraping server and removed from previous code
# removed: setDBCustomerScrapingInProgress(customerId)
# removed: setDBScrapingInProgressForAllAccountsInProgressForCustomer(customerId)
# removed: setDBCustomerScrapingNOTInProgress(customerId)
# removed: setDBScrapingInProgressForAllAccountsNOTInProgressForCustomer(customerId)
#
# fixed:
# scrapingServerResponse.json['status'] = STATUS_RESULT_SUCCESS
# -> 
# scrapingServerResponse.json['status'] != STATUS_RESULT_SUCCESS
# 
# 1.0
# init


# CONSTANTS

SCRAPING_SERVER_API_TOKEN = 'some-secret-token'
SCRAPING_SERVER_START_SCRAPING_API_ENDPOINT = 'https://scraping.server.url'

STATUS_RESULT_FAILED = False    # necessary result is not reached
STATUS_RESULT_SUCCESS = True    # got necessary result

# MAIN FUNCTIONS

def instantScrapingStart(req, resp):

    # validate user and get id from http request
    customerId = getCustomerIdFromReqSession(req)
    if not customerId:
        return resp(HttpUnauthorizedErrorCode,
                    {'data': None,          # no data
                     'status': STATUS_RESULT_FAILED,
                     'meta': {'code': 401, 'system_msg': 'Wrong credentials'}})

    # get customer object (ORM or struct or tuple or similar) with access to all fields
    customer = getCustomerFields(customerId)
    # break if the scraping is in progress
    if customer.ScrapingInProgress == True:
        return resp({'data': None,
                     'status': STATUS_RESULT_FAILED,
                     'meta': {'code': 200, 'system_msg': 'The scraping is not started. Already in progress.'}})

    # break if it was scraped recently
    if customer.LastScrapingFinishedTimeStamp > getDateTimeThresholdToStartInstantScraping():
        return resp({'data': None,
                     'status': STATUS_RESULT_FAILED,
                     'meta': {'code': 200, 'system_msg': 'The scraping is not started. It was scraped recently.'}})

    # call scraping server to start scraping
    # of all accounts and financial entities for specific
    # scrapingServerResponse  - http response result
    # JSON data format:
    #  {
    #       'data' : type: List or Dict,     // any valuable data
    #       'status':  type: boolean        // call target is reached or not
    #       'meta': {
    #                'code': type: int,      // soft code, usually similar to http code
    #                'system_msg': string  // some system message in human readable format
    #               }
    #   }
    scrapingServerResponse = httpRequestScrapingServerApi(
        SCRAPING_SERVER_START_SCRAPING_API_ENDPOINT,
        SCRAPING_SERVER_API_TOKEN,
        customerId
    )

    # process scraping server response

    # FAILED 
    if (scrapingServerResponse.httpCode != 200
        # 2.0: bugfix: ==STATUS_RESULT_SUCCESS -> !=STATUS_RESULT_SUCCESS 
        or scrapingServerResponse.json['status'] != STATUS_RESULT_SUCCESS):
        return resp({'data': None,
                     'status': STATUS_RESULT_FAILED,
                     'meta': {'code': 200,
                              'system_msg': 'The scraping is not started. Scraping server returns error code'}})
    # OK
    return resp({'data': None,
                 'status': STATUS_RESULT_SUCCESS,
                 'meta': {'code': 200, 'system_msg': 'The scraping is started'}})

