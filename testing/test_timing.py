import _pytest.timing as Timing


def test_store() -> None:
    start_time = Timing.time()
    Timing.sleep(0.5)
    Timing.StopTimer()

    try:
        Timing.StopTimer()
    except Exception as e:
        print("!! Error:", e)
        assert True
    else:
        assert False

    Timing.sleep(1)
    Timing.StartTimer()
    Timing.sleep(0.5)
    assert int(Timing.time()) == int(start_time + 1)

    try:
        Timing.StartTimer()
    except Exception as e:
        print("!! Error:", e)
        assert True
    else:
        assert False

    # Reset the timer for other tests to start from clean
    Timing._paused_for = 0
