#!/usr/bin/env python3
#
# Retrieve comic links from a LINE Webtoon comic RSS feed.
#

import sys
import os
import argparse
from urllib import request
from urllib.error import URLError
import xml.etree.ElementTree as eltree
from urllib import parse
import re
import subprocess
import time

FILENAME = sys.argv[0]

link_dler = "webtoon-dl.py"
cache_file = os.environ["HOME"] + "/.cache/rss-link-dl"

"""Argparse override to print usage to stderr on argument error."""
class ArgumentParserUsage(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help(sys.stderr)
        sys.exit(2)

"""Print usage and exit depending on given exit code."""
def usage(exit_code):
    if exit_code == 0:
        pipe = sys.stdout
    else:
        # if argument was non-zero, print to STDERR instead
        pipe = sys.stderr

    parser.print_help(pipe)
    sys.exit(exit_code)

"""Log a message to a specific pipe (defaulting to stdout)."""
def log_message(message, pipe=sys.stdout):
    print("{}: {}".format(FILENAME, message), file=pipe)

"""If verbose, log an event."""
def log(message):
    if not args.verbose:
        return
    log_message(message)

"""Log an error. If given a 2nd argument, exit using that error code."""
def error(message, exit_code=None):
    log_message("error: " + message, sys.stderr)
    if exit_code:
        sys.exit(exit_code)



parser = ArgumentParserUsage(description="Retrieve comic links from a LINE Webtoon comic RSS feed.")
parser.add_argument("-v", "--verbose", action="store_true", help="be verbose")
parser.add_argument("rss", metavar="RSS", help="URL to comic RSS feed")
parser.add_argument("-d", "--dir", action="store", default=".", help="base directory name to store episodes in (default: .)")
args = parser.parse_args()

# force verbosity for now
args.verbose = True

try:
    with request.urlopen(args.rss) as page:
        data = page.read()
    got_rss = True
except:
    error("connection error", 1)

links = {}
feed = eltree.fromstring(data)
for item in feed.iter("item"):
    title = item.find("title").text
    with open(cache_file, "r") as f:
        seen_links = f.read().split("\n")
    if title in seen_links:
        log("title cached, not downloading: " + title)
    else:
        log("downloading title: " + title)
        link = item.find("link").text

        # get episode number (to use as directory)
        link_parsed = parse.urlparse(link)
        episode_num = int(parse.parse_qs(link_parsed.query)["episode_no"][0])

        # fix episode number (theirs is always 1 higher?)
        episode_num -= 1

        # add to links dict
        links[episode_num] = link

        log("adding title to cache file")
        with open(cache_file, "a") as f:
            f.write(title + "\n")

# all links downloaded: process them
if len(links) > 0:
    log("processing links with {}".format(link_dler))
    for title, link in links.items():
        subprocess.call([link_dler, "-d", "{}/{}".format(args.dir, str(title)), link])
else:
    log("no links to download")
