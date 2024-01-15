import sys
from pathlib import Path
from types import ModuleType

from _pytest._py import os_path

_ON_CASEINSENSITIVE_OS = sys.platform.startswith("win")


def test_casesensitivepath(tmp_path: Path) -> None:
    dirname_with_caps = tmp_path / "Testdir"
    dirname_with_caps.mkdir()
    real_filename = dirname_with_caps / "_test_casesensitivepath.py"
    with real_filename.open("wb"):
        pass
    real_linkname = dirname_with_caps / "_test_casesensitivepath_link.py"
    real_linkname.symlink_to(real_filename)

    # Test path resolving

    original = str(real_filename)
    expected = str(real_filename)
    assert os_path.casesensitivepath(original) == expected

    original = str(real_filename).lower()
    if _ON_CASEINSENSITIVE_OS:
        expected = str(real_filename)
    else:
        expected = str(real_filename).lower()
    assert os_path.casesensitivepath(original) == expected

    # Test symlink preservation

    original = str(real_linkname)
    expected = str(real_linkname)
    assert os_path.casesensitivepath(original) == expected

    original = str(real_linkname).lower()
    expected = str(real_linkname).lower()
    assert os_path.casesensitivepath(original) == expected


def test_module_casesensitivepath(tmp_path: Path) -> None:
    dirname_with_caps = tmp_path / "Testdir"
    dirname_with_caps.mkdir()
    real_filename = dirname_with_caps / "_test_module_casesensitivepath.py"
    with real_filename.open("wb"):
        pass
    real_linkname = dirname_with_caps / "_test_module_casesensitivepath_link.py"
    real_linkname.symlink_to(real_filename)

    mod = ModuleType("dummy.name")

    mod.__file__ = None
    assert os_path.module_casesensitivepath(mod) is None

    # Test path resolving

    original = str(real_filename)
    expected = str(real_filename)
    mod.__file__ = original
    assert os_path.module_casesensitivepath(mod) == expected

    original = str(real_filename).lower()
    if _ON_CASEINSENSITIVE_OS:
        expected = str(real_filename)
    else:
        expected = str(real_filename).lower()
    mod.__file__ = original
    assert os_path.module_casesensitivepath(mod) == expected

    # Test symlink preservation

    original = str(real_linkname)
    expected = str(real_linkname)
    mod.__file__ = original
    assert os_path.module_casesensitivepath(mod) == expected

    original = str(real_linkname).lower()
    expected = str(real_linkname).lower()
    mod.__file__ = original
    assert os_path.module_casesensitivepath(mod) == expected
