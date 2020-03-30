from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import errno
import fcntl
import getpass
import locale
import logging
import os
import random
import subprocess
import sys
import textwrap
import time

from struct import unpack, pack
from termios import TIOCGWINSZ

from hsuite import context, constants as C
from hsuite.utils._text import to_bytes, to_text
from hsuite.utils.six import with_metaclass
from hsuite.utils.color import stringc
from hsuite.utils.singleton import Singleton


class Display(with_metaclass(Singleton, object)):
    def __init__(self, verbosity=0):
        self.columns = None
        self.verbosity = verbosity

        self._set_column_width()

    def display(self, msg, color=None, stderr=False, screen_only=False, log_only=False, newline=True):
        """Display a message to the user.."""

        nocolor = msg
        if color:
            msg = stringc(msg, color)

        if not log_only:
            if not msg.endswith(u'\n') and newline:
                msg2 = msg + u'\n'
            else:
                msg2 = msg

            msg2 = to_bytes(
                msg2, encoding=self._output_encoding(stderr=stderr))
            if sys.version_info >= (3,):
                msg2 = to_text(msg2, self._output_encoding(
                    stderr=stderr), errors='replace')

            if not stderr:
                fileobj = sys.stdout
            else:
                fileobj = sys.stderr

            fileobj.write(msg2)

            try:
                fileobj.flush()
            except IOError as e:
                if e.errno != errno.EPIPE:
                    raise

    def v(self, msg):
        return self.verbose(msg, caplevel=0)

    def vv(self, msg):
        return self.verbose(msg, caplevel=1)

    def vvv(self, msg):
        return self.verbose(msg, caplevel=2)

    def debug(self, msg):
        if context.CLIARGS['debugging']:
            self.display(
                "%6d %0.5f: %s" % (os.getpid(), time.time(), msg), color=C.COLOR_DEBUG)

    def verbose(self, msg, caplevel=2):
        to_stderr = C.VERBOSE_TO_STDERR
        if self.verbosity > caplevel:
            self.display(msg, color=C.COLOR_VERBOSE, stderr=to_stderr)

    def warning(self, msg):
        self.display("[WARNING]: %s" % msg, color=C.COLOR_WARN, stderr=True)

    def banner(self, msg, color=C.COLOR_BANNER, cows=True):
        """
        Prints a header-looking line with cowsay or stars with length
        depending on terminal width (3 minimum).
        """

        msg = msg.strip()
        star_len = self.columns - len(msg)
        if star_len <= 3:
            star_len = 3

        stars = u"*" * star_len
        self.display("%s %s" % (msg, stars), color=color)

    def error(self, msg, wrap_text=True):
        self.display(
            "[ERROR]: %s" % msg, color=C.COLOR_ERROR, stderr=True)

    def critical(self, msg, ex=0):
        self.display(
            u"\n[CRITICAL]: %s" % msg, color=C.COLOR_CRITICAL, stderr=True)

        if exi:
            sys.exit(ex)

    @staticmethod
    def prompt(msg, private=False):
        prompt_string = to_bytes(msg, encoding=Display._output_encoding())
        if sys.version_info >= (3,):
            prompt_string = to_text(prompt_string)

        if private:
            return getpass.getpass(prompt_string)
        else:
            return input(prompt_string)

    @staticmethod
    def _output_encoding(stderr=False):
        encoding = locale.getpreferredencoding()
        if encoding in ('mac-roman',):
            encoding = 'utf-8'
        return encoding

    def _set_column_width(self):
        if os.isatty(0):
            tty_size = unpack('HHHH', fcntl.ioctl(
                0, TIOCGWINSZ, pack('HHHH', 0, 0, 0, 0)))[1]
        else:
            tty_size = 0
        self.columns = max(79, tty_size - 1)
