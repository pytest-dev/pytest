============================
Contribution getting started
============================

Contributions are highly welcomed and appreciated.  Every little help counts,
so do not hesitate!

.. contents:: Contribution links
   :depth: 2


.. _submitplugin:

Submit a plugin, co-develop pytest
----------------------------------

Pytest development of the core, some plugins and support code happens
in repositories living under:

- `the pytest-dev github organisation <https://github.com/pytest-dev>`_

- `the pytest-dev bitbucket team <https://bitbucket.org/pytest-dev>`_

All pytest-dev Contributors team members have write access to all contained
repositories.  pytest core and plugins are generally developed
using `pull requests`_ to respective repositories.

You can submit your plugin by subscribing to the `pytest-dev mail list
<https://mail.python.org/mailman/listinfo/pytest-dev>`_ and writing a
mail pointing to your existing pytest plugin repository which must have
the following:

- PyPI presence with a ``setup.py`` that contains a license, ``pytest-``
  prefixed, version number, authors, short and long description.

- a ``tox.ini`` for running tests using `tox <http://tox.testrun.org>`_.

- a ``README.txt`` describing how to use the plugin and on which
  platforms it runs.

- a ``LICENSE.txt`` file or equivalent containing the licensing
  information, with matching info in ``setup.py``.

- an issue tracker unless you rather want to use the core ``pytest``
  issue tracker.

If no contributor strongly objects and two agree, the repo will be
transferred to the ``pytest-dev`` organisation and you'll become a
member of the ``pytest-dev Contributors`` team, with commit rights
to all projects. We recommend that each plugin has at least three
people who have the right to release to pypi.


.. _reportbugs:

Report bugs
-----------

Report bugs for pytest at https://github.com/pytest-dev/pytest/issues

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting,
  specifically Python interpreter version,
  installed libraries and pytest version.
* Detailed steps to reproduce the bug.

If you can write a demonstration test that currently fails but should pass (xfail),
that is a very useful commit to make as well, even if you can't find how
to fix the bug yet.

.. _submitfeedback:

Submit feedback for developers
------------------------------

Do you like pytest?  Share some love on Twitter or in your blog posts!

We'd also like to hear about your propositions and suggestions.  Feel free to
`submit them as issues <https://github.com/pytest-dev/pytest/issues>`__ and:

* Set the "kind" to "enhancement" or "proposal" so that we can quickly find
  about them.
* Explain in detail how they should work.
* Keep the scope as narrow as possible.  This will make it easier to implement.
* If you have required skills and/or knowledge, we are very happy for
  :ref:`pull requests <pull-requests>`.

.. _fixbugs:

Fix bugs
--------

Look through the GitHub issues for bugs.  Here is sample filter you can use:
https://github.com/pytest-dev/pytest/labels/bug

:ref:`Talk <contact>` to developers to find out how you can fix specific bugs.

Don't forget to check the issue trackers of your favourite plugins, too!

.. _writeplugins:

Implement features
------------------

Look through the GitHub issues for enhancements.  Here is sample filter you
can use:
https://github.com/pytest-dev/pytest/labels/enhancement

:ref:`Talk <contact>` to developers to find out how you can implement specific
features.

Write documentation
-------------------

pytest could always use more documentation.  What exactly is needed?

* More complementary documentation.  Have you perhaps found something unclear?
* Documentation translations.  We currently have only English.
* Docstrings.  There can never be too many of them.
* Blog posts, articles and such -- they're all very appreciated.

You can also edit documentation files directly in the Github web interface
without needing to make a fork and local copy. This can be convenient for
small fixes.

.. _`pull requests`:
.. _pull-requests:

Preparing Pull Requests on GitHub
---------------------------------

.. note::
  What is a "pull request"?  It informs project's core developers about the
  changes you want to review and merge.  Pull requests are stored on
  `GitHub servers <https://github.com/pytest-dev/pytest/pulls>`_.
  Once you send pull request, we can discuss it's potential modifications and
  even add more commits to it later on.

There's an excellent tutorial on how Pull Requests work in the
`GitHub Help Center <https://help.github.com/articles/using-pull-requests/>`_,
but here is a simple overview:

#. Fork the
   `pytest GitHub repository <https://github.com/pytest-dev/pytest>`__.  It's
   fine to use ``pytest`` as your fork repository name because it will live
   under your user.

#. Clone your fork locally using `git <https://git-scm.com/>`_ and create a branch::

    $ git clone git@github.com:YOUR_GITHUB_USERNAME/pytest.git
    $ cd pytest
    # now, to fix a bug create your own branch off "master":
    
        $ git checkout -b your-bugfix-branch-name master

    # or to instead add a feature create your own branch off "features":
    
        $ git checkout -b your-feature-branch-name features

   Given we have "major.minor.micro" version numbers, bugfixes will usually 
   be released in micro releases whereas features will be released in 
   minor releases and incompatible changes in major releases.

   If you need some help with Git, follow this quick start
   guide: https://git.wiki.kernel.org/index.php/QuickStart

#. Install tox

   Tox is used to run all the tests and will automatically setup virtualenvs
   to run the tests in.
   (will implicitly use http://www.virtualenv.org/en/latest/)::

    $ pip install tox

#. Run all the tests

   You need to have Python 2.7 and 3.5 available in your system.  Now
   running tests is as simple as issuing this command::

    $ python runtox.py -e linting,py27,py35

   This command will run tests via the "tox" tool against Python 2.7 and 3.5
   and also perform "lint" coding-style checks.  ``runtox.py`` is
   a thin wrapper around ``tox`` which installs from a development package
   index where newer (not yet released to pypi) versions of dependencies
   (especially ``py``) might be present.

#. You can now edit your local working copy.

   You can now make the changes you want and run the tests again as necessary.

   To run tests on py27 and pass options to pytest (e.g. enter pdb on failure)
   to pytest you can do::

    $ python runtox.py -e py27 -- --pdb

   or to only run tests in a particular test module on py35::

    $ python runtox.py -e py35 -- testing/test_config.py

#. Commit and push once your tests pass and you are happy with your change(s)::

    $ git commit -a -m "<commit message>"
    $ git push -u

   Make sure you add a CHANGELOG message, and add yourself to AUTHORS. If you
   are unsure about either of these steps, submit your pull request and we'll
   help you fix it up.

#. Finally, submit a pull request through the GitHub website using this data::

    head-fork: YOUR_GITHUB_USERNAME/pytest
    compare: your-branch-name

    base-fork: pytest-dev/pytest
    base: master          # if it's a bugfix
    base: feature         # if it's a feature


