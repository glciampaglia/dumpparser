''' Handler classes. '''

import sys
import re

cdef isChild(stack, tag):
    try:
        return stack.index(tag) > 0
    except ValueError:
        return False

cdef class BaseHandler:
    cdef public int verbose
    cdef readonly int num_rows
    cdef public stdout
    cdef _stack, _data, _nskeys, _nsnames, _ns
    def __init__(self, verbose=0, stdout=sys.stdout):
        self.verbose = verbose
        self.stdout = stdout
        self.num_rows = 0
        self._stack = []
        self._data = ''
    def startElem(self,name,attributes):
        try:
            handler = getattr(self,'start_' + name)
            return handler(name,attributes)
        except AttributeError:
            if self.verbose:
                sys.stderr.write('no handler for <%s>\n' % name)
        finally:
            self._stack.insert(0,name)
    def endElem(self,name):
        try:
            handler = getattr(self,'end_' + name)
            return handler(name)
        except AttributeError:
            if self.verbose:
                sys.stderr.write('no handler for <%s/>\n' % name)
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
        if self.verbose:
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
    cdef log_title
    def end_timestamp(self,name):
        self.stdout.write(self._data + '\t')
    def end_type(self,name):
        self.stdout.write(self._data + '\t')
    def end_action(self,name):
        self.stdout.write(self._data + '\t')
    def end_logtitle(self,name):
        self.log_title = self._data
        self.stdout.write(self._data + '\t')
    def end_comment(self,name):
        self.stdout.write(self._data + '\t')
    def end_id(self,name):
        self.stdout.write(self._data + '\n')
    def end_logitem(self,name):
        self.num_rows = self.num_rows + 1
        ns = self.get_namespace(self.log_title)
        self.stdout.write(ns + '\n')

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
