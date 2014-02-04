# -*- coding: utf-8 -*-

import time


class Logs(object):
    _list = []

    def append(self, thing):
        self._list.append(thing)

    def reset(self):
        self._list = []

    def __repr__(self):
        return "\n".join(self._list)

    def html(self):
        return "<br/>".join(self._list)

    def last(self, num=3):
#        return "\n".join([line for line in self._list
#                          if line.startswith('EVENT:')
#                              or line.startswith('ALARM:')][-num:])
        return "\n".join(self._list[-num:])

    def last_html(self, num=3):
        return "<br/>".join(self._list[-num:])


LOGS = Logs()


class Env(object):
    def __init__(self):
        self.send_image_f = False
        self.send_message_f = False

        self.level = 1
        self.arm = False
        self.disarm = False
        self.mute = False

        self.status = None
        self.get_status = False


ENV = Env()


class Action(object):
    @staticmethod
    def alive():
        return "True"

    @staticmethod
    def photo():
        ENV.send_image_f = "Photo asked by rest API"
        return "True"

    @staticmethod
    def status():
        ENV.status = None
        ENV.get_status = True
        while not ENV.status:
            time.sleep(1)

        return ENV.status

    @staticmethod
    def arm(level=1):
        ENV.arm = True
        ENV.level = level
        return "Done"

    @staticmethod
    def disarm():
        ENV.disarm = True
        return "Done"

    @staticmethod
    def mute():
        ENV.mute = True
        return "Done"

    @staticmethod
    def logs():
        return LOGS.html()

    @staticmethod
    def droplogs():
        html = LOGS.html()
        LOGS.reset()
        return html
