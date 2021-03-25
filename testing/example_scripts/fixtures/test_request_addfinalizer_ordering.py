import pytest


@pytest.fixture
def first(request):
    def factory():
        print("SETUP (4) instance")
        request.addfinalizer(lambda: print("TEARDOWN (4) instance"))

    print("SETUP (1) first")
    yield factory
    print("TEARDOWN (1) first")


@pytest.fixture
def second(request):
    print("SETUP (2) second")
    yield 1
    print("TEARDOWN (2) second")


def test_order(request, first, second):
    print("SETUP (3) test")
    request.addfinalizer(lambda: print("TEARDOWN (3) test"))
    first()
