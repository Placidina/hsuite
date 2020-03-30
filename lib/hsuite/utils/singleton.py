from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from threading import RLock


class Singleton(type):
    """Metaclass for classes that wish to implement Singleton functionality."""

    def __init__(cls, name, bases, dct):
        super(Singleton, cls).__init__(name, bases, dct)
        cls.__instance = None
        cls.__rlock = RLock()

    def __call__(cls, *args, **kw):
        if cls.__instance is not None:
            return cls.__instance

        with cls.__rlock:
            if cls.__instance is None:
                cls.__instance = super(Singleton, cls).__call__(*args, **kw)

        return cls.__instance
