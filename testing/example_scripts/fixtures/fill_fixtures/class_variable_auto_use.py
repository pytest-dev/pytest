import pytest


class Test(object):
    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def setup(cls):
        cls.url = "localhost:5000"

    def test_url(self):
        assert self.url == "localhost:5000"
