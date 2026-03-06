# mypy: allow-untyped-defs
from __future__ import annotations

import os
from pathlib import Path
import re
import warnings

from _pytest import nodes
from _pytest.compat import legacy_path
from _pytest.outcomes import OutcomeException
from _pytest.pytester import Pytester
from _pytest.warning_types import PytestWarning
import pytest


def test_node_from_parent_disallowed_arguments() -> None:
    with pytest.raises(TypeError, match="session is"):
        nodes.Node.from_parent(None, session=None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="config is"):
        nodes.Node.from_parent(None, config=None)  # type: ignore[arg-type]


def test_node_direct_construction_deprecated() -> None:
    with pytest.raises(
        OutcomeException,
        match=(
            r"Direct construction of _pytest\.nodes\.Node has been deprecated, please "
            r"use _pytest\.nodes\.Node\.from_parent.\nSee "
            r"https://docs\.pytest\.org/en/stable/deprecations\.html#node-construction-changed-to-node-from-parent"
            r" for more details\."
        ),
    ):
        nodes.Node(None, session=None)  # type: ignore[arg-type]


def test_subclassing_both_item_and_collector_deprecated(
    request, tmp_path: Path
) -> None:
    """
    Verifies we warn on diamond inheritance as well as correctly managing legacy
    inheritance constructors with missing args as found in plugins.
    """
    # We do not expect any warnings messages to issued during class definition.
    with warnings.catch_warnings():
        warnings.simplefilter("error")

        class SoWrong(nodes.Item, nodes.File):
            def __init__(self, fspath, parent):
                """Legacy ctor with legacy call # don't wana see"""
                super().__init__(fspath, parent)

            def collect(self):
                raise NotImplementedError()

            def runtest(self):
                raise NotImplementedError()

    with pytest.warns(PytestWarning) as rec:
        SoWrong.from_parent(
            request.session, fspath=legacy_path(tmp_path / "broken.txt")
        )
    messages = [str(x.message) for x in rec]
    assert any(
        re.search(".*SoWrong.* not using a cooperative constructor.*", x)
        for x in messages
    )
    assert any(
        re.search("(?m)SoWrong .* should not be a collector", x) for x in messages
    )


@pytest.mark.parametrize(
    "warn_type, msg", [(DeprecationWarning, "deprecated"), (PytestWarning, "pytest")]
)
def test_node_warn_is_no_longer_only_pytest_warnings(
    pytester: Pytester, warn_type: type[Warning], msg: str
) -> None:
    items = pytester.getitems(
        """
        def test():
            pass
    """
    )
    with pytest.warns(warn_type, match=msg):
        items[0].warn(warn_type(msg))


def test_node_warning_enforces_warning_types(pytester: Pytester) -> None:
    items = pytester.getitems(
        """
        def test():
            pass
    """
    )
    with pytest.raises(
        ValueError, match="warning must be an instance of Warning or subclass"
    ):
        items[0].warn(Exception("ok"))  # type: ignore[arg-type]


class TestNormSep:
    """Tests for the norm_sep helper function."""

    def test_forward_slashes_unchanged(self) -> None:
        """Forward slashes pass through unchanged."""
        assert nodes.norm_sep("a/b/c") == "a/b/c"

    def test_backslashes_converted(self) -> None:
        """Backslashes are converted to forward slashes."""
        assert nodes.norm_sep("a\\b\\c") == "a/b/c"

    def test_mixed_separators(self) -> None:
        """Mixed separators are all normalized to forward slashes."""
        assert nodes.norm_sep("a\\b/c\\d") == "a/b/c/d"

    def test_pathlike_input(self, tmp_path: Path) -> None:
        """PathLike objects are converted to string with normalized separators."""
        # Create a path and verify it's normalized
        result = nodes.norm_sep(tmp_path / "subdir" / "file.py")
        assert "\\" not in result
        assert "subdir/file.py" in result

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        assert nodes.norm_sep("") == ""

    def test_windows_absolute_path(self) -> None:
        """Windows absolute paths have backslashes converted."""
        assert nodes.norm_sep("C:\\Users\\test\\project") == "C:/Users/test/project"


def test__check_initialpaths_for_relpath() -> None:
    """Ensure that it handles dirs, and does not always use dirname."""
    cwd = Path.cwd()

    initial_paths = frozenset({cwd})

    assert nodes._check_initialpaths_for_relpath(initial_paths, cwd) == ""

    sub = cwd / "file"
    assert nodes._check_initialpaths_for_relpath(initial_paths, sub) == "file"

    outside = Path("/outside-this-does-not-exist")
    assert nodes._check_initialpaths_for_relpath(initial_paths, outside) is None


def test_failure_with_changed_cwd(pytester: Pytester) -> None:
    """
    Test failure lines should use absolute paths if cwd has changed since
    invocation, so the path is correct (#6428).
    """
    p = pytester.makepyfile(
        """
        import os
        import pytest

        @pytest.fixture
        def private_dir():
            out_dir = 'ddd'
            os.mkdir(out_dir)
            old_dir = os.getcwd()
            os.chdir(out_dir)
            yield out_dir
            os.chdir(old_dir)

        def test_show_wrong_path(private_dir):
            assert False
    """
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines([str(p) + ":*: AssertionError", "*1 failed in *"])


class TestNodeidPrefixComputation:
    """Tests for nodeid prefix computation for paths outside rootdir."""

    def test_path_in_site_packages_found(self, tmp_path: Path) -> None:
        """Test _path_in_site_packages finds paths inside site-packages."""
        fake_site_packages = tmp_path / "site-packages"
        fake_site_packages.mkdir()
        pkg_path = fake_site_packages / "mypackage" / "tests" / "test_foo.py"
        pkg_path.parent.mkdir(parents=True)
        pkg_path.touch()

        site_packages = frozenset([fake_site_packages])
        result = nodes._path_in_site_packages(pkg_path, site_packages)

        assert result is not None
        sp_dir, rel_path = result
        assert sp_dir == fake_site_packages
        assert rel_path == Path("mypackage/tests/test_foo.py")

    def test_path_in_site_packages_not_found(self, tmp_path: Path) -> None:
        """Test _path_in_site_packages returns None for paths outside site-packages."""
        fake_site_packages = tmp_path / "site-packages"
        fake_site_packages.mkdir()
        other_path = tmp_path / "other" / "test_foo.py"
        other_path.parent.mkdir(parents=True)
        other_path.touch()

        site_packages = frozenset([fake_site_packages])
        result = nodes._path_in_site_packages(other_path, site_packages)

        assert result is None

    def test_compute_nodeid_inside_rootpath(self, tmp_path: Path) -> None:
        """Test nodeid computation for paths inside rootpath."""
        rootpath = tmp_path / "project"
        rootpath.mkdir()
        test_file = rootpath / "tests" / "test_foo.py"
        test_file.parent.mkdir(parents=True)
        test_file.touch()

        result = nodes.compute_nodeid_prefix_for_path(
            path=test_file,
            rootpath=rootpath,
            invocation_dir=rootpath,
            site_packages=frozenset(),
        )

        assert result == "tests/test_foo.py"

    def test_compute_nodeid_outside_rootpath(self, tmp_path: Path) -> None:
        """Test nodeid computation for paths outside rootpath uses bestrelpath."""
        rootpath = tmp_path / "project"
        rootpath.mkdir()
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_foo.py"
        test_file.touch()

        result = nodes.compute_nodeid_prefix_for_path(
            path=test_file,
            rootpath=rootpath,
            invocation_dir=rootpath,
            site_packages=frozenset(),
        )

        # Uses bestrelpath since outside rootpath
        assert result == "../tests/test_foo.py"

    def test_compute_nodeid_in_site_packages(self, tmp_path: Path) -> None:
        """Test nodeid computation for paths in site-packages uses site:// prefix."""
        rootpath = tmp_path / "project"
        rootpath.mkdir()
        fake_site_packages = tmp_path / "site-packages"
        fake_site_packages.mkdir()
        pkg_test = fake_site_packages / "mypackage" / "tests" / "test_foo.py"
        pkg_test.parent.mkdir(parents=True)
        pkg_test.touch()

        result = nodes.compute_nodeid_prefix_for_path(
            path=pkg_test,
            rootpath=rootpath,
            invocation_dir=rootpath,
            site_packages=frozenset([fake_site_packages]),
        )

        assert result == "site://mypackage/tests/test_foo.py"

    def test_compute_nodeid_nearby_relative(self, tmp_path: Path) -> None:
        """Test nodeid computation for nearby paths uses relative path."""
        rootpath = tmp_path / "project"
        rootpath.mkdir()
        sibling = tmp_path / "sibling" / "tests" / "test_foo.py"
        sibling.parent.mkdir(parents=True)
        sibling.touch()

        result = nodes.compute_nodeid_prefix_for_path(
            path=sibling,
            rootpath=rootpath,
            invocation_dir=rootpath,
        )

        assert result == "../sibling/tests/test_foo.py"

    def test_compute_nodeid_far_away_absolute(self, tmp_path: Path) -> None:
        """Test nodeid computation for far-away paths uses absolute path."""
        rootpath = tmp_path / "deep" / "nested" / "project"
        rootpath.mkdir(parents=True)
        far_away = tmp_path / "other" / "location" / "tests" / "test_foo.py"
        far_away.parent.mkdir(parents=True)
        far_away.touch()

        result = nodes.compute_nodeid_prefix_for_path(
            path=far_away,
            rootpath=rootpath,
            invocation_dir=rootpath,
        )

        # Should use absolute path since it's more than 2 levels up
        # Use nodes.SEP for cross-platform compatibility (nodeids always use forward slashes)
        assert result == str(far_away).replace(os.sep, nodes.SEP)

    def test_compute_nodeid_rootpath_itself(self, tmp_path: Path) -> None:
        """Test nodeid computation for rootpath itself returns empty string."""
        rootpath = tmp_path / "project"
        rootpath.mkdir()

        result = nodes.compute_nodeid_prefix_for_path(
            path=rootpath,
            rootpath=rootpath,
            invocation_dir=rootpath,
        )

        assert result == ""
