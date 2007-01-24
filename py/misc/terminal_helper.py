import sys, os

terminal_width = int(os.environ.get('COLUMNS', 80))-1

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


