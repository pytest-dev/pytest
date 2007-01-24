import py
Option = py.test.config.Option

option = py.test.config.addoptions("boxing test options",
    Option('', '--skip-kill-test', action='store_true', default=False,
           dest='skip_kill_test',
           help='skip a certain test that checks for os.kill results, this '
                'should be used when kill() is not allowed for the current '
                'user'),
)
