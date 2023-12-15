import traceback
from typing import List, Tuple

from custom_libs.db import db_funcs
from custom_libs.db.db_logger import DBLogger
from custom_libs.scrape_logger import ScrapeLogger
from project import settings as project_settings
from project.custom_types import DBTransfer, DBMovementByTransfer, GroupOfTransfersNotLinkedMultipleMovs

__version__ = '3.0.0'

__changelog__ = """
3.0.0
renamed module from link_transfers_to_movements
use DBLogger
fixed 'completed' log msg (now will be saved in DB)
2.1.1
db log msgs with named args
2.1.0
added bankinter transfer link to movement support based on operational date
get_movement_id_by_transfer_by_value_date
get_movements_by_transfer_by_value_date
get_movement_id_from_movs
get_movement_id_by_transfer_by_operational_date
get_movements_by_transfer_by_operational_date
link_transfers_to_movements_bankinter
2.0.0
moved all sql statements to db_funcs
special new custom_types
fixed typing
upd log msgs
1.1.3
link_transfers_not_linked_due_to_multiple_statements_by_value_date
delete_duplicated_transfers_by_value_date
1.1.2
fixed log msg
1.1.1
upd type hints
upd logging
1.1.0
fmt
upd logging
traceback exn
1.0.0
init
"""

ID_STATEMENT_NO_VINCULABLE = 'No vinculable'
ID_STATEMENT_MULTIPLE_VINCULACION = 'Multiple vinculacion'
NOT_LINKED_REASON_VARIOS_MOVIMIENTOS = 'Se han encontrado varios movimientos para vincular'


class TransfersLinker:
    def __init__(self, db_customer_id: int, fin_entity_name: str, db_financial_entity_access_id: int = None):
        self._db_customer_id = db_customer_id
        self._fin_entity_name = fin_entity_name
        self.logger = ScrapeLogger('Transferencias', db_customer_id, db_financial_entity_access_id)
        self.db_logger = DBLogger(
            'Transferencias',
            db_customer_id=db_customer_id,
            db_financial_entity_access_id=db_financial_entity_access_id,
            fin_entity_name=self._fin_entity_name
        )

    # main method
    def link_transfers_to_movements(self) -> bool:
        """Links transfers to statements.
        IdStatements in transfers will point InitialStatementId in statements
        """
        self.logger.info('Link transfers to movements')
        self.db_logger.accesos_log_info("Inicio: Vinculación transferencias a movimientos")
        try:
            if self._fin_entity_name == 'BBVA':
                ok = self._delete_duplicated_transfers_by_value_date()
                if not ok:
                    return False
                # TODO review succeed treatment in a multi entity context.
                ok = self.link_transfers_to_movements_bbva()
                return ok
            if self._fin_entity_name == 'BANKINTER':
                ok = self._delete_duplicated_transfers_by_operational_date()
                if not ok:
                    return False
                # TODO review succeed treatment in a multi entity context.
                ok = self.link_transfers_to_movements_bankinter()
                return ok
            else:
                self.logger.warning('{}: unimplemented fin entity'.format(self._fin_entity_name))
        except Exception as exn:
            self.logger.error('link_transfers_to_movements: HANDLED EXCEPTION: {}'.format(
                traceback.format_exc()
            ))
            self.db_logger.accesos_log_error(
                message="link_transfers_to_movements() -> ",
                exception_str=str(exn)
            )
        finally:
            self.logger.info('Ended linking transfers to movements')
            self.db_logger.accesos_log_info("Fin: Vinculación transferencias a movimientos")
        # if unsupported fin_entity_name
        return False

    def get_movement_id_by_transfer_by_value_date(self, transfer: DBTransfer) -> Tuple[str, str]:
        # WARN: Fecha operación in movements does not match fecha contable in transfers for BBVA
        # AND OperationalDate = CONVERT(datetime, '{operational_date}', 103)
        self.logger.info(
            '{}: get movement id by transfer: operational date={}, amount={}'.format(
                transfer.AccountId,
                transfer.OperationalDate.strftime(project_settings.SCRAPER_DATE_FMT),
                transfer.Amount
            )
        )
        movs = db_funcs.TransfersFuncs.get_movements_by_transfer_by_value_date(
            transfer)  # type: List[DBMovementByTransfer]
        return self.get_movement_id_from_movs(transfer, movs)

    def get_movement_id_by_transfer_by_operational_date(self, transfer: DBTransfer) -> Tuple[str, str]:
        self.logger.info(
            '{}: get movement id by transfer: operational date={}, amount={}'.format(
                transfer.AccountId,
                transfer.OperationalDate.strftime(project_settings.SCRAPER_DATE_FMT),
                transfer.Amount
            )
        )
        movs = db_funcs.TransfersFuncs.get_movements_by_transfer_by_operational_date(
            transfer)  # type: List[DBMovementByTransfer]
        return self.get_movement_id_from_movs(transfer, movs)

    def get_movement_id_from_movs(self,
                                  transfer: DBTransfer,
                                  movs: List[DBMovementByTransfer]) -> Tuple[str, str]:
        statement_id = ''
        not_linked_reason = ''
        if len(movs) == 1:
            statement_id_str = str(movs[0].InitialId)
        elif len(movs) == 0:
            statement_id_str = ID_STATEMENT_NO_VINCULABLE
            not_linked_reason = (
                "La Transferencia {} de la cuenta {} con fecha valor={} y con importe={} "
                'no se pudo vincular a movimiento'.format(
                    transfer.NameOrder + ' ' + transfer.Description,
                    transfer.AccountId,
                    transfer.ValueDate.strftime(project_settings.SCRAPER_DATE_FMT),
                    transfer.Amount
                )
            )
        else:
            statement_id_str = ID_STATEMENT_MULTIPLE_VINCULACION
            not_linked_reason = '{}: {}'.format(
                NOT_LINKED_REASON_VARIOS_MOVIMIENTOS,
                len(movs)
            )

            # Dictionary with columns in transfer to be
            # found in StatementExtendedDescription of movement
            transf_matching_fields = [
                transfer.Description,
                transfer.Reference,
                transfer.Obrservation,
                transfer.NameOrder,
                transfer.AccountOrder
            ]

            for field in transf_matching_fields:
                movs_by_fields = [
                    mov for mov in movs
                    if mov.StatementExtendedDescription
                       and field in mov.StatementExtendedDescription
                ]
                if len(movs_by_fields) == 1:
                    statement_id_str = movs_by_fields[0].InitialId
                    not_linked_reason = ''
                    break
        self.logger.info(
            '{}: get movement id by transfer: operational date={}, '
            'amount={}, statement id={}, not linked reason={}'.format(
                transfer.AccountId,
                transfer.OperationalDate.strftime(project_settings.SCRAPER_DATE_FMT),
                transfer.Amount,
                statement_id_str,
                not_linked_reason
            )
        )

        return statement_id_str, not_linked_reason

    def link_transfers_to_movements_bbva(self):
        # Updates transfers statement id with initial id of the associated movement
        db_transfers_null_statements = db_funcs.TransfersFuncs.get_transfers_w_statement_id_null(
            self._db_customer_id,
            self._fin_entity_name
        )  # type: List[DBTransfer]
        self.logger.info('link_transfers_to_movements_bbva: got {} '
                         'transfers where statement_id is null'.format(len(db_transfers_null_statements)))
        for transfer in db_transfers_null_statements:
            statement_id_str, not_linked_reason = self.get_movement_id_by_transfer_by_value_date(transfer)
            if project_settings.IS_UPDATE_DB:
                self._set_transfer_statement_id(
                    transfer.AccountId,
                    transfer.Id,
                    statement_id_str,
                    not_linked_reason
                )

        _ok = self.link_transfers_not_linked_due_to_multiple_statements_by_value_date()
        return True

    def link_transfers_to_movements_bankinter(self):
        # Updates transfers statement id with initial id of the associated movement
        db_transfers_null_statements = db_funcs.TransfersFuncs.get_transfers_w_statement_id_null(
            self._db_customer_id,
            self._fin_entity_name
        )  # type: List[DBTransfer]
        self.logger.info('link_transfers_to_movements_bankinter: got {} '
                         'transfers where statement_id is null'.format(len(db_transfers_null_statements)))
        for transfer in db_transfers_null_statements:
            statement_id_str, not_linked_reason = self.get_movement_id_by_transfer_by_operational_date(transfer)
            if project_settings.IS_UPDATE_DB:
                self._set_transfer_statement_id(
                    transfer.AccountId,
                    transfer.Id,
                    statement_id_str,
                    not_linked_reason
                )

        _ok = self.link_transfers_not_linked_due_to_multiple_statements_by_value_date()
        return True

    def _delete_duplicated_transfers_by_value_date(self) -> bool:
        """Delete duplicated transfers by ValueDate instead OperationalDate"""
        self.logger.info('delete duplicated transfers by ValueDate')
        if project_settings.IS_UPDATE_DB:
            db_funcs.TransfersFuncs.delete_duplicated_transfers_by_value_date(self._db_customer_id, self._fin_entity_name)
        return True

    def _delete_duplicated_transfers_by_operational_date(self) -> bool:
        """Delete duplicated transfers by OperationalDate"""
        self.logger.info('delete duplicated transfers by OperationalDate')
        if project_settings.IS_UPDATE_DB:
            db_funcs.TransfersFuncs.delete_duplicated_transfers_by_operational_date(self._db_customer_id, self._fin_entity_name)
        return True

    def link_transfers_not_linked_due_to_multiple_statements_by_value_date(self) -> bool:
        """ Try to link those transfers with multiple possible ascociated movements """

        self.logger.info('get transfers not linked to statement due to multiple possible statements')
        groups_of_transfers_not_linked = \
            self._get_groups_of_transfers_not_linked_due_to_multiple_statements_by_value_date()

        for group_of_transfers in groups_of_transfers_not_linked:
            fin_ent_account_id = group_of_transfers.FinancialEntityAccountId  # type: str
            account_id = group_of_transfers.AccountId  # type: int
            amount = group_of_transfers.Amount  # type: float
            # '13/03/2019'
            value_date_str = group_of_transfers.ValueDate  # type: str
            mov_ids_not_linked = self._get_statements_not_linked_due_to_multiple_transfers(
                fin_ent_account_id,
                account_id,
                amount,
                operational_date_str=None,
                value_date_str=value_date_str
            )
            transf_ids_not_linked = self._get_transfers_ids_not_linked_due_to_multiple_statements(
                fin_ent_account_id,
                account_id,
                amount,
                operational_date_str=None,
                value_date_str=value_date_str
            )
            for idx, transfer_id in enumerate(transf_ids_not_linked):
                not_linked_reason = ''
                len_transfers = group_of_transfers.FILAS  # type: int
                len_statements = len(mov_ids_not_linked)
                if len_transfers == len_statements:
                    initial_id_str = str(mov_ids_not_linked[idx])
                else:
                    initial_id_str = ID_STATEMENT_NO_VINCULABLE
                    not_linked_reason = (
                        'La Transferencia de la cuenta {} (id={}) con fecha valor={} y con importe={} '
                        'no se pudo vincular a movimiento porque se encontraron {} '
                        'transferencias y {} movimientos'.format(
                            fin_ent_account_id,
                            account_id,
                            value_date_str,
                            amount,
                            len_transfers,
                            len_statements
                        )
                    )
                self._set_transfer_statement_id(
                    account_id,
                    transfer_id,
                    initial_id_str,
                    not_linked_reason
                )

        return True

    def _get_groups_of_transfers_not_linked_due_to_multiple_statements_by_value_date(
            self
    ) -> List[GroupOfTransfersNotLinkedMultipleMovs]:
        """Get transfers not linked to statement due to multiple possible statements"""

        self.logger.info('get transfers not linked to statement due to multiple possible statements')
        transf_groups = db_funcs.TransfersFuncs.get_transfers_not_linked_due_to_multiple_statements_by_value_date()

        self.logger.info('got {} groups of transfers not linked to statement '
                         'due to multiple possible statements'.format(len(transf_groups)))

        return transf_groups

    def _get_transfers_ids_not_linked_due_to_multiple_statements(
            self,
            fin_ent_account_id: str,
            account_id: int,
            amount: float,
            operational_date_str: str = None,
            value_date_str: str = None) -> List[int]:
        """Get transfers ids not linked to transfer due to multiple
        possible statements for an account, amount and date
        date fmt is 31/12/2020
        """
        self.logger.info(
            '{} (id={}): get transfers ids not linked due to multiple statements: '
            'operational_date={}, value_date={}, amount={}'.format(
                fin_ent_account_id,
                account_id,
                operational_date_str,
                value_date_str,
                amount
            )
        )
        transf_ids = db_funcs.TransfersFuncs.get_transf_ids_not_linked_due_to_multiple_statements(
            account_id=account_id,
            operational_date_str=operational_date_str,
            value_date_str=value_date_str,
            amount=amount
        )

        return transf_ids

    def _set_transfer_statement_id(
            self,
            account_id: int,
            transfer_id: int,
            statement_id_str: str,
            not_linked_reason: str = '') -> bool:
        """Set transfer id statement and eventually not linked reason"""
        self.logger.info(
            'account id={}: set transfer statement_id: transfer_id={}, statement_id={}'.format(
                account_id,
                transfer_id,
                statement_id_str
            )
        )
        if project_settings.IS_UPDATE_DB:
            db_funcs.TransfersFuncs.set_transfer_statement_id(
                transfer_id=transfer_id,
                statement_id_str=statement_id_str,
                not_linked_reason=not_linked_reason
            )
        return True

    def _get_statements_not_linked_due_to_multiple_transfers(
            self,
            fin_ent_account_id: str,
            account_id: int,
            amount: float,
            operational_date_str: str = None,
            value_date_str: str = None) -> List[int]:
        """Get statements not linked to transfer due to multiple possible transfers
        date fmt is '31/12/2020'
        :returns [mov_id]
        """
        self.logger.info(
            '{} (id={}): get statements not linked due to multiple transfers: '
            'operational_date={}, value_date={}, amount={}'.format(
                fin_ent_account_id,
                account_id,
                operational_date_str,
                value_date_str,
                amount
            )
        )

        mov_ids = db_funcs.TransfersFuncs.get_mov_ids_not_linked_due_to_multiple_transfers(
            account_id=account_id,
            operational_date_str=operational_date_str,
            value_date_str=value_date_str,
            amount=amount
        )

        return mov_ids
