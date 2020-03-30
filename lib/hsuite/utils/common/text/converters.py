from __future__ import absolute_import, division, print_function
__metaclass__ = type

import datetime
import json

from hsuite.utils._text import to_bytes, to_native, to_text
from hsuite.utils.common._collections_compat import Set
from hsuite.utils.six import (
    binary_type,
    iteritems,
    text_type,
)


def _json_encode_fallback(obj):
    if isinstance(obj, Set):
        return list(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError("Cannot json serialize %s" % to_native(obj))


def jsonify(data, **kwargs):
    for encoding in ('utf-8', 'latin-1'):
        try:
            return json.dumps(data, encoding=encoding, default=_json_encode_fallback, **kwargs)
        except TypeError:
            try:
                new_data = container_to_text(data, encoding=encoding)
            except UnicodeDecodeError:
                continue

            return json.dumps(new_data, default=_json_encode_fallback, **kwargs)
        except UnicodeDecodeError:
            continue

    raise UnicodeError("Invalid unicode encoding encountered")


def container_to_bytes(d, encoding='utf-8', errors='surrogate_or_strict'):
    """
    Recursively convert dict keys and values to byte str.
    Specialized for json return because this only handles, lists, tuples,
    and dict types (the the json module returns).
    """

    if isinstance(d, text_type):
        return to_bytes(d, encoding=encoding, errors=errors)
    elif isinstance(d, dict):
        return dict(container_to_bytes(o, encoding, errors) for o in iteritems(d))
    elif isinstance(d, list):
        return [container_to_bytes(o, encoding, errors) for o in d]
    elif isinstance(d, tuple):
        return tuple(container_to_bytes(o, encoding, errors) for o in d)
    else:
        return d


def container_to_text(d, encoding='utf-8', errors='surrogate_or_strict'):
    """
    Recursively convert dict keys and values to byte str.
    Specialized for json return because this only handles, lists, tuples,
    and dict types (the json module returns).
    """

    if isinstance(d, binary_type):
        return to_text(d, encoding=encoding, errors=errors)
    elif isinstance(d, dict):
        return dict(container_to_text(o, encoding, errors) for o in iteritems(d))
    elif isinstance(d, list):
        return [container_to_text(o, encoding, errors) for o in d]
    elif isinstance(d, tuple):
        return tuple(container_to_text(o, encoding, errors) for o in d)
    else:
        return d
