
import py

def test_dupfile(): 
    somefile = py.std.os.tmpfile() 
    flist = []
    for i in range(5): 
        nf = py.io.dupfile(somefile)
        assert nf != somefile
        assert nf.fileno() != somefile.fileno()
        assert nf not in flist 
        print >>nf, i,
        flist.append(nf) 
    for i in range(5): 
        f = flist[i]
        f.close()
    somefile.seek(0)
    s = somefile.read()
    assert s.startswith("01234")
    somefile.close()
