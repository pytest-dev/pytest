from __future__ import generators
import sys
import os
import py
from py.__.misc import terminal_helper

class Out(object):
    tty = False
    fullwidth = terminal_helper.terminal_width
    def __init__(self, file):
        self.file = py.io.dupfile(file)

    def sep(self, sepchar, title=None, fullwidth=None):
        if not fullwidth:
            fullwidth = self.fullwidth
        # the goal is to have the line be as long as possible
        # under the condition that len(line) <= fullwidth
        if title is not None:
            # we want 2 + 2*len(fill) + len(title) <= fullwidth
            # i.e.    2 + 2*len(sepchar)*N + len(title) <= fullwidth
            #         2*len(sepchar)*N <= fullwidth - len(title) - 2
            #         N <= (fullwidth - len(title) - 2) // (2*len(sepchar))
            N = (fullwidth - len(title) - 2) // (2*len(sepchar))
            fill = sepchar * N
            line = "%s %s %s" % (fill, title, fill)
        else:
            # we want len(sepchar)*N <= fullwidth
            # i.e.    N <= fullwidth // len(sepchar)
            line = sepchar * (fullwidth // len(sepchar))
        # in some situations there is room for an extra sepchar at the right,
        # in particular if we consider that with a sepchar like "_ " the
        # trailing space is not important at the end of the line
        if len(line) + len(sepchar.rstrip()) <= fullwidth:
            line += sepchar.rstrip()
        self.line(line)

class TerminalOut(Out):
    tty = True
    def __init__(self, file):
        super(TerminalOut, self).__init__(file)

    def sep(self, sepchar, title=None):
        super(TerminalOut, self).sep(sepchar, title,
                                     terminal_helper.get_terminal_width())

    def write(self, s):
        self.file.write(str(s))
        self.file.flush()

    def line(self, s=''):
        if s:
            self.file.write(s + '\n')
        else:
            self.file.write('\n')
        self.file.flush()

    def rewrite(self, s=''):
        #self.write('\x1b[u%s' % s) - this escape sequence does
        # strange things, or nothing at all, on various terminals.
        # XXX what is it supposed to do in the first place??
        self.write(s)

class FileOut(Out):
    def write(self, s):
        self.file.write(str(s))
        self.file.flush()

    def line(self, s=''):
        if s:
            self.file.write(str(s) + '\n')
        else:
            self.file.write('\n')
        self.file.flush()

    def rewrite(self, s=''):
        self.write(s)

def getout(file):
    # XXX investigate further into terminal output, this is not enough
    #
    if file is None: 
        file = py.std.sys.stdout 
    elif hasattr(file, 'send'):
        file = WriteFile(file.send) 
    elif callable(file):
        file = WriteFile(file)
    if hasattr(file, 'isatty') and file.isatty(): 
        return TerminalOut(file)
    else:
        return FileOut(file)

class WriteFile(object): 
    def __init__(self, writemethod): 
        self.write = writemethod 
    def flush(self): 
        return 

