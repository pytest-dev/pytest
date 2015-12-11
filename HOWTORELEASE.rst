How to release pytest
--------------------------------------------

Note: this assumes you have already registered on pypi.

#. Create a branch for the release named ``release-VERSION``:

   * If you will release a micro version (``1.2.3``), create the branch from ``master``::

        git checkout -b release-1.2.3 master


   * If you will release a minor version (``1.3.0``), create the branch from ``features``
     and make sure it is up to date with the latest ``master``::

        git checkout -b release-1.3.0 features
        git merge master

   All commits for the release should be made in this branch.

#. Bump version numbers in ``_pytest/__init__.py`` (setup.py reads it)

#. Check and finalize ``CHANGELOG``.

#. Write ``doc/en/announce/release-VERSION.txt`` (use the one from a
   previous version as a template).

   Use this command line to obtain the list of contributors for the release::

      git log 1.2.2..HEAD --format='%aN' | sort -u # lists the names of authors involved

#. Include ``doc/en/announce/release-VERSION.txt`` into ``doc/en/announce/index.txt``.

#. Regenerate the docs examples using tox, and check for regressions::

      pip install regendoc
      tox -e regen
      git diff


#. Push changes to GitHub and open a Pull Request. Proceed
   when other pytest developers give it a ``+1``.

#. Build the docs, you need a virtualenv with py and sphinx
   installed::

      cd doc/en
      make html


#. Upload the docs::

      cd doc/en
      make install  # or "installall" if you have LaTeX installed for PDF

   This requires ssh-login permission on ``pytest.org`` because it uses
   ``rsync``.

   .. note:: the ``install`` target of ``doc/en/Makefile`` defines where the
     rsync goes to, typically to the ``latest`` section of ``pytest.org``.

     If you are making the first version of a minor release (e.g. ``1.2.0``),
     you also need to manually create a symlink for "latest"::

       ssh pytest-dev@pytest.org
       ln -s 1.2 latest

     Browse to http://pytest.org/latest/ to verify.

#. Tag the release::

      git tag VERSION
      git push VERSION


#. Create source and wheel distributions and upload them to pypi::

      git status  # make sure your working copy is clean and up-to-date with upstream
      python setup.py sdist bdist_wheel upload


#. Send release announcement to mailing lists:

   * pytest-dev@python.org
   * testing-in-python@lists.idyll.org
   * python-announce-list@python.org

#. Merge your release branch into ``master``.

#. At this point the release is done. Congratulations!

#. Update version numbers in ``_pytest/__init__.py`` and ``CHANGELOG`` in the main branches:

   * If you released a micro version (``1.2.3``):
        - ``master``: update to to the next micro version (``1.2.4.dev0``).
        - ``features``: merge ``master`` into ``features``, and open a PR to ensure CI passes.

   * If you released a minor version (``1.3.0``):
        - ``master``: update to the next micro version (``1.3.1.dev0``).
        - ``features``: merge with ``master`` so you get ``1.3.1.dev0`` into your ``CHANGELOG``, and add a new entry for the next minor version (``1.4.0.dev0``).

