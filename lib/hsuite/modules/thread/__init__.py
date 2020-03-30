from __future__ import absolute_import, division, print_function
__metaclass__ = type

from threading import Thread as T, Lock as LockThread

from hsuite.utils.six import PY3

if PY3:
    class Thread(T):
        def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
            T.__init__(self, group, target, name, args, kwargs)
            self._return = None

        def run(self):
            if self._target is not None:
                self._return = self._target(*self._args, **self._kwargs)

        def wait(self, *args):
            T.join(self, *args)
            return self._return
else:
    class Thread(T):
        def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, verbose=None):
            T.__init__(self, group, target, name, args, kwargs, verbose)
            self._return = None

        def run(self):
            if self._Thread__target is not None:
                self._return = self._Thread__target(
                    *self._Thread__args, **self._Thread__kwargs)

        def join(self):
            T.join(self)
            return self._return
