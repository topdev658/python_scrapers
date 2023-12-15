import datetime
import logging
import traceback
from concurrent import futures
from typing import Union

from raven import Client

from custom_libs.send_email import email_err_notifications
from project import settings as project_settings
from project.custom_types import DOUBLE_AUTH_REQUIRED_TYPE_COMMON

# from custom_libs.send_email import email_warn_notifications

__version__ = '4.2.0'

__changelog__ = """
4.2.0
use ERR_BALANCE_NOTIFICATION_EMAILS, ERR_NOT_BALANCE_NOTIFICATION_EMAILS
4.1.0
log_credentials_error with optional last_resp_url, last_resp_text
4.0.0
removed accesos_log.. methods (moved to DBLogger) 
3.12.0
accesos_log..: more params, renamed params
more type hints
3.11.0
accesos_log_info
accesos_log_error
accesos_log
3.10.0
_msg with shorter prefixes
3.9.0
don't send emails with 'DOUBLE AUTH' messages
optimize imports
3.8.0
is_sentry as param
3.7.1
detected reason: changed msg
3.7.0
log_non_credentials_error_w_reason
changed text in login-related err msgs
3.6.0
ScrapeLogger.error: now supports is_print, is_send_email, is_html options
3.5.0
Don't send err msgs to Sentry (commented related code),
bcs Sentry will be used only to log 'start scraping' events from main_launcher
Comments upd
3.4.0
warning: don't send email
3.3.3
log_non_credentials_error: upd msg
3.3.2
print warning msg with time and level info
3.3.1
fixed print msg
3.3.0
utcnow
3.2.0
add datetime info for print functions to get time of probable segfaults explicitly
3.1.0
sentry integration
3.0.0
log_futures_exc: is_success result
2.1.0
+ warning
2.0.1
todo added
2.0.0
log_credentials_error
log_non_credentials_error
1.1.0
traceback
"""


class ScrapeLogger:
    """Logger with additional scraper-based information in logs.
    It adds data to log message:
    - scraper name;
    - db_customer_id;
    - db_financial_entity_access_id.
    """

    def __init__(
            self,
            scraper_name: str,
            db_customer_id: Union[None, int, str],
            db_financial_entity_access_id: Union[None, int, str],
            db_logger_name: str = None):
        """
        :param scraper_name: ...
        :param db_customer_id: ...
        :param db_financial_entity_access_id: ...
        :param db_logger_name: special logger name used by accesos_log.. functions,
                               it will be writen into accesos_Log table (Logger field);
                               if not provided, then scraper_name will be used
        """
        self._scraper_name = scraper_name
        self._db_customer_id = db_customer_id
        self._db_financial_entity_access_id = db_financial_entity_access_id
        self._db_logger_name = db_logger_name or scraper_name  # only for accesos_Log table
        self.sentry_client = Client(project_settings.SENTRY_API_TOKEN)

    def _msg(self, text: str, is_html=False) -> str:
        """
        :param text: msg text
        :param is_html: if True, then wraps text into <html> tags and replaces '\n' to <br>
        :returns formatted message with necessary prefixes
        """
        msg = (
            "{scraper_name}: "
            "-u {customer_id} -a {fin_entity_access_id}: "
            "{text}".format(
                scraper_name=self._scraper_name,
                customer_id=self._db_customer_id,
                fin_entity_access_id=self._db_financial_entity_access_id,
                text=text
            )
        )
        if is_html:
            msg = msg.replace('\n', '<br>')
            msg = ('<html><head>{}</head>'
                   '<body>{}</body></html>'.format(project_settings.MSG_HTML_STYLES, msg))
        return msg

    def _print(self, level: str, msg: str) -> None:
        now = '{}'.format(datetime.datetime.utcnow())[:19]
        print('{}:{}:{}'.format(now, level, msg))

    def info(self, text: str) -> None:
        msg = self._msg(text)
        self._print('INFO', msg)
        logging.info(msg)

    def error(self, text: str, is_print=True, is_send_email=True, is_html=False, is_sentry=True) -> None:
        """Use only for:
        - to log expected raised exceptions, not for business logic;
        - to log expected layout errors - those errors are critical;
        - to log login errors.
        All those errors are important, in other cases use info()

        + Sends err email notification
        :param text: msg text
        :param is_print: allows to  explicitly suppress printing
            (default is True)
        :param is_send_email: allows to explicitly suppress email sending
            It is necessary only to allow to send different messages to
            text output (file/stderr) and to email boxes.
            In any case, then send_email.email_err_notifications
            checks project settings and sends only if it is allowed their
            (default is True)
        :param is_html: set to true if you want to send html message
            Note: don't wrap your msg into <html> and <body> tags,
            don't use <style> - they will be added automatically
            (default is False)
        :param is_sentry: send to sentry or not
        """
        msg = self._msg(text, is_html)
        if is_print:
            self._print('ERROR', msg)
            logging.error(msg)
        if is_sentry:
            self.sentry_client.captureMessage(msg)

        # Don't send also 'DOUBLE AUTH' emails (we keep the history in sentry, logs and DB)
        if not is_send_email or (DOUBLE_AUTH_REQUIRED_TYPE_COMMON in msg):
            return

        if 'BALANCE INTEGRITY' in msg:
            email_err_notifications(msg, project_settings.ERR_BALANCE_NOTIFICATION_EMAILS, is_html)
        else:
            email_err_notifications(msg, project_settings.ERR_NOT_BALANCE_NOTIFICATION_EMAILS, is_html)

    def warning(self, text: str, is_sentry=True) -> None:
        """Use only for:  movements comparator"""

        msg = self._msg(text)
        self._print('WARNING', msg)
        logging.warning(msg)
        if is_sentry:
            self.sentry_client.captureMessage(msg, level='warning')
        # Commented to reduce number of msgs and emails
        # email_warn_notifications(msg)

    def log_futures_exc(self, function_title: str, futures_dict: dict) -> bool:
        """Handles exceptions of the futures.
        Use only to log exceptions if there are no results,
        or implement similar handler in the main function of the scraper to process results in place.
        :returns: is_success based on func results (is_success=False only if func result==False or Exception)
        """
        is_success = True
        for future in futures.as_completed(futures_dict):
            future_id = futures_dict[future]
            try:
                result = future.result()
                # Note: only exactly False result are handled as unsuccessful
                if result is False:
                    self.info(
                        '{function_title} failed: {future_id}: {result}'.format(
                            function_title=function_title,
                            future_id=future_id,
                            result=result
                        )
                    )
                    is_success = False
                else:
                    self.info(
                        '{function_title} success: {future_id}: {result}'.format(
                            function_title=function_title,
                            future_id=future_id,
                            result=result
                        )
                    )

            except Exception as exc:
                self.error(
                    '{function_title} failed: {future_id}: !!! EXCEPTION !!! {exc}'.format(
                        function_title=function_title,
                        future_id=future_id,
                        exc=traceback.format_exc()
                    )
                )
                is_success = False
        return is_success

    def log_credentials_error(self, last_resp_url: str = None, last_resp_text: str = None) -> None:
        if last_resp_url and last_resp_text:
            self.error("Can't log in. Wrong credentials. Set financial entity inactive. LAST RESPONSE:\n{}\n{}".format(
                last_resp_url,
                last_resp_text
            ))
        else:
            self.error("Can't log in. Wrong credentials. Set financial entity inactive")

    def log_non_credentials_error(self, current_url: str, page_source: str) -> None:
        """Log and send err notification with details (url, response_text)"""
        self.error(
            "Can't log in. Unknown reason (not a credentials error). "
            "Try later. Finishing now.\nRESPONSE:\n{}\n{}".format(current_url, page_source)
        )

    def log_non_credentials_error_w_reason(self, current_url: str, page_source: str, reason: str) -> None:
        """Log and send err notification with details (reason, url, response text)"""
        self.error(
            "Can't log in. DETECTED REASON: {}\n"
            "Try later. Finishing now.\nRESPONSE:\n{}\n{}".format(reason, current_url, page_source)
        )
