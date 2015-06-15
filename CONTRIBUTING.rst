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

All pytest-dev team members have write access to all contained
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
member of the ``pytest-dev`` team, with commit rights to all projects.
We recommend that each plugin has at least three people who have the
right to release to pypi.


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
* Documentation translations.  We currently have English and Japanese versions.
* Docstrings.  There's never too much of them.
* Blog posts, articles and such -- they're all very appreciated.

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
    $ git checkout pytest-2.7      # if you want to fix a bug for the pytest-2.7 series
    $ git checkout master          # if you want to add a feature bound for the next minor release
    $ git branch your-branch-name  # your feature/bugfix branch

   If you need some help with Git, follow this quick start
   guide: https://git.wiki.kernel.org/index.php/QuickStart

#. Create a development environment
   (will implicitly use http://www.virtualenv.org/en/latest/)::

    $ make develop
    $ source .env/bin/activate

#. You can now edit your local working copy.

   You need to have Python 2.7 and 3.4 available in your system.  Now
   running tests is as simple as issuing this command::

    $ python runtox.py -e py27,py34,flakes

   This command will run tests via the "tox" tool against Python 2.7 and 3.4
   and also perform "flakes" coding-style checks.  ``runtox.py`` is
   a thin wrapper around ``tox`` which installs from a development package
   index where newer (not yet released to pypi) versions of dependencies
   (especially ``py``) might be present.

   To run tests on py27 and pass options (e.g. enter pdb on failure)
   to pytest you can do::

    $ python runtox.py -e py27 -- --pdb

   or to only run tests in a particular test module on py34::

    $ python runtox.py -e py34 -- testing/test_config.py

#. Commit and push once your tests pass and you are happy with your change(s)::

    $ git commit -a -m "<commit message>"
    $ git push -u

#. Finally, submit a pull request through the GitHub website:

   .. image:: img/pullrequest.png
    :width: 700px
    :align: center

   ::

    head-fork: YOUR_GITHUB_USERNAME/pytest
    compare: your-branch-name

    base-fork: pytest-dev/pytest
    base: master          # if it's a feature
    base: pytest-VERSION  # if it's a bugfix


