How to release pytest
--------------------------------------------

Note: this assumes you have already registered on pypi.

1. Create a branch for the release (for example: ``release-5.9.8``). All commits
   should be made in this branch.

1. Bump version numbers in _pytest/__init__.py (setup.py reads it)

2. Check and finalize CHANGELOG.

3. Write doc/en/announce/release-VERSION.txt and include
   it in doc/en/announce/index.txt::

        git log 5.9.7..HEAD --format='%aN' | sort -u # lists the names of authors involved

7. Regenerate the docs examples using tox, and check for regressions::

      tox -e regen
      git diff


8. Build the docs, you need a virtualenv with py and sphinx
   installed::

      cd doc/en
      python plugins_index/plugins_index.py
      make html

   Commit any changes before tagging the release.

9. Tag the release::

      git tag VERSION
      git push

10. Upload the docs using doc/en/Makefile::

      cd doc/en
      make install  # or "installall" if you have LaTeX installed for PDF

    This requires ssh-login permission on pytest.org because it uses
    rsync.
    Note that the ``install`` target of ``doc/en/Makefile`` defines where the
    rsync goes to, typically to the "latest" section of pytest.org.

    If you are making a minor release (e.g. 5.4), you also need to manually
    create a symlink for "latest"::

       ssh pytest-dev@pytest.org
       ln -s 5.4 latest

    Browse to pytest.org to verify.

11. Publish to pypi::

      devpi push pytest-VERSION pypi:NAME

    where NAME is the name of pypi.python.org as configured in your ``~/.pypirc``
    file `for devpi <http://doc.devpi.net/latest/quickstart-releaseprocess.html?highlight=pypirc#devpi-push-releasing-to-an-external-index>`_.


12. Send release announcement to mailing lists:

    - pytest-dev
    - testing-in-python
    - python-announce-list@python.org


13. **after the release** Bump the version number in ``_pytest/__init__.py``,
    to the next Minor release version (i.e. if you released ``pytest-2.8.0``,
    set it to ``pytest-2.9.0.dev1``).

14. merge the actual release into the features branch and do a pull request against it
