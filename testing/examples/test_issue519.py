from _pytest.pytester import Pytester


def test_510(pytester: Pytester) -> None:
    pytester.copy_example("issue_519.py")
    pytester.runpytest("issue_519.py")
