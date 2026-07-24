from __future__ import annotations

from collections.abc import Collection
from collections.abc import Iterator
from collections.abc import Mapping
import heapq
import pprint

from _pytest._io.pprint import _safe_key
from _pytest._io.saferepr import saferepr
from _pytest.assertion._typing import _HighlightFunc


def _compare_eq_mapping(
    left: Mapping[object, object],
    right: Mapping[object, object],
    highlighter: _HighlightFunc,
    verbose: int = 0,
    extra_items_max_lines: int | None = None,
) -> Iterator[str]:
    set_left = set(left)
    set_right = set(right)
    common = set_left.intersection(set_right)
    same = {k: left[k] for k in common if left[k] == right[k]}
    if same and verbose < 2:
        yield f"Omitting {len(same)} identical items, use -vv to show"
    elif same:
        yield "Common items:"
        yield from highlighter(pprint.pformat(same)).splitlines()
    diff = {k for k in common if left[k] != right[k]}
    if diff:
        yield "Differing items:"
        for k in diff:
            yield (
                highlighter(saferepr({k: left[k]}))
                + " != "
                + highlighter(saferepr({k: right[k]}))
            )
    extra_left = set_left - set_right
    len_extra_left = len(extra_left)
    if len_extra_left:
        yield f"Left contains {len_extra_left} more item{'' if len_extra_left == 1 else 's'}:"
        yield from _format_extra_items(
            left, extra_left, highlighter, extra_items_max_lines
        )
    extra_right = set_right - set_left
    len_extra_right = len(extra_right)
    if len_extra_right:
        yield f"Right contains {len_extra_right} more item{'' if len_extra_right == 1 else 's'}:"
        yield from _format_extra_items(
            right, extra_right, highlighter, extra_items_max_lines
        )


def _format_extra_items(
    mapping: Mapping[object, object],
    keys: Collection[object],
    highlighter: _HighlightFunc,
    max_lines: int | None,
) -> Iterator[str]:
    """Render the "X contains N more items" subdict."""
    if max_lines is None or len(keys) <= max_lines:
        # If no need to truncate, let pprint handle it.
        yield from highlighter(
            pprint.pformat({k: mapping[k] for k in keys})
        ).splitlines()
    else:
        # To avoid spending effort on formatting entries that would be truncated,
        # only format the needed entries, keeping the sorting that pprint would use.
        for k in heapq.nsmallest(max_lines, keys, key=_safe_key):
            yield highlighter(saferepr({k: mapping[k]}))
