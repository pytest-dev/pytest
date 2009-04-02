import py

class FigleafPlugin:
    def pytest_addoption(self, parser):
        group = parser.addgroup('figleaf options')
        group.addoption('-F', action='store_true', default=False,
                dest = 'figleaf',
                help=('trace coverage with figleaf and write HTML '
                     'for files below the current working dir'))
        group.addoption('--figleaf-data', action='store', default='.figleaf',
                dest='figleafdata',
                help='path coverage tracing file.')
        group.addoption('--figleaf-html', action='store', default='html',
                dest='figleafhtml', 
                help='path to the coverage html dir.')

    def pytest_configure(self, config):
        if config.getvalue('figleaf'):
            try:
                import figleaf
                import figleaf.annotate_html
            except ImportError:
                raise config.Error('Could not import figleaf module')
            self.figleaf = figleaf
            self.figleaf.start()

    def pytest_terminal_summary(self, terminalreporter):
        if hasattr(self, 'figleaf'):
            config = terminalreporter.config
            datafile = py.path.local(config.getvalue('figleafdata'))
            tw = terminalreporter._tw
            tw.sep('-', 'figleaf')
            tw.line('Writing figleaf data to %s' % (datafile))
            self.figleaf.stop()
            self.figleaf.write_coverage(str(datafile))
            coverage = self.get_coverage(datafile, config)

            reportdir = py.path.local(config.getvalue('figleafhtml'))
            tw.line('Writing figleaf html to file://%s' % (reportdir))
            self.figleaf.annotate_html.prepare_reportdir(str(reportdir))
            exclude = []
            self.figleaf.annotate_html.report_as_html(coverage, 
                    str(reportdir), exclude, {})

    def get_coverage(self, datafile, config):
        # basepath = config.topdir
        basepath = py.path.local()
        data = self.figleaf.read_coverage(str(datafile))
        d = {}
        coverage = self.figleaf.combine_coverage(d, data)
        for path in coverage.keys():
            if not py.path.local(path).relto(basepath):
                del coverage[path]
        return coverage


def test_generic(plugintester):
    plugintester.apicheck(FigleafPlugin)

def test_functional(testdir):
    py.test.importorskip("figleaf")
    testdir.plugins.append('figleaf')
    testdir.makepyfile("""
        def f():    
            x = 42
        def test_whatever():
            pass
        """)
    result = testdir.runpytest('-F')
    assert result.ret == 0
    assert result.stdout.fnmatch_lines([
        '*figleaf html*'
        ])
    #print result.stdout.str()
