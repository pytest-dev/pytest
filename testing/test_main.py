from _pytest.main import ExitCode


def test_ExitCode():
    exc_0 = ExitCode(0)
    assert exc_0 == 0
    assert repr(exc_0) == "<ExitCode.OK: 0>"

    exc_99 = ExitCode(99)
    assert exc_99 == 99
    assert repr(exc_99) == "<ExitCode.CUSTOM: 99>"
