
How to release pytest (draft)
--------------------------------------------

1. bump version numbers in pytest/__init__.py (setup.py reads it)

2. check and finalize CHANGELOG

3. write doc/en/announce/release-VERSION.txt and include
   it in doc/en/announce/index.txt

4. use devpi for uploading a release tarball to a staging area:
   - ``devpi use https://devpi.net/USER/dev`` 
   - ``devpi upload``

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

7. Regenerate the docs using the toplevel makefile::
      make docs

8. Upload the docs using the toplevel makefile::
      make upload-docs
   This requires ssh-login permission on pytest.org because it uses
   rsync.
   Note that the "install" target of doc/en/Makefile defines where the
   rsync goes to, typically to the "latest" section of pytest.org.

9. publish to pypi "devpi push pytest-2.6.2 pypi:NAME" where NAME 
   is the name of pypi.python.org as configured in your 
   ~/.pypirc file -- it's the same you would use with 
   "setup.py upload -r NAME"

10. send release announcement to mailing lists:

   pytest-dev
   testing-in-python
   python-announce-list@python.org

