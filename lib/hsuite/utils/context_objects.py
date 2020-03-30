from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from abc import ABCMeta

from hsuite.utils.common._collections_compat import (
    Container, Mapping, Sequence, Set)
from hsuite.utils.common.collections import ImmutableDict
from hsuite.utils.six import add_metaclass, binary_type, text_type
from hsuite.utils.singleton import Singleton


def _make_immutable(obj):
    """Recursively convert a container and objects inside of it into immutable data types."""

    if isinstance(obj, (text_type, binary_type)):
        return obj
    elif isinstance(obj, Mapping):
        temp_dict = {}
        for key, value in obj.items():
            if isinstance(value, Container):
                temp_dict[key] = _make_immutable(value)
            else:
                temp_dict[key] = value

        return ImmutableDict(temp_dict)
    elif isinstance(obj, Set):
        temp_set = set()
        for value in obj:
            if isinstance(value, Container):
                temp_set.add(_make_immutable(value))
            else:
                temp_set.add(value)

        return frozenset(temp_set)
    elif isinstance(obj, Sequence):
        temp_sequence = []
        for value in obj:
            if isinstance(value, Container):
                temp_sequence.append(_make_immutable(value))
            else:
                temp_sequence.append(value)

        return tuple(temp_sequence)

    return obj


class _ABCSingleton(Singleton, ABCMeta):
    """Combine ABCMeta based classes with Singleton based classes."""

    pass


class CLIArgs(ImmutableDict):
    """Hold a parsed copy of cli arguments."""

    def __init__(self, mapping):
        toplevel = {}
        for key, value in mapping.items():
            toplevel[key] = _make_immutable(value)

        super(CLIArgs, self).__init__(toplevel)

    @classmethod
    def from_options(cls, options):
        return cls(vars(options))


@add_metaclass(_ABCSingleton)
class GlobalCLIArgs(CLIArgs):
    """Globally hold a parsed copy of cli arguments."""

    pass
