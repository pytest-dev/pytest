from __future__ import annotations

import sys
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import SubRequest


def test_dummy_test_with_traceback(
    request: SubRequest, capteesys: CaptureFixture[str]
) -> None:
    print("Hello world stdout", flush=True)
    print("Hello world stderr", file=sys.stderr, flush=True)
