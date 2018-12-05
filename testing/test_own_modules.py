import subprocess
import sys
import types

import _pytest
import pytest

KNOWN_BAD = {"_pytest.assertion"}


def _get_modules():
    for module in vars(_pytest).values():
        if isinstance(module, types.ModuleType):
            name = module.__name__
            marks = [pytest.mark.xfail] if name in KNOWN_BAD else []
            yield pytest.param(name, marks=marks)


@pytest.mark.parametrize("module_name", sorted(_get_modules()))
def test_module_warning_free(module_name):
    # fmt: off
    subprocess.check_call([
        sys.executable,
        "-W", "error",
        # from virtualenv on appveyor
        "-W", "ignore:.*mode is deprecated.*:DeprecationWarning",
        # from bruno testing in a venv
        "-W", "ignore:.*Not importing directory.*:ImportWarning",
        "-c", "import " + module_name,
    ])
