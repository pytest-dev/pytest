.. _backwards-compatibility:

Backwards Compatibility Policy
==============================

Keeping backwards compatibility has a very high priority in the pytest project. Although we have deprecated functionality over the years, most of it is still supported. All deprecations in pytest were done because simpler or more efficient ways of accomplishing the same tasks have emerged, making the old way of doing things unnecessary.

With the pytest 3.0 release we introduced a clear communication scheme for when we will actually remove the old busted joint and politely ask you to use the new hotness instead, while giving you enough time to adjust your tests or raise concerns if there are valid reasons to keep deprecated functionality around.

To communicate changes we are already issuing deprecation warnings, but they are not displayed by default. In pytest 3.0 we changed the default setting so that pytest deprecation warnings are displayed if not explicitly silenced (with ``--disable-pytest-warnings``).

We will only remove deprecated functionality in major releases (e.g. if we deprecate something in 3.0 we will remove it in 4.0), and keep it around for at least two minor releases (e.g. if we deprecate something in 3.9 and 4.0 is the next release, we will not remove it in 4.0 but in 5.0).
