import codecs
import string
import random

from hsuite.utils.six import PY3, text_type, binary_type


try:
    codecs.lookup_error('surrogateescape')
    HAS_SURROGATEESCAPE = True
except LookupError:
    HAS_SURROGATEESCAPE = False


_COMPOSED_ERROR_HANDLERS = frozenset((None, 'surrogate_or_replace',
                                      'surrogate_or_strict',
                                      'surrogate_then_replace'))


def to_bytes(obj, encoding='utf-8', errors=None, nonstring='simplerepr'):
    """Make sure that a string is a byte string."""

    if isinstance(obj, binary_type):
        return obj

    original_errors = errors
    if errors in _COMPOSED_ERROR_HANDLERS:
        if HAS_SURROGATEESCAPE:
            errors = 'surrogateescape'
        elif errors == 'surrogate_or_strict':
            errors = 'strict'
        else:
            errors = 'replace'

    if isinstance(obj, text_type):
        try:
            return obj.encode(encoding, errors)
        except UnicodeEncodeError:
            if original_errors in (None, 'surrogate_then_replace'):
                return_string = obj.encode('utf-8', 'surrogateescape')
                return_string = return_string.decode('utf-8', 'replace')
                return return_string.encode(encoding, 'replace')
            raise

    if nonstring == 'simplerepr':
        try:
            value = str(obj)
        except UnicodeError:
            try:
                value = repr(obj)
            except UnicodeError:
                return to_bytes('')
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'empty':
        return to_bytes('')
    elif nonstring == 'strict':
        raise TypeError("obj must be a string type")
    else:
        raise TypeError(
            "Invalid value %s for to_bytes' nonstring parameter" % nonstring)

    return to_bytes(value, encoding, errors)


def to_text(obj, encoding='utf-8', errors=None, nonstring='simplerepr'):
    """Make sure that a string is a text string."""

    if isinstance(obj, text_type):
        return obj

    if errors in _COMPOSED_ERROR_HANDLERS:
        if HAS_SURROGATEESCAPE:
            errors = 'surrogateescape'
        elif errors == 'surrogate_or_strict':
            errors = 'strict'
        else:
            errors = 'replace'

    if isinstance(obj, binary_type):
        return obj.decode(encoding, errors)

    if nonstring == 'simplerepr':
        try:
            value = str(obj)
        except UnicodeError:
            try:
                value = repr(obj)
            except UnicodeError:
                return u''
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'empty':
        return u''
    elif nonstring == 'strict':
        raise TypeError("obj must be a string type")
    else:
        raise TypeError(
            "Invalid value %s for to_text's nonstring parameter" % nonstring)

    return to_text(value, encoding, errors)


def random_string(size=6):
    """Generate a random string of fixed size."""

    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(size))


#: :py:func:`to_native`
#:      Transform a variable into the native str type for the python version
#:
#:      On Python2, this is an alias for
#:      :func:`~*.utils.to_bytes`.  On Python3 it is an alias for
#:      :func:`~*.utils.to_text`.  It makes it easier to
#:      transform a variable into the native str type for the python version
#:      the code is running on.  Use this when constructing the message to
#:      send to exceptions or when dealing with an API that needs to take
#:      a native string.  Example::
#:
#:          try:
#:              1//0
#:          except ZeroDivisionError as e:
#:              raise MyException('Encountered and error: %s' % to_native(e))
if PY3:
    to_native = to_text
else:
    to_native = to_bytes
