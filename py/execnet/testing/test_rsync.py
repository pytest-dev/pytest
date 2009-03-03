import py
from py.execnet import RSync


def setup_module(mod):
    mod.gw = py.execnet.PopenGateway()
    mod.gw2 = py.execnet.PopenGateway()

def teardown_module(mod):
    mod.gw.exit()
    mod.gw2.exit()


class DirSetup:
    def setup_method(self, method):
        name = "%s.%s" %(self.__class__.__name__, method.func_name)
        self.tmpdir = t = py.test.ensuretemp(name)
        self.source = t.join("source")
        self.dest1 = t.join("dest1")
        self.dest2 = t.join("dest2")

class TestRSync(DirSetup):
    def test_notargets(self):
        rsync = RSync(self.source)
        py.test.raises(IOError, "rsync.send()")
        assert rsync.send(raises=False) is None

    def test_dirsync(self):
        dest = self.dest1
        dest2 = self.dest2
        source = self.source

        for s in ('content1', 'content2', 'content2-a-bit-longer'): 
            source.ensure('subdir', 'file1').write(s) 
            rsync = RSync(self.source)
            rsync.add_target(gw, dest)
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
        rsync.add_target(gw, dest)
        rsync.send()
        assert dest.join('subdir', 'file1').check(file=1)
        assert dest2.join('subdir', 'file1').check(file=1)
        rsync = RSync(source)
        rsync.add_target(gw, dest, delete=True)
        rsync.add_target(gw2, dest2)
        rsync.send()
        assert not dest.join('subdir', 'file1').check() 
        assert dest2.join('subdir', 'file1').check() 

    def test_dirsync_twice(self):
        source = self.source
        source.ensure("hello")
        rsync = RSync(source)
        rsync.add_target(gw, self.dest1)
        rsync.send()
        assert self.dest1.join('hello').check()
        py.test.raises(IOError, "rsync.send()")
        assert rsync.send(raises=False) is None
        rsync.add_target(gw, self.dest2)
        rsync.send()
        assert self.dest2.join('hello').check()
        py.test.raises(IOError, "rsync.send()")
        assert rsync.send(raises=False) is None

    def test_rsync_default_reporting(self):
        source = self.source
        source.ensure("hello")
        cap = py.io.StdCapture()
        try:
            rsync = RSync(source)
            rsync.add_target(gw, self.dest1)
            rsync.send()
        finally:
            out, err = cap.reset()
        assert out.find("hello") != -1

    def test_rsync_non_verbose(self):
        source = self.source
        source.ensure("hello")
        cap = py.io.StdCapture()
        try:
            rsync = RSync(source, verbose=False)
            rsync.add_target(gw, self.dest1)
            rsync.send()
        finally:
            out, err = cap.reset()
        assert not out
        assert not err

    def test_symlink_rsync(self):
        if py.std.sys.platform == 'win32':
            py.test.skip("symlinks are unsupported on Windows.")
        source = self.source
        dest = self.dest1
        self.source.ensure("existant")
        source.join("rellink").mksymlinkto(source.join("existant"), absolute=0)
        source.join('abslink').mksymlinkto(source.join("existant"))
        
        rsync = RSync(source)
        rsync.add_target(gw, dest)
        rsync.send()
        
        assert dest.join('rellink').readlink() == dest.join("existant")
        assert dest.join('abslink').readlink() == dest.join("existant")

    def test_callback(self):
        dest = self.dest1
        source = self.source
        source.ensure("existant").write("a" * 100)
        source.ensure("existant2").write("a" * 10)
        total = {}
        def callback(cmd, lgt, channel):
            total[(cmd, lgt)] = True

        rsync = RSync(source, callback=callback)
        #rsync = RSync()
        rsync.add_target(gw, dest)
        rsync.send()

        assert total == {("list", 110):True, ("ack", 100):True, ("ack", 10):True}

    def test_file_disappearing(self):
        dest = self.dest1
        source = self.source 
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
        rsync.add_target(gw, dest)
        rsync.send()
        assert rsync.x == 1
        assert len(dest.listdir()) == 1
        assert len(source.listdir()) == 1
        
