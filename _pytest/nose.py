""" run test suites written for nose. """

import pytest, py
import inspect
import sys

def pytest_runtest_makereport(__multicall__, item, call):
    SkipTest = getattr(sys.modules.get('nose', None), 'SkipTest', None)
    if SkipTest:
        if call.excinfo and call.excinfo.errisinstance(SkipTest):
            # let's substitute the excinfo with a py.test.skip one
            call2 = call.__class__(lambda: py.test.skip(str(call.excinfo.value)), call.when)
            call.excinfo = call2.excinfo


def pytest_runtest_setup(item):
    if isinstance(item, (pytest.Function)):
        if isinstance(item.parent, pytest.Generator):
            gen = item.parent
            if not hasattr(gen, '_nosegensetup'):
                call_optional(gen.obj, 'setup')
                if isinstance(gen.parent, pytest.Instance):
                    call_optional(gen.parent.obj, 'setup')
                gen._nosegensetup = True
        if not call_optional(item.obj, 'setup'):
            # call module level setup if there is no object level one
            call_optional(item.parent.obj, 'setup')

def pytest_runtest_teardown(item):
    if isinstance(item, pytest.Function):
        if not call_optional(item.obj, 'teardown'):
            call_optional(item.parent.obj, 'teardown')
        #if hasattr(item.parent, '_nosegensetup'):
        #    #call_optional(item._nosegensetup, 'teardown')
        #    del item.parent._nosegensetup

def pytest_make_collect_report(collector):
    if isinstance(collector, pytest.Generator):
        call_optional(collector.obj, 'setup')

def call_optional(obj, name):
    method = getattr(obj, name, None)
    if method:
        # If there's any problems allow the exception to raise rather than
        # silently ignoring them
        method()
        return True
