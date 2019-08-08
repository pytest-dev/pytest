import subprocess
import sys
import types
from typing import Dict

import _pytest
import pytest
from _pytest.mark import MarkDecorator

KNOWN_BAD: Dict[str, MarkDecorator] = {}


def _modvalues(module):
    for submodule in vars(module).values():
        if isinstance(submodule, types.ModuleType):
            name = submodule.__name__
            yield pytest.param(name, marks=KNOWN_BAD.get(name, []))


def _get_modules():
    yield from _modvalues(_pytest)
    yield from _modvalues(_pytest.config)
    yield from _modvalues(_pytest.mark)


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
