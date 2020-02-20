Release Procedure
-----------------

Our current policy for releasing is to aim for a bug-fix release every few weeks and a minor release every 2-3 months. The idea
is to get fixes and new features out instead of trying to cram a ton of features into a release and by consequence
taking a lot of time to make a new one.

Preparing: Automatic Method
~~~~~~~~~~~~~~~~~~~~~~~~~~~

We have developed an automated workflow for releases, that uses GitHub workflows and is triggered
by opening an issue or issuing a comment one.

The comment must be in the form::

    @pytestbot please prepare release from BRANCH

Where ``BRANCH`` is ``master`` or one of the maintenance branches.

After that, the workflow should publish a PR and notify that it has done so as a comment
in the original issue.

Preparing: Manual Method
~~~~~~~~~~~~~~~~~~~~~~~~

.. important::

    pytest releases must be prepared on **Linux** because the docs and examples expect
    to be executed on that platform.

To release a version ``MAJOR.MINOR.PATCH``, follow these steps:

#. For major and minor releases, create a new branch ``MAJOR.MINOR.x`` from the
   latest ``master`` and push it to the ``pytest-dev/pytest`` repo.

#. Create a branch ``release-MAJOR.MINOR.PATCH`` from the ``MAJOR.MINOR.x`` branch.

   Ensure your are updated and in a clean working tree.

#. Using ``tox``, generate docs, changelog, announcements::

    $ tox -e release -- MAJOR.MINOR.PATCH

   This will generate a commit with all the changes ready for pushing.

#. Open a PR for the ``release-MAJOR.MINOR.PATCH`` branch targeting ``MAJOR.MINOR.x``.


Releasing
~~~~~~~~~

Both automatic and manual processes described above follow the same steps from this point onward.

#. After all tests pass and the PR has been approved, tag the release commit
   in the ``MAJOR.MINOR.x`` branch and push it. This will publish to PyPI::

     git tag MAJOR.MINOR.PATCH
     git push git@github.com:pytest-dev/pytest.git MAJOR.MINOR.PATCH

   Wait for the deploy to complete, then make sure it is `available on PyPI <https://pypi.org/project/pytest>`_.

#. Merge the PR.

#. Cherry-pick the CHANGELOG / announce files to the ``master`` branch::

       git fetch --all --prune
       git checkout origin/master -b cherry-pick-release
       git cherry-pick --no-commit -m1 origin/MAJOR.MINOR.x
       git checkout origin/master -- changelog
       git commit  # no arguments

#. Send an email announcement with the contents from::

     doc/en/announce/release-<VERSION>.rst

   To the following mailing lists:

   * pytest-dev@python.org (all releases)
   * python-announce-list@python.org (all releases)
   * testing-in-python@lists.idyll.org (only major/minor releases)

   And announce it on `Twitter <https://twitter.com/>`_ with the ``#pytest`` hashtag.
