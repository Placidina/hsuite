# S3Dump

[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/Placidina/s3dump/blob/master/LICENSE)

S3Dump is a security tool for enumerate and download files from AWS S3 buckets.

## General

This tool was developed in order to improve the [AWSBucketDump](https://github.com/jordanpotti/AWSBucketDump) tool.

Some improvements:

- `structure improvement`
- `setuptools`
- `proxy`
- `raw bucket name`
- And more ...

## Usage

```sh
usage: hsuite-s3dump [-h] [--version] [-v] [--debug] (-b BUCKET | --list-buckets LIST_BUCKETS) [-d] [-o OUT] [-w LIST_KEYWORDS] [-m MAX_FILE_SIZE]
              [-t THREADS] [-p PROXY] [--out-interesting OUT_INTERESTING]

Run S3Dump

optional arguments:
  --debug               Enable debugging mode
  --list-buckets LIST_BUCKETS
                        File path that has a bucket name list
  --out-interesting OUT_INTERESTING
                        File name to save interesting urls
  --version             Show program's version number, config file location, configured module search path, module location, executable location and
                        exit
  -b BUCKET, --bucket BUCKET
                        Bucket name
  -d, --download        Enable download files
  -h, --help            show this help message and exit
  -m MAX_FILE_SIZE, --max-file-size MAX_FILE_SIZE
                        Maximum file size to download
  -o OUT, --out OUT     Path where downloads will be saved
  -p PROXY, --proxy PROXY
                        Using proxy
  -t THREADS, --threads THREADS
                        Number of threads
  -v, --verbose         Verbose mode (-vvv for more)
  -w LIST_KEYWORDS, --list-keywords LIST_KEYWORDS
                        File path that contains a list of keywords for grep
```
