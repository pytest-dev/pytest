import pytest


@pytest.fixture
def state():
    return {}


@pytest.fixture
def setup_for_foo(state):
    state["setup"] = True


@pytest.fixture
def foo_explicit(setup_for_foo, state):
    return state["setup"] is True


def test_foo_explicit(foo_explicit):
    assert foo_explicit


@pytest.fixture
@pytest.mark.usefixtures("setup_for_foo")
def foo_implicit(state):
    return state["setup"] is True


def test_foo_implicit(foo_implicit):
    assert foo_implicit
