from __future__ import annotations

import sys
from typing import Any

import pytest

sys.path.append("testing")
from downstream_testing import downstream_runner  # noqa: E402

xfail = pytest.mark.xfail

DUMMY_YAML_COMBINATION = """---
name: dummy-include
jobs:
  test:
    runs-on: ubuntu-20.04

    strategy:
      fail-fast: false
      matrix:
        include:
        - name: i-do-not-start-with-py
          python: 3.6
          allow_failure: false

        - name: py310-dj40-postgres-xdist-coverage
          python: '3.10'
          allow_failure: false

        - name: py36-exclude-me
          python: 3.6
          allow_failure: false

        - name: py37-exclude-me
          python: 3.7
          allow_failure: false
"""

DUMMY_YAML_NO_COMBINATION = """---
name: dummy-no-include
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: [3.6, 3.7, 3.8, 3.9, "3.10", pypy3]
        exclude:
          - os: windows-latest
            python-version: pypy3
"""


@pytest.fixture()
def mock_schema_combination(monkeypatch):
    def mock_load_schema_combination(repo: str) -> dict[str, Any]:
        return {
            "matrix": ["matrix", "include"],
            "tox_cmd_build": {
                "base": "name",
                "prefix": "py",
                "sub": {"pattern": "-coverage$", "replace": ""},
            },
            "python_version": "python",
        }

    monkeypatch.setattr(
        downstream_runner, "load_matrix_schema", mock_load_schema_combination
    )


@pytest.fixture()
def mock_schema_no_combination(monkeypatch):
    def mock_load_schema_no_combination(repo: str) -> dict[str, Any]:
        return {
            "matrix": ["matrix", "python-version"],
            "tox_cmd_build": {
                "base": "",
                "prefix": "",
                "sub": {"pattern": "(\\d|py\\d)\\.*(\\d+)", "replace": "py\\1\\2"},
            },
            "python_version": "python",
        }

    monkeypatch.setattr(
        downstream_runner, "load_matrix_schema", mock_load_schema_no_combination
    )


@pytest.mark.downstream
class TestDownstreamRunnerConstructor:
    @pytest.mark.parametrize(
        "args",
        [
            pytest.param(tuple(), marks=xfail),
            pytest.param(("repo",), marks=xfail),
            pytest.param(("repo", "yaml_source"), marks=xfail),
            ("pytest-downstream", "yaml_source", ["jobs"]),
        ],
        ids=["no args", "repo only", "missing jobs", "all args"],
    )
    def test_args(self, args, mock_schema_combination) -> None:
        downstream_runner.DownstreamRunner(*args)

    @pytest.mark.parametrize(
        "kwargs",
        [
            ("matrix_exclude", "exclude"),
            ("dry_run", True),
        ],
        ids=["matrix_exclude", "dry_run"],
    )
    def test_kwargs(self, kwargs, mock_schema_combination) -> None:
        args = ("pytest-downstream", "yaml_source", ["test"])
        new_kwargs = {kwargs[0]: kwargs[1]}
        runner = downstream_runner.DownstreamRunner(*args, **new_kwargs)

        assert kwargs[1] == getattr(runner, kwargs[0])


@pytest.mark.downstream
class TestDownstreamRunnerProperties:
    def test_yaml_tree_file_doesnt_exist(self, mock_schema_combination) -> None:
        runner = downstream_runner.DownstreamRunner(
            "pytest-downstream", "yaml_source", ["test"], dry_run=True
        )

        with pytest.raises(FileNotFoundError):
            runner.yaml_tree

    def test_yaml_tree_bad_yaml(self, mock_schema_combination, tmp_path) -> None:
        yaml_source = tmp_path / "test.yml"
        yaml_source.write_text("---\n:")

        runner = downstream_runner.DownstreamRunner(
            "pytest-downstream", yaml_source, ["test"], dry_run=True
        )

        with pytest.raises(RuntimeError) as excinfo:
            runner.yaml_tree
        assert str(yaml_source) in excinfo.exconly(tryshort=True)

    def test_yaml_tree_empty_yaml(self, mock_schema_combination, tmp_path) -> None:
        yaml_source = tmp_path / "test.yml"
        yaml_source.write_text("---")

        runner = downstream_runner.DownstreamRunner(
            "pytest-downstream", yaml_source, ["test"], dry_run=True
        )

        with pytest.raises(RuntimeError) as excinfo:
            runner.yaml_tree
        assert str(yaml_source) in excinfo.exconly(tryshort=True)

    def test_yaml_tree_passing_yaml(self, mock_schema_combination, tmp_path) -> None:
        yaml_source = tmp_path / "test.yml"
        yaml_source.write_text(DUMMY_YAML_COMBINATION)

        runner = downstream_runner.DownstreamRunner(
            "pytest-downstream", yaml_source, ["test"], dry_run=True
        )

        assert runner.yaml_tree["name"] == "dummy-include"
        assert "test" in runner.yaml_tree["jobs"]

    def test_matrix_combination(self, mock_schema_combination, tmp_path) -> None:
        yaml_source = tmp_path / "test.yml"
        yaml_source.write_text(DUMMY_YAML_COMBINATION)

        runner = downstream_runner.DownstreamRunner(
            "pytest-downstream", yaml_source, ["test"], dry_run=True
        )

        assert all(
            [
                matrice.get("tox_cmd", "").startswith("py")
                for matrice in runner.matrix["test"]
            ]
        )

    def test_matrix_no_combination(self, mock_schema_no_combination, tmp_path) -> None:
        yaml_source = tmp_path / "test.yml"
        yaml_source.write_text(DUMMY_YAML_NO_COMBINATION)

        runner = downstream_runner.DownstreamRunner(
            "pytest-downstream", yaml_source, ["test"], dry_run=True
        )

        assert all(
            [
                matrice.get("tox_cmd", "").startswith("py")
                for matrice in runner.matrix["test"]
            ]
        )

    def test_matrix_combination_matrix_exclude(
        self, mock_schema_combination, tmp_path
    ) -> None:
        yaml_source = tmp_path / "test.yml"
        yaml_source.write_text(DUMMY_YAML_COMBINATION)
        matrix_to_exclude = ["py36-exclude-me", "py37-exclude-me"]

        runner = downstream_runner.DownstreamRunner(
            "pytest-downstream",
            yaml_source,
            ["test"],
            matrix_exclude=matrix_to_exclude,
            dry_run=True,
        )

        matrix_names = {matrice["name"] for matrice in runner.matrix["test"]}
        assert matrix_names.isdisjoint(set(matrix_to_exclude))

    def test_matrix_no_combination_matrix_exclude(
        self, mock_schema_no_combination, tmp_path
    ) -> None:
        yaml_source = tmp_path / "test.yml"
        yaml_source.write_text(DUMMY_YAML_NO_COMBINATION)
        matrix_to_exclude = ["3.6", "3.7"]

        runner = downstream_runner.DownstreamRunner(
            "pytest-downstream",
            yaml_source,
            ["test"],
            matrix_exclude=matrix_to_exclude,
            dry_run=True,
        )

        matrix_names = {matrice["name"] for matrice in runner.matrix["test"]}
        assert matrix_names.isdisjoint({"py36", "py37"})


@pytest.mark.downstream
class TestDownstreamRunnerBuild:
    def test_build_run_combination_matrix(
        self, mock_schema_combination, tmp_path
    ) -> None:
        yaml_source = tmp_path / "test.yml"
        yaml_source.write_text(DUMMY_YAML_COMBINATION)
        matrix_to_exclude = ["py36-exclude-me", "py37-exclude-me"]

        runner = downstream_runner.DownstreamRunner(
            "pytest-downstream",
            yaml_source,
            ["test"],
            matrix_exclude=matrix_to_exclude,
            dry_run=True,
        )

        run = runner.build_run()
        assert run == {
            "py310-dj40-postgres-xdist-coverage": [
                "tox -e py310-dj40-postgres-xdist",
            ]
        }

    def test_build_run_no_combination_matrix(
        self, mock_schema_no_combination, tmp_path
    ) -> None:
        yaml_source = tmp_path / "test.yml"
        yaml_source.write_text(DUMMY_YAML_NO_COMBINATION)
        matrix_to_exclude = ["3.6", "3.7"]

        runner = downstream_runner.DownstreamRunner(
            "pytest-downstream",
            yaml_source,
            ["test"],
            matrix_exclude=matrix_to_exclude,
            dry_run=True,
        )

        run = runner.build_run()
        assert run == {
            "py310": ["tox -e py310"],
            "py38": ["tox -e py38"],
            "py39": ["tox -e py39"],
            "pypy3": ["tox -e pypy3"],
        }
