import py
from py.execnet import RSync


def pytest_funcarg__gw1(request):
    return request.cached_setup(
        setup=py.execnet.PopenGateway,
        teardown=lambda val: val.exit(),
        scope="module"
    )
pytest_funcarg__gw2 = pytest_funcarg__gw1

def pytest_funcarg__dirs(request):
    t = request.getfuncargvalue('tmpdir')
    class dirs:
        source = t.join("source")
        dest1 = t.join("dest1")
        dest2 = t.join("dest2")
    return dirs

class TestRSync:
    def test_notargets(self, dirs):
        rsync = RSync(dirs.source)
        py.test.raises(IOError, "rsync.send()")
        assert rsync.send(raises=False) is None

    def test_dirsync(self, dirs, gw1, gw2):
        dest = dirs.dest1
        dest2 = dirs.dest2
        source = dirs.source

        for s in ('content1', 'content2', 'content2-a-bit-longer'): 
            source.ensure('subdir', 'file1').write(s) 
            rsync = RSync(dirs.source)
            rsync.add_target(gw1, dest)
            rsync.add_target(gw2, dest2)
            rsync.send()
            assert dest.join('subdir').check(dir=1)
            assert dest.join('subdir', 'file1').check(file=1)
            assert dest.join('subdir', 'file1').read() == s 
            assert dest2.join('subdir').check(dir=1)
            assert dest2.join('subdir', 'file1').check(file=1)
            assert dest2.join('subdir', 'file1').read() == s 
            for x in dest, dest2:
                fn = x.join("subdir", "file1")
                fn.setmtime(0)
        
        source.join('subdir').remove('file1')
        rsync = RSync(source)
        rsync.add_target(gw2, dest2)
        rsync.add_target(gw1, dest)
        rsync.send()
        assert dest.join('subdir', 'file1').check(file=1)
        assert dest2.join('subdir', 'file1').check(file=1)
        rsync = RSync(source)
        rsync.add_target(gw1, dest, delete=True)
        rsync.add_target(gw2, dest2)
        rsync.send()
        assert not dest.join('subdir', 'file1').check() 
        assert dest2.join('subdir', 'file1').check() 

    def test_dirsync_twice(self, dirs, gw1, gw2):
        source = dirs.source
        source.ensure("hello")
        rsync = RSync(source)
        rsync.add_target(gw1, dirs.dest1)
        rsync.send()
        assert dirs.dest1.join('hello').check()
        py.test.raises(IOError, "rsync.send()")
        assert rsync.send(raises=False) is None
        rsync.add_target(gw1, dirs.dest2)
        rsync.send()
        assert dirs.dest2.join('hello').check()
        py.test.raises(IOError, "rsync.send()")
        assert rsync.send(raises=False) is None

    def test_rsync_default_reporting(self, capsys, dirs, gw1):
        source = dirs.source
        source.ensure("hello")
        rsync = RSync(source)
        rsync.add_target(gw1, dirs.dest1)
        rsync.send()
        out, err = capsys.readouterr()
        assert out.find("hello") != -1

    def test_rsync_non_verbose(self, capsys, dirs, gw1):
        source = dirs.source
        source.ensure("hello")
        rsync = RSync(source, verbose=False)
        rsync.add_target(gw1, dirs.dest1)
        rsync.send()
        out, err = capsys.readouterr()
        assert not out
        assert not err

    def test_symlink_rsync(self, dirs, gw1):
        if py.std.sys.platform == 'win32':
            py.test.skip("symlinks are unsupported on Windows.")
        source = dirs.source
        dest = dirs.dest1
        dirs.source.ensure("existant")
        source.join("rellink").mksymlinkto(source.join("existant"), absolute=0)
        source.join('abslink').mksymlinkto(source.join("existant"))
        
        rsync = RSync(source)
        rsync.add_target(gw1, dest)
        rsync.send()
        
        assert dest.join('rellink').readlink() == dest.join("existant")
        assert dest.join('abslink').readlink() == dest.join("existant")

    def test_callback(self, dirs, gw1):
        dest = dirs.dest1
        source = dirs.source
        source.ensure("existant").write("a" * 100)
        source.ensure("existant2").write("a" * 10)
        total = {}
        def callback(cmd, lgt, channel):
            total[(cmd, lgt)] = True

        rsync = RSync(source, callback=callback)
        #rsync = RSync()
        rsync.add_target(gw1, dest)
        rsync.send()

        assert total == {("list", 110):True, ("ack", 100):True, ("ack", 10):True}

    def test_file_disappearing(self, dirs, gw1):
        dest = dirs.dest1
        source = dirs.source 
        source.ensure("ex").write("a" * 100)
        source.ensure("ex2").write("a" * 100)

        class DRsync(RSync):
            def filter(self, x):
                assert x != source
                if x.endswith("ex2"):
                    self.x = 1
                    source.join("ex2").remove()
                return True

        rsync = DRsync(source)
        rsync.add_target(gw1, dest)
        rsync.send()
        assert rsync.x == 1
        assert len(dest.listdir()) == 1
        assert len(source.listdir()) == 1
        
