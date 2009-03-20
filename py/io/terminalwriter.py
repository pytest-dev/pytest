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

if sys.platform == 'win32':
    # ctypes access to the Windows console

    STD_OUTPUT_HANDLE = -11
    STD_ERROR_HANDLE  = -12
    FOREGROUND_BLUE      = 0x0001 # text color contains blue.
    FOREGROUND_GREEN     = 0x0002 # text color contains green.
    FOREGROUND_RED       = 0x0004 # text color contains red.
    FOREGROUND_WHITE     = 0x0007
    FOREGROUND_INTENSITY = 0x0008 # text color is intensified.
    BACKGROUND_BLUE      = 0x0010 # background color contains blue.
    BACKGROUND_GREEN     = 0x0020 # background color contains green.
    BACKGROUND_RED       = 0x0040 # background color contains red.
    BACKGROUND_WHITE     = 0x0070
    BACKGROUND_INTENSITY = 0x0080 # background color is intensified.

    def GetStdHandle(kind):
        import ctypes
        return ctypes.windll.kernel32.GetStdHandle(kind)

    def SetConsoleTextAttribute(handle, attr):
        import ctypes
        ctypes.windll.kernel32.SetConsoleTextAttribute(
            handle, attr)

    def _getdimensions():
        import ctypes
        from ctypes import wintypes

        SHORT = ctypes.c_short
        class COORD(ctypes.Structure):
            _fields_ = [('X', SHORT),
                        ('Y', SHORT)]
        class SMALL_RECT(ctypes.Structure):
            _fields_ = [('Left', SHORT),
                        ('Top', SHORT),
                        ('Right', SHORT),
                        ('Bottom', SHORT)]
        class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
            _fields_ = [('dwSize', COORD),
                        ('dwCursorPosition', COORD),
                        ('wAttributes', wintypes.WORD),
                        ('srWindow', SMALL_RECT),
                        ('dwMaximumWindowSize', COORD)]
        STD_OUTPUT_HANDLE = -11
        handle = GetStdHandle(STD_OUTPUT_HANDLE)
        info = CONSOLE_SCREEN_BUFFER_INFO()
        ctypes.windll.kernel32.GetConsoleScreenBufferInfo(
            handle, ctypes.byref(info))
        # Substract one from the width, otherwise the cursor wraps
        # and the ending \n causes an empty line to display.
        return info.dwSize.Y, info.dwSize.X - 1

def get_terminal_width():
    try:
        height, width = _getdimensions()
    except (SystemExit, KeyboardInterrupt), e:
        raise
    except:
        # FALLBACK
        width = int(os.environ.get('COLUMNS', 80))-1
    # XXX the windows getdimensions may be bogus, let's sanify a bit 
    width = max(width, 40) # we alaways need 40 chars
    return width

terminal_width = get_terminal_width()

# XXX unify with _escaped func below
def ansi_print(text, esc, file=None, newline=True, flush=False):
    if file is None:
        file = sys.stderr
    text = text.rstrip()
    if esc and not isinstance(esc, tuple):
        esc = (esc,)
    if esc and sys.platform != "win32" and file.isatty():
        text = (''.join(['\x1b[%sm' % cod for cod in esc])  +  
                text +
                '\x1b[0m')     # ANSI color code "reset"
    if newline:
        text += '\n'

    if esc and sys.platform == "win32" and file.isatty():
        if 1 in esc:
            bold = True
            esc = tuple([x for x in esc if x != 1])
        else:
            bold = False
        esctable = {()   : FOREGROUND_WHITE,                 # normal
                    (31,): FOREGROUND_RED,                   # red
                    (32,): FOREGROUND_GREEN,                 # green
                    (33,): FOREGROUND_GREEN|FOREGROUND_RED,  # yellow
                    (34,): FOREGROUND_BLUE,                  # blue
                    (35,): FOREGROUND_BLUE|FOREGROUND_RED,   # purple
                    (36,): FOREGROUND_BLUE|FOREGROUND_GREEN, # cyan
                    (37,): FOREGROUND_WHITE,                 # white
                    (39,): FOREGROUND_WHITE,                 # reset
                    }
        attr = esctable.get(esc, FOREGROUND_WHITE)
        if bold:
            attr |= FOREGROUND_INTENSITY
        STD_OUTPUT_HANDLE = -11
        STD_ERROR_HANDLE = -12
        if file is sys.stderr:
            handle = GetStdHandle(STD_ERROR_HANDLE)
        else:
            handle = GetStdHandle(STD_OUTPUT_HANDLE)
        SetConsoleTextAttribute(handle, attr)
        file.write(text)
        SetConsoleTextAttribute(handle, FOREGROUND_WHITE)
    else:
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
        self.hasmarkup = hasattr(file, 'isatty') and file.isatty() 

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


class Win32ConsoleWriter(object):

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
        self.hasmarkup = hasattr(file, 'isatty') and file.isatty()

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
            if self.hasmarkup:
                handle = GetStdHandle(STD_OUTPUT_HANDLE)

            if self.hasmarkup and kw:
                attr = 0
                if kw.pop('bold', False):
                    attr |= FOREGROUND_INTENSITY

                if kw.pop('red', False):
                    attr |= FOREGROUND_RED
                elif kw.pop('blue', False):
                    attr |= FOREGROUND_BLUE
                elif kw.pop('green', False):
                    attr |= FOREGROUND_GREEN
                else:
                    attr |= FOREGROUND_WHITE

                SetConsoleTextAttribute(handle, attr)
            self._file.write(s)
            self._file.flush()
            if self.hasmarkup:
                SetConsoleTextAttribute(handle, FOREGROUND_WHITE)

    def line(self, s='', **kw):
        self.write(s + '\n', **kw)

if sys.platform == 'win32':
    TerminalWriter = Win32ConsoleWriter

class WriteFile(object): 
    def __init__(self, writemethod): 
        self.write = writemethod 
    def flush(self): 
        return 


