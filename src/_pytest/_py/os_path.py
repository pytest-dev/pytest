import os
from types import ModuleType
from typing import Optional


def module_casesensitivepath(module: ModuleType) -> Optional[str]:
    """Return the canonical __file__ of the module without resolving symlinks."""
    path = module.__file__
    if path is None:
        return None
    return casesensitivepath(path)


def casesensitivepath(path: str) -> str:
    """Return the case-sensitive version of the path."""
    resolved_path = os.path.realpath(path)
    if resolved_path.lower() == path.lower():
        return resolved_path
    # Patch has one or more symlinks. Todo: find the correct path casing.
    return path
