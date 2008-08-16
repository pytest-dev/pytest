import pdb, sys, linecache

class Pdb(pdb.Pdb):
    def do_list(self, arg):
        self.lastcmd = 'list'
        last = None
        if arg:
            try:
                x = eval(arg, {}, {})
                if type(x) == type(()):
                    first, last = x
                    first = int(first)
                    last = int(last)
                    if last < first:
                        # Assume it's a count
                        last = first + last
                else:
                    first = max(1, int(x) - 5)
            except:
                print '*** Error in argument:', repr(arg)
                return
        elif self.lineno is None:
            first = max(1, self.curframe.f_lineno - 5)
        else:
            first = self.lineno + 1
        if last is None:
            last = first + 10
        filename = self.curframe.f_code.co_filename
        breaklist = self.get_file_breaks(filename)
        try:
            for lineno in range(first, last+1):
                # start difference from normal do_line
                line = self._getline(filename, lineno)
                # end difference from normal do_line
                if not line:
                    print '[EOF]'
                    break
                else:
                    s = repr(lineno).rjust(3)
                    if len(s) < 4: s = s + ' '
                    if lineno in breaklist: s = s + 'B'
                    else: s = s + ' '
                    if lineno == self.curframe.f_lineno:
                        s = s + '->'
                    print s + '\t' + line,
                    self.lineno = lineno
        except KeyboardInterrupt:
            pass
    do_l = do_list

    def _getline(self, filename, lineno):
        if hasattr(filename, "__source__"):
            try:
                return filename.__source__.lines[lineno - 1] + "\n"
            except IndexError:
                return None
        return linecache.getline(filename, lineno)

def post_mortem(t):
    # again, a copy of the version in pdb.py
    p = Pdb()
    p.reset()
    while t.tb_next is not None:
        t = t.tb_next
    p.interaction(t.tb_frame, t)

def set_trace():
    # again, a copy of the version in pdb.py
    Pdb().set_trace(sys._getframe().f_back)


