# encoding: utf-8

import pytest
import doctest

class MyDocTestRunner(doctest.DocTestRunner):

    def __init__(self):
        doctest.DocTestRunner.__init__(self)

    def report_failure(self, out, test, example, got):
        raise AssertionError("'{}' evaluates to '{}', not '{}'".format(
            example.source.strip(), got.strip(), example.want.strip()))


class TestApprox:

    def test_approx_doctests(self):
        parser = doctest.DocTestParser()
        test = parser.get_doctest(
                pytest.approx.__doc__,
                {'approx': pytest.approx},
                pytest.approx.__name__,
                None, None,
        )
        runner = MyDocTestRunner()
        runner.run(test)

    def test_repr_string(self):
        # Just make sure the Unicode handling doesn't raise any exceptions.
        print(pytest.approx(1.0))
        print(pytest.approx([1.0, 2.0, 3.0]))

