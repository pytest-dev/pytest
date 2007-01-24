import py
from py.execnet import RSync


def setup_module(mod):
    mod.gw = py.execnet.PopenGateway()
    mod.gw2 = py.execnet.PopenGateway()

def teardown_module(mod):
    mod.gw.exit()
    mod.gw2.exit()


def test_dirsync():
    base = py.test.ensuretemp('dirsync')
    dest = base.join('dest') 
    dest2 = base.join('dest2') 
    source = base.mkdir('source') 

    for s in ('content1', 'content2-a-bit-longer'): 
        source.ensure('subdir', 'file1').write(s) 
        rsync = RSync()
        rsync.add_target(gw, dest)
        rsync.add_target(gw2, dest2)
        rsync.send(source)
        assert dest.join('subdir').check(dir=1)
        assert dest.join('subdir', 'file1').check(file=1)
        assert dest.join('subdir', 'file1').read() == s 
        assert dest2.join('subdir').check(dir=1)
        assert dest2.join('subdir', 'file1').check(file=1)
        assert dest2.join('subdir', 'file1').read() == s 
    
    source.join('subdir').remove('file1')
    rsync = RSync()
    rsync.add_target(gw2, dest2)
    rsync.add_target(gw, dest)
    rsync.send(source)
    assert dest.join('subdir', 'file1').check(file=1)
    assert dest2.join('subdir', 'file1').check(file=1)
    rsync = RSync(delete=True)
    rsync.add_target(gw2, dest2)
    rsync.add_target(gw, dest)
    rsync.send(source)
    assert not dest.join('subdir', 'file1').check() 
    assert not dest2.join('subdir', 'file1').check() 

def test_symlink_rsync():
    if py.std.sys.platform == 'win32':
        py.test.skip("symlinks are unsupported on Windows.")
    base = py.test.ensuretemp('symlinkrsync')
    dest = base.join('dest')
    source = base.join('source')
    source.ensure("existant")
    source.join("rellink").mksymlinkto(source.join("existant"), absolute=0)
    source.join('abslink').mksymlinkto(source.join("existant"))
    
    rsync = RSync()
    rsync.add_target(gw, dest)
    rsync.send(source)
    
    assert dest.join('rellink').readlink() == dest.join("existant")
    assert dest.join('abslink').readlink() == dest.join("existant")

def test_callback():
    base = py.test.ensuretemp('callback')
    dest = base.join("dest")
    source = base.join("source")
    source.ensure("existant").write("a" * 100)
    source.ensure("existant2").write("a" * 10)
    total = {}
    def callback(cmd, lgt, channel):
        total[(cmd, lgt)] = True

    rsync = RSync(callback=callback)
    #rsync = RSync()
    rsync.add_target(gw, dest)
    rsync.send(source)

    assert total == {("list", 110):True, ("ack", 100):True, ("ack", 10):True}

