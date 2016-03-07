import pytest
import doctest

class MyDocTestRunner(doctest.DocTestRunner):

    def __init__(self):
        doctest.DocTestRunner.__init__(self)

    def report_failure(self, out, test, example, got):
        raise AssertionError("'{}' evaluates to '{}', not '{}'".format(
            example.source.strip(), got.strip(), example.want.strip()))


class TestApprox:

    def test_approx(self):
        parser = doctest.DocTestParser()
        test = parser.get_doctest(
                pytest.approx.__doc__,
                {'approx': pytest.approx},
                pytest.approx.__name__,
                None, None,
        )
        runner = MyDocTestRunner()
        runner.run(test)


