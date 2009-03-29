import py

class FigleafPlugin:
    def pytest_addoption(self, parser):
        group = parser.addgroup('figleaf options')
        group.addoption('-F', action='store_true', default=False,
                dest = 'figleaf',
                help='trace coverage with figleaf and write HTML')
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
            data_file = terminalreporter.config.getvalue('figleafdata')
            data_file = py.path.local(data_file)
            tw = terminalreporter._tw
            tw.sep('-', 'figleaf')
            tw.line('Writing figleaf data to %s' % (data_file))
            self.figleaf.stop()
            self.figleaf.write_coverage(str(data_file))
            data = self.figleaf.read_coverage(str(data_file))
            d = {}
            coverage = self.figleaf.combine_coverage(d, data)
            # TODO exclude pylib
            exclude = []

            reportdir = terminalreporter.config.getvalue('figleafhtml')
            reportdir = py.path.local(reportdir)
            tw.line('Writing figleaf html to file://%s' % (reportdir))
            self.figleaf.annotate_html.prepare_reportdir(str(reportdir))
            self.figleaf.annotate_html.report_as_html(coverage, 
                    str(reportdir), exclude, {})

def test_generic(plugintester):
    plugintester.apicheck(FigleafPlugin)

def test_functional(testdir):
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
    print result.stdout.str()
    assert 0
