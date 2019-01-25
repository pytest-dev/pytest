import subprocess
import sys
import types

import _pytest
import pytest

KNOWN_BAD = {
    "_pytest.assertion": [
        pytest.mark.xfail("sys.version_info[0]==3", reason="assertion uses imp")
    ]
}


def _get_modules():
    for module in vars(_pytest).values():
        if isinstance(module, types.ModuleType):
            name = module.__name__
            yield pytest.param(name, marks=KNOWN_BAD.get(name, []))


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
        # virtualenv bug
        "-W", "ignore:the imp:DeprecationWarning:distutils",
        "-c", "import " + module_name,
    ])
