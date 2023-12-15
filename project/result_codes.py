"""
result_codes defines the codes which the scraping process returns

Code types:
0. Ok
1. wrong credentials (This means that the Access has been locked)
2. Service unavailable. This means that the finantial entity web is down
3. Scraping error. This means that the scraping process is wrong

Text descriptions can be extended with useful information

DB table: _TesoraliaCustomerFinanialEntityAccess
SP: CustomerFinancialEntityAccessWithCode


some codes marked as 'used' and some are not
"""

__version__ = '1.10.0'
__changelog__ = """
1.10.0 2023.07.31
added ERR_NOT_LOGGED_IN_DETECTED_REASON_DOUBLE_AUTH_WITH_DEACTIVATION result code
1.9.0 2023.07.28
fixed description for ERR_LAST_MOVEMENT_SAVED_NOT_IN_SCRAPED_MOVEMENTS 
1.8.0 2023.07.13
resultCodes synchronized with AccountsStatus ids changes
1.7.0 2023.05.16
added ERR_NOT_LOGGED_IN_DETECTED_REASON_PASSWORD_CHANGE result code
resultCodes synchronized with AccessStatus ids changes
1.6.0
added ERR_NOT_LOGGED_IN_DETECTED_REASON_EXPIRED_USER result code
1.5.0
added ERR_BLOCKED_USER result code
1.4.1
comments for account-level statuses
1.4.0
more account-level result codes
also see commit FEW_MOVEMENTS_REACHED_DATE_LIMIT
1.3.0
account-level result codes
fmt
1.2.0
WRN_N43_DOWNLOAD_IS_NOT_ACTIVATED
1.1.0
ERR_N43_DOWNLOAD_IS_NOT_ACTIVATED
"""

# todo: use unused codes to improve err logging

from project.custom_types import ResultCode

# NOTE: NEED TO USE CODE TYPE STR BECAUSE IT'S THE TYPE OF THE DB FIELD TO AVOID UNCLEAR CONVERSIONS

IN_PROGRESS = ResultCode('1', 'IN_PROGRESS')  # used
SUCCESS = ResultCode('0', 'SUCCESS')  # used

# The scraping process was finished successfully
# but there were warnings / weak errors during the scraping process
SUCCESS_WITH_WEAK_ERRORS = ResultCode('0', 'SUCCESS_WITH_WEAK_ERRORS')

# ERRORS

# Not logged in
ERR_WRONG_CREDENTIALS = ResultCode('2', 'ERR_WRONG_CREDENTIALS')  # used
ERR_NOT_LOGGED_IN_UNKNOWN_REASON = ResultCode('8', 'ERR_NOT_LOGGED_IN_UNKNOWN_REASON')  # used
ERR_NOT_LOGGED_IN_DETECTED_REASON = ResultCode('7', 'ERR_NOT_LOGGED_IN_DETECTED_REASON')  # used
ERR_NOT_LOGGED_IN_DETECTED_REASON_DOUBLE_AUTH = ResultCode(
    '3',
    'ERR_NOT_LOGGED_IN_DETECTED_REASON: DOUBLE AUTH REQUIRED'
)  # used
ERR_NOT_LOGGED_IN_DETECTED_REASON_DOUBLE_AUTH_WITH_DEACTIVATION = ResultCode(
    '15',
    'ERR_NOT_LOGGED_IN_DETECTED_REASON: 2FA WITH DEACTIVATION'
)
ERR_NOT_LOGGED_IN_DETECTED_REASON_EXPIRED_USER = ResultCode(
    '6',
    'ERR_NOT_LOGGED_IN_DETECTED_REASON: EXPIRED USER'
)  # used
ERR_NOT_LOGGED_IN_DETECTED_REASON_PASSWORD_CHANGE = ResultCode(
    '4',
    'ERR_NOT_LOGGED_IN_DETECTED_REASON: PASSWORD CHANGE'
)  # used
ERR_BLOCKED_USER = ResultCode('5', 'ERR_BLOCKED_USER')  # used

# Connection errors
ERR_CONNECTION_REFUSED = ResultCode('2', 'ERR_CONNECTION_REFUSED')
ERR_PROXY_DOWN = ResultCode('2', 'ERR_PROXY_DOWN')
ERR_WEBSITE_DOWN = ResultCode('2', 'ERR_WEBSITE_DOWN')
ERR_ANOTHER_CONNECTION_ERROR = ('2', 'ERR_ANOTHER_CONNECTION_ERROR')

# Parsing error (new layout)
ERR_PARSING_ERROR = ResultCode('3', 'ERR_PARSING_ERROR')
ERR_UNEXPECTED_RESPONSE = ResultCode('3', 'ERR_UNEXPECTED_RESPONSE')

# Common
ERR_COMMON_SCRAPING_ERROR = ResultCode('10', 'ERR_COMMON_SCRAPING_ERROR')  # used

# Raised exception
ERR_UNHANDLED_EXCEPTION = ResultCode('9', 'ERR_UNHANDLED_EXCEPTION')  # used

# Collisions
ERR_EQUAL_ACCESS_COLLISION = ResultCode('11', 'ERR_EQUAL_ACCESS_UNRESOLVED_COLLISION')  # used

# If fin entity informs about it (Ruralvia, IberCaja)
WRN_N43_DOWNLOAD_IS_NOT_ACTIVATED = ResultCode('12', 'WRN_N43_DOWNLOAD_IS_NOT_ACTIVATED')

# Account-level

# Changed movement in the past, maps to 'no matching movements to fix from'.
# To fix it, must find the point where saved and web movements are the same and then re-scrape.
ERR_BALANCE_NO_PIVOT_MOVEMENT = ResultCode('1', 'ERR_BALANCE_NO_PIVOT_MOVEMENT')

# Scraped less than saved (0 or more, but less than saved), and the account balance has been changed.
# One of reasons: disabled account on bank-side where movements are not available anymore,
# but the balance has been changed between scraping jobs.
# In some other cases it will be replaced to 'ERR_BALANCE_FEW_MOVEMENTS_HISTORICAL_DATE_LIMIT'
# Another reason: temporary scraping problems, usually disappear on re-scraping.
ERR_BALANCE_FEW_MOVEMENTS = ResultCode('2', 'ERR_BALANCE_FEW_MOVEMENTS')

# Same as ERR_BALANCE_FEW_MOVEMENTS, but also data_from == min_allowed_date_from,
# this means that the last saved movement is older than 90 days (or custom limit)
ERR_BALANCE_FEW_MOVEMENTS_HISTORICAL_DATE_LIMIT = ResultCode('19', 'ERR_BALANCE_FEW_MOVEMENTS_HISTORICAL_DATE_LIMIT')

# Scraping problem: the scraper wasn't able to extract consistent movements (where next_temp_balance != prev_temp_balance + movement_amount)
# Usually indicates about broken pagination or some corner cases, should be redirected to me
ERR_BALANCE_INCONSISTENT_MOVEMENTS = ResultCode('3', 'ERR_BALANCE_INCONSISTENT_MOVEMENTS')

# Rare case.
# It appears when _TesoraliaAccounts.Balance != last of _TesoraliaStatements.TempBalance
# Appears on hard interruption, maybe on duplicated accounts, dirty manual manipulations or some uncoverered cases on bank side with incative accounts.
# This usually then raises 'EXUCUTION FLOW COLLISION' when the scraper can't rollback account balances.
# 1st step: you can fill _TesoraliaAccounts.Balance from last of _TesoraliaStatements.TempBalance and then re-scrape, usually it's enough to fix it.
# If it repeats, then inform me.
ERR_BALANCE_UNALIGNED = ResultCode('4', 'ERR_BALANCE_UNALIGNED')

# These two is direct mapping from some transitional error messages, I added them to keep the things consistent, they shouldn't happen with the current scraping configuration.
# In any case, redirect them to me.
ERR_BALANCE_BAD_DB_DATA = ResultCode('5', 'ERR_BALANCE_BAD_DB_DATA')  # back compat, shouldn't happen
ERR_BALANCE_SAVED_UNFIXED = ResultCode('6', 'ERR_BALANCE_SAVED_UNFIXED')  # back compat, shouldn't happen

# These indicate about account-level scraping problems.
# Some of them are floating errors and may disappear on re-scraping.
# If they are repeating, then the scraper should be improved to avoid such problems.
# In some cases ERR_CANT_SWITCH_TO_ACCOUNT, ERR_CANT_SWITCH_TO_CONTRACT tells that the account is inactive.
# So, these cases better should be confirmed manually and then you can decide what to do with related accounts
ERR_CANT_SWITCH_TO_CONTRACT = ResultCode('7', 'ERR_CANT_SWITCH_TO_CONTRACT')
ERR_CANT_SWITCH_TO_ACCOUNT = ResultCode('8', 'ERR_CANT_SWITCH_TO_ACCOUNT')
ERR_CANT_LOGIN_CONCURRENTLY = ResultCode('9', 'ERR_CANT_LOGIN_CONCURRENTLY')

# Account scraping was interrupted due to some account-level conditions.
# Rare thing, only 2 scrapers use it (Cajamar, BancoMontepio) and it tells that the scraper detected that it won't be able to extract all movements properly.
# Only logs can tell the exact reason (last account error), for now, in both cases the reason is the bank-side restricted pagination for many movements per date.
# Let's see when It happens again, can be solved by skipping the date when the problem appeared, but some movements can be lost.
# Another option: some magic with ASC or DESC filter options. I did t last time.
# But again, it's a rare case
ERR_BREAKING_CONDITIONS = ResultCode('10', 'ERR_BREAKING_CONDITIONS')

# That's it, account-level 2FA.
# A case for Ruralvia-based scrapers.
# But don't mess it with 2FA appearing with date_from (or -f) older than 90 days (as I told, it shouldn't happen for regular scraping with proper configuration)
# This case is permanent and doesn't relate to date_from, 2FA appears each time when anyone tries to open account movements (or even balance).
# Usually it indicates that the account is not accessible for the scraper.
# 2 options:
# - deactivate account on DB level
# - ask the customer do remove this extra restriction, to alow access to the account
ERR_ACCOUNT_DOUBLE_AUTH = ResultCode('11', 'ERR_ACCOUNT_DOUBLE_AUTH')

# Detected disabled account, no movements allowed.
# Should be confirmed manually and then the account should be deactivated in DB.
ERR_DISABLED_ACCOUNT = ResultCode('12', 'ERR_DISABLED_ACCOUNT')  # on bank level

# DB err, can appear only when some critical problems occur with DB.
# Should be fixed ASAP
ERR_CANT_INSERT_MOVEMENTS_DB_ERR = ResultCode('13', 'ERR_CANT_INSERT_MOVEMENTS_DB_ERR')

# Info message, related to the new feature 'scrape only specific accounts' (Sabadell).
# In this case skipped accounts will be marked this way.
SKIPPED_EXPLICITLY = ResultCode('14', 'SKIPPED_EXPLICITLY')  # if not in 'process_only_accounts' (Sabadell)

# This should be a temporary state for accounts
# when 'state_reset' tool resets 'scraping in progress' state by timing.
# As the tool doesn't interrupt the real scraping process (and only useful for web portal state representation),
# then, at the end of scraping job, the scraper changes this status to SUCCESS or any of error/wrn statuses.
# But, it is a permanent state for accounts totally unavailable on the website but
# existing in DB with Active=1. Those accounts should be marked as inactive (after confirmation)
WRN_STATE_RESET = ResultCode('15', 'WRN_STATE_RESET')

# Scraped less than saved, but balance is the same
WRN_FEW_MOVEMENTS = ResultCode('20', 'WRN_FEW_MOVEMENTS')

# Scraped less than saved, balance is the same, date_from == min_allowed_date_from
# this means last saved movement older than 90 days (or custom limit)
WRN_FEW_MOVEMENTS_HISTORICAL_DATE_LIMIT = ResultCode('18', 'WRN_FEW_MOVEMENTS_HISTORICAL_DATE_LIMIT')

# Last movement saved is not included in scraped movements.
# To fix it must find the point where saved and web movements are the same and then re-scrape.
# If the previous point cannot be found you can force account to be updated with FORCE_UPDATE_MOVEMENTS_ACCOUNTS Example:
# FORCE_UPDATE_MOVEMENTS_ACCOUNTS=<fin_ent_account_id_1>,<fin_ent_account_id_2>.' python main_launcher.py -a access_id_1,acces_id_2
ERR_LAST_MOVEMENT_SAVED_NOT_IN_SCRAPED_MOVEMENTS = ResultCode('24', 'ERR_LAST_MOVEMENT_SAVED_NOT_IN_SCRAPED_MOVEMENTS')

