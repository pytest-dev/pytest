import sys


def test_stdout():
    print("STDOUT")


def test_stderr():
    sys.stderr.write("STDERR\n")


class TestClassStdout(object):

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass

    def test_stdout(self):
        print("STDOUT")


class TestClassStdoutSetup(object):

    def setup_method(self, method):
        print("SETUP")

    def teardown_method(self, method):
        pass

    def test_stdout(self):
        pass


class TestClassStdoutAllPhases(object):

    def setup_method(self, method):
        print("SETUP")

    def teardown_method(self, method):
        print("TEARDOWN")

    def test_stdout(self):
        print("TEST")


class TestClassFailing(object):

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass

    def test_stderr(self):
        sys.stderr.write("STDERR\n")
