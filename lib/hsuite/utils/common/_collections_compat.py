from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    """Python 3.3+ branch."""
    from collections.abc import (
        MappingView,
        ItemsView,
        KeysView,
        ValuesView,
        Mapping, MutableMapping,
        Sequence, MutableSequence,
        Set, MutableSet,
        Container,
        Hashable,
        Sized,
        Callable,
        Iterable,
        Iterator,
    )
except ImportError:
    """Use old lib location under 2.6-3.2."""
    from collections import (
        MappingView,
        ItemsView,
        KeysView,
        ValuesView,
        Mapping, MutableMapping,
        Sequence, MutableSequence,
        Set, MutableSet,
        Container,
        Hashable,
        Sized,
        Callable,
        Iterable,
        Iterator,
    )
