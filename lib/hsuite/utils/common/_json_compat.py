from __future__ import absolute_import, division, print_function
__metaclass__ = type

import types
import json

# Detect the python-json library which is incompatible
try:
    if not isinstance(json.loads, types.FunctionType) or not isinstance(json.dumps, types.FunctionType):
        raise ImportError(
            "json.loads or json.dumps were not found in the imported json library.")
except AttributeError:
    raise ImportError("python-json was detected, which is incompatible.")
