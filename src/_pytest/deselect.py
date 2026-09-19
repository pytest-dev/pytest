"""Recording of the reason why items were deselected.

The reason is *side-channeled* through the config stash for the duration of a
:hook:`pytest_deselected` call instead of being passed to the hook as an
argument.

That is a workaround, not a design: the natural spelling is
``pytest_deselected(items, reason)``.  It is not available because
``pytest_deselected`` is a hook third party plugins *call* -- calling it from a
``pytest_collection_modifyitems`` implementation is part of the documented
contract -- and pluggy cannot yet evolve the arguments of a hook *call*.
Adding ``reason`` to the hookspec would leave every existing caller passing no
reason, and a caller that cannot pass one is indistinguishable from a caller
that has nothing to say, so the argument could never become required either.

Consequently nothing here is public: pytest records reasons for its own
deselections and reads them back in its own reporting.  A plugin can neither
supply a reason nor read one, and items a plugin deselects are reported without
one.  Making the channel public is pointless while the underlying hook cannot
carry the value; see https://github.com/pytest-dev/pytest/issues/15036 and
https://github.com/pytest-dev/pluggy/issues/170 before building on it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from _pytest.stash import StashKey


if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.nodes import Item


#: Set only while a ``pytest_deselected`` call started by :func:`deselect_items`
#: is in progress.
deselection_reason_key = StashKey[str]()


def deselect_items(config: Config, items: Sequence[Item], reason: str) -> None:
    """Call :hook:`pytest_deselected` for *items*, recording *reason*.

    *reason* is phrased as the answer to "why is this item not selected?", e.g.
    ``"-m 'slow' did not match"``.
    """
    with config.stash.replaced(deselection_reason_key, reason):
        config.hook.pytest_deselected(items=items)


def get_deselection_reason(config: Config) -> str | None:
    """The reason for the ``pytest_deselected`` call currently in progress.

    ``None`` when the caller did not record one, which is the case for every
    caller outside of pytest itself.
    """
    return config.stash.get(deselection_reason_key, None)
