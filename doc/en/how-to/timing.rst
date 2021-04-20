.. _timing:


How to control the test time
===============================================================



Use case
------------

This feature can be very handy when you want to exclude parts of your test(s)
in the total time count at the end of all the tests.


Usage
------------

Suppose we have the following tests:

.. code-block:: python

    import pytests
    from time import sleep as MainCalculation
    from time import sleep as Bootstrap
    from time import sleep as Cleanup


    @pytest.mark.parametrize("i", range(5))
    def test_num(i):
        Bootstrap(i * 2)
        res = MainCalculation(i)
        Cleanup(i // 2)

        assert res == True

If we wanted to measure, or at least look after, the performance of our test(s),
it'd be pretty complex.

So now there is the ability to do so by using :func:`pytest.StartTimer` & :func:`pytest.StopTimer`.

Here's how the previous code will look like after the modification:

.. code-block:: python

    import pytest
    from time import sleep as MainCalculation
    from time import sleep as Bootstrap
    from time import sleep as Cleanup


    @pytest.mark.parametrize("i", range(5))
    def test_num(i):
        # Stoping the timer before the bootstrap step.
        pytest.StopTimer()
        Bootstrap(i * 2)
        # Starting (or if yo be precise continuing) the timer as we do our main step.
        pytest.StartTimer()
        res = MainCalculation(i)
        # Stoping the timer before the cleanup step.
        pytest.StopTimer()
        Cleanup(i // 2)
        # "Strating" the timer back (to live), otherwise it'll be "frozen" from the last stop.
        pytest.StartTimer()

        assert res == True

Now we got a slightly longer code, but hey, we added functionality and nevertheless it's now
fully customizable, time-wise :)
