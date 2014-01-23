============
Contributing
============

Contributions are highly welcomed and appreciated.  Every little help counts,
so do not hesitate!


Types of contributions
======================

Report bugs
-----------

Report bugs at https://bitbucket.org/hpk42/pytest/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting,
  specifically Python interpreter version,
  installed libraries and pytest version.
* Detailed steps to reproduce the bug.

Submit feedback for developers
------------------------------

Do you like pytest?  Share some love on Twitter or in your blog posts!

We'd also like to hear about your propositions and suggestions.  Feel free to
`submit them as issues <https://bitbucket.org/hpk42/pytest/issues>`__ and:

* Set the "kind" to "enhancement" or "proposal" so that we can quickly find
  about them.
* Explain in detail how they should work.
* Keep the scope as narrow as possible.  This will make it easier to implement.
* If you have required skills and/or knowledge, we are very happy for
  pull requests (see below).


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

pytest could always use more documentation.  What exactly is needed?

* More complementary documentation.  Have you perhaps found something unclear?
* Documentation translations.  We currently have English and Japanese versions.
* Docstrings.  There's never too much of them.
* Blog posts, articles and such -- they're all very appreciated.

Preparing Pull Requests on Bitbucket
=====================================

The primary development platform for pytest is BitBucket.  You can find all
the issues there and submit pull requests.  There is, however,
a `GitHub mirror <https://github.com/hpk42/pytest/>`__ available, too,
although it only allows for submitting pull requests.  For a GitHub
contribution guide look :ref:`below <contribution-on-github>`.

1. Fork the `pytest bitbucket repository <https://bitbucket.org/hpk42/pytest>`__. It's fine to 
  use ``pytest`` as your fork repository name because it will live
  under your user.

.. _virtualenvactivate:

2. Create and activate a fork-specific virtualenv 
   (http://www.virtualenv.org/en/latest/)::

    $ virtualenv pytest-venv
    $ source pytest-venv/bin/activate

.. _checkout:

3. Clone your fork locally and create a branch::

    $ hg clone ssh://hg@bitbucket.org/YOUR_BITBUCKET_USERNAME/pytest
    $ cd pytest
    $ hg branch <yourbranchname> 

.. _testing-pytest:

4. You can now edit your local working copy.  To test you need to
   install the "tox" tool into your virtualenv::

    $ pip install tox

  You need to have Python 2.7 and 3.3 available in your system.  Now
  running tests is as simple as issuing this command::

    $ python runtox.py -e py27,py33,flakes

  This command will run tests via the "tox" tool against Python 2.7 and 3.3 
  and also perform "flakes" coding-style checks.  ``runtox.py`` is
  a thin wrapper around ``tox`` which installs from a development package
  index where newer (not yet released to pypi) versions of dependencies
  (especially ``py``) might be present.

  To run tests on py27 and pass options (e.g. enter pdb on failure) 
  to pytest you can do::

    $ python runtox.py -e py27 -- --pdb 

  or to only run tests in a particular test module on py33::

    $ python runtox.py -e py33 -- testing/test_config.py

5. Commit and push once your tests pass and you are happy with your change(s)::

    $ hg commit -m"<commit message>"
    $ hg push -b .

6. Finally, submit a pull request through the BitBucket website::

    source: <your user>/pytest
    branch: <yourbranchname>

    target: hpk42/pytest
    branch: default

.. _contribution-on-github:

Preparing Pull Requests on Github
=====================================

.. warning::

  Remember that GitHub is **not** a default development platform for pytest
  and it doesn't include e.g. issue list.

1. Fork the `pytest github repository <https://github.com/hpk42/pytest/>`__.

2. :ref:`create and activate virtualenv <virtualenvactivate>`.

3. Clone your github fork locally and create a branch::

    $ git clone git@github.com:YOUR_GITHUB_USERNAME/pytest.git
    $ cd pytest
    $ git branch <yourbranchname>
    $ git checkout <yourbranchname>

4. :ref:`test your changes <testing-pytest>`.

5. Commit your changes and push to GitHub::

    $ git add PATH/TO/MODIFIED/FILE  # to add changes to staging
    $ git commit -am"<commit message>"
    $ git push origin <yourbranchname>

6. Submit a pull request through the GitHub website using the schema::

    base fork: hpk42/pytest
    base: master

    head fork: <your user>/pytest
    compare: <yourbranchname>
