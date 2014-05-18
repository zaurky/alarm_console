# -*- coding: utf-8 -*-

from datetime import datetime
import sys

import email
from email.utils import parseaddr
import gnupg
from imapclient import IMAPClient, SEEN

from alarm.shared import Action
from alarm.smtp import SMTP


class IMAP(object):
    server = None

    def __init__(self, username, password, server):
        self.host = server
        self.username = username
        self.password = password

        self.login()
        self.gpg = gnupg.GPG()

        self.smtp = SMTP(username, password, server, username, username)

        sys.stderr.write('--- Imap api initialized ---\n')

    def login(self):
        self.server = IMAPClient(self.host, use_uid=False, ssl=True)
        self.server.login(self.username, self.password)

    def get_from(self, msgid):
        subject = self.server.fetch(msgid, ['BODY[HEADER.FIELDS (FROM)]'])
        return subject[1]['BODY[HEADER.FIELDS (FROM)]'].strip().replace(
                'From: ', '')

    def get_body(self, _msgid):
        return self.server.fetch(1, ['BODY'])[1]['BODY']

    @staticmethod
    def _get_content(body):
        for line in [line.strip() for line in body.split('\n')]:
            if line == '-----BEGIN PGP SIGNATURE-----':
                return
            if (line.startswith('----')
                or line.startswith('Hash:')
                or line == ''):
                continue
            yield line

    def get_content(self, body):
        return '\n'.join(self._get_content(body))

    _params = {
        'arm': ['level', 2],
    }

    def logs(self, mail_to, title):
        title = '[Alarm] %s %s' % (
                datetime.now().strftime("%d/%m/%Y %H:%M:%S"), title)
        logs = Action.logs()
        self.smtp.send_mail(title, logs, mail_to=mail_to)

    def run(self):
        for action in ['alive', 'photo', 'status', 'arm', 'disarm',
                       'mute', 'logs', 'droplogs', 'alive']:

            try:
                _select_info = self.server.select_folder(action)
            except:
                self.login()
                _select_info = self.server.select_folder(action)

            messages = self.server.search(['NOT SEEN'])

            if not messages:
                continue

            sys.stderr.write('%d messages in %s\n' % (len(messages), action))

            msgids = []
            response = self.server.fetch(messages, ['FLAGS', 'RFC822.SIZE'])
            for msgid, data in response.iteritems():
                msgids.append(msgid)
                if action == 'alive':
                    open('/var/local/alarm.imap.alive', 'a').close()
                    continue

                sys.stderr.write('   ID %d: %d bytes, flags=%s\n' % (msgid,
                                                        data['RFC822.SIZE'],
                                                        data['FLAGS']))

                msg = self.server.fetch([msgid], ['RFC822'])
                msg = email.message_from_string(msg[msgid]['RFC822'])
                _name, mail_from = parseaddr(msg['from'])
                body = msg.get_payload()
                try:
                    verify = self.gpg.verify(body)
                except:
                    continue

                if verify.valid:
                    if action != self.get_content(body):
                        continue
                    sys.stderr.write('Asked by %s' % verify.username)

                    # TODO handle arm params
                    if hasattr(self, action):
                        getattr(self, action)(mail_from, action)
                    else:
                        getattr(Action, action)()

            sys.stderr.write("put %s as seen\n" % msgids)
            self.server.set_flags(msgids, [SEEN])
