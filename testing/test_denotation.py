# content of test_sample.py
import pytest


@pytest.mark.test
def mul():
    assert 24 == (4 * 6)


def my_test():
    print("test_answer")
    assert 5 == 5
