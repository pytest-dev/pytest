from typing import Any
from typing import Callable
from typing import List
from typing import Tuple


class Callback:
    def __init__(self) -> None:
        self._funcs: List[Tuple[Callable[..., Any], Any, Any]] = []

    def register(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self._funcs.append((func, args, kwargs))

    def execute(self) -> None:
        for func, args, kwargs in reversed(self._funcs):
            func(*args, **kwargs)
