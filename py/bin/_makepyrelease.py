#!/usr/bin/env python 

from _findpy import py
import sys

pydir = py.path.local(py.__file__).dirpath()
rootdir = pydir.dirpath()

def gen_manifest(): 
    pywc = py.path.svnwc(pydir)
    status = pywc.status(rec=True)
    #assert not status.modified 
    #assert not status.deleted  
    #assert not status.added  
    versioned = dict([(x.localpath,1) for x in status.allpath()])

    l = []
    for x in rootdir.visit(None, lambda x: x.basename != '.svn'): 
        if x.check(file=1): 
            names = [y.basename for y in x.parts()]
            if '.svn' in names: 
                l.append(x) 
            elif x in versioned: 
                l.append(x) 
    l.append(rootdir / "setup.py")
    l = [x.relto(rootdir) for x in l]
    l.append("")
    s = "\n".join(l) 
    return s 

def trace(arg): 
    lines = str(arg).split('\n') 
    prefix = "[trace] "
    prefix = "* " 
    indent = len(prefix)  
    ispace = " " * indent
    lines = [ispace + line for line in lines]
    if lines: 
        lines[0] = prefix + lines[0][indent:]
    for line in lines: 
        print >>py.std.sys.stdout, line 

def make_distfiles(tmpdir): 
    """ return distdir with tar.gz and zipfile. """ 
    manifest = tmpdir.join('MANIFEST')
    trace("generating %s" %(manifest,))
    content = gen_manifest() 
    manifest.write(content) 
    trace("wrote %d files into manifest file" %len(content.split('\n')))

    distdir = tmpdir.ensure('dist', dir=1)
    oldir = rootdir.chdir()
    try: 
        from py.__.misc.dist import setup 
        trace("invoking sdist, generating into %s" % (distdir,)) 
        setup(py, script_name="setup.py", 
              script_args=('-q', 'sdist', '--no-prune', 
                           '-m', str(manifest), 
                           '--formats=gztar,zip',  
                           '-d', str(distdir)))
        setup(py, script_name="setup.py", 
              script_args=('-q', 'bdist_wininst', 
                           #'-m', str(manifest), 
                           '-d', str(distdir)))
    finally: 
        oldir.chdir()
    return distdir 


def pytest(unpacked): 
    trace("py-testing %s" % unpacked)
    old = unpacked.chdir()
    try: 
        import os
        os.system("python py/bin/py.test py") 
    finally: 
        old.chdir()
    
def unpackremotetar(tmpdir, strurl): 
    import tarfile, urllib
    f = urllib.urlopen(strurl)
    basename = strurl.split('/')[-1]
    target = tmpdir.join(basename)
    trace("downloading to %s" %(target,))
    target.write(f.read())

    trace("extracting to %s" %(target,))
    old = tmpdir.chdir()
    try: 
        py.process.cmdexec("tar zxf %s" %(target,))
    finally: 
        old.chdir()
    prefix = '.tar.gz'
    assert basename.endswith(prefix) 
    stripped = basename[:-len(prefix)]
    unpacked = tmpdir.join(stripped) 
    assert unpacked
    return unpacked 
       
def checksvnworks(unpacked): 
    pywc = py.path.svnwc(unpacked.join('py'))
    trace("checking versioning works: %s" %(pywc,))
    status = pywc.status(rec=True)
    assert not status.modified 
    assert not status.deleted 
    assert not status.unknown 

def pytest_remote(address, url): 
    gw = py.execnet.SshGateway(address)
    basename = url[url.rfind('/')+1:]
    purebasename = basename[:-len('.tar.gz')]

    def mytrace(x, l=[]): 
        l.append(x)
        if x.endswith('\n'): 
            trace("".join(l))
            l[:] = []
            
    channel = gw.remote_exec(stdout=mytrace, stderr=sys.stderr, source="""
        url = %(url)r
        basename = %(basename)r
        purebasename = %(purebasename)r
        import os, urllib
        f = urllib.urlopen(url) 
        print "reading from", url 
        s = f.read()
        f.close()
        f = open(basename, 'w')
        f.write(s) 
        f.close()
        if os.path.exists(purebasename):
            import shutil 
            shutil.rmtree(purebasename) 
        os.system("tar zxf %%s" %% (basename,))
        print "unpacked", purebasename 
        os.chdir(purebasename)
        print "testing at %(address)s ..."
        #os.system("python py/bin/py.test py")
        import commands
        status, output = commands.getstatusoutput("python py/bin/py.test py")
        #print output 
        print "status:", status

    """ % locals())
    channel.waitclose(200.0)
    
if __name__ == '__main__': 
    py.magic.invoke(assertion=True) 
    version = py.std.sys.argv[1]
    assert py.__package__.version == version, (
            "py package has version %s\nlocation: %s" % 
            (py.__package__.version, pydir))

    tmpdir = py.path.local.get_temproot().join('makepyrelease-%s' % version) 
    if tmpdir.check(): 
        trace("removing %s" %(tmpdir,))
        tmpdir.remove()
    tmpdir.mkdir() 
    trace("using tmpdir %s" %(tmpdir,))

    distdir = make_distfiles(tmpdir) 
    targz = distdir.join('py-%s.tar.gz' % version)
    zip = distdir.join('py-%s.zip' % version)
    files = distdir.listdir() 
    for fn in files: 
        assert fn.check(file=1) 

    remotedir = 'codespeak.net://www/codespeak.net/htdocs/download/py/' 
    source = distdir  # " ".join([str(x) for x in files]) 
    trace("rsyncing %(source)s to %(remotedir)s" % locals())
    py.process.cmdexec("rsync -avz %(source)s/ %(remotedir)s" % locals())

    ddir = tmpdir.ensure('download', dir=1)
    URL = py.__package__.download_url # 'http://codespeak.net/download/py/' 
    unpacked = unpackremotetar(ddir, URL)
    assert unpacked == ddir.join("py-%s" % (version,))

    #checksvnworks(unpacked) 
    #pytest(unpacked)

    pytest_remote('test@codespeak.net', py.__package__.download_url)



