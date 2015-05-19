
How to release pytest (draft)
--------------------------------------------

1. bump version numbers in _pytest/__init__.py (setup.py reads it)

2. check and finalize CHANGELOG

3. write doc/en/announce/release-VERSION.txt and include
   it in doc/en/announce/index.txt

4. use devpi for uploading a release tarball to a staging area:
   - ``devpi use https://devpi.net/USER/dev`` 
   - ``devpi upload --formats sdist,bdist_wheel``

5. run from multiple machines:
   - ``devpi use https://devpi.net/USER/dev`` 
   - ``devpi test pytest==VERSION``

6. check that tests pass for relevant combinations with
   ``devpi list pytest`` 
   or look at failures with "devpi list -f pytest".
   There will be some failed environments like e.g. the py33-trial 
   or py27-pexpect tox environments on Win32 platforms
   which is ok (tox does not support skipping on
   per-platform basis yet).

7. Regenerate the docs examples using tox::
      # Create and activate a virtualenv with regendoc installed
      # (currently needs revision 4a9ec1035734)
      tox -e regen

8. Build the docs, you need a virtualenv with, py and sphinx
   installed::
      cd docs/en
      make html

9. Tag the release::
      hg tag VERSION

10. Upload the docs using docs/en/Makefile::
      cd docs/en
      make install  # or "installall" if you have LaTeX installed
   This requires ssh-login permission on pytest.org because it uses
   rsync.
   Note that the "install" target of doc/en/Makefile defines where the
   rsync goes to, typically to the "latest" section of pytest.org.

11. publish to pypi "devpi push pytest-VERSION pypi:NAME" where NAME 
   is the name of pypi.python.org as configured in your 
   ~/.pypirc file -- it's the same you would use with 
   "setup.py upload -r NAME"

12. send release announcement to mailing lists:

   pytest-dev
   testing-in-python
   python-announce-list@python.org

