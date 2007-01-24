import py, md5


def rsync(gw, sourcedir, destdir, **options): 
    for name in options: 
        assert name in ('delete',) 

    channel = gw.remote_exec("""
        import os, stat, shutil, md5
        destdir, options = channel.receive() 
        modifiedfiles = []

        def remove(path):
            assert path.startswith(destdir)
            try:
                os.unlink(path)
            except OSError:
                # assume it's a dir
                shutil.rmtree(path)

        def receive_directory_structure(path, relcomponents):
            #print "receive directory structure", path
            try:
                st = os.lstat(path)
            except OSError:
                st = None
            msg = channel.receive()
            if isinstance(msg, list):
                if st and not stat.S_ISDIR(st.st_mode):
                    os.unlink(path)
                    st = None
                if not st:
                    os.mkdir(path)
                entrynames = {}
                for entryname in msg:
                    receive_directory_structure(os.path.join(path, entryname),
                        relcomponents + [entryname])
                    entrynames[entryname] = True
                if options.get('delete'): 
                    for othername in os.listdir(path):
                        if othername not in entrynames:
                            otherpath = os.path.join(path, othername)
                            remove(otherpath)
            else:
                if st and stat.S_ISREG(st.st_mode):
                    f = file(path, 'rb')
                    data = f.read()
                    f.close()
                    mychecksum = md5.md5(data).digest()
                else:
                    if st:
                        remove(path)
                    mychecksum = None
                if mychecksum != msg:
                    channel.send(relcomponents)
                    modifiedfiles.append(path)
        receive_directory_structure(destdir, [])
        channel.send(None)  # end marker
        for path in modifiedfiles:
            data = channel.receive()
            f = open(path, 'wb')
            f.write(data)
            f.close()
    """)
    
    channel.send((str(destdir), options))

    def send_directory_structure(path):
        if path.check(dir=1):
            subpaths = path.listdir()
            print "sending directory structure", path
            channel.send([p.basename for p in subpaths])
            for p in subpaths:
                send_directory_structure(p)
        elif path.check(file=1):
            data = path.read()
            checksum = md5.md5(data).digest()
            channel.send(checksum)
        else:
            raise ValueError, "cannot sync %r" % (path,)
    send_directory_structure(sourcedir)
    while True:
        modified_rel_path = channel.receive()
        if modified_rel_path is None:
            break
        modifiedpath = sourcedir.join(*modified_rel_path)
        data = modifiedpath.read()
        channel.send(data)
    channel.waitclose()

def copy(gw, source, dest):
    channel = gw.remote_exec("""
        import md5
        localfilename = channel.receive()
        try:
            f = file(localfilename, 'rb')
            existingdata = f.read()
            f.close()
        except (IOError, OSError):
            mycrc = None
        else:
            mycrc = md5.md5(existingdata).digest()
        remotecrc = channel.receive()
        if remotecrc == mycrc:
            channel.send(None)
        else:
            channel.send(localfilename)
            newdata = channel.receive()
            f = file(localfilename, 'wb')
            f.write(newdata)
            f.close()
    """)
    channel.send(str(dest))
    f = file(str(source), 'rb')
    localdata = f.read()
    f.close()
    channel.send(md5.md5(localdata).digest())
    status = channel.receive()
    if status is not None:
        assert status == str(dest)  # for now
        channel.send(localdata)
    channel.waitclose()


def setup_module(mod):
    mod.gw = py.execnet.PopenGateway()

def teardown_module(mod):
    mod.gw.exit()


def test_filecopy():
    dir = py.test.ensuretemp('filecopy')
    source = dir.ensure('source')
    dest = dir.join('dest')
    source.write('hello world')
    copy(gw, source, dest)
    assert dest.check(file=1)
    assert dest.read() == 'hello world'
    source.write('something else')
    copy(gw, source, dest)
    assert dest.check(file=1)
    assert dest.read() == 'something else'

def test_dirsync():
    base = py.test.ensuretemp('dirsync')
    dest = base.join('dest') 
    source = base.mkdir('source') 

    for s in ('content1', 'content2'): 
        source.ensure('subdir', 'file1').write(s) 
        rsync(gw, source, dest)
        assert dest.join('subdir').check(dir=1)
        assert dest.join('subdir', 'file1').check(file=1)
        assert dest.join('subdir', 'file1').read() == s 
    
    source.join('subdir').remove('file1')
    rsync(gw, source, dest)
    assert dest.join('subdir', 'file1').check(file=1)
    rsync(gw, source, dest, delete=True)
    assert not dest.join('subdir', 'file1').check() 

