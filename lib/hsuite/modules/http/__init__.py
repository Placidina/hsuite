from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from requests import Session


class HTTP(Session):
    def __init__(self, proxy=None):
        super(HTTP, self).__init__()

        if proxy:
            self.proxies = dict(http=proxy, https=proxy)
