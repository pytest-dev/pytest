"""
Tested with coverage 2.85 and pygments 1.0

TODO:
    + 'html-output/*,cover' should be deleted
    + credits for coverage
    + credits for pygments
    + 'Install pygments' after ImportError is to less
    + is the way of determining DIR_CSS_RESOURCE ok?
    + write plugin test
    + '.coverage' still exists in py.test execution dir
"""

import os
import sys
import re
import shutil
from StringIO import StringIO

import py

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter
except ImportError:
    print "Install pygments" # XXX
    sys.exit(0)


DIR_CUR             = str(py.path.local())
REPORT_FILE         = os.path.join(DIR_CUR, '.coverage')
DIR_ANNOTATE_OUTPUT = os.path.join(DIR_CUR, '.coverage_annotate')
COVERAGE_MODULES    = set()
# coverage output parsing
REG_COVERAGE_SUMMARY  = re.compile('([a-z_\.]+) +([0-9]+) +([0-9]+) +([0-9]+%)')
REG_COVERAGE_SUMMARY_TOTAL  = re.compile('(TOTAL) +([0-9]+) +([0-9]+) +([0-9]+%)')
DEFAULT_COVERAGE_OUTPUT     = '.coverage_annotation'
# HTML output specific
DIR_CSS_RESOURCE    = os.path.dirname(__import__('pytest_coverage').__file__)
CSS_RESOURCE_FILES  = ['header_bg.jpg', 'links.gif']

COVERAGE_TERM_HEADER = "\nCOVERAGE INFORMATION\n" \
                        "====================\n"
HTML_INDEX_HEADER = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
        <html>
          <head>
          <title>py.test - Coverage Index</title>

          <style type="text/css">
          table {
         font-size:0.9em;
         font-family: Arial, Helvetica, verdana sans-serif;
         background-color:#fff;
         border-collapse: collapse;
         width: 500px;
        }
        caption {
         font-size: 25px;
         color: #1ba6b2;
         font-weight: bold;
         text-align: left;
         background: url(header_bg.jpg) no-repeat top left;
         padding: 10px;
         margin-bottom: 2px;
        }
        thead th {
         border-right: 1px solid #fff;
         color:#fff;
         text-align:center;
         padding:2px;
         text-transform:uppercase;
         height:25px;
         background-color: #a3c159;
         font-weight: normal;
        }
        tfoot {
         color:#1ba6b2;
         padding:2px;
         text-transform:uppercase;
         font-size:1.2em; 
         font-weigth: bold;
         margin-top:6px;
         border-top: 6px solid #e9f7f6;
        }
        tfoot td {
         text-align: left;
        }
        tbody tr {
         background-color:#fff;
         border-bottom: 1px solid #f0f0f0;
        }
        tbody td {
         color:#414141;
         padding:5px;
         text-align:left;
        }
        tbody th {
         text-align:left;
         padding:2px;
        }
        tbody td a, tbody th a {
         color:#6C8C37;
         text-decoration:none;
         font-weight:normal; 
         display:block;
         background: transparent url(links.gif) no-repeat 0% 50%;
         padding-left:15px;
        }
        tbody td a:hover, tbody th a:hover {
         color:#009193;
         text-decoration:none;
        }

        </style>

          </head>
          <body
          <table >
          <caption>Module Coverage</caption>
          <tbody>
            <thead>
            <tr>
              <th>Module</th>
              <th>Statements</th>
              <th>Executed</th>
              <th>Coverage</th>
            </tr>
            </thead>'''
HTML_INDEX_FOOTER = '''  </tbody>
          </table>
          </body>
        </html>'''


class CoverageHtmlFormatter(HtmlFormatter):
    """XXX: doc"""

    def __init__(self, *args, **kwargs):
        HtmlFormatter.__init__(self,*args, **kwargs)
        self.annotation_infos = kwargs.get('annotation_infos')

    def _highlight_lines(self, tokensource):
        """
        XXX: doc
        """

        hls = self.hl_lines
        self.annotation_infos = [None] + self.annotation_infos
        hls = [l for l, i in enumerate(self.annotation_infos) if i] 
        for i, (t, value) in enumerate(tokensource):
            if t != 1:
                yield t, value
            if i + 1 in hls: # i + 1 because Python indexes start at 0
                if self.annotation_infos[i+1] == "!":
                    yield 1, '<span style="background-color:#FFE5E5">%s</span>' \
                                          % value
                elif self.annotation_infos[i+1] == ">":
                    yield 1, '<span style="background-color:#CCFFEB">%s</span>' \
                                          % value
                else:
                    raise ValueError("HHAHA: %s" % self.annotation_infos[i+1])
            else:
                yield 1, value


def _rename_annotation_files(module_list, dir_annotate_output):
    for m in module_list:
        mod_fpath = os.path.basename(m.__file__)
        if mod_fpath.endswith('pyc'):
            mod_fpath = mod_fpath[:-1]
        old = os.path.join(dir_annotate_output, '%s,cover'% mod_fpath)
        new = os.path.join(dir_annotate_output, '%s,cover'% m.__name__)
        if os.path.isfile(old):
            shutil.move(old, new)
            yield new

def _generate_module_coverage(mc_path, anotation_infos, src_lines):
    #XXX: doc
    
    code = "".join(src_lines)
    mc_path = "%s.html" % mc_path
    lexer = get_lexer_by_name("python", stripall=True)
    formatter = CoverageHtmlFormatter(linenos=True, noclasses=True,
            hl_lines=[1], annotation_infos=anotation_infos)
    result = highlight(code, lexer, formatter)
    fp = open(mc_path, 'w')
    fp.write(result)
    fp.close()

def _parse_modulecoverage(mc_fpath):
    #XXX: doc

    fd = open(mc_fpath, 'r')
    anotate_infos = []
    src_lines = []
    for line in fd.readlines():
        anotate_info = line[0:2].strip()
        if not anotate_info:
            anotate_info = None
        src_line = line[2:]
        anotate_infos.append(anotate_info)
        src_lines.append(src_line)
    return mc_fpath, anotate_infos, src_lines 

def _parse_coverage_summary(fd):
    """Parses coverage summary output."""

    if hasattr(fd, 'readlines'):
        fd.seek(0)
        for l in fd.readlines():
            m = REG_COVERAGE_SUMMARY.match(l)
            if m:
                # yield name, stmts, execs, cover
                yield m.group(1), m.group(2), m.group(3), m.group(4)
            else:
                m = REG_COVERAGE_SUMMARY_TOTAL.match(l)
                if m:
                    # yield name, stmts, execs, cover
                    yield m.group(1), m.group(2), m.group(3), m.group(4)


def _get_coverage_index(mod_name, stmts, execs, cover, annotation_dir):
    """
    Generates the index page where are all modulare coverage reports are
    linked.
    """

    if mod_name == 'TOTAL':
        return '<tfoot><tr style="text-align: center;font-weigth:bold;font-size:1.2em; "><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr></tfoot>\n' % (mod_name, stmts, execs, cover)
    covrep_fpath = os.path.join(annotation_dir, '%s,cover.html' % mod_name)
    assert os.path.isfile(covrep_fpath) == True
    fname = os.path.basename(covrep_fpath)
    modlink = '<a href="%s">%s</a>' % (fname, mod_name)
    return '<tr style="text-align: center;"><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n' % (modlink, stmts, execs, cover)


class CoveragePlugin:
    def pytest_addoption(self, parser):
        group = parser.addgroup('coverage options')
        group.addoption('-C', action='store_true', default=False,
                dest = 'coverage',
                help=('displays coverage information.'))
        group.addoption('--coverage-html', action='store', default=False,
                dest='coverage_annotation',
                help='path to the coverage HTML output dir.')
        group.addoption('--coverage-css-resourcesdir', action='store',
                default=DIR_CSS_RESOURCE,
                dest='coverage_css_ressourcedir',
                help='path to dir with css-resources (%s) for '
                    'being copied to the HTML output dir.' % \
                            ", ".join(CSS_RESOURCE_FILES))

    def pytest_configure(self, config):
        if config.getvalue('coverage'):
            try:
                import coverage
            except ImportError:
                raise config.Error("To run use the coverage option you have to install " \
                        "Ned Batchelder's coverage: "\
                        "http://nedbatchelder.com/code/modules/coverage.html")
            self.coverage = coverage
            self.summary = None

    def pytest_terminal_summary(self, terminalreporter):
        if hasattr(self, 'coverage'):
            self.coverage.stop()
            module_list = [sys.modules[mod] for mod in COVERAGE_MODULES]
            module_list.sort()
            summary_fd  = StringIO()
            # get coverage reports by module list
            self.coverage.report(module_list, file=summary_fd) 
            summary = COVERAGE_TERM_HEADER + summary_fd.getvalue()
            terminalreporter._tw.write(summary)

            config = terminalreporter.config
            dir_annotate_output = config.getvalue('coverage_annotation')
            if dir_annotate_output:
                if dir_annotate_output == "":
                    dir_annotate_output = DIR_ANNOTATE_OUTPUT
                # create dir
                if os.path.isdir(dir_annotate_output):
                    shutil.rmtree(dir_annotate_output)
                os.mkdir(dir_annotate_output)
                # generate annotation text files for later parsing
                self.coverage.annotate(module_list, dir_annotate_output)
                # generate the separate module coverage reports
                for mc_fpath in _rename_annotation_files(module_list, \
                        dir_annotate_output):
                    # mc_fpath, anotate_infos, src_lines from _parse_do
                    _generate_module_coverage(*_parse_modulecoverage(mc_fpath))
                # creating contents for the index pagee for coverage report
                idxpage_html = StringIO()
                idxpage_html.write(HTML_INDEX_HEADER)
                total_sum = None
                for args in _parse_coverage_summary(summary_fd):
                    # mod_name, stmts, execs, cover = args
                    idxpage_html.write(_get_coverage_index(*args, \
                            **dict(annotation_dir=dir_annotate_output)))
                idxpage_html.write(HTML_INDEX_FOOTER)
                idx_fpath = os.path.join(dir_annotate_output, 'index.html')
                idx_fd = open(idx_fpath, 'w')
                idx_fd.write(idxpage_html.getvalue())
                idx_fd.close()

            dir_css_resource_dir = config.getvalue('coverage_css_ressourcedir')
            if dir_annotate_output and dir_css_resource_dir != "":
                if not os.path.isdir(dir_css_resource_dir):
                    raise config.Error("CSS resource dir not found: '%s'" % \
                            dir_css_resource_dir)
                for r in CSS_RESOURCE_FILES:
                    src = os.path.join(dir_css_resource_dir, r)
                    if os.path.isfile(src):
                        dest = os.path.join(dir_annotate_output, r)
                        shutil.copy(src, dest)

    def pyevent__collectionstart(self, collector):
        if isinstance(collector, py.__.test.pycollect.Module):
            COVERAGE_MODULES.update(getattr(collector.obj, 
                'COVERAGE_MODULES', []))

    def pyevent__testrunstart(self):
        if hasattr(self, 'coverage'):
            self.coverage.erase()
            self.coverage.start()


# ===============================================================================
# plugin tests 
# ===============================================================================
# XXX
'''
def test_generic(plugintester):
    plugintester.apicheck(EventlogPlugin)

    testdir = plugintester.testdir()
    testdir.makepyfile("""
        def test_pass():
            pass
    """)
    testdir.runpytest("--eventlog=event.log")
    s = testdir.tmpdir.join("event.log").read()
    assert s.find("TestrunStart") != -1
    assert s.find("ItemTestReport") != -1
    assert s.find("TestrunFinish") != -1
'''
