from custom_libs.db import db_funcs
from project import settings as project_settings

__version__ = '1.2.0'
__changelog__ = """
1.2.0
new path to call db funcs
1.1.0
__must_update_db
1.0.0
"""


class DBLogger:
    """Special logger to save messages into DB in accesos_Log table."""

    def __init__(
            self,
            logger_name: str,
            db_customer_id: int = None,
            db_financial_entity_access_id: int = None,
            fin_entity_name: str = None,
            launcher_id: str = project_settings.LAUNCHER_DEFAULT_ID) -> None:
        """
        :param logger_name: mapped to accesos_Log.Logger
        :param launcher_id: mapped to accesos_Log.Thread (think 'orchestraror execution thread')

        """
        self._db_customer_id = db_customer_id
        self._db_financial_entity_access_id = db_financial_entity_access_id
        self._logger_name = logger_name
        self._launcher_id = launcher_id
        self._fin_entity_name = fin_entity_name
        # Check once on init
        self._must_update_db = self.__must_update_db()

    def __must_update_db(self) -> bool:
        must = (
                not project_settings.IS_PRODUCTION_DB  # always update PRE
                or (
                        project_settings.IS_PRODUCTION_DB  # only if all conditions are True for PROD
                        and project_settings.IS_UPDATE_DB
                        and project_settings.IS_DEPLOYED
                )
        )
        return must

    def accesos_log_info(self, message: str, status: str = None) -> None:
        """Logs information trace into accesos_Log DB table for report purposes"""
        self.accesos_log(level='INFO', message=message, status=status)

    def accesos_log_error(self, message: str, exception_str: str = None, status: str = None) -> None:
        """Logs error trace into accesos_Log DB table for report purposes"""
        self.accesos_log(
            level='ERROR',
            message=message,
            exception_str=exception_str,
            status=status
        )

    def accesos_log(self,
                    level: str,
                    message: str,
                    exception_str: str = None,
                    status: str = None) -> None:
        """Logs into accesos_Log DB table for report purposes
        :param level: str like 'INFO', 'ERROR', mapped to accesos_Log.Level
        :param message: mapped to accesos_Log.Message
        :param exception_str: mapped to accesos_Log.Exception
        :param status: mapped to accesos_Log.Status
        """
        if self._must_update_db:
            db_funcs.DBLoggerFuncs.add_log_to_accesos_log(
                launcher_id=self._launcher_id,
                logger_name=self._logger_name,
                level=level,
                fin_entity_name=self._fin_entity_name,
                message=message,
                exception_str=exception_str,
                customer_id=self._db_customer_id,
                customer_financial_entity_access_id=self._db_financial_entity_access_id,
                status=status
            )
