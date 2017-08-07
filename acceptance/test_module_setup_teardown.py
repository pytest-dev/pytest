def setup_module(module):
    pass


def teardown_module(module):
    print("TD MO")


def test_passing():
    assert True


def test_failing():
    assert False


class TestClassPassing(object):

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass

    def test_passing(self):
        assert True


class TestClassFailing(object):

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        print("TD M")

    def test_failing(self):
        assert False