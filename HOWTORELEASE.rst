How to release pytest
--------------------------------------------

.. important::

    pytest releases must be prepared on **linux** because the docs and examples expect
    to be executed in that platform.

#. Install development dependencies in a virtual environment with::

    pip3 install -r tasks/requirements.txt

#. Create a branch ``release-X.Y.Z`` with the version for the release. Make sure it is up to date
   with the latest ``master`` (for patch releases) and with the latest ``features`` merged with
   the latest ``master`` (for minor releases). Ensure your are in a clean work tree.

#. Check and finalize ``CHANGELOG.rst`` (will be automated soon).

#. Execute to automatically generate docs, announcements and upload a package to
   your ``devpi`` staging server::

     invoke generate.pre_release <VERSION> <DEVPI USER> --password <DEVPI PASSWORD>

   If ``--password`` is not given, it is assumed the user is already logged in. If you don't have
   an account, please ask for one!

#. Run from multiple machines::

     devpi use https://devpi.net/USER/dev
     devpi test pytest==VERSION

   Alternatively, you can use `devpi-cloud-tester <https://github.com/nicoddemus/devpi-cloud-tester>`_ to test
   the package on AppVeyor and Travis (follow instructions on the ``README``).

#. Check that tests pass for relevant combinations with::

       devpi list pytest

   or look at failures with "devpi list -f pytest".

#. Feeling confident? Publish to PyPI::

      invoke generate.publish_release <VERSION> <DEVPI USER> <PYPI_NAME>

   where PYPI_NAME is the name of pypi.python.org as configured in your ``~/.pypirc``
   file `for devpi <http://doc.devpi.net/latest/quickstart-releaseprocess.html?highlight=pypirc#devpi-push-releasing-to-an-external-index>`_.


#. After a minor/major release, merge ``features`` into ``master`` and push (or open a PR).
