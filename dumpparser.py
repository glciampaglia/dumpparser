#!/usr/bin/env python 

''' XML sax parser for the event log dump. Produces output for mysqlimport. '''

from __future__ import with_statement
from contextlib import closing
import sys
import xml.parsers.expat as ep
from codecs import open, getwriter 
from gzip import GzipFile
from locale import getpreferredencoding
from time import time as time_now
from _dumpparser import PageHandler,RevisionHandler,LoggingHandler

# use this to write to stdout UTF-8 encoded strings
def set_stdout(compress=False):
#    enc = 'UTF-8' if sys.stdout.isatty() else getpreferredencoding()
    stdout = GzipFile(fileobj=sys.stdout) if compress else sys.stdout
    return getwriter('UTF-8')(stdout)

_stdout = set_stdout()

class XMLParser(object):
    ''' base class of SAX parser '''
    def __init__(self, handler):
        ''' by defaults produces output that can be piped to xmlimport. Else use
        sep and encl to customize the field separator string and the field enclosing
        characters. if debug is set to 1 information on the parsing is printed
        to stderr. '''
        self.handler = handler
        self.parser = ep.ParserCreate('UTF-8')
        self.parser.StartElementHandler = handler.startElem
        self.parser.EndElementHandler = handler.endElem
        self.parser.CharacterDataHandler = handler.character
        self.parser.buffer_text = True
        if not self.parser.returns_unicode:
            from warnings import warn
            warn('Expat parser doesn\'t return unicode', category=UserWarning)
    def parseFile(self,filename):
        start_time = time_now()
        self.filename = filename
        try:
            with closing(open(filename)) as f:
                self.parser.ParseFile(f)
        finally:
            parsing_time = time_now() - start_time
            parsing_speed = self.handler.num_rows / float(parsing_time)
            parsed_rows = self.handler.num_rows
            info = dict(time=parsing_time, speed=parsing_speed,
                    rows=parsed_rows)
            print >> sys.stderr
            print >> sys.stderr,\
                    'Time: %(time)g s, Rows: %(rows)d, Speed: %(speed)g revs/s' % info
            if parsing_time < 1:
                print >> sys.stderr, 'Figures may be inaccurate!'
    def parse(self):
        self.filename = '-'
        self.parser.ParseFile(sys.stdin)

if __name__ == '__main__':
    from optparse import OptionParser
    usage = 'syntax: %prog [options] type [ file | - ]'
    op = OptionParser(usage=usage)
    op.add_option('-c','--compress',help='compress output', dest='compress',
            action='store_true', default=False)
    op.add_option('-v','--verbose',help='verbose output', dest='verbose',
            action='store_true', default=False)
    options,args = op.parse_args()
    if len(args) < 1:
        op.error('specify a parser type')
    if options.compress:
        _stdout = set_stdout(True)
    t = args[0]
    if t == 'logging':
        handler = LoggingHandler(options.verbose, _stdout)
    elif t == 'page':
        handler = PageHandler(options.verbose, _stdout)
    elif t == 'revision':
        handler = RevisionHandler(options.verbose, _stdout)
    else:
        op.error('unknown parser type: %s' % t)
    try:
        xml_parser = XMLParser(handler)
        if len(args) > 1:
            xml_parser.parseFile(args[1])
        else:
            xml_parser.parse()
    except ep.ExpatError,e:
        print >> sys.stderr, e.args[0]
        sys.exit(1)
    # XXX <Fri Apr 30 11:02:07 CEST 2010> why it is not catched?!
    except KeyboardInterrupt:
        sys.exit(0)

