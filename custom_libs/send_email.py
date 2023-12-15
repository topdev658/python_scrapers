import smtplib
import socket
from email.mime.text import MIMEText
from typing import List, Union

from custom_libs import log
from project import settings as project_settings

__version__ = '2.5.0'

__changelog__ = """
2.5.0
email_err_notifications: now accepts recipients, hostname in subj
2.4.1
recipients: check type using isinstance (for linters)
2.4.0
log short exception descr if can't send email
2.3.0
disable sentry notif if can't send email
2.2.0
send html if necessary
2.1.2
msg upd
2.1.1
fix err if empty TO
2.1.0
send non-ascii text
2.0.0
err and warn notifications different emails
1.1.0
email_warn_notifications
"""


# http://stackoverflow.com/questions/10147455/how-to-send-an-email-with-gmail-as-provider-using-python
# https://stackoverflow.com/questions/5910104/python-how-to-send-utf-8-e-mail
def _send_email(user: str, pwd: str, to: Union[str, List[str]],
                subject: str, body: str, is_html=False):
    if not to:
        return

    try:
        gmail_user = user
        gmail_pwd = pwd
        sender = user
        recipients = to if isinstance(to, list) else [to]

        msg = MIMEText(body)
        msg.set_charset("utf-8")
        if is_html:
            msg.set_type('text/html')

        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(sender, recipients, msg.as_string())
        server.close()
        print('emailed successfully')
    except Exception as exc:
        log.log_err("Can't send email: {}".format(exc), is_sentry=False)


def _host() -> str:
    """Short host name"""
    return socket.gethostname().split('.')[0]


def email_err_notifications(text: str, to: List[str], is_html=False):
    if project_settings.IS_SEND_NOTIFICATIONS:
        _send_email(
            user='tesnotificator@gmail.com',
            pwd='tes1notificator2',
            to=to,
            subject='Tesoralia: scraping ERROR ({})'.format(_host()),
            body=text,
            is_html=is_html
        )


def email_warn_notifications(text: str, is_html=False):
    if project_settings.IS_SEND_NOTIFICATIONS:
        _send_email(
            user='tesnotificator@gmail.com',
            pwd='tes1notificator2',
            to=project_settings.WARN_NOTIFICATION_EMAILS,
            subject='Tesoralia: scraping WARNING ({})'.format(_host()),
            body=text,
            is_html=is_html
        )


if __name__ == '__main__':
    msg_html = """
    <html>
        <head>
            <style>
                th, td {border: 1px solid #ddd;}
            </style>
        </head>
        <body>
            
            <table cellspacing="0">
                <tr>
                    <th>v1</th>
                    <th>v2</th>
                </tr>
                <tr>
                    <td>1:1</td>
                    <td>1:2</td>
                </tr>
                <tr>
                    <td>2:1</td>
                    <td>2:2</td>
                </tr>
            </table>
        </body>
    </html>
    """
    email_err_notifications(msg_html, to=project_settings.ERR_NOT_BALANCE_NOTIFICATION_EMAILS, is_html=True)
    # email_err_notifications('== TEST TEST TEST ==\n err notification')
    # email_warn_notifications('== TEST TEST TEST ==\n warn notification')
    print('Done')
