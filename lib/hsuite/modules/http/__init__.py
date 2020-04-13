from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from requests import Session
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from requests_ntlm import HttpNtlmAuth


class HTTP(Session):
    def __init__(self, headers=None, proxy=None):
        super(HTTP, self).__init__()

        if proxy:
            self.proxies = dict(http=proxy, https=proxy)

        if headers:
            self.headers = headers
