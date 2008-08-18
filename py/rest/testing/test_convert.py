import py
from py.__.rest.convert import convert_dot, latexformula2png
from py.__.rest.testing.setup import getdata

def setup_module(mod):
    required = 'gs', 'dot', 'latex', 'epstopdf', 
    for exe in required:
        if not py.path.local.sysfind(exe):
            py.test.skip("%r not found, required: %r" %(exe, required))
    mod.datadir = getdata()

def test_convert_dot():
    # XXX not really clear that the result is valid pdf/eps
    dot = datadir.join("example1.dot")
    convert_dot(dot, "pdf")
    pdf = dot.new(ext="pdf")
    assert pdf.check()
    pdf.remove()
    convert_dot(dot, "eps")
    eps = dot.new(ext="eps")
    assert eps.check()
    eps.remove()

def test_latexformula():
    png = datadir.join("test.png")
    formula = r'$$Entropy(T) = - \sum^{m}_{j=1}  \frac{|T_j|}{|T|} \log \frac{|T_j|}{|T|}$$'
    #does not crash
    latexformula2png(formula, png)
    assert png.check()
    png.remove()
