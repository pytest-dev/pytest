"""
Test importing of all internal packages and modules.

This ensures all internal packages can be imported without needing the pytest
namespace being set, which is critical for the initialization of xdist.
"""
import pkgutil
import subprocess
import sys

import _pytest
import pytest


def _modules():
    return sorted(
        n
        for _, n, _ in pkgutil.walk_packages(
            _pytest.__path__, prefix=_pytest.__name__ + "."
        )
    )


@pytest.mark.slow
@pytest.mark.parametrize("module", _modules())
def test_no_warnings(module):
    # fmt: off
    subprocess.check_call((
        sys.executable,
        "-W", "error",
        # https://github.com/pytest-dev/pytest/issues/5901
        "-W", "ignore:The usage of `cmp` is deprecated and will be removed on or after 2021-06-01.  Please use `eq` and `order` instead.:DeprecationWarning",  # noqa: E501
        "-c", "import {}".format(module),
    ))
    # fmt: on


def test_pytest_collect_attribute(_sys_snapshot):
    from types import ModuleType

    del sys.modules["pytest"]

    import pytest

    assert isinstance(pytest.collect, ModuleType)
    assert pytest.collect.Item is pytest.Item

    with pytest.raises(ImportError):
        import pytest.collect
