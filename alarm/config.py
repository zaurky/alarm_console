# -*- coding: utf-8 -*-

from optparse import OptionParser
import yaml

try:
    from yaml import CSafeLoader as YAMLLoader
except ImportError:
    from yaml import SafeLoader as YAMLLoader


class Config(OptionParser):
    exit_char = 'q'
    menu_char = 'm'
    photo_char = 'p'
    _conf = None

    def __init__(self, usage=None, description=None):
        with open('/etc/alarmapi.yaml') as fdesc:
            self._conf = yaml.load(fdesc, YAMLLoader)

        OptionParser.__init__(self, usage=usage, description=description)
        self.add_option("-p", "--port",
            dest = "port",
            help = "port, a number (default 0) or a device name",
            default = self._conf['main'].get('port'),
        )

        self.add_option("-b", "--baud",
            dest = "baudrate",
            action = "store",
            type = 'int',
            help = "set baud rate, default %default",
            default = self._conf['main'].get('baud', 115200),
        )
        self.add_option('--image', dest='image',
                        default=self._conf['main'].get('image'))

        self.add_option('--host', dest='host',
                        default=self._conf['email'].get('host'))
        self.add_option('--username', dest='username',
                        default=self._conf['email'].get('username'))
        self.add_option('--password', dest='password',
                        default=self._conf['email'].get('password'))
        self.add_option('--mail_to', dest='mail_to',
                        default=self._conf['email'].get('mail_to'))
        self.add_option('--enable_email_api', dest='email_api',
                        default=self._conf['email'].get('enable_api', False))

        self.add_option('--api_host', dest='api_host',
                        default=self._conf['rest'].get('host'))
        self.add_option('--disable_rest_api', dest='rest_api',
                        default=self._conf['rest'].get('disable_api', False))

        (self.options, args) = self.parse_args()

        port = self.options.port
        baudrate = self.options.baudrate
        if args:
            if self.options.port is not None:
                self.error("no arguments are allowed,"
                           " options only when --port is given")
            self.options.port = args.pop(0)
            if args:
                try:
                    baudrate = int(args[0])
                except ValueError:
                    self.error("baud rate must be a number, not %r" % args[0])
                args.pop(0)
            if args:
                self.error("too many arguments")
        else:
            if port is None:
                self.options.port = 0

    @property
    def port(self):
        return self.options.port

    @property
    def baudrate(self):
        return self.options.baudrate


ARMCODE = "1"
DISARMCODE = "2"
MUTECODE = "3"
STATUSCODE = "4"
