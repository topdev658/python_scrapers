# NAMING
* 2FA / DOUBLE AUTH - Two-factor authorization
* OTP - one-time password, one-time token (used for 2FA)
* Environ cookies - the cookies which a website sets after confirmed 2FA
* Receipt - a PDF document attached to a movement from movement list area
* Correspondence - all correspondence from mailbox
* Correspondence document - one correspondence document
* Movement = payment statement
* Access - DB entry with credentials for a fin entity (db accesos_AccClientes)
* Organization = Company = Sub-contract (for multi-contract accesses)
  

# Scraper DB integration

## Initialize DB connector

`self.db_connector = DBConnector(self.db_customer_id, self.db_financial_entity_access_id)`

## Set financial entity inactive if not logged in

`self.db_connector.set_financial_entity_inactive()`

* That means possible wrong credentials. Need to check it manually then

## Update balances

`self.db_connector.balances_upload_mass(accounts_scraped: List[AccountScraped])`

* New accounts will be created automatically
* All account should be from one financial entity (default by design)
* All historical logs entries will be created automatically


## Update movements

`self.db_connector.movements_upload_mass_and_mark_account_as_scrap_finished(account_no: str, movements_scraped: List[MovementScraped])`

* Only new movements will be added (will be checked if exists by all fields)
* All movements should be from one account
* Send explicit `account_no` parameter to handle cases when there are no movements
* After updating the account will be marked as `scraping is finished`
* All historical entries will be created automatically

## Get date_start_from for movements

`self.db_connector.get_last_movements_scraping_finished_date_str_by_fin_ent_acc_id(fin_ent_account_id, account_no)`

* use `fin_ent_account_id` and `account_no` both because `fin_ent_account_id` possible can be not unique (due to short number) and `acount_no` can be empty if wrong iban code, but when we filter using both, we get obviously unique account id
* the function returns min(max(MaxValueDate), max(MaxOperationalDate)) of movements of the account to start scraping from correct date

## Get list of FinancialEntityAccesses to scrape

* it's implemented at `main_launcher` level so you don't have to extract list manually

* at the `db_funcs` level there are:

  *  `get_financial_entity_accesses` to get accesses filtered by time intervals `NECESSARY_INTERVAL_BTW_SUCCESSFUL_SCRAP_OF_FIN_ENT` and `NECESSARY_INTERVAL_BTW_FAILED_SCRAP_OF_FIN_ENT`, which will be called during scraping on demand. This approach allows avoid scraping requests from UI, requested with with too short intervals 
 
  * `get_financial_entity_accesses_all_customers_scraping` to get accesses which additionally filtered by time interval  `NECESSARY_INTERVAL_BTW_SUCCESSFUL_SCRAP_OF_FIN_ENT_ALL_CUSTOMERS_SCRAPING`,  which will be called during scarping of all customers at one time (nightly scraping). This approach allows run the scraping several times per night to try to scrape failed accesses (due to connection issues or if the site is down) without touching of successfully scraped accesses
  
  * FinEntAcc scraping still in progress - it will be excluded from the list of accesses to scrape (to redefine this behavior, db_funcs:253)


# Return scraping codes (success and errors)

* return the code explicitly when possible as part of `return` statement (i.e. from `main` function of a scraper)
* if you raise up exception from the code, add `result_code` (which is a text string) to exception text, then in the caller it will be handled by containing text in the exception.
* you can return additional data from the scraper as part of `return` statement (i.e. time metrics or debug info). But be sure that all basic logs are saved from the scraper, not from caller.


# Create organization

* Only one organization with same NameOriginal per Customer will be created (`add_accounts_and_organiz_if_not_exist_or_update__wo_mov_scrap_fin`) to be used from different FinEntAccesses
 
* Mark `DefaultOrganization=1` if create organization with default name (this flag should be passed as parameter with account)

# Scraping in progress

* If CustomerFinancialEntityAccess marked as 'IN PROGRESS', the scraping will not start

# PossibleInactive

* The "PossibleIncative" verification starts from basic_result_success function, that means, it will be executed only if successful scraping
* If the account (saved in the DB) NOT IN the list of scraped accounts of the financial entity access, it will be marked as `PossibleInacive=1`, doesn't matter which value of the flag initially
* If the account (saved in the DB) IN the list of scraped accounts of the financial entity access, it will be marked as `PossibleInacive=0`, doesn't matter which 

# LOGS

* Check `server_start_cronjob.log` as cumulative web server and scraping log (filled by print function from the scripts)
* Check `main_launcher_<UID>__<DATE>__<TIME>.log` to get exact scraping log
* Check `server__<DATE>__<TIME>.log` to get logs of web server requests 

# DEBUG SEGFAULT

* `$ grep fault /var/log/kern.log`
* Also, you can launch with special flag to get segfault message in logs: `python3 -X faulthandler main_launcher_receipts.py`

# NIGHTLY SCRAPING

* Launch it first time in green-time-tunnel (project/settings.py `GREEN_TIME_SCRAPING_TUNNEL_HRS_ALL_CUSTOMERS_SCRAPING = (0, 4)`)
* Launch it second time after green-time-tunnel to try re-scrape failed accesses 
* If necessary, you can run manually several instances of main_launcher at once - they will not scrape same accesses at the same time
* Note: `GREEN_TIME_SCRAPING_TUNNEL_HRS_ALL_CUSTOMERS_SCRAPING` sets the time in UTC, but the server's cron uses local time.


# Account's timestamps

* There are several timestamps:
 `LastScrapingAttemptStartedTimeStamp` and  `LastBalancesScrapingStartedTimeStamp`, `LastBalancesScrapingFinishedTimeStamp`, `LastMovementsScrapingStartedTimeStamp`, `LastMovementsScrapingFinishedTimeStamp`, 
* `LastScrapingAttemptStartedTimeStamp` is changing at each scraping job
*  `LastBalancesScrapingStartedTimeStamp`, `LastBalancesScrapingFinishedTimeStamp`, `LastMovementsScrapingStartedTimeStamp`, `LastMovementsScrapingFinishedTimeStamp`, are changing during the current sraping job, BUT if fails then all these timestamps rolls back to the previous SUCCESSFULLY finished scraping job's values 
* SO, if `LastScrapingAttemptStartedTimeStamp` > any of values of other timestamps (which are related to successfully finished scraping jobs) that means there were failed attempts and need to pay attention for it.

# N43 logic

As discussed. Please find below the logic we need you to implement to identify the financial entity accesses to scrape for N43 files and some additional mandatory considerations to implement per each account scraper.


To help you simplify the process, we are providing you two similar SPs than online scraper to help you obtain active clients and active financial entity access for N43 download.

* `[lportal].[dbo].[ActiveCustomersForNightlyBatch_N43]`. This one brings you the list of all active customers for N43 scraping. No parameters are required exactly in the same way it is for online scraper SP  ActiveCustomersForNightlyBatch
* `[lportal].[dbo].[CustomerFinancialEntityAccessWithCodeByCustomerId_N43]`. This one brings you the list of active financial entity access for the client you have selected. CustomerId is required exactly in the same way it is for online scraper SP CustomerFinancialEntityAccessWithCodeByCustomerId
* We have also implemented a third additional SP for account level considerations. 
Once you have scraped the list of accounts and before you download N43 files we will need y to call this SP  
`[lportal].[dbo].[GetLastStatementDateFromAccount_N43]`. 
CustomerID and AccountNo are mandatory in this SP. 
This will always return one account individual record with LastStatementDate and ActiveAccount.

**And this is the logic we need you to implement based on this SP execution:**

If no record is returned. This means that the account is new account, so you have to scrape it and download the N43 file with the following date criterias…
* `date_from = today - 90 days`
* `date_to = today – 1`

Clear log evidence if account is new.

If record is returned. This means that the account is available. There are two options here
* If ActiveAccount is 0 then don’t do anything and go for the next account. Clear log evidence if account is inactive
* If ActiveAccount is 1 then you have to scrape it and download the N43 file with the following date criterias…

        date_from = LastStatementDate + 1 day
        date_to = today – 1 day

Clear log evidence if account is active.


Regards,

Raul.

 

 
