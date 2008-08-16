"""

Helper functions for writing to terminals and files. 

"""


import sys, os
import py

def get_terminal_width():
    try:
        import termios,fcntl,struct
        call = fcntl.ioctl(0,termios.TIOCGWINSZ,"\000"*8)
        height,width = struct.unpack( "hhhh", call ) [:2]
        terminal_width = width
    except (SystemExit, KeyboardInterrupt), e:
        raise
    except:
        # FALLBACK
        terminal_width = int(os.environ.get('COLUMNS', 80))-1
    return terminal_width

terminal_width = get_terminal_width()

def ansi_print(text, esc, file=None, newline=True, flush=False):
    if file is None:
        file = sys.stderr
    text = text.rstrip()
    if esc and sys.platform != "win32" and file.isatty():
        if not isinstance(esc, tuple):
            esc = (esc,)
        text = (''.join(['\x1b[%sm' % cod for cod in esc])  +  
                text +
                '\x1b[0m')     # ANSI color code "reset"
    if newline:
        text += '\n'
    file.write(text)
    if flush:
        file.flush()

class Out(object):
    tty = False
    def __init__(self, file):
        self.file = py.io.dupfile(file)
        self.fullwidth = get_terminal_width()

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
                                     self.terminal_width)

    def write(self, s):
        self.file.write(str(s))
        self.file.flush()

    def line(self, s=''):
        if s:
            self.file.write(s + '\n')
        else:
            self.file.write('\n')
        self.file.flush()

    def xxxrewrite(self, s=''):
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

    def xxxrewrite(self, s=''):
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

