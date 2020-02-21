from typing import Any
from typing import cast
from typing import Dict
from typing import Generic
from typing import TypeVar
from typing import Union


__all__ = ["Store", "StoreToken"]


T = TypeVar("T")
D = TypeVar("D")


class StoreToken(Generic[T]):
    """StoreToken is an object used as a key to a Store.

    A token is associated with the type T of the value of the key.

    A token is unique and cannot conflict with another token.
    """

    __slots__ = ()

    @classmethod
    def mint(self) -> "StoreToken[T]":
        """Create a new token."""
        return StoreToken()


class Store:
    """Store is a type-safe heterogenous mutable mapping that
    allows keys and value types to be defined separately from
    where it is defined.

    Usually you will be given an object which has a ``Store``:

    .. code-block:: python

        store: Store = some_object.store

    If a module wants to store data in this Store, it mints tokens
    for its keys (at the module level):

    .. code-block:: python

        some_str_token = StoreToken[str].mint()
        some_bool_token = StoreToken[bool].mint()

    To store information:

    .. code-block:: python

        # Value type must match the token.
        store[some_str_token] = "value"
        store[some_bool_token] = True

    To retrieve the information:

    .. code-block:: python

        # The static type of some_str is str.
        some_str = store[some_str_token]
        # The static type of some_bool is bool.
        some_bool = store[some_bool_token]

    Why use this?
    -------------

    Problem: module Internal defines an object. Module External, which
    module Internal doesn't know about, receives the object and wants to
    attach information to it, to be retrieved later given the object.

    Bad solution 1: Module External assigns private attributes directly on
    the object. This doesn't work well because the type checker doesn't
    know about these attributes and it complains about undefined attributes.

    Bad solution 2: module Internal adds a ``Dict[str, Any]`` attribute to
    the object. Module External stores its data in private keys of this dict.
    This doesn't work well because retrieved values are untyped.

    Good solution: module Internal adds a ``Store`` to the object. Module
    External mints Tokens for its own keys. Module External stores and
    retrieves its data using its tokens.
    """

    __slots__ = ("_store",)

    def __init__(self) -> None:
        self._store = {}  # type: Dict[StoreToken[Any], object]

    def __setitem__(self, token: StoreToken[T], value: T) -> None:
        """Set a value for token."""
        self._store[token] = value

    def __getitem__(self, token: StoreToken[T]) -> T:
        """Get the value for token.

        Raises KeyError if the token wasn't set before.
        """
        return cast(T, self._store[token])

    def get(self, token: StoreToken[T], default: D) -> Union[T, D]:
        """Get the value for token, or return a default if the
        token wasn't set before."""
        try:
            return self[token]
        except KeyError:
            return default

    def __delitem__(self, token: StoreToken[T]) -> None:
        """Delete the value for token.

        Raises KeyError if the token wasn't set before.
        """
        del self._store[token]

    def __contains__(self, token: StoreToken[T]) -> bool:
        """Returns whether token was set."""
        return token in self._store
