#!/usr/bin/env python
from contextlib import nested, closing
import sys
import gzip
import pstats
import cProfile
from argparse import ArgumentParser

from dumpparser import LoggingDumpParser

parser = ArgumentParser(description='profiles dumpparser.py')
parser.add_argument('input', help='gzip compressed input file')
parser.add_argument('type', help='parser type')
parser.add_argument('output', help='profiling stats output file')

if __name__ == '__main__':
    ns = parser.parse_args()
    with nested(closing(gzip.GzipFile(ns.input)),
            closing(open('/dev/null','w'))) as (infile, outfile):
        dp = LoggingDumpParser(outfile)
        cProfile.runctx('dp.parse(infile)', globals(), locals(), ns.output)
    stats = pstats.Stats(ns.output)
    stats.strip_dirs().sort_stats("time").print_stats()
