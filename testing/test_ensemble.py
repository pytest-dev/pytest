"""Tests for the experimental _pytest.ensemble API."""

from __future__ import annotations

from pathlib import Path

from _pytest.config import Config
from _pytest.ensemble import ConfigSpec
from _pytest.ensemble import configured
import pytest


class TestConfigSpec:
    def test_rootpath_required(self) -> None:
        with pytest.raises(ValueError, match="rootpath is required"):
            with configured(ConfigSpec()):
                pass

    def test_rootpath_must_be_dir(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="not a directory"):
            with configured(ConfigSpec(rootpath=tmp_path / "missing")):
                pass

    def test_essential_plugins_validated(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match=r"essential plugins.*runner"):
            with configured(ConfigSpec(rootpath=tmp_path, plugins=("python", "mark"))):
                pass

    def test_load_conftests_unsupported(self, tmp_path: Path) -> None:
        with pytest.raises(NotImplementedError, match="conftest"):
            with configured(ConfigSpec(rootpath=tmp_path, load_conftests=True)):
                pass

    def test_configured_basics(self, tmp_path: Path) -> None:
        spec = ConfigSpec(rootpath=tmp_path, args=("-k", "nothing"))
        with configured(spec) as config:
            assert config.rootpath == tmp_path
            assert config.inipath is None
            assert config.args == []
            assert config.args_source is Config.ArgsSource.SPEC
            assert config.getoption("keyword") == "nothing"
            assert config.invocation_params.dir == tmp_path
        # paired teardown ran
        assert not config._configured

    def test_inicfg_is_authoritative(self, tmp_path: Path) -> None:
        spec = ConfigSpec(rootpath=tmp_path, inicfg={"usefixtures": ["myfix"]})
        with configured(spec) as config:
            assert config.getini("usefixtures") == ["myfix"]

    def test_excluded_plugins_absent(self, tmp_path: Path) -> None:
        with configured(ConfigSpec(rootpath=tmp_path)) as config:
            assert config.pluginmanager.get_plugin("capturemanager") is None
            assert config.pluginmanager.get_plugin("terminalreporter") is None
            assert not config.pluginmanager.hasplugin("capture")
            assert not config.pluginmanager.hasplugin("terminal")
            assert not config.pluginmanager.hasplugin("cacheprovider")

    def test_spec_derivation_helpers(self) -> None:
        spec = ConfigSpec()
        derived = spec.with_plugins("capture").without_plugins("unittest")
        assert "capture" in derived.plugins
        assert "unittest" not in derived.plugins
        # frozen: original unchanged
        assert "capture" not in spec.plugins
