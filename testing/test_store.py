import pytest
from _pytest.store import Store
from _pytest.store import StoreToken


def test_store() -> None:
    store = Store()

    token1 = StoreToken[str].mint()
    token2 = StoreToken[int].mint()

    # Basic functionality - single token.
    assert token1 not in store
    store[token1] = "hello"
    assert token1 in store
    assert store[token1] == "hello"
    assert store.get(token1, None) == "hello"
    store[token1] = "world"
    assert store[token1] == "world"
    # Has correct type (no mypy error).
    store[token1] + "string"

    # No interaction with another token.
    assert token2 not in store
    assert store.get(token2, None) is None
    with pytest.raises(KeyError):
        store[token2]
    with pytest.raises(KeyError):
        del store[token2]
    store[token2] = 1
    assert store[token2] == 1
    # Has correct type (no mypy error).
    store[token2] + 20
    del store[token1]
    with pytest.raises(KeyError):
        del store[token1]
    with pytest.raises(KeyError):
        store[token1]

    # Can't accidentally add attributes to store object itself.
    with pytest.raises(AttributeError):
        store.foo = "nope"  # type: ignore[attr-defined] # noqa: F821

    # No interaction with anoter store.
    store2 = Store()
    token3 = StoreToken[int].mint()
    assert token2 not in store2
    store2[token2] = 100
    store2[token3] = 200
    assert store2[token2] + store2[token3] == 300
    assert store[token2] == 1
    assert token3 not in store
