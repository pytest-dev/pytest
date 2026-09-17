.. _maintenance:

=================
Maintenance Guide
=================

This guide collects the process the pytest team follows once contributions
arrive: how pull requests are merged, how fixes reach a patch release, and how
the issue and pull request queues are kept manageable.

Contributors do not need to read it in order to open a pull request -- see
:ref:`contributing` for that -- but nothing here is secret, and knowing how a
change travels after review makes a contribution easier to prepare.


Running CI on a branch
----------------------

Pushing a branch named ``test-me-*`` to the main repository runs the full test
matrix on it, without opening a pull request. This is useful to check a change
against Windows, macOS and the interpreters you do not have locally before
asking anyone to look at it.


Merge/squash guidelines
-----------------------

When a PR is approved and ready to be integrated to the ``main`` branch, one has the option to *merge* the commits unchanged, or *squash* all the commits into a single commit.

Here are some guidelines on how to proceed, based on examples of a single PR commit history:

1. Miscellaneous commits:

   * ``Implement X``
   * ``Fix test_a``
   * ``Add myself to AUTHORS``
   * ``fixup! Fix test_a``
   * ``Update tests/test_integration.py``
   * ``Merge origin/main into PR branch``
   * ``Update tests/test_integration.py``

   In this case, prefer to use the **Squash** merge strategy: the commit history is a bit messy (not in a derogatory way, often one just commits changes because they know the changes will eventually be squashed together), so squashing everything into a single commit is best. You must clean up the commit message, making sure it contains useful details.

2. Separate commits related to the same topic:

   * ``Implement X``
   * ``Add myself to AUTHORS``
   * ``Update CHANGELOG for X``

   In this case, prefer to use the **Squash** merge strategy: while the commit history is not "messy" as in the example above, the individual commits do not bring much value overall, specially when looking at the changes a few months/years down the line.

3. Separate commits, each with their own topic (refactorings, renames, etc), but still have a larger topic/purpose.

   * ``Refactor class X in preparation for feature Y``
   * ``Remove unused method``
   * ``Implement feature Y``

   In this case, prefer to use the **Merge** strategy: each commit is valuable on its own, even if they serve a common topic overall. Looking at the history later, it is useful to have the removal of the unused method separately on its own commit, along with more information (such as how it became unused in the first place).

4. Separate commits, each with their own topic, but without a larger topic/purpose other than improve the code base (using more modern techniques, improve typing, removing clutter, etc).

   * ``Improve internal names in X``
   * ``Add type annotations to Y``
   * ``Remove unnecessary dict access``
   * ``Remove unreachable code due to EOL Python``

   In this case, prefer to use the **Merge** strategy: each commit is valuable on its own, and the information on each is valuable in the long term.


As mentioned, those are overall guidelines, not rules cast in stone. This topic was discussed in `#12633 <https://github.com/pytest-dev/pytest/discussions/12633>`_.


*Backport PRs* (as those created automatically from a ``backport`` label) should always be **squashed**, as they preserve the original PR author.


Backporting bug fixes for the next patch release
------------------------------------------------

Pytest makes a feature release every few weeks or months. In between, patch releases
are made to the previous feature release, containing bug fixes only. The bug fixes
usually fix regressions, but may be any change that should reach users before the
next feature release.

Bugs are fixed on ``main`` first, with a regular pull request, and reach the
maintenance branch from there. The exception is a bug that no longer applies to
``main``, which is fixed on the maintenance branch directly.

The backport itself is done by the `patchback <https://patchback.github.io/>`__ bot.
Add a ``backport 1.2.x`` label to the pull request -- using the actual release series,
see https://github.com/pytest-dev/pytest/releases -- and patchback cherry-picks the
merge commit onto ``1.2.x`` and opens the backport pull request. The label works
before or after the merge, so a backport that was not planned for can still be had by
labelling the merged pull request.


When patchback cannot do it
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the cherry-pick conflicts, patchback gives up and says so on the pull request.
Only then is the backport done by hand:

#. ``git checkout origin/1.2.x -b backport-XXXX`` # use the main PR number here

#. Locate the merge commit on the PR, in the *merged* message, for example:

    nicoddemus merged commit 0f8b462 into pytest-dev:main

#. ``git cherry-pick -x -m1 REVISION`` # use the revision you found above (``0f8b462``).

#. Resolve the conflict, then open a PR targeting ``1.2.x``:

   * Prefix the message with ``[1.2.x]``.
   * Delete the PR body, it usually contains a duplicate commit message.


Who does the backporting
~~~~~~~~~~~~~~~~~~~~~~~~

Applying the label is part of merging: whoever merges a bug fix on ``main`` should
add the ``backport x.x.x`` label, and adding it afterwards costs nothing if it was
missed.

The question of who does the work only arises when patchback fails and someone has to
resolve the conflict:

1. If the bug was fixed by a core developer, it is the main responsibility of that core developer
   to do the backport.
2. However, often the merge is done by another maintainer, in which case it is nice of them to
   do the backport procedure if they have the time.
3. For bugs submitted by non-maintainers, it is expected that a core developer will do
   the backport, normally the one that merged the PR on ``main``.
4. If anyone notices a bug which is fixed on ``main`` but has not been backported --
   because the *needs backport* or *backport x.x.x* label was never applied, or because
   patchback failed and nobody picked it up -- they are also welcome to open the backport
   pull request themselves. The procedure is simple and really
   helps with the maintenance of the project.

All the above are not rules, but merely some guidelines/suggestions on what we should expect
about backports.

Backports should be **squashed** (rather than **merged**), as doing so preserves the original PR author correctly.

Handling stale issues/PRs
-------------------------

Stale issues/PRs are those where pytest contributors have asked for questions/changes
and the authors didn't get around to answer/implement them yet after a somewhat long time, or
the discussion simply died because people seemed to lose interest.

There are many reasons why people don't answer questions or implement requested changes:
they might get busy, lose interest, or just forget about it,
but the fact is that this is very common in open source software.

The pytest team really appreciates every issue and pull request, but being a high-volume project
with many issues and pull requests being submitted daily, we try to reduce the number of stale
issues and PRs by regularly closing them. When an issue/pull request is closed in this manner,
it is by no means a dismissal of the topic being tackled by the issue/pull request, but it
is just a way for us to clear up the queue and make the maintainers' work more manageable. Submitters
can always reopen the issue/pull request in their own time later if it makes sense.

When to close
~~~~~~~~~~~~~

Here are a few general rules the maintainers use to decide when to close issues/PRs because
of lack of inactivity:

* Issues labeled ``question`` or ``needs information``: closed after 14 days inactive.
* Issues labeled ``proposal``: closed after six months inactive.
* Pull requests: after one month, consider pinging the author, update linked issue, or consider closing. For pull requests which are nearly finished, the team should consider finishing it up and merging it.

The above are **not hard rules**, but merely **guidelines**, and can be (and often are!) reviewed on a case-by-case basis.

Closing pull requests
~~~~~~~~~~~~~~~~~~~~~

When closing a Pull Request, we should acknowledge the time, effort, and interest demonstrated by the person who submitted it. As mentioned previously, it is not the intent of the team to dismiss a stalled pull request entirely but to merely to clear up our queue, so a message like the one below is warranted when closing a pull request that went stale:

    Hi <contributor>,

    First of all, we would like to thank you for your time and effort on working on this, the pytest team deeply appreciates it.

    We noticed it has been awhile since you have updated this PR, however. pytest is a high activity project, with many issues/PRs being opened daily, so it is hard for us maintainers to track which PRs are ready for merging, for review, or need more attention.

    So for those reasons, we think it is best to close the PR for now, but with the only intention to clean up our queue, it is by no means a rejection of your changes. We still encourage you to re-open this PR (it is just a click of a button away) when you are ready to get back to it.

    Again we appreciate your time for working on this, and hope you might get back to this at a later time!

    <bye>

Closing issues
--------------

When a pull request is submitted to fix an issue, add text like ``closes #XYZW`` to the PR description and/or commits (where ``XYZW`` is the issue number). See the `GitHub docs <https://help.github.com/en/github/managing-your-work-on-github/linking-a-pull-request-to-an-issue#linking-a-pull-request-to-an-issue-using-a-keyword>`_ for more information.

When an issue is due to user error (e.g. misunderstanding of a functionality), please politely explain to the user why the issue raised is really a non-issue and ask them to close the issue if they have no further questions. If the original requester is unresponsive, the issue will be handled as described in the section `Handling stale issues/PRs`_ above.


.. _plugin-transfer:

Transferring a plugin to pytest-dev
-----------------------------------

Once a plugin submitted as described in :ref:`submitplugin` has been accepted,
the repository is transferred to the ``pytest-dev`` organisation. Here is how
that usually proceeds (using a repository named ``joedoe/pytest-xyz`` as
example):

* ``joedoe`` transfers repository ownership to ``pytest-dev`` administrator ``calvin``.
* ``calvin`` creates ``pytest-xyz-admin`` and ``pytest-xyz-developers`` teams, inviting ``joedoe`` to both as **maintainer**.
* ``calvin`` transfers repository to ``pytest-dev`` and configures team access:

  - ``pytest-xyz-admin`` **admin** access;
  - ``pytest-xyz-developers`` **write** access;
