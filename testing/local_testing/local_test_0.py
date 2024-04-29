import pytest


@pytest.mark.parametrize("arg1, arg2", [(1, 1)])
def test_parametrization(arg1: int, arg2: int) -> None:
    assert arg1 == arg2
    assert arg1 + 1 == arg2 + 1


# Gets the error: In test_parametrization: indirect fixture '(1, 1)' doesn't exist
# Goal is to change this message into a more beginner friendly message.

# The error message lives in this path: pytest/src/_pytest/python.py


# ("arg1", "arg2"), and "arg1, arg2" works, but cannot put in default parameters as normal function
