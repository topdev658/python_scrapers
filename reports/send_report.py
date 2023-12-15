import os
import sys
import time
import smtplib
import traceback
from email.mime.text import MIMEText


__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""


# http://stackoverflow.com/questions/10147455/how-to-send-an-email-with-gmail-as-provider-using-python
# https://stackoverflow.com/questions/5910104/python-how-to-send-utf-8-e-mail
def _send_email(user, pwd, to, subject, body, is_html=False):
    if not to:
        return

    gmail_user = user
    gmail_pwd = pwd
    sender = user
    recipients = to if type(to) is list else [to]

    msg = MIMEText(body)
    msg.set_charset("utf-8")
    if is_html:
        msg.set_type('text/html')

    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    try:
        server = smtplib.SMTP("smtp1.eurovia.es", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(sender, recipients, msg.as_string())
        server.close()
        print('emailed successfully')
    except:
        print(traceback.format_exc())

def email_err_notifications(body_text, to_list, subject):
    if True:
        try:
            _send_email(
                user='smtp@tesoralia.com',
                pwd='EurfhhxW3jnq7V',
                to=to_list,
                subject=subject,
                body=body_text,
                is_html=False
            )
        except:
            print(traceback.format_exc())


def get_text_body():
	f = open('.body','r')
	text_body = f.read()
	f.close()
	return text_body
	

if __name__ == '__main__':
   
    to = os.environ['TO']
    to_list = to.split(",");

    subject = os.environ['SUBJECT']
    #print("to: {}".format(to_list))
    #print("subject: {}".format(subject))
    #sys.exit(0)
    email_err_notifications(get_text_body(), to_list, subject)
    print('Done')

