import py
Option = py.test.config.Option

option = py.test.config.addoptions("execnet options",
        Option('-S', '',
               action="store", dest="sshtarget", default=None,
               help=("target to run tests requiring ssh, e.g. "
                     "user@codespeak.net")),
    )

