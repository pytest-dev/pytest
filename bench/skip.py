from six.moves import range
import pytest


SKIP = True


@pytest.mark.parameterize("x", range(5000))
def test_foo(x):
    if SKIP:
        pytest.skip("heh")
