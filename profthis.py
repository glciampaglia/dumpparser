#!/usr/bin/env python
from contextlib import closing
import sys
import gzip
import pstats
import cProfile
from argparse import ArgumentParser

parser = ArgumentParser(description='profiles dumpparser.py')
parser.add_argument('input', help='gzip compressed input file')
parser.add_argument('type', help='parser type')
parser.add_argument('output', help='profiling stats output file')

if __name__ == '__main__':
    ns = parser.parse_args()
    with closing(gzip.GzipFile(ns.input)) as f:
        sys.stdout = open('/dev/null','w')
        from dumpparser import DumpParser 
        dp = DumpParser(ns.type, False, False)
        try:
            cProfile.runctx('dp.parse(f)', globals(), locals(), ns.output)
        finally:
            sys.stdout = sys.__stdout__
    stats = pstats.Stats(ns.output)
    stats.strip_dirs().sort_stats("time").print_stats()
