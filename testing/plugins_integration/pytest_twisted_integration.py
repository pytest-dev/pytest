import pytest_twisted
import twisted.internet.task


def sleep(seconds):
    import twisted.internet.reactor

    return twisted.internet.task.deferLater(
        clock=twisted.internet.reactor,
        delay=0,
    )


@pytest_twisted.inlineCallbacks
def test_inlineCallbacks():
    yield sleep(0)


@pytest_twisted.ensureDeferred
async def test_inlineCallbacks():
    await sleep(0)
