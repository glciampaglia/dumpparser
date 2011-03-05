''' Cython extension module '''

import sys
import re
# from datetime import datetime

# def parse_time(timestr):
#     return str(datetime.strptime(timestr,'%Y-%m-%dT%H:%M:%SZ'))


cdef isChild(stack, tag):
    try:
        return stack.index(tag) > 0
    except ValueError:
        return False

cdef class BaseHandler:
    cdef public int debug
    cdef readonly int num_rows
    cdef public stdout
    cdef _stack, _data, _nskeys, _nsnames, _ns
    def __init__(self, debug=0, stdout=sys.stdout):
        self.debug = debug
        self.stdout = stdout
        self.num_rows = 0
        self._stack = []
        self._data = ''
    def startElem(self,name,attributes):
        try:
            handler = getattr(self,'start_' + name)
            return handler(name,attributes)
        except AttributeError:
            if self.debug:
                sys.stderr.write('no handler <%s>\n' % name)
# TODO <Gio  5 Ago 2010 10:53:30 CEST> add a reference to the expat parser?
#                 sys.stderr.write('%s:%s no handler <%s>' % (self.filename,
#                         self.parser.CurrentLineNumber, name))
        finally:
            self._stack.insert(0,name)
    def endElem(self,name):
        try:
            handler = getattr(self,'end_' + name)
            return handler(name)
        except AttributeError:
            if self.debug:
                sys.stderr.write('no handler <%s/>\n' % name)
#                 sys.stderr.write('%s:%s no handler <%s/>' % (self.filename,
#                         self.parser.CurrentLineNumber, name))
        finally:
            self._stack.pop(0)
            self._data = None
    def character(self, data):
        self._data = data
    def start_namespaces(self,name,attributes):
        self._nskeys 	= []
        self._nsnames 	= []
    def end_namespaces(self,name):
        self._ns = dict( zip(self._nsnames, self._nskeys) )
        if self.debug:
            for k,v in self._ns.iteritems():
                self.stdout.write("%s\t:%s" % (v, k))
    def start_namespace(self,name,attributes):
        self._nskeys.append(attributes['key'])
    def end_namespace(self,name):
        # the default namespace is <namespace key="0" /> so _data is None
        self._nsnames.append(self._data)
    def get_namespace(self,url):
        for ns,code in self._ns.iteritems():
            if re.compile('^%s:' % ns).match(url) is not None:
                return code
        return '0'
    def new_row(self):
        self.stdout.write('\n')
        self.num_rows += 1

cdef class PageHandler(BaseHandler):
    cdef page_title
    def end_title(self,name):
        self.page_title = self._data
        self.stdout.write(self._data + '\t')
    def end_id(self,name):
        if isChild(self._stack, 'contributor'):
            pass
        elif isChild(self._stack, 'revision'):
            pass
        else:
            self.stdout.write(self._data + '\t')
    def end_page(self,name):
        self.num_rows = self.num_rows + 1
        ns = self.get_namespace(self.page_title)
        self.stdout.write(ns + '\n')

cdef class LoggingHandler(BaseHandler):
    pass

cdef class RevisionHandler(BaseHandler):
    cdef rev_page, rev_user, rev_user_text
    def start_revision(self,name,attributes):
        self.stdout.write(self.rev_page + '\t')
    def start_contributor(self,name,attributes):
        self.rev_user = '0'
    def end_contributor(self,name):
        self.stdout.write(self.rev_user + '\t' + self.rev_user_text + '\t')
    def end_id(self,name):
        if isChild(self._stack,'contributor'):
            self.rev_user = self._data
        elif isChild(self._stack,'revision'):
            self.stdout.write(self._data + '\t')
        else:
            # revision of the page, will be printed at <start_revision>
            self.rev_page = self._data
    def end_username(self, name):
        txt = self._data.replace('\t','\\t').replace('\n','\\n')
        self.rev_user_text = txt
    def end_timestamp(self, name):
        self.stdout.write(self._data + '\t')
    def end_ip(self, name):
        txt = self._data.replace('\t','\\t').replace('\n','\\n')
        self.rev_user_text = txt
    def end_comment(self, name):
        txt = self._data.replace('\t','\\t').replace('\n','\\n')
        self.stdout.write('"' + txt + '"' + '\n')
        self.num_rows += 1

# 
# class EventLogHandler(MediaWikiDumpHandler):
#     ''' 
#     SAX Parser for the event log dump. Format of the dump is:
# 
#     <mediawiki>
#       <logitem>
#         <id>175873</id>
#         <timestamp>2005-05-11T15:34:52Z</timestamp>
#         <contributor>
#           <username>Ahoerstemeier</username>
#           <id>7580</id>
#         </contributor>
#         <comment>content was: 'Will Ashbrook is a pretty good kid I know at school.'</comment>
#         <type>delete</type>
#         <action>delete</action>
#         <logtitle>Will Ashbrook</logtitle>
#         <params xml:space="preserve" />
#       </logitem>
#     </mediawiki> 
# 
#     produces output suitable for mysqldump with following columns:
#         logitem-id timestamp type action logtitle 
#     '''
#     fields = [
#         'log_id',
#         'log_type',
#         'log_action',
#         'log_timestamp',
#         'log_user',
#         'log_namespace',
#         'log_title',
#         'log_comment',
#         'log_params',
#         'log_deleted',
#     ]
#     defaults = {'log_namespace' : '0'}
#     def __init__(self,**kwargs):
#         super(EventLogHandler,self).__init__(**kwargs)
#     def end_timestamp(self,name):
#         self._line['log_timestamp' ] = parse_time(self._data)
#     def end_type(self,name):
#         self._line['log_type'] = self._data
#     def end_action(self,name):
#         self._line['log_action'] = self._data
#     def end_logtitle(self,name):
#         self._line['log_title'] = '"%s"' % self._data
#     def end_comment(self,name):
#         self._line['log_comment'] = '"%s"' % self._data
#     def end_id(self,name):
#         if isChild(self._stack,'contributor'):
#             self._line['log_user'] = self._data
#         else:
#             self._line['log_id'] = self._data
#     def end_logitem(self,name):
#         ''' note that this is not 100% faithful in that the logging table may
#         contain some rows with namespace < 0. See the MW database in layout. '''
#         self._line['log_namespace'] = self.get_namespace(self._line['log_title'])
#         self.print_row()
# 
