from collections import namedtuple
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Tuple, Optional, NamedTuple

__version__ = '1.48.0'
__changelog__ = """
1.48.0 2023.07.31
added DOBLE_AUTH_TYPE_WITH_DEACTIVATION
1.47.0 2023.06.23
added INVALID_PDF_MARKER
1.46.0 2023.06.07
added DOCUMENT_TYPE_CORRESPONDENCE, DOCUMENT_TYPE_RECEIPT
1.45.0 2023.05.23
MovementScraped, MovementSaved: added new fields Receipt and ReceiptChecksum
1.44.0 2023.05.16
added PASSWORD_CHANGE_TYPE_COMMON
1.43.0
added EXPIRED_USER_TYPE_COMMON
1.42.0
added BLOCKED_USER_TYPE_COMMON
1.41.0
added DelayedInterest, InvoiceNumber to fee_scraped
1.40.0
new PDF_UNKNOWN_ACCOUNT_NO: PDF without associated account
1.39.0
MT940FileDownloaded
1.38.0
Cookie
1.37.0
POSTradePoint: 
  DownloadTimeStamp (added in the type) is FechaDescarga
  LastDownloadedOperationalDate is FechaUltimaDescargaCorrecta (added in DB)
1.36.0
POSTradePoint
POSCollection
POSMovement
1.35.0
AccountToDownloadCorrespondence
1.34.1
upd comments
1.34.0
DBFinancialEntityAccessForN43: TempFolder bool field
1.33.0
DBFinancialEntityAccessForN43: LastSuccessDownload field 
1.32.0
ScraperParamsCommon: launcher_id field
1.31.1
more type hints
1.31.0
MovementTPV
1.30.0
TransferScraped: new field TempBalance
DBTransfer: new field TempBalance
1.29.0
DBMovementByTransfer, GroupOfTransfersNotLinkedMultipleMovs
DBTransfer: new fields, Amount is float
1.28.0
DBCustomerForN43, DBFinancialEntityAccessForN43
1.27.0
AccountSavedWithTempBalance: with field 'Active'
1.26.0
fixed, upd, added type annotations:
  TransferScraped, DBTransfer, DBTransferAccountConfig, DBTransferFilter, DBMovementConsideredTransfer
1.25.1
DBTransferAccountConfig: fix typing
1.25.0
TransferParsed, TransferScraped, DBTransferAccountConfig, DBTransferFilter, DBMovementConsideredTransfer
1.24.0
renamed to CorrespondenceDocParsed, CorrespondenceDocScraped, CorrespondenceDocChecked 
1.23.0
DocumentScraped, CorrespondenceFromList: currency fields
1.22.0
DocumentScraped: use datetime for DocumentDate
1.21.0
MovementSaved, MovementScraped: ExportTimeStamp field 
1.20.0
CorrespondenceFromList
1.19.0
DocumentChecked
typed NamedTuple for correspondence/document-related types
1.18.0
double auth types
1.17.0
InitialId support
1.16.1
actual MainResult
1.16.0
MainResult alias
1.15.0
MovementSaved: CreateTimeStamp field
1.14.0
DAF:
LeasingContractScraped: added new field PendingRepayment 
LeasingFeeScraped: added new field InsuranceAmount
1.13.0
DAF:
LeasingContractParsed
LeasingContractScraped
LeasingFeeParsed
LeasingFeeScraped
1.12.0
DAF:
extended CheckScraped 
CheckCollectionParsed
CheckCollectionScraped
1.11.0
extended MovementScraped
removed MovementScrapedWExtractedInfo (not used since extended MovementScraped)
removed DBCustomerMinData (not used)
1.10.0
DAF:
CheckParsed
CheckScraped
1.9.0
DAF: 
DocumentTextInfo
DocumentScraped: added StatementId
1.8.1
fixed type hint to pass mypy
1.8.0
ScraperParamsCommon: db_customer
DBCustomer: ExtendedDescriptionFlag
1.7.0
DAF:
DocumentParsed
DocumentScraped
DBOrganization
1.6.0
DBAccount with Balance field
AccountSavedWithTempBalance
1.5.1
MovementScrapedWExtractedInfo structure definition: correct name
1.5.0
DAF: MovementScrapedWExtractedInfo
1.4.0
DBFinancialEntityAccessThirdLoginPass
1.3.0
MovementScraped: StatementExtendedDescription
1.2.0
ScraperParamsCommon: date_to_str
1.1.0
AccountParsed
MovementParsed
"""

# double auth (2FA)
DOUBLE_AUTH_REQUIRED_TYPE_COMMON = 'DOUBLE AUTH required'
# (one-time-password == one-time-token)
DOUBLE_AUTH_REQUIRED_TYPE_OTP = 'DOUBLE AUTH required (one-time-token)'
DOUBLE_AUTH_REQUIRED_TYPE_COOKIE = 'DOUBLE AUTH required (90-day-cookie)'
DOBLE_AUTH_TYPE_WITH_DEACTIVATION = 'DOUBLE AUTH required (access with 2FA deactivate)'

BLOCKED_USER_TYPE_COMMON = 'BLOCKED USER'
EXPIRED_USER_TYPE_COMMON = 'EXPIRED USER'
PASSWORD_CHANGE_TYPE_COMMON = 'PASSWORD CHANGE'

# pdf without associated account
PDF_UNKNOWN_ACCOUNT_NO = 'Sin cuenta asociada'

# document origin
DOCUMENT_TYPE_CORRESPONDENCE = 'CORRESPONDENCE'
DOCUMENT_TYPE_RECEIPT = 'RECEIPT'

# got HTML instead of desired PDF
INVALID_PDF_MARKER = b'<!DOCTYPE html'

# account_no type
ACCOUNT_NO_TYPE_IBAN = 'IBAN'
ACCOUNT_NO_TYPE_BBAN = 'BBAN'
ACCOUNT_NO_TYPE_UNKNOWN = 'UNKNOWN'

# account type
ACCOUNT_TYPE_DEBIT = 0
ACCOUNT_TYPE_CREDIT = 1

# movements ordering
MOVEMENTS_ORDERING_TYPE_ASC = 'ASC'  # oldest is the first in the list
MOVEMENTS_ORDERING_TYPE_DESC = 'DESC'  # newest is the first in the list

# Type alias for flexible dict account_parsed
AccountParsed = Dict[str, Any]

# Type alias for flexible dict movement_parsed
MovementParsed = Dict[str, Any]

ResultCode = namedtuple(
    'ResultCode', [
        'code',
        'description'
    ]
)

MainResult = Tuple[ResultCode, Optional[str]]  # (result_code, msg)

AccountScraped = namedtuple(
    'AccountScraped', [
        'FinancialEntityAccountId',
        'AccountNo',
        'AccountNoFormat',
        'AccountNoCountry',
        'Type',  # 0 - Cuenta corriente (ACCOUNT_TYPE_DEBIT), 1 - Cuenta Crédito (ACCOUNT_TYPE_CREDIT)
        'Currency',
        'Balance',
        'OrganizationName',  # will be replaced with Organization Id at DBConnector
        'CustomerId',
        'BalancesScrapingInProgress',
        'BalancesScrapingStartedTimeStamp',
        'BalancesScrapingFinishedTimeStamp',
        'MovementsScrapingInProgress',
        'MovementsScrapingStartedTimeStamp',
        'IsDefaultOrganization',
        'IsActiveOrganization'
    ]
)

# Used by BasicScraper._align_accounts_balances()
AccountSavedWithTempBalance = NamedTuple(
    'AccountSavedWithTempBalance', [
        ('Id', int),
        ('FinancialEntityAccountId', str),
        ('Balance', Decimal),
        ('TempBalance', Decimal),
        ('Active', bool)
    ]
)

MovementScraped = namedtuple(
    'MovementScraped', [
        # 'AccountNo', # NOT USED NOW. Pass AccountNo and FinEntAccId as parameters of db_funcs
        'Amount',
        'TempBalance',
        'OperationalDate',
        'ValueDate',
        'StatementDescription',
        'StatementExtendedDescription',
        'OperationalDatePosition',
        'KeyValue',
        'StatementReceiptDescription',
        'StatementReference1',
        'StatementReference2',
        'Bankoffice',
        'Payer',
        # Special val for exporting functionality. Usually None.
        # But might be updated from the appropriate movement_saved
        # if it's a renewed movement
        # (suitable only for balance_integrity error fixes)
        'CreateTimeStamp',  # Optional[str]
        # None for the very new movement,
        # Prev val Id for renewed
        'InitialId',  # Optional[int]
        'ExportTimeStamp',  # Optional[str]
        'Receipt',  # Optional[int]
        'ReceiptChecksum'  # Optional[str]
    ]
)

# StatementExtendedDescription is not used here to avoid too 'noisy' log msgs
MovementSaved = namedtuple(
    'MovementSaved', [
        # 'AccountNo', # NOT USED NOW. Pass AccountNo and FinEntAccId as parameters of db_funcs
        'Id',
        'Amount',
        'TempBalance',
        'OperationalDate',
        'ValueDate',
        'StatementDescription',
        'OperationalDatePosition',
        'KeyValue',
        'CreateTimeStamp',  # str like '20170118 02:56:03.638'
        'ExportTimeStamp',  # optional str like '20170118 02:56:03.638'
        # Read the val from this DB's field or fill from Id if there were no renewed movs
        # (if there is no value in InitialId then this movement wasn't re-inserted yet)
        'InitialId',  # Optional[int]
        'Receipt',  # Optional[int]
        'ReceiptChecksum'  # Optional[str]
    ]
)

DBCustomer = namedtuple(
    'DBCustomer', [
        'Id',
        'Name',
        'ScrapingInProgress',
        'LastScrapingStartedTimeStamp',
        'LastScrapingFinishedTimeStamp',
        'CreateTimeStamp',
        'LastUpdateTimeStamp',
        'BalancesScrapingInProgress',
        'LastBalancesUpdateTimeStamp',
        'ExtendedDescriptionFlag'
    ]
)

DBCustomerForN43 = NamedTuple(
    'DBCustomerForN43', [
        ('Id', int),
        ('Name', str),
    ]
)

DBFinancialEntityAccessForN43 = NamedTuple(
    'DBFinancialEntityAccessForN43', [
        ('Id', int),
        ('AccessFirstLoginValue', str),
        ('AccessPasswordLoginValue', str),
        ('AccessSecondLoginValue', str),
        ('CustomerId', int),
        ('FinancialEntityAccessFirstLoginLabel', str),
        ('FinancialEntityAccessId', int),
        ('FinancialEntityAccessName', str),
        ('FinancialEntityAccessPasswordLoginLabel', str),
        ('FinancialEntityAccessSecondLoginLabel', str),
        ('FinancialEntityAccessUrl', str),
        ('FinancialEntityId', int),
        # dt of last 'SUCCESS' entry in accesos_Log table
        ('LastSuccessDownload', Optional[datetime]),
        ('TempFolder', Optional[bool])
    ]
)

DBCustomerToUpdateState = namedtuple(
    'DBCustomerToUpdateState', [
        'Id',
        'ScrapingInProgress',
        'ScrapingStartedTimeStamp',
        'ScrapingFinishedTimeStamp',
    ]
)

DBFinancialEntityAccess = namedtuple(
    'DBFinancialEntityAccess', [
        'Id',
        'AccessFirstLoginValue',
        'AccessPasswordLoginValue',
        'AccessSecondLoginValue',
        'CustomerId',
        'FinancialEntityAccessFirstLoginLabel',
        'FinancialEntityAccessId',
        'FinancialEntityAccessName',
        'FinancialEntityAccessPasswordLoginLabel',
        'FinancialEntityAccessSecondLoginLabel',
        'FinancialEntityAccessUrl',
        'FinancialEntityId',
        'CreateTimeStamp',
        'LastScrapingFinishedTimeStamp',
        'LastScrapingStartedTimeStamp',
        'LastUpdateTimeStamp',
        'ScrapingInProgress',
        'LastResponseTesoraliaCode'
    ]
)

# special additional login parameters
DBFinancialEntityAccessThirdLoginPass = namedtuple(
    'DBFinancialEntityAccessThirdLoginPass', [
        'AccessThirdLoginValue',  # mapped to accessThirdLoginValue
        'AccessPasswordThirdLoginValue',  # mapped to accessPasswordThirdLoginValue
    ]
)

DBFinancialEntityAccessToUpdateState = namedtuple(
    'DBFinancialEntityAccessToUpdateState', [
        'Id',
        'ScrapingInProgress',
        'ScrapingStartedTimeStamp',
        'ScrapingFinishedTimeStamp'
    ]
)

DBFinancialEntityAccessWithCodesToUpdateState = namedtuple(
    'DBFinancialEntityAccessWithCodesToUpdateState', [
        'Id',
        'ScrapingInProgress',
        'ScrapingStartedTimeStamp',
        'ScrapingFinishedTimeStamp',
        'HttpStatusResponseCode',
        'HttpStatusResponseDescription',
        'ResponseTesoraliaCode',
        'ResponseTesoraliaDescription'
    ]
)

DBAccount = namedtuple(
    'DBAccount', [
        'Id',
        'Balance',
        'FinancialEntityAccountId',
        'UpdateTimeStamp',
        'BalancesScrapingInProgress',
        'MovementsScrapingInProgress',
        'LastBalancesScrapingStartedTimeStamp',
        'LastBalancesScrapingFinishedTimeStamp',
        'LastMovementsScrapingStartedTimeStamp',
        'LastMovementsScrapingFinishedTimeStamp',
        'CustomerFinancialEntityAccessId',
        'PossibleInactive'
    ]
)

RunnerOnDemandParams = NamedTuple(
    'RunnerOnDemandParams', [
        ('customer_id', int),
        ('date_from_str', Optional[str]),
        ('date_to_str', Optional[str]),
    ]
)

RunnerOnDemandSecondaryParams = NamedTuple(
    'RunnerOnDemandSecondaryParams', [
        ('customer_id', str),
        ('date_from_str', str),
        ('date_to_str', str),
        ('fin_ent_access_id', str),
    ]
)

ScraperParamsCommon = NamedTuple(
    'ScraperParamsCommon', [
        ('date_from_str', Optional[str]),
        ('date_to_str', Optional[str]),
        ('db_customer', DBCustomer),
        ('db_financial_entity_access', DBFinancialEntityAccess),
        ('launcher_id', str)
    ]
)

AccountToDownloadCorrespondence = NamedTuple(
    'AccountToDownloadCorrespondence', [
        ('Id', int),  # DB Account Id
        ('FinancialEntityAccountId', str)
    ]
)

CorrespondenceDocParsed = NamedTuple(
    'CorrespondenceDocParsed', [
        ('type', str),  # 'EXTRACTOS DE CUENTA'
        ('account_no', str),
        ('operation_date', datetime),
        ('value_date', Optional[datetime]),
        ('amount', Optional[float]),
        ('currency', Optional[str]),
        ('descr', str),  # 'ASISTENCIA A JUNTA', ''
        ('extra', dict),  # any extra info appropriate for a specific scraper
    ]
)

# Correspondence document
CorrespondenceDocScraped = NamedTuple(
    'CorrespondenceDocScraped', [
        ('CustomerId', int),
        ('OrganizationId', int),
        ('FinancialEntityId', int),
        ('ProductId', str),  # Account IBAN
        ('ProductType', str),
        ('DocumentDate', datetime),
        ('Description', str),
        ('DocumentType', str),
        ('DocumentText', str),
        ('Checksum', str),
        ('AccountId', Optional[int]),  # DB Account Id
        ('StatementId', Optional[int]),  # DB Movement Id
        ('Amount', Optional[float]),
        ('Currency', Optional[str])
    ]
)

CorrespondenceDocChecked = NamedTuple(
    'CorrespondenceDocChecked', [
        ('IsToAdd', bool),
        ('AccountId', Optional[int]),  # DB Account Id
        ('AccountNo', Optional[str])
    ]
)

DocumentTextInfo = NamedTuple(
    'DocumentTextInfo', [
        ('OperationalDate', str),
        ('ValueDate', str),  # '' if missing
        ('Amount', Optional[float]),
        ('StatementDescription', Optional[str])
    ]
)

DBOrganization = namedtuple(
    'DBOrganization', [
        'Id',
        'Name',
        'NameOriginal'
    ]
)

# Type alias for flexible dict check_parsed
CheckParsed = Dict[str, Any]

CheckScraped = namedtuple(
    'CheckScraped', [
        'CheckNumber',
        'CaptureDate',
        'ExpirationDate',
        'PaidAmount',
        'NominalAmount',
        'ChargeAccount',
        'ChargeCIF',
        'DocCode',
        'Stamped',
        'State',
        'KeyValue',
        'Receipt',
        'CustomerId',
        'FinancialEntityId',
        'AccountId',
        'AccountNo',
        'StatementId',
        'CollectionId',
    ]
)

# Type alias for flexible dict check_collection_parsed
CheckCollectionParsed = Dict[str, Any]

CheckCollectionScraped = namedtuple(
    'CheckCollectionScraped', [
        'CustomerId',
        'FinancialEntityId',
        'AccountId',
        'AccountNo',
        'StatementId',
        'OfficeDC',
        'CheckType',
        'CollectionReference',
        'Amount',
        'CollectionDate',
        'State',
        'CheckQuantity',
        'KeyValue',
    ]
)

# Type alias for flexible dict leasing_contract_parsed
LeasingContractParsed = Dict[str, Any]

LeasingContractScraped = namedtuple(
    'LeasingContractScraped', [
        'CustomerId',
        'FinancialEntityId',
        'AccountId',
        'AccountNo',
        'Office',
        'ContractReference',
        'ContractDate',
        'ExpirationDate',
        'FeesQuantity',
        'Amount',
        'Taxes',
        'ResidualValue',
        'InitialInterest',
        'CurrentInterest',
        'PendingRepayment',
        'KeyValue'
    ]
)

# Type alias for flexible dict leasing_fee_parsed
LeasingFeeParsed = Dict[str, Any]

LeasingFeeScraped = namedtuple(
    'LeasingFeeScraped', [
        'FeeReference',
        'FeeNumber',
        'OperationalDate',
        'Currency',
        'Amount',
        'TaxesAmount',
        'InsuranceAmount',
        'FeeAmount',
        'FinRepayment',
        'FinPerformance',
        'PendingRepayment',
        'State',
        'KeyValue',
        'StatementId',
        'ContractId',
        'DelayInterest',
        'InvoiceNumber',
    ]
)

# Type alias for flexible dict check_parsed
TransferParsed = Dict[str, Any]

TransferScraped = NamedTuple(
    'TransferScraped', [
        ('AccountId', int),
        ('CustomerId', int),
        ('OperationalDate', str),  # db fmt
        ('ValueDate', str),  # db fmt
        ('Amount', float),
        ('TempBalance', Optional[float]),
        ('Currency', str),
        ('AccountOrder', str),
        ('NameOrder', str),
        ('Concept', str),
        ('Reference', str),
        ('Description', str),
        ('Observation', str),
        ('FinancialEntityName', str),
        ('IdStatement', Optional[str]),  # str to set 'not linked' ('No vinculable') then by TransfersLinker
    ]
)

DBTransfer = NamedTuple(
    'DBTransfer', [
        ('Id', int),
        ('AccountId', int),
        ('CustomerId', int),
        ('OperationalDate', datetime),
        ('ValueDate', datetime),
        ('Amount', float),
        ('TempBalance', Optional[float]),
        ('Currency', str),
        ('AccountOrder', str),
        ('NameOrder', str),
        ('Concept', str),
        ('Reference', str),
        ('Description', str),
        ('Obrservation', str),  # VB: id 948906, 'NULL' - is it ok?
        ('Entity', str),  # 'BBVA'
        ('IdStatement', str),  # can be 'No vinculable', VB: set Optional if not linked yet - ?
        ('FechaRegistro', datetime),
        ('UpdateIdStatementDate', datetime),
        ('NotLinkedReason', str),
    ]
)

DBTransferAccountConfig = NamedTuple(
    'DBTransferAccountConfig', [
        ('AccountId', int),
        ('FinancialEntityAccountId', str),
        ('CustomerFinancialEntityAccessId', int),
        ('LastScrapedTransfersTimeStampWithOffset', datetime),
    ]
)

DBTransferFilter = NamedTuple(
    'DBTransferFilter', [
        ('AccountId', int),
        ('BankCode', str),
        ('NavigationType', str),
        ('OriginField', str),
        ('LogicOverField', Optional[str]),
        ('DestinyField', str),  # destination/target?
        ('Active', bool),
    ]
)

DBMovementByTransfer = NamedTuple(
    'DBMovementByTransfer', [
        ('InitialId', str),
        ('StatementDescription', str),
        ('StatementExtendedDescription', str)
    ]
)

# for get_transfers_not_linked_due_to_multiple_statements_by_value_date
GroupOfTransfersNotLinkedMultipleMovs = NamedTuple(
    'GroupOfTransfersNotLinkedMultipleMovs', [
        ('FILAS', int),  # 2 -- number of not linked transfers in the group
        ('AccountId', int),  # 4723,
        ('FinancialEntityAccountId', str),  # ES5401825699620201504494
        ('ValueDate', str),  # '30/11/2018'
        ('Amount', float)  # from Decimal('168.75000000000000000000')
    ]
)

DBMovementConsideredTransfer = NamedTuple(
    'DBMovementConsideredTransfer', [
        ('OperationalDate', datetime),
        ('ValueDate', datetime),
        ('Amount', float),
        ('AccountId', int),
        ('StatementExtendedDescription', str),
        ('InitialId', int),
    ]
)

# The process will download the information from the following columns:
# It's only for RedSys
MovementTPV = NamedTuple(
    'MovementTPV', [
        ('NoComercio', str),  # CompanyNo
        ('Fecha', datetime),  # Date
        ('NumeroTerminal', int),  # Nº de terminal
        ('TipoOperacion', str),  # Tipo operación, OperationType
        ('NumeroPedido', str),  # Número de pedido, OrderNumber
        ('ResultadoOperacion', str),  # Resultado operación y código, OperationResultAndCode
        ('Importe', str),  # Amount (+ currency info + extra info)
        # Card original currency
        ('ImporteNeto', Optional[str]),  # Importe Neto field, NetAmount
        ('CierreSesion', Optional[str]),  # Cierre de sesión, Logout?
        ('TipoPago', Optional[str]),  # Tipo de pago, PaymentType
        ('NumeroTarjeta', Optional[str]),  # Nº Tarjeta, CardNumber
        ('Titular', Optional[str]),  # Titular (contiene el CIF), Holder
    ]
)

Cookie = NamedTuple('Cookie', [
    ('name', str),
    ('value', str),
    ('domain', str),
    ('path', str),
])

MT940FileDownloaded = NamedTuple('MT940FileDownloaded', [
    ('file_name', str),
    ('file_content', bytes)
])

# POS

POSTradePoint = NamedTuple(
    'POSTradePoint', [
        ('Id', int),  # DB Id
        ('AccessId', int),  # accesosClienteId
        ('CommercialId', int),  # IdComercio
        ('Active', bool),  # Activo
        ('CreateTimeStamp', datetime),  # FechaRegistro
        ('DownloadTimeStamp', datetime),  # FechaDescarga
        ('LastDownloadedOperationalDate', date),  # FechaUltimaDescargaCorrecta
    ]
)

# Generic POS
POSMovement = NamedTuple('POSMovement', [
    ('date', date),  # 28/06/2021
    ('time', str),  # '20:18'
    ('card_number', str),  # '5163________1808'
    ('amount', float),  # 1000.00
    ('commission_percent', str),  # '-0,30%'
    ('commission_amount', float),
    ('descr', str),  # 'VENTA'
    ('date_position', int),  # 1
    ('collection_ref', str),  # '6031381816'
    ('currency', str),  # 'EUR'
])


class POSCollection:
    def __init__(self, trade_point_id: int, logger) -> None:
        self.trade_point_id = trade_point_id
        self.oper_date = None  # type: Optional[date]
        self.logger = logger
        self.ref = ''  # No remesa
        self.movements = []  # type: List[POSMovement]
        self.declared_number_of_movs = 0
        self.base = 0.0
        self.amount = 0.0
        self.commission = 0.0

    def build(self) -> None:
        """Necessary to call after the moment when at least one movement has been inserted"""
        if self.movements:
            mov = self.movements[0]
            self.ref = mov.collection_ref
            self.oper_date = mov.date

    def add_movement(self, mov: POSMovement) -> None:
        self.movements.append(mov)

    def validate_number_of_movs(self) -> bool:
        """Compares declared and actual number of movements"""
        ok = self.declared_number_of_movs == len(self.movements)
        if not ok:
            self.logger.warning(
                '{}: incomplete collection detected: '
                'number of movements declared {}, actual {}. Skip'.format(
                    self._log_prefix(),
                    self.declared_number_of_movs,
                    len(self.movements)
                )
            )
        return ok

    def validate_mov_collection_ids(self) -> bool:
        """Checks that all movements of the collection have same collection_id """
        ok = len({m.collection_ref for m in self.movements}) == 1
        if not ok:
            self.logger.warning('{}: mixed collection detected. Skip')
        return ok

    def _log_prefix(self) -> str:
        return 'trade point {}: collection {} @ {}'.format(
            self.trade_point_id,
            self.ref,
            self.movements[0].date.strftime('%d/%m/%Y') if self.movements else '??'
        )

    def __repr__(self):
        assert self.oper_date  # it should be set before actual usage
        return '{}({} @ {} with {} movs)'.format(
            self.__class__.__name__,
            self.ref,
            self.oper_date.strftime('%d/%m/%Y'),
            self.declared_number_of_movs
        )
