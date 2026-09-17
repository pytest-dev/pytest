============================
Contributing
============================

Contributions are highly welcomed and appreciated.  Every little bit of help counts,
so do not hesitate!


.. _submitfeedback:

Feature requests and feedback
-----------------------------

Do you like pytest?  Share some love on social media or in your blog posts!

We'd also like to hear about your propositions and suggestions.  Feel free to
`submit them as issues <https://github.com/pytest-dev/pytest/issues>`_ and:

* Explain in detail how they should work.
* Keep the scope as narrow as possible.  This will make it easier to implement.


.. _reportbugs:

Report bugs
-----------

Report bugs for pytest in the `issue tracker <https://github.com/pytest-dev/pytest/issues>`_.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting,
  specifically the Python interpreter version, installed libraries, and pytest
  version.
* Detailed steps to reproduce the bug.

If you can write a demonstration test that currently fails but should pass
(xfail), that is a very useful commit to make as well, even if you cannot
fix the bug itself.


.. _fixbugs:

Fix bugs
--------

Look through the `GitHub issues for bugs <https://github.com/pytest-dev/pytest/labels/type:%20bug>`_.
See also the `"good first issue" issues <https://github.com/pytest-dev/pytest/labels/good%20first%20issue>`_
that are friendly to new contributors.

`Talk to developers <https://docs.pytest.org/en/stable/contact.html>`_ to find out how you can fix specific bugs. To indicate that you are going
to work on a particular issue, add a comment to that effect on the specific issue.

Don't forget to check the issue trackers of your favourite plugins, too!

.. _writeplugins:

Implement features
------------------

Look through the `GitHub issues for enhancements <https://github.com/pytest-dev/pytest/labels/type:%20enhancement>`_.

`Talk to developers <https://docs.pytest.org/en/stable/contact.html>`_ to find out how you can implement specific
features.

Changes to documented behaviour are subject to our
`backwards compatibility policy <https://docs.pytest.org/en/stable/backwards-compatibility.html>`_,
and removals go through the
`deprecation process <https://docs.pytest.org/en/stable/deprecations.html>`_ first.

Write documentation
-------------------

Pytest could always use more documentation.  What exactly is needed?

* More complementary documentation.  Have you perhaps found something unclear?
* Documentation translations.  We currently have only English.
* Docstrings.  There can never be too many of them.
* Blog posts, articles and such -- they're all very appreciated.

You can also edit documentation files directly in the GitHub web interface,
without using a local copy.  This can be convenient for small fixes.

.. note::
    Build the documentation locally with the following command:

    .. code:: bash

        $ tox -e docs

    The built documentation should be available in ``doc/en/_build/html``,
    where 'en' refers to the documentation language.

Pytest has an API reference which in large part is
`generated automatically <https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`_
from the docstrings of the documented items. Pytest uses the
`Sphinx docstring format <https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html>`_.
For example:

.. code-block:: python

    def my_function(arg: ArgType) -> Foo:
        """Do important stuff.

        More detailed info here, in separate paragraphs from the subject line.
        Use proper sentences -- start sentences with capital letters and end
        with periods.

        Can include annotated documentation:

        :param short_arg: An argument which determines stuff.
        :param long_arg:
            A long explanation which spans multiple lines, overflows
            like this.
        :returns: The result.
        :raises ValueError:
            Detailed information when this can happen.

        .. versionadded:: 6.0

        Including types into the annotations above is not necessary when
        type-hinting is being used (as in this example).
        """


.. _submitplugin:

Submitting Plugins to pytest-dev
--------------------------------

Development of the pytest core, support code, and some plugins happens
in repositories living under the ``pytest-dev`` organisations:

- `pytest-dev on GitHub <https://github.com/pytest-dev>`_

All pytest-dev Contributors team members have write access to all contained
repositories.  Pytest core and plugins are generally developed
using `pull requests`_ to respective repositories.

The objectives of the ``pytest-dev`` organisation are:

* Having a central location for popular pytest plugins
* Sharing some of the maintenance responsibility (in case a maintainer no
  longer wishes to maintain a plugin)

You can submit your plugin by posting a new topic in the `pytest-dev GitHub Discussions
<https://github.com/pytest-dev/pytest/discussions>`_ pointing to your existing pytest plugin repository which must have
the following:

- PyPI presence with packaging metadata that contains a ``pytest-``
  prefixed name, version number, authors, short and long description.

- a `tox configuration <https://tox.readthedocs.io/en/latest/config.html#configuration-discovery>`_
  for running tests using `tox <https://tox.readthedocs.io>`_.

- a ``README`` describing how to use the plugin and on which
  platforms it runs.

- a ``LICENSE`` file containing the licensing information, with
  matching info in its packaging metadata.

- an issue tracker for bug reports and enhancement requests.

- a `changelog <https://keepachangelog.com/>`_.

If no contributor strongly objects and two agree, the repository can then be
transferred to the ``pytest-dev`` organisation.

The steps an administrator takes to perform the transfer are described in
the `maintenance guide <https://github.com/pytest-dev/pytest/blob/main/doc/en/maintenance.rst#transferring-a-plugin-to-pytest-dev>`__.

The ``pytest-dev/Contributors`` team has write access to all projects, and
every project administrator is in it. We recommend that each plugin has at least three
people who have the right to release to PyPI.

Repository owners can rest assured that no ``pytest-dev`` administrator will ever make
releases of your repository or take ownership in any way, except in rare cases
where someone becomes unresponsive after months of contact attempts.
As stated, the objective is to share maintenance and avoid "plugin-abandon".


.. _ai-contributions:

AI/LLM-Assisted Contributions Policy
-------------------------------------

We welcome contributions from all developers, including those who use AI/LLM tools
as part of their workflow. We genuinely encourage you to reach for these tools when
they help you learn, explore, and produce better work. However, we have requirements
to protect the time and effort of our reviewers:

**We use these tools ourselves.** Several pytest-core maintainers have access to
Anthropic's open-source grant (including Opus on Claude Max). We reach for AI daily
and value it — which is exactly why this policy is about *human effort*, not about the
tools. The bar is the one we hold ourselves to: understand what you ship, and stand
behind it.

**Real effort earns real investment.** If you have genuinely worked on a change — even
a rough or imperfect one — and can talk about it, we are glad to review it, give
feedback, and help you improve it, AI-assisted or not. What we ask for is your
engagement, not perfection. The line is human effort and accountability, never the
tools you used to get there.

**You are responsible for your contribution.** Regardless of how the code was
produced, the person submitting a pull request must understand the changes and be
able to respond to review feedback. If a reviewer asks questions or requests changes,
they expect to interact with someone who can engage substantively, not an automated
loop replaying prompts.

**Purely agentic contributions are not accepted.** Pull requests that are entirely
generated by AI agents, with no meaningful human review, understanding, or oversight,
will be closed. Every contribution must demonstrate that a human has reviewed,
understood, and taken responsibility for the changes. If you submit it, you own it.

**Unattended automation is an attack on the commons.** A contribution that shows
little to no human effort — unattended agent output, bulk-generated changes, PRs the
author cannot explain — is not collaboration. It is a denial-of-service on a volunteer
team: it spends finite review capacity that belongs to people who are genuinely trying
to learn and build. This is bigger than pytest — flooding *any* open-source project
with unattended AI output is hostile to a shared resource all of us depend on.

**We recognize the patterns, and we ban with prejudice.** Having driven these tools
daily, we know the tell-tale signatures of unattended agent output ("clankers"): the
generic commit prose, the confidently-wrong diffs, the inability to answer a simple
"why," the drive-by PR against an issue the author never engaged with. We will be
honest: the last several months of painful, low-quality bot contributions have left us
trigger-happy, and when those patterns show up we no longer spend a review cycle
coaxing a bot — we close and ban with prejudice. If you are a real person who happens
to trip a false positive, just talk to us; a human who understands their change is
always welcome, and we would far rather talk to you than to a script.

**Credit AI tools via attribution.** If AI agents helped produce your code or
commits, consider adding ``Co-authored-by`` trailers to your commit messages to
credit them. This is not required, but helps reviewers set expectations and is
appreciated.


Context
~~~~~~~

With the advent of unsupervised agentic tools like OpenClaw,
there has been a rise in low-quality contributions
where an agent produces a large number of low-quality pull requests.
Oftentimes this can look similar to a human beginner with new access to tools
and trying to learn, but in practice it is usually an unsupervised agentic tool
generating changes without meaningful human review.

When a human contributor is learning, we are glad to invest time to help,
give feedback, and guide them in the right direction. With fully agentic,
unsupervised tools, that same review effort does not support anyone's learning
or growth. Instead, it diverts limited maintainer time away from improving the
project and supporting engaged contributors.

There is also an asymmetry at play: someone is prioritizing what we review
without making an equivalent investment of time or effort.
When a contributor works on an issue themselves, they invest real time, effectively
earning influence over what the project focuses on. Unsupervised agentic contributions
expect to set that priority at near-zero cost to the sender, while shifting the
entire burden onto maintainers.

Fully agentic contributions invert the intended benefit of these tools: rather than
saving time, they create avoidable review and triage work. There is no accountable
human author thoughtfully iterating on feedback, only automated output driven
by prompts.

From our own experience using coding agents, we know they must be carefully prompted,
supervised, and checked by humans. Even modern models can make serious mistakes when
operating at framework or tooling level, and those mistakes can be subtle and
time-consuming to diagnose.

Running such tools unsupervised on open-source projects imposes this cost on
maintainers and other contributors without their consent. Our goal with this policy
is to set clear expectations, protect reviewer time, and ensure that contributions
remain collaborative, respectful, and sustainable.


.. _`pull requests`:
.. _pull-requests:

Preparing Pull Requests
-----------------------

Short version
~~~~~~~~~~~~~

#. Fork the repository and create a branch off ``main``.

#. Fetch the tags from upstream, they are needed to install the checkout::

    $ git fetch --tags https://github.com/pytest-dev/pytest

#. Set up the environment and the `pre-commit <https://pre-commit.com>`_ hook::

    $ uv sync --group dev
    $ uv run pre-commit install

#. Run the tests and the checks CI runs::

    $ uv run pytest
    $ uv run pre-commit run -a

#. Write a ``changelog`` entry, for example ``changelog/2574.bugfix.rst`` --
   see `changelog/README.rst <https://github.com/pytest-dev/pytest/blob/main/changelog/README.rst>`__
   for the available types.

#. Unless your change is trivial or a small documentation fix (e.g. a typo or a
   reword of a small section), add yourself to the ``AUTHORS`` file, in
   alphabetical order.


Long version
~~~~~~~~~~~~

What is a "pull request"?  It informs the project's core developers about the
changes you want to review and merge.  Pull requests are stored on
`GitHub servers <https://github.com/pytest-dev/pytest/pulls>`_.
Once you send a pull request, we can discuss its potential modifications and
even add more commits to it later on. There's an excellent tutorial on how Pull
Requests work in the
`GitHub Help Center <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests>`_.

Here is a simple overview, with pytest-specific bits:

#. Fork the
   `pytest GitHub repository <https://github.com/pytest-dev/pytest>`__.  It's
   fine to use ``pytest`` as your fork repository name because it will live
   under your user.

#. Clone your fork locally using `git <https://git-scm.com/>`_ and create a branch::

    $ git clone git@github.com:YOUR_GITHUB_USERNAME/pytest.git
    $ cd pytest
    $ git fetch --tags https://github.com/pytest-dev/pytest
    # now, create your own branch off "main":

        $ git checkout -b your-bugfix-branch-name main

   Given we have "major.minor.micro" version numbers, bug fixes will usually
   be released in micro releases whereas features will be released in
   minor releases and incompatible changes in major releases.

   pytest derives its version from the git tags, so a checkout without them
   cannot be installed. If you cloned with ``--depth`` or from a fork that has
   no tags, add the main repository as a remote and fetch them::

     $ git remote add upstream https://github.com/pytest-dev/pytest
     $ git fetch upstream --tags

   If you need some help with Git, follow this quick start
   guide: https://git.wiki.kernel.org/index.php/QuickStart

#. Create the development environment.

   We recommend `uv <https://docs.astral.sh/uv/>`_, which resolves the pinned
   development dependencies from ``uv.lock``::

     $ uv sync --group dev

   This creates ``.venv`` with pytest installed in editable mode, together with
   the ``dev`` :pep:`735` dependency group. Prefix commands with ``uv run`` to
   use that environment, or activate it as usual.

   .. important::

      Run the test suite from this environment, not from a pytest installed in
      your user site-packages. Parts of the suite launch pytest in subprocesses
      with a scrubbed environment, and an installation that is only visible via
      the user site will disappear for those subprocesses -- with failures that
      have nothing to do with your change.

   Without ``uv``, the equivalent needs ``pip`` 25.1 or newer::

     $ python3 -m venv .venv
     $ source .venv/bin/activate  # Linux/macOS
     $ .venv\Scripts\activate.bat  # Windows
     $ pip install -e . --group dev

#. Install the `pre-commit <https://pre-commit.com>`_ hook::

     $ uv run pre-commit install

   Afterwards ``pre-commit`` runs on every commit and re-formats files when
   necessary -- it is what keeps formatting, typing and the smaller
   project-specific checks consistent, so there is no separate style guide to
   memorise. To check the whole tree the way CI does::

     $ uv run pre-commit run -a

   Some hooks (``pyright``, ``pylint``, ``pyupgrade``) are configured for the
   ``manual`` stage and run neither on commit nor in CI.

#. Run the tests::

     $ uv run pytest                                # the whole suite
     $ uv run pytest testing/test_config.py         # a single module
     $ uv run pytest testing/test_config.py --pdb   # drop into pdb on failure

   The suite is large; while working on a change it is usually enough to run
   the modules that cover it and leave the rest to CI.

#. Test against other interpreters and dependency combinations with
   `tox <https://tox.wiki>`_.

   ``tox`` builds the environments CI uses. Install it with the ``tox-uv``
   plugin, which makes it reuse ``uv`` for those environments::

     $ uv tool install tox --with tox-uv

     $ tox -e py                             # your default interpreter
     $ tox -e linting,py                     # plus the pre-commit checks
     $ tox -e py313 -- testing/test_config.py

   ``tox.ini`` lists the available environments, including the ones for
   optional dependencies such as ``xdist``, ``numpy`` or ``twisted``.

#. Create a new changelog entry in ``changelog``. The file should be named
   ``<issueid>.<type>.rst``, where *issueid* is the number of the issue related
   to the change; see
   `changelog/README.rst <https://github.com/pytest-dev/pytest/blob/main/changelog/README.rst>`__
   for the available types and how to word an entry.
   You may skip the changelog entry if the change doesn't affect the documented
   behaviour of pytest. If there is no issue, open the pull request first and
   use its number.

#. Add yourself to ``AUTHORS`` file if not there yet, in alphabetical order.

#. Commit and push once your tests pass and you are happy with your change(s)::

    $ git commit -a -m "<commit message>"
    $ git push -u

#. Finally, submit a pull request through the GitHub website using this data::

    head-fork: YOUR_GITHUB_USERNAME/pytest
    compare: your-branch-name

    base-fork: pytest-dev/pytest
    base: main


Where things live
~~~~~~~~~~~~~~~~~

==========================  ====================================================
``src/_pytest/``            the implementation, mostly one module per builtin
                            plugin
``src/pytest/``             the public ``pytest`` namespace, re-exporting from
                            ``_pytest``
``testing/``                the test suite, largely mirroring ``src/_pytest``
``changelog/``              news fragments for the next release
``doc/en/``                 the documentation sources
``scripts/``                release and maintenance helpers
``bench/``                  benchmarks used when discussing performance
==========================  ====================================================


Writing Tests
~~~~~~~~~~~~~

Writing tests for plugins or for pytest itself is often done using the `pytester fixture <https://docs.pytest.org/en/stable/reference/reference.html#pytester>`_, as a "black-box" test.

For example, to ensure a simple test passes you can write:

.. code-block:: python

    def test_true_assertion(pytester):
        pytester.makepyfile(
            """
            def test_foo():
                assert True
        """
        )
        result = pytester.runpytest()
        result.assert_outcomes(failed=0, passed=1)


Alternatively, it is possible to make checks based on the actual output of the terminal using
*glob-like* expressions:

.. code-block:: python

    def test_true_assertion(pytester):
        pytester.makepyfile(
            """
            def test_foo():
                assert False
        """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["*assert False*", "*1 failed*"])

When choosing a file where to write a new test, take a look at the existing files and see if there's
one file which looks like a good fit. For example, a regression test about a bug in the ``--lf`` option
should go into ``test_cacheprovider.py``, given that this option is implemented in ``cacheprovider.py``.
If in doubt, go ahead and open a PR with your best guess and we can discuss this over the code.

Joining the Development Team
----------------------------

Commit access is an invitation the development team extends once a contributor
has shown a developed sense for the project -- its scope, its conventions, and
what a change costs the people who depend on it.  We look for that across
contributions, reviews and discussions rather than in any single pull request,
so there is nothing to clear on demand; if we haven't reached out yet, that is
not a verdict on your work -- sometimes no-one has thought to offer.

The invitation does not change how you contribute: everyone goes through the
same pull-request-and-review process, and no-one merges their own pull requests
unless already approved.  It does mean you can take a fuller part in the
development process, since you can merge other contributors' pull requests once
you have reviewed them.

What the team does with contributions once they arrive -- reviewing, merging,
backporting and closing stale work -- is described in the
`maintenance guide <https://github.com/pytest-dev/pytest/blob/main/doc/en/maintenance.rst>`__.
