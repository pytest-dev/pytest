"""

Helper functions for writing to terminals and files. 

"""


import sys, os
import py

def _getdimensions():
    import termios,fcntl,struct
    call = fcntl.ioctl(0,termios.TIOCGWINSZ,"\000"*8)
    height,width = struct.unpack( "hhhh", call ) [:2]
    return height, width 

def get_terminal_width():
    try:
        height, width = _getdimensions()
    except (SystemExit, KeyboardInterrupt), e:
        raise
    except:
        # FALLBACK
        width = int(os.environ.get('COLUMNS', 80))-1
    return width

terminal_width = get_terminal_width()

# XXX unify with _escaped func below
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

class TerminalWriter(object):
    _esctable = dict(black=30, red=31, green=32, yellow=33, 
                     blue=34, purple=35, cyan=36, white=37,
                     Black=40, Red=41, Green=42, Yellow=43, 
                     Blue=44, Purple=45, Cyan=46, White=47,
                     bold=1, light=2, blink=5, invert=7)

    def __init__(self, file=None, stringio=False):
        if file is None:
            if stringio:
                self.stringio = file = py.std.cStringIO.StringIO()
            else:
                file = py.std.sys.stdout 
        elif callable(file):
            file = WriteFile(file)
        self._file = file
        self.fullwidth = get_terminal_width()
        self.hasmarkup = sys.platform != "win32" and \
                        hasattr(file, 'isatty') and file.isatty() 

    def _escaped(self, text, esc):
        if esc and self.hasmarkup:
            text = (''.join(['\x1b[%sm' % cod for cod in esc])  +  
                text +'\x1b[0m')
        return text

    def markup(self, text, **kw):
        esc = []
        for name in kw:
            if name not in self._esctable:
                raise ValueError("unknown markup: %r" %(name,))
            if kw[name]:
                esc.append(self._esctable[name])
        return self._escaped(text, tuple(esc))

    def sep(self, sepchar, title=None, fullwidth=None, **kw):
        if fullwidth is None:
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

        self.line(line, **kw)

    def write(self, s, **kw):
        if s:
            s = str(s)
            if self.hasmarkup and kw:
                s = self.markup(s, **kw)
            self._file.write(s)
        self._file.flush()

    def line(self, s='', **kw):
        if s:
            s = self.markup(s, **kw)
            self._file.write(s + '\n')
        else:
            self._file.write('\n')
        self._file.flush()

class WriteFile(object): 
    def __init__(self, writemethod): 
        self.write = writemethod 
    def flush(self): 
        return 


