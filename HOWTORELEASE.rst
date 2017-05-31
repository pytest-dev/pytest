How to release pytest
--------------------------------------------

.. important::

    pytest releases must be prepared on **Linux** because the docs and examples expect
    to be executed in that platform.

#. Install development dependencies in a virtual environment with::

    pip3 install -r tasks/requirements.txt

#. Create a branch ``release-X.Y.Z`` with the version for the release.

   * **patch releases**: from the latest ``master``;

   * **minor releases**: from the latest ``features``; then merge with the latest ``master``;

   Ensure your are in a clean work tree.

#. Generate docs, changelog, announcements and upload a package to
   your ``devpi`` staging server::

     invoke generate.pre_release <VERSION> <DEVPI USER> --password <DEVPI PASSWORD>

   If ``--password`` is not given, it is assumed the user is already logged in ``devpi``.
   If you don't have an account, please ask for one.

#. Open a PR for this branch targeting ``master``.

#. Test the package

   * **Manual method**

     Run from multiple machines::

       devpi use https://devpi.net/USER/dev
       devpi test pytest==VERSION

     Check that tests pass for relevant combinations with::

       devpi list pytest

   * **CI servers**

     Configure a repository as per-instructions on
     devpi-cloud-test_ to test the package on Travis_ and AppVeyor_.
     All test environments should pass.

#. Publish to PyPI::

      invoke generate.publish_release <VERSION> <DEVPI USER> <PYPI_NAME>

   where PYPI_NAME is the name of pypi.python.org as configured in your ``~/.pypirc``
   file `for devpi <http://doc.devpi.net/latest/quickstart-releaseprocess.html?highlight=pypirc#devpi-push-releasing-to-an-external-index>`_.

#. After a minor/major release, merge ``features`` into ``master`` and push (or open a PR).

.. _devpi-cloud-test: https://github.com/obestwalter/devpi-cloud-test
.. _AppVeyor: https://www.appveyor.com/
.. _Travis: https://travis-ci.org
