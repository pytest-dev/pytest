import sys
sys.path.insert(0, '/root/.openclaw/workspace-fork/pytest-work/src')

from _pytest.python import IdMaker

class CustomDict:
    def __init__(self, data):
        self._data = data
    def __getattr__(self, item):
        return self._data[item]

val = CustomDict({"a": 1})
result = IdMaker([], [], None, None, None, None)._idval(val, "a", 6)
assert result == "a6", f"Expected 'a6', got {result!r}"
print("Test passed!")
