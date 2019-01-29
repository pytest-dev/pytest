Python 2.7 and 3.4 support plan
===============================

Python 2.7 EOL is fast approaching, with
upstream support `ending in 2020 <https://legacy.python.org/dev/peps/pep-0373/#id4>`__.
Python 3.4's last release is scheduled for
`March 2019 <https://www.python.org/dev/peps/pep-0429/#release-schedule>`__. pytest is one of
the participating projects of the https://python3statement.org.

We plan to drop support for Python 2.7 and 3.4 at the same time with the release of **pytest 5.0**,
scheduled to be released by **mid-2019**. Thanks to the `python_requires <https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires>`__ ``setuptools`` option,
Python 2.7 and Python 3.4 users using a modern ``pip`` version
will install the last compatible pytest ``4.X`` version automatically even if ``5.0`` or later
are available on PyPI.

During the period **from mid-2019 and 2020**, the pytest core team plans to make
bug-fix releases of the pytest ``4.X`` series by back-porting patches to the ``4.x-maintenance``
branch.

**After 2020**, the core team will no longer actively back port-patches, but the ``4.x-maintenance``
branch will continue to exist so the community itself can contribute patches. The
core team will be happy to accept those patches and make new ``4.X`` releases **until mid-2020**.
