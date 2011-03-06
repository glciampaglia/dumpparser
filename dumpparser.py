#!/usr/bin/env python 

import re
import sys
from string import whitespace
from argparse import ArgumentParser, FileType
from xml.parsers.expat import ParserCreate
from codecs import getwriter 
from time import time

# source: source: http://en.wikipedia.org/wiki/Help:Namespaces
# note that whitespaces must be escaped in verbose regular expressions
nspattern = re.compile('''
^               # beginning of string
(               # any of the following ...
Talk|
User|
User\ talk|
Wikipedia|
Wikipedia\ talk|
File|
File talk|
MediaWiki|
MediaWiki\ talk|
Template|
Template\ talk|
Help|
Help\ talk|
Category|
Category\ talk|
Thread|
Thread talk|
Summary|
Summary\ talk|
Portal|
Portal\ talk|
Book|
Book\ talk|
Special|
Media
):              # closing colon
''', re.VERBOSE)

wspattern = re.compile('[%s]' % whitespace)

class BaseDumpParser(object):
    ''' MediaWiki XML database dump parser '''
    def __init__(self, outfile, sep='\t', encl='"'):
        self.outfile = getwriter('UTF-8')(outfile)
        self.sep = sep
        self.encl = encl
        self.num_rows = 0
        self.stack = [] # XXX could use a deque
        self.data = ''
        self.nskeys = []
        self.nsnames = []
        self.parser = ParserCreate('UTF-8')
        if not self.parser.returns_unicode:
            from warnings import warn
            warn('Expat parser doesn\'t return unicode', category=UserWarning)
        self.parser.StartElementHandler = self.startElem
        self.parser.EndElementHandler = self.endElem
        self.parser.CharacterDataHandler = self.character
        self.parser.buffer_text = True
    def startElem(self, name, attributes):
        self.attr = attributes
        self.stack.insert(0, name)
        if name == 'namespace':
            self.nsnames.append(attributes['key'])
    def endElem(self, name):
        if name == 'namespace':
            self.nsnames.append(self.data)
        elif name == 'namespaces':
            self.ns = dict(zip(self.nsnames, self.nskeys))
        elif name in self.EMIT_TAG:
            self.emit(newline=(name == self.NEW_ROW_TAG))
        self.data = '' 
        self.attr = None
        self.stack.pop(0)
    def character(self, data):
        self.data = data.strip()    # XXX See if writing in a buffer isn't faster
    def emit(self, newline=False):
        if wspattern.search(self.data):
            self.data = self.encl + self.data + self.encl
        if newline:
            self.data += '\n'
            self.num_rows += 1
        else:
            self.data += self.sep
        self.outfile.write(self.data)
    def resolvens(self, title):
        m = nspattern.match(title)
        if m is None:
            return '0'
        else:
            key = m.group()[:-1] # strip the ending colon
            return self._ns[key]
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
                'rows' : self.num_rows,
                'speed': float(self.num_rows) / (end_time - start_time)
        }
        print >> sys.stderr, 'Time: %(time)g s, Rows: %(rows)d, Speed: '\
                '%(speed)g rows/s' % info

class LoggingDumpParser(BaseDumpParser):
    NEW_ROW_TAG = 'logitem'
    EMIT_TAG = [
            'logitem',
            'id',
            'timestamp',
            'username',
            'comment',
            'type',
            'action',
            'logtitle'
    ]

class RevisionDumpParser(BaseDumpParser):
    pass

class PageDumpParser(BaseDumpParser):
    pass

def make_parser():
    ''' creates and initializes the command line argument parser '''
    parser = ArgumentParser(description='Parse the XML dump of a Mediawiki '
            'database')
    parser.add_argument('type', help='Parser type', choices=[
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

def main(args):
    if args.type == 'logging':
        dumpparser = LoggingDumpParser(stdout)
    elif parsertype == 'page':
        dumpparser = PageDumpParser(stdout)
    elif parsertype == 'revision':
        dumpparser = RevisionDumpParser(stdout)
    else:
        raise ValueError('unknown parser type: %s' % args.type)
    dumpparser.parse(ns.input)

if __name__ == '__main__':
    parser = make_parser()
    ns = parser.parse_args()
    try:
        main(ns)
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

