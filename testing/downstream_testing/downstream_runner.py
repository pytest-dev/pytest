from __future__ import annotations

import argparse
import configparser
import json
import logging
import os.path
import re
import shlex
import subprocess
from collections import UserDict
from typing import Any
from typing import Iterable
from typing import Match
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from typing_extensions import TypedDict

logging.basicConfig(
    format="%(levelname)s | %(module)s.%(funcName)s | %(message)s", level="INFO"
)
logger = logging.getLogger(__name__)


parser = argparse.ArgumentParser(description="downstream Actions runner")
parser.add_argument("repo", help="Name of the repo.")
parser.add_argument("source", nargs=1, help="Path to source YAML file.")
parser.add_argument("jobs", nargs="+", help="Job names to use.")
parser.add_argument(
    "--matrix-exclude", nargs="*", default=[], help="Exclude these matrix names."
)
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Do not run parsed downstream action. Only display the generated command list.",
)

if TYPE_CHECKING:
    _BaseUserDict = UserDict[Any, Any]

    class SchemaBase(TypedDict):
        repo: str

    class SchemaToxBase(TypedDict):
        base: str
        prefix: str
        sub: dict[str, str]

    class SchemaType(SchemaBase, total=False):
        matrix: list[str]
        tox_cmd_build: SchemaToxBase
        python_version: str

else:
    _BaseUserDict = UserDict


def load_matrix_schema(repo: str) -> SchemaType:
    """Loads the matrix schema for `repo`"""
    schema: SchemaType = {"repo": repo}
    working_dir = os.getcwd()
    schema_path = os.path.join(
        working_dir, "testing", "downstream_testing", "action_schemas.json"
    )
    logger.debug("Loading schema: %s", schema_path)
    if os.path.exists(schema_path):
        with open(schema_path) as schema_file:
            try:
                schema = json.load(schema_file)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Error decoding '{schema_path}'") from exc
    else:
        raise FileNotFoundError(f"'{schema_path}' not found.")

    if repo in schema:
        logger.debug("'%s' schema loaded: %s", repo, schema)
        return schema[repo]  # type: ignore
    else:
        raise RuntimeError(
            f"'{repo}' schema definition not found in actions_schema.json"
        )


TOX_DEP_FILTERS = {
    "pytest-rerunfailures": {
        "src": "pytest-rerunfailures @ git+https://github.com/pytest-dev/pytest-rerunfailures.git",
        "condition": r"^pytest-rerunfailures.*",
        "has_gen": r"pytest-rerunfailures\w*:",
    },
    "pytest-xdist": {
        "src": "pytest-xdist",
        "condition": r"^pytest.*pytest-xdist",
        "has_gen": r"pytest\{.*\,7\d.*\}",
    },
    "pytest": {
        "src": f"pytest @ file://{os.getcwd()}",
        "condition": r"^pytest(?!\-)",
        "has_gen": r"pytest\w*",
    },
}


class ToxDepFilter(_BaseUserDict):
    def __init__(self) -> None:
        self.data = TOX_DEP_FILTERS

    def matches_condition(self, match: str) -> str | None:
        """Checks if `match` matches any conditions"""
        match_found = None
        for key, val in self.data.items():
            if "xdist" in match:
                logging.debug(
                    "matches_condition: %s", re.search(val["condition"], match)
                )
            if re.search(val["condition"], match):
                match_found = key
                break

        return match_found

    def matches_gen_exp(self, dep: str, match: str) -> Match[str] | None:
        """Checks if `match` matches `dep`['has_gen'] condition."""
        return re.match(self.data[dep]["has_gen"], match)

    def filter_dep(self, match: str) -> dict[Any, Any] | None:
        """Filters `match` based on conditions and returns the `src` dependency."""
        filtered_match = None
        dep_condition = self.matches_condition(match)
        if dep_condition is not None:
            dep_gen_exp = self.matches_gen_exp(dep_condition, match)
            if dep_gen_exp:
                filtered_match = {
                    "src": self.data[dep_condition]["src"],
                    "gen_exp": dep_gen_exp[0],
                }
                logger.debug("toxenv dependency updated: %s", filtered_match)
        return filtered_match


class DownstreamRunner:
    def __init__(
        self,
        repo: str,
        yaml_source: str,
        jobs: Iterable[str],
        matrix_exclude: Iterable[str] = (),
        dry_run: bool = False,
    ) -> None:
        self.repo = repo
        self.yaml_source = yaml_source
        self.matrix_exclude = matrix_exclude
        self.job_names = jobs
        self.dry_run = dry_run

        self._yaml_tree: dict[str, Any] | None = None
        self._matrix: dict[str, Any] | None = None
        self.matrix_schema: SchemaType = load_matrix_schema(self.repo)

    @property
    def yaml_tree(self) -> dict[str, Any]:
        """The YAML tree built from the `self.yaml_source` file."""
        if self._yaml_tree is None:
            with open(self.yaml_source) as f:
                _yaml_tree = yaml.safe_load(f.read())

            if _yaml_tree is None:
                raise SystemExit("Supplied YAML source failed to parse.")
            else:
                self._yaml_tree = _yaml_tree

        return self._yaml_tree

    def inject_pytest_dep(self) -> None:
        """Ensure pytest is a dependency in tox.ini to allow us to use the 'local'
        version of pytest.
        """
        ini_path = self.repo + "/tox.ini"
        pytest_dep = TOX_DEP_FILTERS["pytest"]["src"]
        tox_source = configparser.ConfigParser()
        tox_source.read_file(open(ini_path))
        found_dep = []
        updated_deps = set()
        section_deps = tox_source.get("testenv", "deps", fallback=None)
        if section_deps:
            tox_dep_filter = ToxDepFilter()
            for dep in section_deps.split("\n"):
                filtered_dep = tox_dep_filter.filter_dep(dep)
                if filtered_dep and filtered_dep["src"] not in found_dep:
                    found_dep.append(filtered_dep["src"])
                    updated_deps.add(
                        f"!{filtered_dep['gen_exp']}: {filtered_dep['src']}"
                    )

            if not [item for item in updated_deps if pytest_dep in item]:
                updated_deps.add(pytest_dep)
            final_deps = "\n".join(updated_deps)
            tox_source["testenv"][
                "deps"
            ] = f"{tox_source['testenv']['deps']}\n{final_deps}"

        with open(ini_path, "w") as f:
            tox_source.write(f)

    def __repr__(self) -> str:
        return str(
            "DownstreamRunner("
            f"repo={self.repo}, "
            f"yaml_source={self.yaml_source}, "
            f"job_names={self.job_names}, "
            f"matrix={self.matrix}, "
            ")"
        )

    @property
    def matrix(self) -> dict[str, Iterable[dict[str, str]]]:
        def parse_matrix(yaml_tree: dict[str, Any]) -> Iterable[Any]:
            parsed_matrix = []  # type: ignore
            pre_parsed: dict[str, Any] | Iterable[str | float] = yaml_tree
            for key in self.matrix_schema["matrix"]:
                if isinstance(pre_parsed, dict):
                    pre_parsed = pre_parsed[key]
            else:
                if isinstance(pre_parsed, list):
                    parsed_matrix = pre_parsed
                else:
                    msg_info = f"repo: {self.repo} | matrix schema: {self.matrix_schema} | parsed result: {pre_parsed}"
                    raise TypeError(
                        f"Parsed Actions matrix is invalid. Should be list/array. {msg_info}"
                    )

            logger.debug("parsed_matrix: %s", parsed_matrix)
            if parsed_matrix:
                tox_base = self.matrix_schema["tox_cmd_build"]["base"]
                tox_prefix = self.matrix_schema["tox_cmd_build"]["prefix"]
                skip_matrices = []
                if "include" in self.matrix_schema["matrix"]:
                    for item in parsed_matrix:
                        if (
                            not item[tox_base].startswith(tox_prefix)
                            or item[tox_base] in self.matrix_exclude
                            or not item.get("os", "ubuntu").startswith("ubuntu")
                        ):
                            skip_matrices.append(item)
                            continue

                        item["tox_cmd"] = re.sub(
                            self.matrix_schema["tox_cmd_build"]["sub"]["pattern"],
                            self.matrix_schema["tox_cmd_build"]["sub"]["replace"],
                            item[tox_base],
                        )
                        logger.debug("re.sub: %s", item[tox_base])

                    for matrice in skip_matrices:
                        parsed_matrix.remove(matrice)

                else:
                    new_parsed_matrix = []
                    for item in parsed_matrix:
                        if str(item) in self.matrix_exclude:
                            continue
                        tox_cmd = re.sub(
                            self.matrix_schema["tox_cmd_build"]["sub"]["pattern"],
                            self.matrix_schema["tox_cmd_build"]["sub"]["replace"],
                            str(item),
                        )
                        new_parsed_matrix.append({"name": tox_cmd, "tox_cmd": tox_cmd})
                    parsed_matrix = new_parsed_matrix

            return parsed_matrix

        if self._matrix is None:
            matrix_items = {}
            for job in self.job_names:
                job_yaml = self.yaml_tree["jobs"][job]["strategy"]
                parsed_matrix = parse_matrix(job_yaml)
                matrix_items[job] = parsed_matrix

            self._matrix = matrix_items
        logger.debug("matrix: %s", self._matrix)
        return self._matrix

    def build_run(self) -> dict[str, list[str]]:
        run = {}
        for job in self.job_names:
            logger.debug("job_name: %s", job)
            for matrix in self.matrix[job]:
                logger.debug("matrix[job]: %s", matrix)
                run[matrix["name"]] = ["pip install tox", f"tox -e {matrix['tox_cmd']}"]

        logger.debug("built run: %s", run)
        return run

    def run(self) -> None:
        self.inject_pytest_dep()
        run_steps = self.build_run()
        os.chdir(self.repo)
        for matrix, steps in run_steps.items():
            for step in steps:
                cmd = shlex.split(step)
                logger.info("--> running: '%s'", step)
                if not self.dry_run:
                    subprocess.run(cmd, encoding="utf-8", check=True)


if __name__ == "__main__":
    cli_args = parser.parse_args()
    if cli_args.dry_run:
        logger.setLevel("DEBUG")
    runner = DownstreamRunner(
        cli_args.repo,
        cli_args.source[0],
        cli_args.jobs,
        matrix_exclude=cli_args.matrix_exclude,
        dry_run=cli_args.dry_run,
    )

    runner.run()
