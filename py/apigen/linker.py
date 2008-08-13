import py
import os
html = py.xml.html

# this here to serve two functions: first it makes the proto part of the temp
# urls (see TempLinker) customizable easily (for tests and such) and second
# it makes sure the temp links aren't replaced in generated source code etc.
# for this file (and its tests) itself.
TEMPLINK_PROTO = 'apigen.temp'

def getrelfspath(dotted_name):
    # XXX need to make sure its imported on non-py lib 
    return eval(dotted_name, {"py": py})

class LazyHref(object):
    def __init__(self, linker, linkid):
        self._linker = linker
        self._linkid = linkid

    def __unicode__(self):
        return unicode(self._linker.get_target(self._linkid))

class Linker(object):
    fromlocation = None

    def __init__(self):
        self._linkid2target = {}

    def get_lazyhref(self, linkid):
        return LazyHref(self, linkid)

    def set_link(self, linkid, target):
        assert linkid not in self._linkid2target, (
                'linkid %r already used' % (linkid,))
        self._linkid2target[linkid] = target

    def get_target(self, linkid):
        linktarget = self._linkid2target[linkid]
        if self.fromlocation is not None:
            linktarget = relpath(self.fromlocation, linktarget)
        return linktarget

    def call_withbase(self, base, func, *args, **kwargs):
        assert self.fromlocation is None
        self.fromlocation = base 
        try:
            return func(*args, **kwargs)
        finally:
            del self.fromlocation 
    
class TempLinker(object):
    """ performs a similar role to the Linker, but with a different approach

        instead of returning 'lazy' hrefs, this returns a simple URL-style
        string

        the 'temporary urls' are replaced on the filesystem after building the
        files, so that means even though a second pass is still required,
        things don't have to be built in-memory (as with the Linker)
    """
    fromlocation = None

    def __init__(self):
        self._linkid2target = {}

    def get_lazyhref(self, linkid):
        return '%s://%s' % (TEMPLINK_PROTO, linkid)

    def set_link(self, linkid, target):
        assert linkid not in self._linkid2target
        self._linkid2target[linkid] = target

    def get_target(self, tempurl, fromlocation=None):
        assert tempurl.startswith('%s://' % (TEMPLINK_PROTO,))
        linkid = '://'.join(tempurl.split('://')[1:])
        linktarget = self._linkid2target[linkid]
        if fromlocation is not None:
            linktarget = relpath(fromlocation, linktarget)
        return linktarget

    _reg_tempurl = py.std.re.compile('["\'](%s:\/\/[^"\s]*)["\']' % (
                                      TEMPLINK_PROTO,))
    def replace_dirpath(self, dirpath, stoponerrors=True):
        """ replace temporary links in all html files in dirpath and below """
        for fpath in dirpath.visit('*.html'):
            html = fpath.read()
            while 1:
                match = self._reg_tempurl.search(html)
                if not match:
                    break
                tempurl = match.group(1)
                try:
                    html = html.replace('"' + tempurl + '"',
                                        '"' + self.get_target(tempurl,
                                                fpath.relto(dirpath)) + '"')
                except KeyError:
                    if stoponerrors:
                        raise
                    html = html.replace('"' + tempurl + '"',
                                        '"apigen.notfound://%s"' % (tempurl,))
            fpath.write(html)
            

def relpath(p1, p2, sep=os.path.sep, back='..', normalize=True):
    """ create a relative path from p1 to p2

        sep is the seperator used for input and (depending
        on the setting of 'normalize', see below) output

        back is the string used to indicate the parent directory

        when 'normalize' is True, any backslashes (\) in the path
        will be replaced with forward slashes, resulting in a consistent
        output on Windows and the rest of the world

        paths to directories must end on a / (URL style)
    """
    if normalize:
        p1 = p1.replace(sep, '/')
        p2 = p2.replace(sep, '/')
        sep = '/'
        # XXX would be cool to be able to do long filename expansion and drive
        # letter fixes here, and such... iow: windows sucks :(
    if (p1.startswith(sep) ^ p2.startswith(sep)): 
        raise ValueError("mixed absolute relative path: %r -> %r" %(p1, p2))
    fromlist = p1.split(sep)
    tolist = p2.split(sep)

    # AA
    # AA BB     -> AA/BB
    #
    # AA BB
    # AA CC     -> CC
    #
    # AA BB 
    # AA      -> ../AA

    diffindex = 0
    for x1, x2 in zip(fromlist, tolist):
        if x1 != x2:
            break
        diffindex += 1
    commonindex = diffindex - 1

    fromlist_diff = fromlist[diffindex:]
    tolist_diff = tolist[diffindex:]

    if not fromlist_diff:
        return sep.join(tolist[commonindex:])
    backcount = len(fromlist_diff)
    if tolist_diff:
        return sep.join([back,]*(backcount-1) + tolist_diff)
    return sep.join([back,]*(backcount) + tolist[commonindex:])

