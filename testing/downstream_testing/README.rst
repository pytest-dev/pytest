Automated Downstream Testing
++++++++++++++++++++++++++++
Testing pytest Plugins With Changes to pytest
=============================================

Overview
--------

- Utilizes Docker (compose) inside a GitHub Actions workflow to establish the necessary environment(s) to run tests.

  - The base image is currently Ubuntu only, and uses ``pyenv`` to have the necessary versions of Python installed.

  - The base image is on Docker Hub, which greatly speeds up each run by avoiding ``pyenv``'s compilation process each time.

  - The completed image contains a PostgreSQL & mySQL layer (needed by ``pytest-django``, at minimum). Additional layers can be added if necessary.

- Utilizes each plugin's current test workflow to formulate the tests to run.

  - The plugin's GitHub Actions workflow is used to get ``tox`` environment settings.

  - The plugin's ``tox`` config is adjusted to ensure the local ``pytest`` is used.

- Uses a static command set: ``pip install tox`` & ``tox -e {toxenv}``.

How To Add Additional Plugin(s)
-------------------------------
**pytest/testing/downstream_testing/actions_schema.json:**
**********************************************************

``actions_schema.json`` outlines both GitHub Actions workflow fields to get information, and how
that information should be manipulated to provide usable tox environments to run a plugin's tests.

Example ``actions_schema.json`` entry:

  .. code:: JSON

    "pytest-django": {
      "matrix": [
        "matrix",
        "include"
      ],
      "tox_cmd_build": {
        "base": "name",
        "prefix": "py",
        "sub": {
          "pattern": "-coverage$",
          "replace": ""
        }
      }
    }

Below are the steps to add a new plugin.

1. Start by adding a new JSON object, with the name of the repo. ``"pytest-django": {}`` in the example above.

2. Add an array named ``matrix``. Array items should point to the strategy matrix from the repo's GitHub Actions
   YAML file. For instance, the ``pytest-django`` example above has a strategy matrix defined as follows:

    .. code:: YAML

      # pytest-django/.github/workflows/main.yml
      jobs:
        tests:
          strategy:
            fail-fast: false
            matrix:
              include:
              - name: linting,docs
                python: 3.8
                allow_failure: false

              - name: py310-dj40-postgres-xdist-coverage
                python: '3.10'
                allow_failure: false


  This makes ``["matrix", "include"]`` our target to parse the ``pytest-django`` strategy. This is a "combination"
  strategy based on the use of ``include``.

  For non-combination strategies, use the matrix field that points to the appropriate choices. Using
  ``pytest-order`` as a non-combination example:

    .. code:: YAML

      # pytest-order/.github/workflows/pythontests.yml
      jobs:
        test:
          runs-on: ${{ matrix.os }}
          strategy:
            fail-fast: false
            matrix:
              os: [ubuntu-latest, windows-latest]
              python-version: [3.6, 3.7, 3.8, 3.9, "3.10", pypy3]

  The corresponding entry in ``actions_schema.json`` points to ``["matrix", "python-version"]``:

    .. code:: JSON

      "pytest-order": {
          "matrix": [
              "matrix",
              "python-version"
          ],

3. Add a JSON object named ``tox_cmd_build``, with three items: ``base``, ``prefix``, and ``sub``.

   - ``base``: For combination strategies (with ``include``), ``base`` is the field to be used as the basis
      of the tox environment. For non-combination strategies, this field is an empty string. ``base: "name"``
      in the ``pytest-django`` example above.

   - ``prefix``: For combination strategies, ``prefix`` is used to [dis]qualify entries in ``base``. For
       non-combination strategies, this field is an emtpy string. ``prefix: "py"`` in the ``pytest-django``
       example above.

   - ``sub``: For both combination and non-combination strategies, this JSON object gives a RegEx matching
      (``pattern``) and a substituition (``replace``) string. Since these are JSON strings, they cannot be
      represented as a Python raw string (``r""``); ensure to properly escape characters.

Any additions can be verified locally with the following process:

1. Have a local copy of a plugin's GitHub Actions workflow YAML file, as well as a ``tox.ini``. These should
   be placed in a folder; recommended folder name is the repo name.

   .. code:: shell

     .
     .. pytest-order/
     .... main.yml
     .... tox.ini

2. Utilize the ``--dry-run`` flag to run the parsing and command step building, without actually executing
   the commands. This will provide debugging information.

   .. code::

      (.venv) ~/pytest:$> python -m testing.downstream_testing.downstream_runner pytest-order pytest-order/pytest-order.yml test --matrix-exclude 3.6 --dry-run

      DEBUG | downstream_runner.load_matrix_schema | Loading schema: /home/sommersoft/Dev/pytest-dev/pytest/testing/downstream_testing/action_schemas.json
      DEBUG | downstream_runner.load_matrix_schema | 'pytest-order' schema loaded: {'matrix': ['matrix', 'python-version'],
      'tox_cmd_build': {'base': '', 'prefix': '', 'sub': {'pattern': '(\\d|py\\d)\\.*(\\d+)', 'replace': 'py\\1\\2'}}, 'python_version': 'python-version'}
      DEBUG | downstream_runner.inject_pytest_dep | toxenv dependencies updated: {'!pytest{60,61,62,624,70}: pytest-xdist', '!pytest50: pytest @ file:///home/pytest'}
      DEBUG | downstream_runner.build_run | job_name: test
      DEBUG | downstream_runner.parse_matrix | parsed_matrix: [3.6, 3.7, 3.8, 3.9, '3.10', 'pypy3']
      DEBUG | downstream_runner.matrix | matrix: {'test': [{'name': 'py37', 'tox_cmd': 'py37'}, {'name': 'py38', 'tox_cmd': 'py38'}, {'name': 'py39', 'tox_cmd': 'py39'},
      {'name': 'py310', 'tox_cmd': 'py310'}, {'name': 'pypy3', 'tox_cmd': 'pypy3'}]}
      DEBUG | downstream_runner.build_run | matrix[job]: {'name': 'py37', 'tox_cmd': 'py37'}
      DEBUG | downstream_runner.build_run | matrix[job]: {'name': 'py38', 'tox_cmd': 'py38'}
      DEBUG | downstream_runner.build_run | matrix[job]: {'name': 'py39', 'tox_cmd': 'py39'}
      DEBUG | downstream_runner.build_run | matrix[job]: {'name': 'py310', 'tox_cmd': 'py310'}
      DEBUG | downstream_runner.build_run | matrix[job]: {'name': 'pypy3', 'tox_cmd': 'pypy3'}
      DEBUG | downstream_runner.build_run | built run: {'py37': ['pip install tox', 'tox -e py37'], 'py38': ['pip install tox', 'tox -e py38'], 'py39': ['pip install tox',
      'tox -e py39'], 'py310': ['pip install tox', 'tox -e py310'], 'pypy3': ['pip install tox', 'tox -e pypy3']}
      INFO | downstream_runner.run | --> running: 'pip install tox'
      INFO | downstream_runner.run | --> running: 'tox -e py37'
      INFO | downstream_runner.run | --> running: 'pip install tox'
      INFO | downstream_runner.run | --> running: 'tox -e py38'
      INFO | downstream_runner.run | --> running: 'pip install tox'
      INFO | downstream_runner.run | --> running: 'tox -e py39'
      INFO | downstream_runner.run | --> running: 'pip install tox'
      INFO | downstream_runner.run | --> running: 'tox -e py310'
      INFO | downstream_runner.run | --> running: 'pip install tox'
      INFO | downstream_runner.run | --> running: 'tox -e pypy3'


**pytest/.github/workflows/downstream_testing.yml:**
*****************************************************
This GitHub Actions workflow orchestrates the various plugin tests, and only requires some minimal information.

Add a new entry to the combination strategy matrix:

1. ``name``: the plugin's repository name.

2. ``repo``: the ``org/name`` of the plugin's GitHub repository.

3. ``docker_profile``: the docker-compose profile to use for this entry. Docker profiles are defined in
   ``pytest/testing/downstream_testing/docker-compose.yml``. At the time of this writing, the available
   profiles are: ``nodb``, ``mysql``, & ``postgres``.

4. ``jobs``: the list of job(s) to use from the plugin's GitHub Actions workflow.

5. ``workflow_name``: the name of the GitHub Actions workflow file to use (located in ``plugin/.github/workflows``).

6. ``matrix_exclude``: any entries to exclude from the selected matrix (combination & non-combination).

.. code:: YAML

  - name: "pytest-django"
    repo: "pytest-dev/pytest-django"
    docker_profile: "postgres"
    jobs: "test"
    workflow_name: "main.yml"
    matrix_exclude: |
      linting,docs py39-dj40-mysql_innodb-coverage ...

  - name: "pytest-django"
    repo: "pytest-dev/pytest-django"
    docker_profile: "mysql"
    jobs: "test"
    workflow_name: "main.yml"
    matrix_exclude: |
      linting,docs py310-dj40-postgres-xdist-coverage ...

.. epigraph::
  Example 1: using ``pytest-django``, which has a combination strategy matrix, we see two (of three) different
  ``downstream_testing.yml`` entries. They each require a different database, so each entry uses the appropriate
  ``docker_profile``. Additionally, to avoid known failures, ``matrix_exclude`` has all items that don't match
  the database in use.

.. code:: YAML

  - name: "pytest-order"
    repo: "pytest-dev/pytest-order"
    docker_profile: "nodb"
    jobs: "test"
    workflow_name: "pythontests.yml"
    matrix_exclude: |
      3.6

.. epigraph::
  Example 2: using ``pytest-order``, which has a non-combination strategy matrix and requires no database.
