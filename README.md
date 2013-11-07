dumpparser
==========

An extensible utility for transforming dumps of Mediawiki database snapshots
(such as those distributed by the Wikimedia Foundation
[at this address](http://dumps.wikimedia.org)) into plain, tab-separated, text
files. This make it possible to feed the data to tools like `mysqlimport`.

The main script is `dumpparser.py`. It is a pure Python script that implements a
SAX parser.

Test
