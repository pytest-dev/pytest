"""
write and report coverage data with 'figleaf'. 

"""
import py
py.test.importorskip("figleaf")
import figleaf.annotate_html

def pytest_addoption(parser):
    group = parser.getgroup('figleaf options')
    group.addoption('--figleaf', action='store_true', default=False,
            dest = 'figleaf',
            help=('trace python coverage with figleaf and write HTML '
                 'for files below the current working dir'))
    group.addoption('--fig-data', action='store', default='.figleaf',
            dest='figleafdata', metavar="dir",
            help='set tracing file, default: ".figleaf".')
    group.addoption('--fig-html', action='store', default='html',
            dest='figleafhtml', metavar="dir",
            help='set html reporting dir, default "html".')

def pytest_configure(config):
    if config.getvalue("figleaf"):
        figleaf.start()

def pytest_terminal_summary(terminalreporter):
    config = terminalreporter.config
    if not config.getvalue("figleaf"):
        return
    datafile = py.path.local(config.getvalue('figleafdata'))
    tw = terminalreporter._tw
    tw.sep('-', 'figleaf')
    tw.line('Writing figleaf data to %s' % (datafile))
    figleaf.stop()
    figleaf.write_coverage(str(datafile))
    coverage = get_coverage(datafile, config)
    reportdir = py.path.local(config.getvalue('figleafhtml'))
    tw.line('Writing figleaf html to file://%s' % (reportdir))
    figleaf.annotate_html.prepare_reportdir(str(reportdir))
    exclude = []
    figleaf.annotate_html.report_as_html(coverage, 
            str(reportdir), exclude, {})

def get_coverage(datafile, config):
    # basepath = config.topdir
    basepath = py.path.local()
    data = figleaf.read_coverage(str(datafile))
    d = {}
    coverage = figleaf.combine_coverage(d, data)
    for path in coverage.keys():
        if not py.path.local(path).relto(basepath):
            del coverage[path]
    return coverage
