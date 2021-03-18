from typing import TYPE_CHECKING

from _pytest.nodes import _imply_path

if TYPE_CHECKING:
    from ..compat import LEGACY_PATH


import functools

# hookname: (Path, LEGACY_PATH)
imply_paths_hooks = {
    "pytest_ignore_collect": ("fspath", "path"),
    "pytest_collect_file": ("fspath", "path"),
    "pytest_pycollect_makemodule": ("fspath", "path"),
    "pytest_report_header": ("startpath", "startdir"),
    "pytest_report_collectionfinish": ("startpath", "startdir"),
}


class PathAwareHookProxy:
    def __init__(self, hook_caller):
        self.__hook_caller = hook_caller

    def __getattr__(self, key):
        if key not in imply_paths_hooks:
            return getattr(self.__hook_caller, key)
        else:
            hook = getattr(self.__hook_caller, key)
            path_var, fspath_var = imply_paths_hooks[key]

            @functools.wraps(hook)
            def fixed_hook(**kw):
                path_value = kw.pop(path_var, None)
                fspath_value: "LEGACY_PATH" = kw.pop(fspath_var, None)
                path_value, fspath_value = _imply_path(path_value, fspath_value)
                kw[path_var] = path_value
                kw[fspath_var] = fspath_value
                return hook(**kw)

            return fixed_hook
