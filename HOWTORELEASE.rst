How to release pytest
--------------------------------------------

Note: this assumes you have already registered on pypi.

1. Create a branch for the release (for example: ``release-1.2.3``). All commits
   should be made in this branch.

1. Bump version numbers in ``_pytest/__init__.py`` (setup.py reads it)

2. Check and finalize CHANGELOG.

3. Write ``doc/en/announce/release-VERSION.txt`` (copy from the previous version).
   Use this command line to obtain the list of contributors for the release::

      git log 1.2.2..HEAD --format='%aN' | sort -u # lists the names of authors involved

3. Include ``doc/en/announce/release-VERSION.txt`` into ``doc/en/announce/index.txt``.

7. Regenerate the docs examples using tox, and check for regressions::

      tox -e regen
      git diff


8. Build the docs, you need a virtualenv with py and sphinx
   installed::

      cd doc/en
      make html

9. Push changes to GitHub and open a Pull Request. Proceed
   when other pytest developers give it a ``+1``.

10. Upload the docs using doc/en/Makefile::

      cd doc/en
      make install  # or "installall" if you have LaTeX installed for PDF

    This requires ssh-login permission on pytest.org because it uses
    rsync.
    Note that the ``install`` target of ``doc/en/Makefile`` defines where the
    rsync goes to, typically to the "latest" section of pytest.org.

    If you are making the first version of a minor release (e.g. ``1.2.0``),
    you also need to manually create a symlink for "latest"::

       ssh pytest-dev@pytest.org
       ln -s 1.2 latest

    Browse to pytest.org to verify.

9. Tag the release::

      git tag VERSION
      git push VERSION


11. Create source and wheel distributions and upload them to pypi::

      git status  # make sure your working copy is clean and up-to-date with upstream
      python setup.py sdist bdist_wheel upload


12. Send release announcement to mailing lists:

    - pytest-dev
    - testing-in-python
    - python-announce-list@python.org

13. Merge ``release-1.2.3`` into ``master``.

13. At this point the release is done. Congratulations!

13. Bump the version number in ``_pytest/__init__.py``,
    to the next release version:

    * If you released a micro version (``1.2.3`` from ``master``), set it to the next
      micro version (``1.2.4.dev0``).
    * If you released a minor version (``1.3.0`` from ``features``), set it
      to the next micro version (``1.3.1.dev0``).

    Create a new entry in ``CHANGELOG`` for the next micro version.

14. Take this opportunity to merge the ``master`` branch into the next-version
    ``release`` branch, opening a Pull Request against it.
