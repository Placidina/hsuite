from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from hsuite.utils._text import to_native


class HSuiteError(Exception):
    def __init__(self, message="", obj=None, show_content=True, suppress_extended_error=False, orig_exc=None):
        super(HSuiteError, self).__init__(message)

        self.message = "%s" % to_native(message)
        if orig_exc:
            self.orig_exc = orig_exc

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message


class HSuiteAssertionError(HSuiteError, AssertionError):
    """Invalid assertion."""

    pass


class HSuiteOptionsError(HSuiteError):
    """Bad or incomplete options passed."""

    pass


class HSuiteParserError(HSuiteError):
    """Something was detected early that is wrong about a playbook or data file."""

    pass
