How to release pytest
--------------------------------------------

Note: this assumes you have already registered on pypi.

1. Bump version numbers in ``_pytest/__init__.py`` (``setup.py`` reads it).

2. Check and finalize ``CHANGELOG.rst``.

3. Write ``doc/en/announce/release-VERSION.txt`` and include
   it in ``doc/en/announce/index.txt``. Run this command to list names of authors involved::

        git log $(git describe --abbrev=0 --tags)..HEAD --format='%aN' | sort -u

4. Regenerate the docs examples using tox::

      tox -e regen

5. At this point, open a PR named ``release-X`` so others can help find regressions or provide suggestions.

6. Use devpi for uploading a release tarball to a staging area::

     devpi use https://devpi.net/USER/dev
     devpi upload --formats sdist,bdist_wheel

7. Run from multiple machines::

     devpi use https://devpi.net/USER/dev
     devpi test pytest==VERSION

   Alternatively, you can use `devpi-cloud-tester <https://github.com/nicoddemus/devpi-cloud-tester>`_ to test
   the package on AppVeyor and Travis (follow instructions on the ``README``).

8. Check that tests pass for relevant combinations with::

       devpi list pytest

   or look at failures with "devpi list -f pytest".

9. Feeling confident? Publish to pypi::

      devpi push pytest==VERSION pypi:NAME

   where NAME is the name of pypi.python.org as configured in your ``~/.pypirc``
   file `for devpi <http://doc.devpi.net/latest/quickstart-releaseprocess.html?highlight=pypirc#devpi-push-releasing-to-an-external-index>`_.

10. Tag the release::

      git tag VERSION <hash>
      git push origin VERSION

    Make sure ``<hash>`` is **exactly** the git hash at the time the package was created.

11. Send release announcement to mailing lists:

    - pytest-dev@python.org
    - python-announce-list@python.org
    - testing-in-python@lists.idyll.org (only for minor/major releases)

    And announce the release on Twitter, making sure to add the hashtag ``#pytest``.

12. **After the release**

  a. **patch release (2.8.3)**:

        1. Checkout ``master``.
        2. Update version number in ``_pytest/__init__.py`` to ``"2.8.4.dev0"``.
        3. Create a new section in ``CHANGELOG.rst`` titled ``2.8.4.dev0`` and add a few bullet points as placeholders for new entries.
        4. Commit and push.

  b. **minor release (2.9.0)**:

        1. Merge ``features`` into ``master``.
        2. Checkout ``master``.
        3. Follow the same steps for a **patch release** above, using the next patch release: ``2.9.1.dev0``.
        4. Commit ``master``.
        5. Checkout ``features`` and merge with ``master`` (should be a fast-forward at this point).
        6. Update version number in ``_pytest/__init__.py`` to the next minor release: ``"2.10.0.dev0"``.
        7. Create a new section in ``CHANGELOG.rst`` titled ``2.10.0.dev0``, above ``2.9.1.dev0``, and add a few bullet points as placeholders for new entries.
        8. Commit ``features``.
        9. Push ``master`` and ``features``.

  c. **major release (3.0.0)**: same steps as that of a **minor release**


