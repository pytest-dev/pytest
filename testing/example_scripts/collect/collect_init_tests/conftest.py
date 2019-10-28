from typing import Set
from typing import Tuple

collected_already = set()  # type: Set[Tuple]


def pytest_collect_file(path, parent):
    # Ensure that the hook is only called once per path.
    key = (path, parent)
    assert key not in collected_already, key
    collected_already.add(key)
