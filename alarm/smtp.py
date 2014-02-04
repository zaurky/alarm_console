# -*- coding: utf-8 -*-

import atexit
import os
from functools import wraps

from smtplib import SMTP as SMTPLib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart


def relog(method):
    """ restart the smtp connection when no longer active """
    @wraps(method)
    def _relog(self, *args, **kwargs):
        if self.server.noop()[0] != 250:
            self.login()
        return method(self, *args, **kwargs)
    return _relog


class SMTP(object):
    """ Class to handle smtp connection and email sending """

    def __init__(self, username, password, host, mail_from, mail_to):
        self.mail_from = mail_from
        self.mail_to = mail_to

        self.username = username
        self.password = password
        self.host = host

        self.login()
        atexit.register(self.quit)

    def login(self):
        self.server = SMTPLib(self.host)
        self.server.login(self.username, self.password)

    def quit(self):
        if self.server.noop()[0] == 250:
            self.server.quit()

    def format_msg(self, title, desc, images=None, mail_to=None):
        """ create a MIMEMultipart with this title, desc, and images """
        msg = MIMEMultipart()
        msg['Subject'] = title
        msg['From'] = self.mail_from
        msg['To'] = mail_to or self.mail_to

        if images:
            for image in images:
                if os.path.exists(image):
                    msg.attach(MIMEImage(file(image).read()))
        msg.attach(MIMEText(desc))

        return msg.as_string()

    @relog
    def send_mail(self, title, desc, images=None, mail_to=None):
        """ send the given MIMEMultipart """
        msg = self.format_msg(title, desc, images, mail_to)
        self.server.sendmail(self.mail_from, mail_to or self.mail_to, msg)
