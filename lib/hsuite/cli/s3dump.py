from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
__requires__ = ['hsuite']

import xmltodict
import shutil
import humanfriendly
import os

from hsuite import context
from hsuite.cli import CLI
from hsuite.errors import HSuiteOptionsError
from hsuite.utils.display import Display
from hsuite.modules import HTTP, Thread, LockThread

from hsuite.utils.six.moves.queue import Queue
from hsuite.utils.six.moves.urllib.parse import urlparse


display = Display()


class S3dumpCLI(CLI):
    def __init__(self, args):
        super(S3dumpCLI, self).__init__(args)

        self.mutex_directory = LockThread()
        self.mutex_interesting = LockThread()

        self.bucket = Queue()
        self.download = Queue()

        self.max_file_size = None
        self.key_words_list = None

    def init_parser(self):
        super(S3dumpCLI, self).init_parser(
            usage="%prog [options]", desc="Run S3Dump")

        bucket = self.parser.add_mutually_exclusive_group(required=True)
        bucket.add_argument(
            '-b', '--bucket', dest='bucket', help="Bucket name")
        bucket.add_argument(
            '--list-buckets', dest='list_buckets', help="File path that has a bucket name list")

        self.parser.add_argument(
            '-d', '--download', dest='download', default=False, action='store_true', help="Enable download files")
        self.parser.add_argument(
            '-o', '--out', dest='out', default='.', help="Path where downloads will be saved")
        self.parser.add_argument(
            '--list-keywords', dest='list_keywords', help="File path that contains a list of keywords for grep")
        self.parser.add_argument(
            '-w', dest='keywords', help="Text separated for \",\" to keywords for grep")
        self.parser.add_argument(
            '-m', '--max-file-size', dest='max_file_size', type=str, default='1M', help="Maximum file size to download")
        self.parser.add_argument(
            '-t', '--threads', dest='threads', type=int, default=1, help="Number of threads")
        self.parser.add_argument(
            '-p', '--proxy', dest='proxy', default=None, help="Using proxy")
        self.parser.add_argument(
            '--out-interesting', dest='out_interesting', help="File name to save interesting urls")

    def post_process_args(self, options):
        options = super(S3dumpCLI, self).post_process_args(options)

        if options.download and not os.access(os.path.dirname(os.path.realpath(options.out)), os.W_OK):
            raise HSuiteOptionsError(
                "%s is not a valid or accessible directory to save dumps" % options.out)

        if options.list_buckets and not os.path.exists(options.list_buckets):
            raise HSuiteOptionsError(
                "%s is not a valid or accessible file." % options.list_buckets)

        if options.list_keywords and not os.path.exists(options.list_keywords):
            raise HSuiteOptionsError(
                "%s is not a valid or accessible file." % options.list_keywords)

        if options.threads <= 0:
            raise HSuiteOptionsError(
                "%s is not a valid threads number." % options.threads)

        if options.out_interesting and not os.access(os.path.dirname(os.path.realpath(options.out_interesting)), os.W_OK):
            raise HSuiteOptionsError(
                "%s is not a valid interesting output" % options.out_interesting)

        try:
            self.max_file_size = humanfriendly.parse_size(
                options.max_file_size)
        except Exception:
            raise HSuiteOptionsError(
                "%s is not a valide size" % options.max_file_size)

        if options.proxy and not urlparse(options.proxy).netloc:
            raise HSuiteOptionsError(
                "%s is not a valid proxy" % options.proxy)

        display.verbosity = options.verbosity
        return options

    def run(self):
        super(S3dumpCLI, self).run()
        display.banner("Starting S3Dump script")

        if context.CLIARGS['list_keywords']:
            with open(context.CLIARGS['list_keywords'], 'r') as content:
                self.key_words_list = [line.strip() for line in content]
        elif context.CLIARGS['keywords']:
            self.key_words_list = context.CLIARGS['keywords'].strip().split(",")

        for i in range(0, context.CLIARGS['threads']):
            display.vv("Starting scan thread %d ..." % i)

            thread = Thread(target=self.scan)
            thread.daemon = True
            thread.start()

        if context.CLIARGS['download']:
            for i in range(0, context.CLIARGS['threads']):
                display.vv("Starting dump thread %d ..." % i)

                thread = Thread(target=self.dump)
                thread.daemon = True
                thread.start()

        if context.CLIARGS['list_buckets']:
            with open(context.CLIARGS['list_buckets']) as buckets:
                for bucket in buckets:
                    url = "http://%s.s3.amazonaws.com" % bucket.rstrip()
                    display.v("Queuing %s ..." % url)
                    self.bucket.put(url)
        else:
            url = "http://%s.s3.amazonaws.com" % context.CLIARGS['bucket']
            display.v("Queuing %s ..." % url)
            self.bucket.put(url)

        self.bucket.join()
        if context.CLIARGS['download']:
            self.download.join()

    @property
    def lock_interesting(self):
        self.mutex_interesting.acquire()

    @property
    def release_interesting(self):
        self.mutex_interesting.release()

    @property
    def lock_directory(self):
        self.mutex_directory.acquire()

    @property
    def release_directory(self):
        self.mutex_directory.release()

    def scan(self):
        http = HTTP(proxy=context.CLIARGS['proxy'])

        while True:
            url = self.bucket.get()

            try:
                display.display("Fetching %s ..." % url)

                response = http.get(url)
                if response.status_code in [403, 404]:
                    if not context.CLIARGS['download']:
                        display.display("%s is not accessible" % url)
                    else:
                        display.v("%s is not accessible" % url)
                elif response.status_code == 200 and 'Content' in response.text:
                    display.display("Pilfering %s ..." % url)

                    keys = []
                    objects = xmltodict.parse(response.text)

                    try:
                        contents = objects['ListBucketResult']['Contents']
                        if not isinstance(contents, list):
                            contents = [contents]

                        for child in contents:
                            if context.CLIARGS['download'] and int(child['Size']) > self.max_file_size:
                                display.warning(
                                    "\"%s/%s\" is a greater than the specified max file size" % (url, child['Key']))
                            else:
                                keys.append(child['Key'])
                    except Exception:
                        pass

                    for words in keys:
                        words = (str(words)).rstrip()
                        collectable = "%s/%s" % (url, words)

                        if self.key_words_list != None and len(self.key_words_list) > 0:
                            for key_word in self.key_words_list:
                                key_word = (str(key_word)).rstrip()
                                if key_word in words:
                                    break

                        self.download.put(collectable)

                        if not context.CLIARGS['download'] and not context.CLIARGS['out_interesting']:
                            display.display("Collectable: %s" % collectable)
                        else:
                            display.vv("Collectable: %s" % collectable)

                        if context.CLIARGS['out_interesting']:
                            try:
                                self.lock_interesting
                                with open(context.CLIARGS['out_interesting'], 'ab+') as interesting:
                                    interesting.write(
                                        collectable.encode('utf-8'))
                                    interesting.write(
                                        '\n'.encode('utf-8'))
                            finally:
                                self.release_interesting
            except Exception as e:
                display.vvv(str(e))

            self.bucket.task_done()

    def dump(self):
        http = HTTP(proxy=context.CLIARGS['proxy'])

        while True:
            url = self.download.get()
            try:
                path = self.make_directory(url)
                filename = (url.split('/')[-1]).rstrip()

                if filename:
                    display.v("Dump %s ..." % url.rstrip())
                    response = http.get(url.rstrip(), stream=True)
                    if 'Content-Length' in response.headers:
                        with open(path, 'wb') as file:
                            shutil.copyfileobj(response.raw, file)

                    response.close()
            except Exception as e:
                display.vvv(str(e))

            self.download.task_done()

    def make_directory(self, url):
        bits = url.split('/')
        directory = context.CLIARGS['out']

        for i in range(2, len(bits) - 1):
            directory = os.path.join(directory, bits[i])

        try:
            self.lock_directory
            if not os.path.isdir(directory):
                os.makedirs(directory)
        except Exception as e:
            display.vvv(str(e))
        finally:
            self.release_directory

        return os.path.join(directory, bits[-1]).rstrip()
