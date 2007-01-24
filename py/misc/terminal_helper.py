import sys, os

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


