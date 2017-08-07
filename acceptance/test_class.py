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
        pass

    def test_failing(self):
        assert False


class TestClassError(object):

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass

    def test_error(self):
        1/0


class TestClassFailingAndErrorTeardown(object):

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        1/0

    def test_error(self):
        assert False


class TestClassErrorSetup(object):

    def setup_method(self, method):
        1/0

    def teardown_method(self, method):
        pass

    def test_passing(self):
        assert True


class TestClassErrorSetupAndTeardown(object):

    def setup_method(self, method):
        1/0

    def teardown_method(self, method):
        1/0

    def test_passing(self):
        assert True


class TestClassErrorTeardown(object):

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        1/0

    def test_passing(self):
        assert True
