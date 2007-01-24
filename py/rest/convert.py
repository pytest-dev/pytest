import py

from py.__.process.cmdexec import ExecutionFailed
# utility functions to convert between various formats

format_to_dotargument = {"png": "png",
                         "eps": "ps",
                         "ps":  "ps",
                         "pdf": "ps",
                        }

def ps2eps(ps):
    # XXX write a pure python version
    if not py.path.local.sysfind("ps2epsi") and \
           not py.path.local.sysfind("ps2eps"):
        raise SystemExit("neither ps2eps nor ps2epsi found")
    try:
        eps = ps.new(ext=".eps")
        py.process.cmdexec('ps2epsi "%s" "%s"' % (ps, eps))
    except ExecutionFailed:
        py.process.cmdexec('ps2eps -l -f "%s"' % ps)

def ps2pdf(ps, compat_level="1.2"):
    if not py.path.local.sysfind("gs"):
        raise SystemExit("ERROR: gs not found")
    pdf = ps.new(ext=".pdf")
    options = dict(OPTIONS="-dSAFER -dCompatibilityLevel=%s" % compat_level,
                   infile=ps, outfile=pdf)
    cmd = ('gs %(OPTIONS)s -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite '
           '"-sOutputFile=%(outfile)s" %(OPTIONS)s -c .setpdfwrite '
           '-f "%(infile)s"') % options
    py.process.cmdexec(cmd)
    return pdf

def eps2pdf(eps):
    # XXX write a pure python version
    if not py.path.local.sysfind("epstopdf"):
        raise SystemExit("ERROR: epstopdf not found")
    py.process.cmdexec('epstopdf "%s"' % eps)

def dvi2eps(dvi, dest=None):
    if dest is None:
        dest = eps.new(ext=".eps")
    command = 'dvips -q -E -n 1 -D 600 -p 1 -o "%s" "%s"' % (dest, dvi)
    if not py.path.local.sysfind("dvips"):
        raise SystemExit("ERROR: dvips not found")
    py.process.cmdexec(command)

def convert_dot(fn, new_extension):
    if not py.path.local.sysfind("dot"):
        raise SystemExit("ERROR: dot not found")
    result = fn.new(ext=new_extension)
    print result
    arg = "-T%s" % (format_to_dotargument[new_extension], )
    py.std.os.system('dot "%s" "%s" > "%s"' % (arg, fn, result))
    if new_extension == "eps":
        ps = result.new(ext="ps")
        result.move(ps)
        ps2eps(ps)
        ps.remove()
    elif new_extension == "pdf":
        # convert to eps file first, to get the bounding box right
        eps = result.new(ext="eps")
        ps = result.new(ext="ps")
        result.move(ps)
        ps2eps(ps)
        eps2pdf(eps)
        ps.remove()
        eps.remove()
    return result
 

class latexformula2png(object):
    def __init__(self, formula, dest, temp=None):
        self.formula = formula
        try:
            import Image
            self.Image = Image
            self.scale = 2 # create a larger image
            self.upscale = 5 # create the image upscale times larger, then scale it down
        except ImportError:
            self.scale = 2
            self.upscale = 1
            self.Image = None
        self.output_format = ('pngmono', 'pnggray', 'pngalpha')[2]
        if temp is None:
            temp = py.test.ensuretemp("latexformula")
        self.temp = temp
        self.latex = self.temp.join('formula.tex')
        self.dvi = self.temp.join('formula.dvi')
        self.eps = self.temp.join('formula.eps')
        self.png = self.temp.join('formula.png')
        self.saveas(dest)

    def saveas(self, dest):
        self.gen_latex()
        self.gen_dvi()
        dvi2eps(self.dvi, self.eps)
        self.gen_png()
        self.scale_image()
        self.png.copy(dest)

    def gen_latex(self):
        self.latex.write ("""
        \\documentclass{article}
        \\pagestyle{empty}
        \\begin{document}

        %s
        \\pagebreak
        
        \\end{document}
        """ % (self.formula))

    def gen_dvi(self):
        origdir = py.path.local()
        self.temp.chdir()
        py.process.cmdexec('latex "%s"' % (self.latex))
        origdir.chdir()

    def gen_png(self):
        tempdir = py.path.local.mkdtemp()
        
        re_bbox = py.std.re.compile('%%BoundingBox:\s*(\d+) (\d+) (\d+) (\d+)')
        eps = self.eps.read()
        x1, y1, x2, y2 = [int(i) for i in re_bbox.search(eps).groups()]
        X = x2 - x1 + 2
        Y = y2 - y1 + 2
        mx = -x1
        my = -y1
        ps = self.temp.join('temp.ps')
        source = self.eps
        ps.write("""
        1 1 1 setrgbcolor
        newpath
        -1 -1 moveto
        %(X)d  -1 lineto
        %(X)d %(Y)d lineto
        -1 %(Y)d lineto
        closepath
        fill
        %(mx)d %(my)d translate
        0 0 0 setrgbcolor
        (%(source)s) run
        
        """ % locals())

        sx = int((x2 - x1) * self.scale * self.upscale)
        sy = int((y2 - y1) * self.scale * self.upscale)
        res = 72 * self.scale * self.upscale
        command = ('gs -q -g%dx%d -r%dx%d -sDEVICE=%s -sOutputFile="%s" '
                   '-dNOPAUSE -dBATCH "%s"') % (
                    sx, sy, res, res, self.output_format, self.png, ps)
        py.process.cmdexec(command)

    def scale_image(self):
        if self.Image is None:
            return
        image = self.Image.open(str(self.png))
        image.resize((image.size[0] / self.upscale,
                      image.size[1] / self.upscale),
                     self.Image.ANTIALIAS).save(str(self.png))

