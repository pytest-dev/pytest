import argparse
import configparser
import json
import logging
import os
import os.path
import re
import shlex
import subprocess

import yaml

logging.basicConfig(format="%(levelname)s | %(module)s.%(funcName)s | %(message)s", level="INFO")
logger = logging.getLogger(__name__)


parser = argparse.ArgumentParser(
    description="downstream Actions runner"
)
parser.add_argument(
    "repo",
    #nargs=1,
    help="Name of the repo."
)
parser.add_argument(
    "source",
    nargs=1,
    help="Path to source YAML file."
)
parser.add_argument(
    "jobs",
    nargs="+",
    help="Job names to use."
)
parser.add_argument(
    "--matrix-exclude",
    nargs="*",
    default=[],
    help="Exclude these matrix names."
)

parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Do not run parsed downstream action. Only display the generated command list."
)

def load_matrix_schema(repo):
    """ Loads the matrix schema for `repo` """
    schema = None
    working_dir = os.getcwd()
    schema_path = os.path.join(
        working_dir,
        "testing",
        "downstream_testing",
        "action_schemas.json"
    )
    logger.debug("loading schema: %s", schema_path)
    if os.path.exists(schema_path):
        with open(schema_path) as schema_file:
            try:
                schema = json.load(schema_file)
            except json.JSONDecodeError:
                logger.error("failed to read action_schemas.json")
    else:
        logger.warning("action_schemas.json not found.")

    if schema is not None and repo in schema:
        schema = schema[repo]
        logger.debug("'%s' schema loaded: %s", repo, schema)
    else:
        schema = None
        logger.warning("'%s' schema not found in actions_schema.json", repo)

    return schema

class DownstreamRunner:
    # TODO: actualize args vs **kwargs
    def __init__(self, **kwargs):
        self.yaml_source = kwargs.get("yaml_source", None)
        if self.yaml_source == None:
            raise SystemExit("No YAML source provided.")
        self._yaml_tree = None
        self.repo = kwargs.get("repo")
        self.matrix_exclude = kwargs.get("matrix_exclude")
        self.job_names = kwargs.get("jobs")
        self._matrix = None
        self._steps = None
        self.dry_run = kwargs.get("dry_run", False)
        self.matrix_schema = load_matrix_schema(self.repo)


    @property
    def yaml_tree(self):
        """ The YAML tree built from the `yaml_source` file. """

        with open(self.yaml_source) as f:
            self._yaml_tree = yaml.safe_load(f.read())
        
        if self._yaml_tree == None:
            raise SystemExit("Supplied YAML source failed to parse.")
        
        return self._yaml_tree

    def inject_pytest_dep(self):
        """ Ensure pytest is a dependency in tox.ini to allow us to use the 'local'
            version of pytest.
        """
        ini_path = self.repo + "/tox.ini"
        pytest_dep = f"pytest @ file://{os.getcwd()}"
        DEPS = {
            "pytest": {
                "src": f"pytest @ file://{os.getcwd()}",
                "condition": lambda x: x.startswith("pytest") and not x.startswith("pytest-"),
                "has_gen": lambda x: re.search(r"pytest\w*:", x)
            },
            "pytest-rerunfailures": {
                "src": "pytest-rerunfailures @ git+https://github.com/pytest-dev/pytest-rerunfailures.git",
                "condition": lambda x: x.startswith("pytest-rerunfailures"),
                "has_gen": lambda x: re.search(r"pytest-rerunfailures\w*:", x)
            },
            "pytest-xdist": {
                "src": "pytest-xdist",
                "condition": lambda x: x.startswith("pytest{") and x.endswith("pytest-xdist"),
                "has_gen": lambda x: re.search(r"pytest\{.*\,7\d.*\}:", x)
            }
        }
        tox_source = configparser.ConfigParser()
        tox_source.read_file(open(ini_path))
        found_dep = []
        for section in tox_source.sections():
            updated_deps = set()
            section_deps = tox_source.get(section, "deps", fallback=None)
            if section_deps:
                for dep in section_deps.split("\n"):
                    for check_dep in DEPS:
                        if DEPS[check_dep]["condition"](dep):
                            has_gen = DEPS[check_dep]["has_gen"](dep)
                            if has_gen is not None and check_dep not in found_dep:
                                found_dep.append(check_dep)
                                updated_deps.add(f"!{has_gen.group()} {DEPS[check_dep]['src']}")
                
                if not [item for item in updated_deps if pytest_dep in item]:
                    updated_deps.add(pytest_dep)
                updated_deps = '\n'.join(updated_deps)
                tox_source[section]["deps"] = f"{tox_source[section]['deps']}\n{updated_deps}"

        with open(ini_path, "w") as f:
            tox_source.write(f)

    def __repr__(self):
        return str(
            "DownstreamRunner("
            f"repo={self.repo}, "
            f"yaml_source={self.yaml_source}, "
            f"job_names={self.job_names}, "
            f"matrix={self.matrix}, "
            f"steps={self.steps}"
            ")"
        )

    @property
    def matrix(self):
        def parse_matrix(yaml_tree):
            parsed_matrix = yaml_tree
            for key in self.matrix_schema["matrix"]:
                parsed_matrix = parsed_matrix[key]
                
            logger.debug("parsed_matrix: %s", parsed_matrix)
            if parsed_matrix != yaml_tree:
                tox_base = self.matrix_schema["tox_cmd_build"]["base"]
                tox_prefix = self.matrix_schema["tox_cmd_build"]["prefix"]
                skip_matrices = []
                if "include" in self.matrix_schema["matrix"]:
                    for item in parsed_matrix:
                        if (not item[tox_base].startswith(tox_prefix) or
                            item[tox_base] in self.matrix_exclude or
                            not item.get("os", "ubuntu").startswith("ubuntu")
                        ):
                            skip_matrices.append(item)
                            continue
                        
                        item["tox_cmd"] = re.sub(
                            self.matrix_schema["tox_cmd_build"]["sub"]["pattern"],
                            self.matrix_schema["tox_cmd_build"]["sub"]["replace"],
                            item[tox_base]
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
                            str(item)
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

    @property
    def steps(self):
        if self._steps is None:
            step_items = {}
            for job in self.job_names:
                if job not in step_items:
                    step_items[job] = []
                for item in self.yaml_tree["jobs"][job]["steps"]:
                    if "run" in item:
                        step_items[job].append(item)
            self._steps = step_items
        return self._steps
    
    def build_run(self):
        run = {}
        for job in self.job_names:
            logger.debug("job_name: %s", job)
            for matrix in self.matrix[job]:
                logger.debug("matrix[job]: %s", matrix)
                run[matrix["name"]] = [
                    "pip install tox",
                    f"tox -e {matrix['tox_cmd']}"
                ]

        logger.debug("built run: %s", run)
        return run

    def run(self):
        self.inject_pytest_dep()
        run_steps = self.build_run()
        os.chdir(self.repo)
        for matrix, steps in run_steps.items():
            for step in steps:
                cmd = shlex.split(step)
                logger.info("--> running: '%s'", step)
                if not self.dry_run:
                    subprocess.run(
                        cmd,
                        encoding="utf-8",
                        check=True
                    )

if __name__ == "__main__":
    cli_args = parser.parse_args()
    if cli_args.dry_run:
        logger.setLevel("DEBUG")
    runner_args = {
        "repo": cli_args.repo,
        "yaml_source": cli_args.source[0],
        "jobs": cli_args.jobs,
        "matrix_exclude": cli_args.matrix_exclude,
        "dry_run": cli_args.dry_run,
    }
    runner = DownstreamRunner(**runner_args)

    runner.run()