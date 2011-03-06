#!/usr/bin/env python 

import sys
from argparse import ArgumentParser, FileType
import xml.parsers.expat as ep
from codecs import getwriter 
from gzip import GzipFile
from time import time
from handlers import PageHandler, RevisionHandler, LoggingHandler

def _utf8stdout(compress=False):
    ''' wraps stdout with a UTF-8 capable writer '''
    _stdout = sys.stdout
    if compress:
        _stdout = GzipFile(fileobj=_stdout)
    return getwriter('UTF-8')(_stdout)

class DumpParser(object):
    ''' MediaWiki XML database dump parser '''
    def __init__(self, parsertype, verbose, compress):
        '''
        Parameters
        ----------
        parsertype - any of {"logging", "page", "revision"}
        verbose    - Boolean, prints additional info
        compress   - Boolean, compresses output with gzip
        '''
        stdout = _utf8stdout(compress=compress)
        if parsertype == 'logging':
            self.handler = LoggingHandler(verbose, stdout)
        elif parsertype == 'page':
            self.handler = PageHandler(verbose, stdout)
        elif parsertype == 'revision':
            self.handler = RevisionHandler(verbose, stdout)
        else:
            raise ValueError('unknown parser type: %s' % parsertype)
        self.parser = ep.ParserCreate('UTF-8')
        self.parser.StartElementHandler = self.handler.startElem
        self.parser.EndElementHandler = self.handler.endElem
        self.parser.CharacterDataHandler = self.handler.character
        self.parser.buffer_text = True
        if not self.parser.returns_unicode:
            from warnings import warn
            warn('Expat parser doesn\'t return unicode', category=UserWarning)
    def parse(self, infile):
        '''
        Parses the contents of infile

        Parameters
        ----------
        infile - open file instance
        '''
        start_time = time()
        if infile.isatty():
            print >> sys.stderr, 'Reading from standard input. '\
                    'Press ^D when done.'
        self.parser.ParseFile(infile)
        end_time = time()
        info = { 
                'time' : end_time - start_time,
                'rows' : self.handler.num_rows,
                'speed': float(self.handler.num_rows) / (end_time - start_time)
        }
        print >> sys.stderr, 'Time: %(time)g s, Rows: %(rows)d, Speed: '\
                '%(speed)g rows/s' % info

def make_parser():
    parser = ArgumentParser(description='Parse the XML dump of a Mediawiki '
            'database')
    parser.add_argument('table', help='Mediawiki table.', choices=[
            'logging',
            'page',
            'revision',
    ])
    parser.add_argument('input', help='Input file.', type=FileType('r'))
    parser.add_argument('-c', '--compress', help='Compress output with gzip.', 
            action='store_true')
    parser.add_argument('-v', '--verbose', help='Verbose parsing output.', 
            action='store_true')
    parser.add_argument('-d', '--debug', help='Raise Python exceptions to the '
            'console', action='store_true')
    return parser


if __name__ == '__main__':
    parser = make_parser()
    ns = parser.parse_args()
    try:
        dumpparser = DumpParser(ns.table, ns.verbose, ns.compress)
        dumpparser.parse(ns.input)
    except:
        ty,val,tb = sys.exc_info()
        if ns.debug:
            raise ty, val, tb
        else:
            if ty is KeyboardInterrupt:
                print
                sys.exit(1)
            name = ty.__name__
            parser.error('%s : %s' % (name, val))

