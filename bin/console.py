#!/usr/bin/python

import serial
import sys

from alarm.config import Config
from alarm.miniterm import Miniterm


def main():
    try:
        config = Config(usage = "%prog [options] [port [baudrate]]",
                        description = "Miniterm - A simple terminal program "
                                      "for the serial port.")

        miniterm = Miniterm(config)
    except serial.SerialException, err:
        sys.stderr.write("could not open port %r: %s\n" % (config.port, err))
        sys.exit(1)

    miniterm.start()
    miniterm.join(True)

    sys.stderr.write("\n--- exit ---\n")
    miniterm.join()


if __name__ == '__main__':
    main()
