# -*- coding: utf-8 -*-

from colorama import Fore, Back, Style
import commands
from datetime import datetime
import serial
from subprocess import call
import sys
import threading
import time

from alarm.config import ARMCODE, DISARMCODE, MUTECODE, STATUSCODE
from alarm.console import Console
from alarm.imap import IMAP
from alarm.shared import ENV, LOGS
from alarm.smtp import SMTP
from alarm.rest import app


class Log(object):
    _alert_in = Fore.BLACK + Back.RED
    _alert_out = Fore.RESET + Back.RESET
    _warn_in = Fore.CYAN
    _warn_out = Fore.RESET
    _distant_in = Fore.YELLOW
    _distant_out = Fore.RESET

    def __init__(self):
        if not sys.stdout.isatty():
            self._alert_in = None
            self._alert_out = None
            self._warn_in = None
            self._warn_out = None
            self._distant_in = None
            self._distant_out = None

    def alert(self, line):
        sys.stdout.write(self._alert_in + line + self._alert_out)

    def warn(self, line):
        sys.stdout.write(self._warn_in + line + self._warn_out)

    def print_distant(self, line):
        sys.stdout.write(self._distant_in + line + self._distant_out)

    def print_local(self, line):
        sys.stdout.write(line)


class Miniterm(object):

    receiver_thread = None
    transmitter_thread = None
    poller_thread = None
    imap_server = None
    api_thread = None
    imap_api_thread = None
    alive = False

    def __init__(self, config):
        self.config = config

        self.console = Console()
        self.console.setup()
        self.log = Log()

        try:
            self.serial = serial.serial_for_url(self.config.port,
                                                self.config.baudrate,
                                                parity='N',
                                                rtscts=False,
                                                xonxoff=False,
                                                timeout=1)
        except AttributeError:
            # happens when the installed pyserial is older than 2.5. use the
            # Serial class directly then.
            self.serial = serial.Serial(self.config.port,
                                        self.config.baudrate,
                                        parity='N',
                                        rtscts=False,
                                        xonxoff=False,
                                        timeout=1)

        self.log.print_local('--- Miniterm on %s: %d,%s,%s ---\n' % (
            self.serial.portstr,
            self.serial.baudrate,
            self.serial.bytesize,
            self.serial.stopbits,
        ))

        self.log.print_local('--- Menu: %s | Help: %s %s | Quit: %s %s ---\n' %
            (config.menu_char, config.menu_char, '\x08',
             config.menu_char, config.exit_char))

        self.echo = False
        self.convert_outgoing = 1 #  CONVERT_CR
        self.newline = '\r' #  CR
        self.dtr_state = True
        self.rts_state = True
        self.break_state = False
        self.host = self.config.options.host
        self.username = self.config.options.username
        self.mail_to = (self.config.options.mail_to
                        or self.config.options.username)
        self.password = self.config.options.password
        self.api_host = self.config.options.api_host
        self.email_api = self.config.options.email_api

        self.smtp = SMTP(self.username, self.password, self.host,
                         self.username, self.mail_to)

    def get_help_text(self):
        return """
--- pySerial (%(version)s) - alarme - help
---
--- %(exit)-8s Exit program
--- %(menu)-8s Menu escape key, followed by:
--- Menu keys:
---       %(itself)-8s Send the menu character itself to remote
---       %(exchar)-8s Send the exit character to remote
---       %(photo)-8s Send a picture from the webcam
---
""" % {'version': getattr(serial, 'VERSION', 'unkown'),
       'exit': self.config.exit_char,
       'menu': self.config.menu_char,
       'itself': self.config.menu_char,
       'exchar': self.config.exit_char,
       'photo': self.config.photo_char}

    def start(self):
        self.alive = True
        # start serial->console thread
        self.receiver_thread = threading.Thread(target=self.reader)
        self.receiver_thread.setDaemon(1)
        self.receiver_thread.start()

        # enter console->serial loop
        self.transmitter_thread = threading.Thread(target=self.writer)
        self.transmitter_thread.setDaemon(1)
        self.transmitter_thread.start()

        # poll on actions
        self.poller_thread = threading.Thread(target=self.poller)
        self.poller_thread.setDaemon(1)
        self.poller_thread.start()

        # poll on the mailbox
        if self.email_api:
            self.imap_server = IMAP(self.username, self.password, self.host)
            self.imap_api_thread = threading.Thread(target=self.imap_api)
            self.imap_api_thread.setDaemon(1)
            self.imap_api_thread.start()

        self.api_thread = threading.Thread(target=self.api)
        self.api_thread.setDaemon(1)
        self.api_thread.start()

    def stop(self):
        self.alive = False

    def join(self, transmit_only=False):
        self.transmitter_thread.join()
        if not transmit_only:
            self.receiver_thread.join()

    def _send_email(self, title, message=None, images=None):
        self.log.print_local('sending message to %s\n' % self.mail_to)
        self.smtp.send_mail(title, message or '', images, self.mail_to)
        self.log.print_local('done\n')

    def send_image(self, message):
        self.log.print_local('taking photos')

        title = '[Alarm] %s' % (datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

        filename = '/tmp/image_%03d.jpeg'
        images = [filename % i for i in range(0, 3)]
        for image in images:
            self.log.print_local('.')
            cmd = 'streamer -t 1 -r 2 -o %s' % image
            commands.getoutput(cmd)

            call(['convert', '-resize', '32x32', '-colors', '32', image,
                  '%s.png' % image])
            time.sleep(1)

        self.log.print_local('\n')

        diff = '%s.png' % (filename % 4)
        call(['composite', '-compose', 'subtract', '%s.png' % images[-2],
              '%s.png' % images[-1], diff])
        images.append(diff)

        self._send_email(title, message or '', images)

    def send_message(self, message):
        title = '[Alarm] %s' % (datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        self._send_email(title, message)

    def parse(self, line):
        LOGS.append("%s : %s" % (
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"), line))
        if line.startswith('ALARM:'):
            ENV.send_image_f = LOGS.last()
        elif line.startswith('ERROR:'):
            ENV.send_message_f = LOGS.last()
        elif line.startswith('INFO: The alarm is') and ENV.get_status:
            ENV.get_status = False
            ENV.status = line

    def api(self):
        try:
            app.run(host=self.api_host)
        except:
            self.log.print_local('Rest API closed')

    def imap_api(self):
        if self.imap_server:
            while self.alive:
                self.imap_server.run()
                time.sleep(30)

    def poller(self):
        while self.alive:
            if ENV.send_image_f:
                self.send_image(ENV.send_image_f)
                ENV.send_image_f = False

            if ENV.send_message_f:
                self.send_message(ENV.send_message_f)
                ENV.send_message_f = False

            if ENV.arm:
                self.serial.write('%s%s' % (ARMCODE, ENV.level))
                ENV.arm = False

            if ENV.disarm:
                self.serial.write(DISARMCODE)
                ENV.disarm = False

            if ENV.mute:
                self.serial.write(MUTECODE)
                ENV.mute = False

            if ENV.get_status:
                self.serial.write(STATUSCODE)

            time.sleep(5)

    def reader(self):
        """loop and copy serial->console"""
        try:
            line = ''
            while self.alive:
                data = self.serial.read(1)
                if data == '\r':
                    continue

                line += data
                if data == '\n':
                    self.log.print_distant(datetime.now().strftime(
                        "%d/%m/%Y %H:%M:%S>  "))
                    if line.startswith('ALARM:'):
                        self.log.alert(line)
                    elif line.startswith('EVENT:') or line.startswith('INFO'):
                        self.log.warn(line)
                    else:
                        self.log.print_distant(line)
                    self.parse(line.strip())
                    line = ''

                sys.stdout.flush()

        except serial.SerialException:
            self.alive = False
            # would be nice if the console reader could be interruptted at this
            # point...
            raise

    def writer(self):
        """loop and copy console->serial until config.exit_char character is
           found. when config.menu_char is found, interpret the next key
           locally.
        """
        menu_active = False
        try:
            while self.alive:
                try:
                    char = self.console.getkey()
                except KeyboardInterrupt:
                    char = '\x03'

                if menu_active:
                    # Menu character again/exit char -> send itself
                    if char in self.config.menu_char:
                        self.serial.write(char)  # send character
                    elif char in self.config.exit_char:
                        self.stop()
                        break  # exit app
                    elif char in 'hH?':  # h, H, ? -> Show help
                        sys.stderr.write(self.get_help_text())
                    elif char in self.config.photo_char:
                        ENV.send_image_f = "Asked by console"
                    else:
                        sys.stderr.write('--- unknown menu character %s ---\n' %
                                         char)
                    menu_active = False
                elif char in self.config.menu_char: # next char will be for menu
                    menu_active = True
                elif char == '\n' or ord(char) == 10:
                    sys.stderr.write('\n')
                else:
                    self.serial.write(char)  # send character
        except:
            self.alive = False
            raise
