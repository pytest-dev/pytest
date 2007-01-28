import py

from py.__.process.cmdexec import ExecutionFailed

font_to_package = {"times": "times", "helvetica": "times",
                   "new century schoolbock": "newcent", "avant garde": "newcent",
                   "palatino": "palatino",
                  }
sans_serif_fonts = {"helvetica": True,
                    "avant garde": True,
                   }


def merge_files(pathlist, pagebreak=False):
    if len(pathlist) == 1:
        return pathlist[0].read()
    sectnum = False
    toc = False
    result = []
    includes = {}
    for path in pathlist:
        lines = path.readlines()
        for line in lines:
            # prevent several table of contents
            # and especially sectnum several times
            if ".. contents::" in line:
                if not toc:
                    toc = True
                    result.append(line)
            elif ".. sectnum::" in line:
                if not sectnum:
                    sectnum = True
                    result.append(line)
            elif line.strip().startswith(".. include:: "):
                #XXX slightly unsafe
                inc = line.strip()[13:]
                if inc not in includes:
                    includes[inc] = True
                    result.append(line)
            else:
                result.append(line)
        if pagebreak:
            result.append(".. raw:: latex \n\n \\newpage\n\n")
    if pagebreak:
        result.pop() #remove the last pagebreak again
    return "".join(result)

def create_stylesheet(options, path):
    fill_in = {}
    if "logo" in options:
        fill_in["have_logo"] = ""
        fill_in["logo"] = options["logo"]
    else:
        fill_in["have_logo"] = "%"
        fill_in["logo"] = ""
    if "font" in options:
        font = options["font"].lower()
        fill_in["font_package"] = font_to_package[font]
        fill_in["specified_font"] = ""
        fill_in["sans_serif"] = font not in sans_serif_fonts and "%" or ""
    else:
        fill_in["specified_font"] = "%"
        fill_in["sans_serif"] = "%"
        fill_in["font_package"] = ""
    if 'toc_depth' in options:
        fill_in["have_tocdepth"] = ""
        fill_in["toc_depth"] = options["toc_depth"]
    else:
        fill_in["have_tocdepth"] = "%"
        fill_in["toc_depth"] = ""
    fill_in["heading"] = options.get("heading", "")
    template_file = path.join("rest.sty.template")
    if not template_file.check():
        template_file = py.magic.autopath().dirpath().join("rest.sty.template")
    return template_file.read() % fill_in

def process_configfile(configfile, debug=False):
    old = py.path.local()
    py.path.local(configfile).dirpath().chdir()
    configfile = py.path.local(configfile)
    path = configfile.dirpath()
    configfile_dic = {}
    py.std.sys.path.insert(0, str(path))
    execfile(str(configfile), configfile_dic)
    pagebreak = configfile_dic.get("pagebreak", False)
    rest_sources = [py.path.local(p)
                    for p in configfile_dic['rest_sources']]
    rest = configfile.new(ext='txt')
    if len(rest_sources) > 1:
        assert rest not in rest_sources
    content = merge_files(rest_sources, pagebreak)
    if len(rest_sources) > 1:
        rest.write(content)
    sty = configfile.new(ext='sty')
    content = create_stylesheet(configfile_dic, path)
    sty.write(content)
    rest_options = None
    if 'rest_options' in configfile_dic:
        rest_options = configfile_dic['rest_options']
    process_rest_file(rest, sty.basename, debug, rest_options)
    #cleanup:
    if not debug:
        sty.remove()
        if rest not in rest_sources:
            rest.remove()
    old.chdir()

def process_rest_file(restfile, stylesheet=None, debug=False, rest_options=None):
    from docutils.core import publish_cmdline
    if not py.path.local.sysfind("pdflatex"):
        raise SystemExit("ERROR: pdflatex not found")
    old = py.path.local()
    f = py.path.local(restfile)
    path = f.dirpath()
    path.chdir()
    pdf = f.new(ext="pdf")
    if pdf.check():
        pdf.remove()
    tex = f.new(ext="tex").basename
    options = [f, "--input-encoding=latin-1", "--graphicx-option=auto",
               "--traceback"]
    if stylesheet is not None:
        sty = path.join(stylesheet)
        if sty.check():
            options.append('--stylesheet=%s' % (sty.relto(f.dirpath()), ))
    options.append(f.new(basename=tex))
    options = map(str, options)
    if rest_options is not None:
        options.extend(rest_options)
    publish_cmdline(writer_name='latex', argv=options)
    i = 0
    while i < 10: # there should never be as many as five reruns, but to be sure
        try:
            latexoutput = py.process.cmdexec('pdflatex "%s"' % (tex, ))
        except ExecutionFailed, e:
            print "ERROR: pdflatex execution failed"
            print "pdflatex stdout:"
            print e.out
            print "pdflatex stderr:"
            print e.err
            raise SystemExit
        if debug:
            print latexoutput
        if py.std.re.search("LaTeX Warning:.*Rerun", latexoutput) is None:
            break
        i += 1
            
    old.chdir()
    #cleanup:
    if not debug:
        for ext in "log aux tex out".split():
            p = pdf.new(ext=ext)
            p.remove()
