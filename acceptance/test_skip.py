import pytest

@pytest.mark.skip(reason="Skip")
def test_skip_function():
    pass


class TestSkipCall(object):

    @pytest.mark.skip(reason="Skip")
    def test_skip_method(self):
        pass


@pytest.mark.skip(reason="Skip")
class TestSkipClass(object):

    def test_skipped_1(self):
        pass

    def test_skipped_2(self):
        pass
