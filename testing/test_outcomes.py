from _pytest.outcomes import OutcomeException


def test_OutcomeException():
    assert repr(OutcomeException()) == "<OutcomeException msg=None>"
    assert repr(OutcomeException(msg="msg")) == "<OutcomeException msg='msg'>"
    assert repr(OutcomeException(msg="msg\nline2")) == "<OutcomeException msg='msg...'>"
    assert (
        repr(OutcomeException(short_msg="short"))
        == "<OutcomeException short_msg='short'>"
    )
