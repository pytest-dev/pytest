import pytest


@pytest.fixture
def first(request):
    def factory():
        print("SETUP instance")
        request.addfinalizer(lambda: print("TEARDOWN instance"))

    print("SETUP first")
    yield factory
    print("TEARDOWN first")


@pytest.fixture
def second(request):
    print("SETUP second")
    yield 1
    print("TEARDOWN second")


def test_order(request, first, second):
    print("SETUP test")
    request.addfinalizer(lambda: print("TEARDOWN test"))
    first()
