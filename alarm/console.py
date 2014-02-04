# -*- coding: utf-8 -*-

import os
import sys
import termios
import atexit


class Console:
    def __init__(self):
        self.fd = sys.stdin.fileno()
        atexit.register(self.cleanup)

    def setup(self):
        self.old = termios.tcgetattr(self.fd)
        new = termios.tcgetattr(self.fd)
        new[3] = new[3] & ~termios.ICANON & ~termios.ECHO & ~termios.ISIG
        new[6][termios.VMIN] = 1
        new[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, new)

    def getkey(self):
        return os.read(self.fd, 1)

    def cleanup(self):
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old)
