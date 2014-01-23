============
Contributing
============

Contributions are highly welcomed and appreciated.  Every little help counts,
so do not hesitate!


Types of contributions
======================

Submit feedback for developers
------------------------------

Do you like py.test?  Share some love on Twitter or in your blog posts!

We'd also like to hear about your propositions and suggestions.  Feel free to
`submit them as issues <https://bitbucket.org/hpk42/pytest/issues>`__ and:

* Set the "kind" to "enhancement" or "proposal" so that we can quickly find
  about them.
* Explain in detail how they should work.
* Keep the scope as narrow as possible.  This will make it easier to implement.
* If you have required skills and/or knowledge, we are very happy for
  pull requests (see below).

Report bugs
-----------

Report bugs at https://bitbucket.org/hpk42/pytest/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting,
  specifically Python interpreter version,
  installed libraries and py.test version.
* Detailed steps to reproduce the bug.

Fix bugs
--------

Look through the BitBucket issues for bugs.  Here is sample filter you can use:
https://bitbucket.org/hpk42/pytest/issues?status=new&status=open&kind=bug

:ref:`Talk <contact>` to developers to find out how you can fix specific bugs.

Implement features
------------------

Look through the BitBucket issues for enhancements.  Here is sample filter you
can use:
https://bitbucket.org/hpk42/pytest/issues?status=new&status=open&kind=enhancement

:ref:`Talk <contact>` to developers to find out how you can implement specific
features.

Write documentation
-------------------

py.test could always use more documentation.  What exactly is needed?

* More complementary documentation.  Have you perhaps found something unclear?
* Documentation translations.  We currently have English and Japanese versions.
* Docstrings.  There's never too much of them.
* Blog posts, articles and such -- they're all very appreciated.

Getting started for contributing
================================

The primary development platform for py.test is BitBucket.  You can find all
the issues there and submit pull requests.  There is, however,
a `GitHub mirror <https://github.com/hpk42/pytest/>`__ available, too,
although it only allows for submitting pull requests.  For a GitHub
contribution guide look :ref:`below <contribution-on-github>`.

1. Fork the py.test `repository <https://bitbucket.org/hpk42/pytest>`__ on BitBucket.

2. Create a local virtualenv (http://www.virtualenv.org/en/latest/)::

    $ virtualenv pytest-venv
    $ cd pytest-venv/
    $ source bin/activate

.. _checkout:

3. Clone your fork locally::

    $ hg clone ssh://hg@bitbucket.org/your_name_here/pytest

.. _installing-dev-pytest:

4. Install your local copy into a virtualenv::

    $ cd pytest/
    $ python setup.py develop

   If that last command complains about not finding the required version
   of "py" then you need to use the development pypi repository::

    $ python setup.py develop -i http://pypi.testrun.org

.. _testing-pytest:

5. When you're done making changes, check that all of them pass all the tests
   (including PEP8 and different Python interpreter versions).  First install
   ``tox``::

    $ pip install tox

  You also need to have Python 2.7 and 3.3 available in your system.  Now
  running tests is as simple as issuing this one command::

    $ tox -e py27,py33

  This command will run tests for both Python 2.7 and 3.3, which is a minimum
  required to get your patch merged.  To run whole test suit issue::

    $ tox

6. Commit your changes and push to BitBucket::

    $ hg branch <yourbranchname>
    $ hg add .
    $ hg commit -m"<commit message>
    $ hg push -b .

7. Submit a pull request through the BitBucket website:

    source: <your user>/pytest
    branch: <yourbranchname>

    target: hpk42/pytest
    branch: default


.. _contribution-using-git:
What about git (and so GitHub)?
-------------------------------

There used to be the pytest github mirror. It was removed in favor of this mercurial one, to remove confusion of people
not knowing where it's better to put their issues and pull requests. Also it wasn't easilily possible to automate
mirroring process.
However, it's still possible to use git to contribute to pytest using tools like https://github.com/buchuki/gitifyhg
which allow you to clone and work mercurial repo still using git.

.. warning::
  Remember that git is **not** a default version control system py.test and you need to be careful using git
  to work with it.

Please read the manual carefully, and then use same contribution manual as for BitBucket.
