import py

Option = py.test.config.Option
option = py.test.config.addoptions("apigen test options",
        Option('', '--webcheck',
               action="store_true", dest="webcheck", default=False,
               help="run XHTML validation tests"
        ),
)

