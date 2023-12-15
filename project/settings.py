import os

import pyodbc
import project.fin_entities_ids as fids

# ===============================
# ===== DEPLOYMENT SWITCHES =====
# ===============================

# NOTE: should be updated for production
IS_DEPLOYED = bool(int(os.getenv('DEPLOYED', '0')))
IS_PRODUCTION_DB = bool(int(os.getenv('PROD_DB', '0')))

# False -> dev - bottle, serial scraping (first scrape, then return http response)
# True  -> prod - gunicorn, async scraping
#   (start the async scraping, return http response, finish the scraping)
IS_API_SERVER_PRODUCTON_MODE = True

# True to hit the DB and False to save scraped data to logs only
# Set False for developing only
IS_UPDATE_DB = bool(int(os.getenv('UPDATE_DB', '1')))

# DEPRECATED (use MAX_CONCURRENT_USERS_SCRAPING) -- TODO delete then
# use or not concurrent processing of users
IS_CONCURRENT_USERS_PROCESSING = bool(int(os.getenv('CONCURRENT_USERS', '1')))

# DEPRECATED (use MAX_CONCURRENT_FIN_ENTITIES_SCRAPING) -- TODO delete then
# use or not concurrent processing of financial entities (accesses)
IS_CONCURRENT_FINANCIAL_ENTITIES_PROCESSING = True

# use or not concurrent scraping of balances and movements of each fin entity
IS_CONCURRENT_SCRAPING = bool(int(os.getenv('CONCURRENT', '1')))

IS_SEND_NOTIFICATIONS = True

# ==================================
# ===== MAIN LAUNCHER SETTINGS  ====
# ==================================

# False - main_laucher can scrape_specific_customer only
# True - main_laucher can scrape_all_customers_where_scraping_not_in_progress
#   (depends on script call parameters)
IS_ALLOW_ALL_CUSTOMERS_SCRAPING_RUN = True

# limit max number of parallel (concurrent) scraping of users
# increase it for speed and reduce to avoid segfault
MAX_CONCURRENT_USERS_SCRAPING = int(os.getenv('MAX_CONCURRENT_USERS', 4))

# limit max number of parallel (concurrent) scraping of fin entities per user
# increase it for speed and reduce to avoid segfault
MAX_CONCURRENT_FIN_ENTITIES_SCRAPING = int(os.getenv('MAX_CONCURRENT_FIN_ENTITIES', 16))

# DEPRECATED (renamed to MAX_CONCURRENT_FIN_ENTITIES_SCRAPING) -- TODO delete then
# limit max number of parallel (concurrent) scraping of fin entities per user
# increase it for speed and reduce to avoid segfault
MAX_FIN_ENTITIES_CONCURRENT_SCRAPING = 16

# the loop should be implemented in the scraper
LOGIN_ATTEMPTS = 3

FINANCIAL_ENTITIES_TO_SCRAPE = [
    fids.BBVA,                           # DONE, netcash: +mov_ext_descr (http req) +checks +receipts +leasing
    fids.BANCOPOPULAR,                   # DONE
    fids.KUTXABANK,                      # DONE
    fids.BANKIA,                         # DONE +mov_ext_descr (no req) +receipts +correspondence
    fids.CAIXA,                          # DONE +mov_ext_descr (http req) +correspondence (multi-pdf)
    fids.SANTANDER,                      # DONE +mov_ext_descr (no req) +receipts (only nuevo login) +checks, +fut movs (hard)
    fids.SABADELL,                       # DONE +mov_ext_descr (http req) +receipts +checks
    fids.DEUTSCHE_BANK,                  # DONE +correspondence
    fids.BANKINTER,                      # DONE +receipts +leasing
    fids.CAJA_RURAL,                     # DONE, ruralvia
    fids.GLOBAL_CAJA,                    # DONE, from ruralvia
    fids.CAJA_RURAL_CASTILLA_LA_MANCHA,  # DONE, from ruralvia
    fids.CAIXA_POPULAR,                  # DONE, from ruralvia
    fids.PICHINCA,                       # DONE, from ruralvia
    fids.IBER_CAJA,                      # DONE, +fut movs (hard)
    fids.CAJAMAR,                        # DONE
    fids.ABANCA,                         # DONE, +correspondence
    fids.LIBERBANK,                      # DONE, +correspondence
    fids.CAIXA_GERAL,                    # DONE
    fids.LABORAL_KUTXA,                  # DONE, +correspondence
    fids.ING,                            # PARTIAL DONE (not all access types)
    fids.TARGO,                          # DONE
    fids.OPENBANK,                       # DONE
    fids.BANTIERRA,                      # DONE, from ruralvia
    fids.CAJA_RURAL_GRANADA,             # DONE, from ruralvia
    fids.TRIODOS,                        # DONE
    fids.NOVOBANCO,                      # PARTIAL DONE (not all access types)
    fids.BANCO_MARE_NOSTRUM,             # DONE
    fids.VOLKSWAGENBANK,                 # DONE, from caixa geral
    fids.BANCO_CAMINOS,                  # DONE
    fids.BANCA_MARCH,                    # DONE, +correspondence
    fids.CASTILLA_LA_MANCHA_LIBERBANK,   # DONE, from liberbank
    fids.UNICAJA,                        # DONE, renamed from caja espana
    fids.CAJA_RURAL_DEL_SUR,             # DONE, from ruralvia
    fids.CAJASUR,                        # DONE, from kutxabank
    fids.ARQUIABANCA,                    # DONE
    fids.PASTOR,                         # DONE, from popular
    fids.CAIXALTEA,                      # DONE, from cajamar
    fids.FIARE_BANCA_ETICA,              # DONE, from ruralvia
    fids.CAJA_INGENIEROS,                # DONE, auth from caixa geral
    fids.BANKOA,                         # DONE, from ruralvia
    fids.RENTA4BANCO,                    # DONE, one account per access tested only
    fids.SOCIETE_GENERALE,               # DONE
    fids.CAIXARURAL_VILAREAL,            # DONE, from cajamar
    fids.BNP_PARIBAS,                    # DONE, one account per access tested only
    fids.BBVA_CONTINENTAL,               # DONE
    fids.SANTANDER_BRASIL,               # DONE
    fids.CAJA_RURAL_DE_NAVARRA,          # DONE, from ruralvia
    fids.CAJA_RURAL_SORIA,               # DONE, from ruralvia
    fids.CAJA_RURAL_SALAMANCA,           # DONE, from ruralvia
    fids.CAJA_RURAL_ZAMORA,              # DONE, from ruralvia
    fids.SANTANDER_CHILE,                # DONE
    fids.BANK_OF_AMERICA,                # IN PROGRESS
    fids.BANCOPOPULAR_DOMINICANO,        # DONE
    fids.SANTANDER_TOTTA,                # DONE
    fids.RBS,                            # DONE
    fids.BANCO_COOPERATIVO,              # DONE, from ruralvia
    fids.EUROCAJA_RURAL,                 # DONE, from ruralvia
    fids.ALPHABANK,                      # DONE, +mov_ext_descr (http req)
    fids.BPI,                            # DONE
    fids.EUROBIC,                        # DONE, +mov_ext_descr (http req)
    fids.CREDITO_AGRICOLA,               # DONE, +mov_ext_descr (no req)
    fids.CAIXA_GERAL_DEPOSITOS,          # DONE, +mov_ext_descr (http req), incremental movs
    fids.BANCO_MONTEPIO,                 # DONE, +mov_ext_descr (http req)
    fids.BRADESCO,                       # DONE, +mov_ext_descr (no req)
    fids.SABADELL_MIAMI,                 # DONE
    fids.CAJA_ALMENDRALEJO,              # DONE
    fids.BANCOFAR,                       # DONE, +mov_ext_descr (http req), auth from caixa geral
    fids.POSTFINANCE,                    # IN PROGRESS
    fids.CAJA_RURAL_CENTRAL,             # DONE
    fids.SABADELL_UK,                    # DONE
    fids.CAIXA_CALLOSA,                  # DONE
    fids.INVERSIS,                       # DONE
    fids.REDSYS,                         # DONE
    fids.EBN,                            # DONE
    fids.CAIXA_GUISSONA,                 # IN PROGRESS
    fids.SANTANDER_MEXICO,               # IN PROGRESS
    fids.PAYPAL,                         # DONE
    fids.EBURY,                          # IN PROGRESS
    fids.CAIXA_BURRIANA,                 # DONE
    fids.BANCA_PUEYO,                    # DONE
    fids.CAJA_RURAL_DE_ARAGON,           # DONE, from ruralvia
    fids.ABANCA_PORTUGAL                 # DONE
]

# list of proxies to use
DEFAULT_PROXIES = [

    # public IP 185.74.81.115
    {
        'http': 'http://:@192.168.195.114:8115',
        'https': 'http://:@192.168.195.114:8115',
    },

    # public IP 185.74.81.116
    {
        'http': 'http://:@192.168.195.114:8116',
        'https': 'http://:@192.168.195.114:8116',
    },

    # public IP 185.74.81.117
    {
        'http': 'http://:@192.168.195.114:8117',
        'https': 'http://:@192.168.195.114:8117',
    },

    # public IP 185.74.81.118
    # use port 8120 instead of 8118 port (which often blocked by websites)
    {
        'http': 'http://:@192.168.195.114:8120',
        'https': 'http://:@192.168.195.114:8120',
    },

    # public IP 185.74.81.119
    {
        'http': 'http://:@192.168.195.114:8119',
        'https': 'http://:@192.168.195.114:8119',
    },

    # {'http': 'http://proxys:4MLDPBEz@91.126.60.95:6677',
    #  'https': 'https://proxys:4MLDPBEz@91.126.60.95:6677'}

    # NEW IP POOL

    # public IP 185.74.80.115
    {
        'http': 'http://:@192.168.195.114:7115',
        'https': 'http://:@192.168.195.114:7115',
    },

    # public IP 185.74.80.116
    {
        'http': 'http://:@192.168.195.114:7116',
        'https': 'http://:@192.168.195.114:7116',
    },

    # public IP 185.74.80.117
    {
        'http': 'http://:@192.168.195.114:7117',
        'https': 'http://:@192.168.195.114:7117',
    },

]

# to get more flexible behavior for bancopopular (as most critical for IP)
RAW_HTTP_LIB_PROXIES = DEFAULT_PROXIES

DEFAULT_USER_AGENT = ('Mozilla/5.0 (Windows NT 6.1; WOW64) '
                      'AppleWebKit/537.22 (KHTML, like Gecko) '
                      'Chrome/25.0.1364.97 Safari/537.22')

# To skip (or wait) a scraping for an access if a scraping in progress detected for the equal access
# ('equal' means with the same credentials but with another id).
# Useful for cases when there are several customers with
# duplicated accesses, and we want to avoid multiple auth sessions
# during the parallel scraping processes.
# For now, if True, then the process that has detected the collision will be finished
# to avoid affecting with the running one.
# Detection is implemented at main_launcher.
IS_DETECT_EQUAL_ACCESS_COLLISIONS = True

# =======================================
# ===== MOVEMENTS SCRAPING SETTINGS  ====
# =======================================

# dates offset before current date (date_from)
# to scrape movements initially (no movements for account in the DB)
SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_INITIALLY = int(os.getenv('MOV_OFFSET', 15))

# dates offset of last scraped movement on re-scraping (there are movements for account in the DB)
# 0 - scrape movement since date of last scraped movement
# use 15 for production
SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_BEFORE_LAST_SCRAPED_MOV = int(os.getenv('MOV_OFFSET', 15))

# For basic_get_date_from. Limit max val of the offset.
# If need to scrape with more offset, change the val via env vars
MAX_OFFSET = int(os.getenv('MAX_OFFSET', 89))

# For basic_get_date_from. Auto-increase offset when it's possible
# to get saved movements from at least 2 dates
MAX_AUTOINCREASING_OFFSET = int(os.getenv('MAX_AUTOINC_OFFSET', 89))

# True - always delete all movements since date_from
# (useful to avoid balance_integrity_error automatically, but
# useless if we want to keep all scraped movements without deleting)
# False - don't delete already scraped movements, just add new
IS_OVERWRITE_MOVEMENTS_ON_RESCRAPING = False

# True - overwrite movements since last correct movement into the DB
# only if it helps to fix balance integrity error
IS_TRY_AUTOFIX_BALANCE_INTEGRITY_ERROR = True

# True - upload even if got balance integrity error
# False - don't upload if got balance integrity error
# in any case we will get email notifications about balance integrity error
IS_UPLOAD_MOVEMENTS_ON_BALANCE_INTEGRITY_ERROR = False

# False - use earlier implemented access-level correspondence conditions
# True - use new access-level 'generic' + account-level correspondence conditions
IS_ACCOUNT_LEVEL_CORRESPONDENCE_CONDITIONS = bool(int(os.getenv('NEW_CORRESPONDENCE_FLAGS', '1')))

# 8 (or any) hours means that the files will be downloaded only if the scraping
# process was launched between 0:00 and 7:59
# to avoid downloading during the daytime scraping
DOWNLOAD_RECEIPTS_IF_HOUR_LESS = 24
DOWNLOAD_CORRESPONDENCE_DOCUMENTS_IF_HOUR_LESS = 24
DOWNLOAD_CHECKS_IF_HOUR_LESS = 24
DOWNLOAD_LEASING_IF_HOUR_LESS = 24

# 8 (or any) hours means that the extended descriptions will be updated only
# if the scraping process was launched between 0:00 and 7:59
# to avoid updating during the daytime scraping
UPDATE_MOVEMENTS_EXTENDED_DESCRIPTIONS_IF_HOUR_LESS = 24

# path for receipts downloading depends on deployed/local and prod/pre
if IS_DEPLOYED:
    if IS_PRODUCTION_DB:
        MAIN_LAUNCHER_LOG_FOLDER = '/mnt/tesoralia_logs/prod/'
        DOWNLOAD_RECEIPTS_TO_FOLDER = '/mnt/tesoralia/prod/files/receipts'
        DOWNLOAD_CORRESPONDENCE_DOCUMENTS_TO_FOLDER = '/mnt/tesoralia/prod/files/documents/correspondence'
        DOWNLOAD_CHECKS_TO_FOLDER = '/mnt/tesoralia/prod/files/documents/checks'
        DOWNLOAD_N43_TO_FOLDER_TEMP = '/mnt/descargas/N43Python-pro'
        DOWNLOAD_N43_TO_FOLDER_FINAL = '/mnt/descargas'
        DOWNLOAD_POS_TO_FOLDER = '/mnt/tesoralia/prod/files/remesas_tpv'
        DOWNLOAD_MT940_TO_FOLDER = '/mnt/tesoralia/prod/files/mt940'
    else:
        MAIN_LAUNCHER_LOG_FOLDER = 'logs'
        DOWNLOAD_RECEIPTS_TO_FOLDER = '/mnt/tesoralia/prep/files/receipts'
        DOWNLOAD_CORRESPONDENCE_DOCUMENTS_TO_FOLDER = '/mnt/tesoralia/prep/files/documents/correspondence'
        DOWNLOAD_CHECKS_TO_FOLDER = '/mnt/tesoralia/prep/files/documents/checks'
        DOWNLOAD_N43_TO_FOLDER_TEMP = '/mnt/descargas/N43Python-pre/temp'
        DOWNLOAD_N43_TO_FOLDER_FINAL = '/mnt/descargas/N43Python-pre/final'
        DOWNLOAD_POS_TO_FOLDER = '/mnt/tesoralia/prep/files/remesas_tpv'
        DOWNLOAD_MT940_TO_FOLDER = '/mnt/tesoralia/prep/files/mt940'

# local (dev) usage
else:
    MAIN_LAUNCHER_LOG_FOLDER = 'logs'
    DOWNLOAD_RECEIPTS_TO_FOLDER = 'downloads/receipts'
    DOWNLOAD_CORRESPONDENCE_DOCUMENTS_TO_FOLDER = 'downloads/correspondence'
    DOWNLOAD_CHECKS_TO_FOLDER = 'downloads/checks'
    DOWNLOAD_N43_TO_FOLDER_TEMP = 'downloads/n43/temp'
    DOWNLOAD_N43_TO_FOLDER_FINAL = 'downloads/n43/final'
    DOWNLOAD_POS_TO_FOLDER = 'downloads/pos'
    DOWNLOAD_MT940_TO_FOLDER = 'downloads/mt940'


# From date_to
DOWNLOAD_CORRESPONDENCE_OFFSET_DAYS = 7
DOWNLOAD_N43_OFFSET_DAYS = 7
DOWNLOAD_N43_OFFSET_DAYS_INITIAL = 15  # only for a new account
DOWNLOAD_TRANSFERS_OFFSET_DAYS = 15
DOWNLOAD_MT940_OFFSET_DAYS_INITIAL = 15  # only for a new account/access

# Consider non-existent account by GetLastStatementDateFromAccount_MT940 as active or not
MT940_IS_ACTIVE_ACCOUNT_IF_NONEXISTENT_IN_DB = True

# ===================================
# ===== FOLDERS AND IP SETTINGS =====
# ===================================

# from the project_root_path; folder to save js scripts (log in encrypters mostly)
JS_HELPERS_FOLDER = 'js_helpers'

if IS_DEPLOYED:
    PROJECT_ROOT_PATH = ''  # ~/ on the prod server
    LOCAL_IP = '0.0.0.0'  # azure, eurovia
else:
    PROJECT_ROOT_PATH = ''
    LOCAL_IP = 'localhost'

# =======================
# ===== DB SETTINGS =====
# =======================

# most recent version
# expect 'ODBC Driver 17 for SQL Server' or 'ODBC Driver 13 for SQL Server'
odbc_driver_available = [d for d in pyodbc.drivers() if 'SQL Server' in d][-1]

if IS_PRODUCTION_DB:
    DB_CONN_STR = ('Driver={{{}}};Server=tcp:192.168.195.121,'
                   '1433;Database=lportal;Uid=_UserSQL;Pwd=#QwK9%QxULoF;'
                   'Connection Timeout=30; Encrypt=no;'.format(odbc_driver_available))
else:
    DB_CONN_STR = ('Driver={{{}}};Server=tcp:192.168.195.125,'
                   '1433;Database=lportal;Uid=_AdminSQL;Pwd=admin9881;'
                   'Connection Timeout=30; Encrypt=no;'.format(odbc_driver_available))

# to avoid deadlocks while db uploading
# 1 to avoid segfault on many concurrent requests
# probably python doesn't create some new futures
# and new connection creates in sam e future
# in any case 1 worker solves the problem
# https://social.msdn.microsoft.com/Forums/sqlserver/en-US/23fafa84-d333-45ac-8bd0-4b76151e8bcc/sql-server-driver-for
# -linux-causes-segmentation-fault?forum=sqldataaccess
# https://stackoverflow.com/questions/10496815/segmentation-fault-when-reconnecting-to-sql-server-database-using
# -pyodbc-on-linu
# UPD: new db/queue_simple always uses 1 output
# this parameter is obsolete
DB_QUEUE_CONCURRENT_WORKERS = 1

# size of batch to split too large list of movements to upload
# need to use to avoid lost movements even on successful uploading result
# should be <=100
MOVEMENTS_TO_UPLOAD_BATCH_SIZE = 50

# size of batch to split too large list of accounts to upload
# need to use to avoid lost accounts even on successful uploading result
# should be <=50
ACCOUNTS_TO_UPLOAD_BATCH_SIZE = 40

# ==================================
# ===== DATES FORMATS SETTINGS =====
# ==================================

LOG_FILENAME_DATETIME_FMT = '%Y%m%d_%H%M%S'
SCRAPER_DATE_FMT = '%d/%m/%Y'
DB_DATE_FMT = '%Y%m%d'  # for uploading; for azure '%Y-%m-%d'
DB_TIMESTAMP_FMT = '%Y%m%d %H:%M:%S.%f'  # strip then by [:-3] to get millis

# =======================================
# ===== SCRAPING INTERVALS SETTINGS =====
# =======================================

# in seconds
LIMIT_PER_CUSTOMER_SCRAPING = 300  # 5 min

NECESSARY_INTERVAL_BTW_SUCCESSFUL_SCRAP_OF_FIN_ENT = int(os.getenv('SCRAP_INTERVAL', 30 * 60))  # 10 or more min
NECESSARY_INTERVAL_BTW_FAILED_SCRAP_OF_FIN_ENT = int(os.getenv('SCRAP_INTERVAL', 2 * 60))  # 2 min

# will be used in nightly scraping
# 7 hours enough (we suggest to start 2nd nighly scraping at 7:00 to update all scraped earlier than 0:00)
NECES_INTER_BTW_SUCCESS_SCRAP_OF_FIN_ENT_ALL_CUST_SCRAP = 7 * 60 * 60

# if the all_customers scraping run in this time period,
# then all accesses will be scraped
# (0, 1) means from 0:00 am to 1:00 am UTC
# we suggest to start 1st nighly launch at 3:00 UTC
GREEN_TIME_SCRAPING_TUNNEL_HRS_ALL_CUSTOMERS_SCRAPING = (0,5)  # was (0,4)

# =================================
# ===== NOTIFICATION SETTINGS =====
# =================================

# Will be used for DB logging
DB_LOGGER_NAME = 'Online Python Orchestration'
DB_LOGGER_NAME_N43 = 'N43 Python Orchestration'
DB_LOGGER_NAME_MT940 = 'MT940 Python Scraper'  # was ...Orchestration
LAUNCHER_DEFAULT_ID = '1'

ERR_BALANCE_NOTIFICATION_EMAILS = [
    'nordborn@gmail.com',
]

ERR_NOT_BALANCE_NOTIFICATION_EMAILS = [
    'nordborn@gmail.com',
    # 'raul.jimenez@tesoralia.com',
    # 'vicente.delacueva@tesoralia.com',
    # 'david.amor@tesoralia.com'
]

WARN_NOTIFICATION_EMAILS = [
    'nordborn@gmail.com',
]

MSG_HTML_STYLES = """
<style>
    td {border-top: 1px solid #ddd; padding: 4px;}
</style>
"""

if IS_DEPLOYED and IS_PRODUCTION_DB:
    # sentry.tesoralia.local -> 192.168.195.100:9000
    # scrapers-python-production
    SENTRY_API_TOKEN = 'http://94723cbd97aa42378b97016568356e17:be413612187f4f6b9621d29d65a6ab0b@192.168.195.100:9000/3'
else:
    # scrapers-python-staging
    SENTRY_API_TOKEN = 'http://d6f56315cfc349cc8de7f953a7926fc2:2e6188312ed2485daa94f734bc4d5631@192.168.195.100:9000/4'


SPLASH_URL = 'http://localhost:8050'

# ==================================
# ==================================
# ==================================

print('Settings initialized. Use {}'.format(odbc_driver_available))
