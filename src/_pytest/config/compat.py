from __future__ import annotations

from pathlib import Path

from ..compat import LEGACY_PATH


def _check_path(path: Path, fspath: LEGACY_PATH) -> None:
    if Path(fspath) != path:
        raise ValueError(
            f"Path({fspath!r}) != {path!r}\n"
            "if both path and fspath are given they need to be equal"
        )
