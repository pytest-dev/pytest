from _pytest.recwarn import RecordedWarning, WarningsRecorder
import inspect
import os
import pytest
import warnings


def _setoption(wmod, arg):
    """
    Copy of the warning._setoption function but does not escape arguments.
    """
    parts = arg.split(':')
    if len(parts) > 5:
        raise wmod._OptionError("too many fields (max 5): %r" % (arg,))
    while len(parts) < 5:
        parts.append('')
    action, message, category, module, lineno = [s.strip()
                                                 for s in parts]
    action = wmod._getaction(action)
    category = wmod._getcategory(category)
    if lineno:
        try:
            lineno = int(lineno)
            if lineno < 0:
                raise ValueError
        except (ValueError, OverflowError):
            raise wmod._OptionError("invalid lineno %r" % (lineno,))
    else:
        lineno = 0
    wmod.filterwarnings(action, message, category, module, lineno)


def pytest_addoption(parser):
    group = parser.getgroup("pytest-warnings")
    group.addoption(
        '-W', '--pythonwarnings', action='append',
        help="set which warnings to report, see -W option of python itself.")
    parser.addini("filterwarnings", type="linelist",
                  help="Each line specifies warning filter pattern which would be passed"
                  "to warnings.filterwarnings. Process after -W and --pythonwarnings.")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    wrec = WarningsRecorder()

    def showwarning(message, category, filename, lineno, file=None, line=None):
        frame = inspect.currentframe()
        if '/_pytest/recwarn' in frame.f_back.f_code.co_filename:
            # we are in test recorder, so this warning is already handled
            return
        wrec._list.append(RecordedWarning(
            message, category, filename, lineno, file, line))
        # still perform old showwarning functionality
        wrec._showwarning(
            message, category, filename, lineno, file=file, line=line)

    args = item.config.getoption('pythonwarnings') or []
    inifilters = item.config.getini("filterwarnings")
    with wrec:
        _showwarning = wrec._showwarning
        warnings.showwarning = showwarning
        wrec._module.simplefilter('once')
        for arg in args:
            wrec._module._setoption(arg)

        for arg in inifilters:
            _setoption(wrec._module, arg)

        yield
        wrec._showwarning = _showwarning

    for warning in wrec.list:
        msg = warnings.formatwarning(
            warning.message, warning.category,
            os.path.relpath(warning.filename), warning.lineno, warning.line)
        fslocation = getattr(item, "location", None)
        if fslocation is None:
            fslocation = getattr(item, "fspath", None)
        else:
            fslocation = "%s:%s" % fslocation[:2]
        fslocation = "in %s the following warning was recorded:\n" % fslocation
        item.config.warn("W0", msg, fslocation=fslocation)
