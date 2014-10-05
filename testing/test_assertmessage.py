
def test_assert_message_fail():
    '''
    Check if custom message with % sign do not raise ValueError
    Later test can be parametrized with other problematic chars
    '''

    MESSAGE = 'Message with %'
       
    try:
        assert False, MESSAGE
    except ValueError, ve:
        assert False, 'ValueError was raised with the following message: ' \
            + ve.message
    except AssertionError, ae:
        assert MESSAGE == ae.message, 'Assertion message: ' + ae.message \
            + ' is different than expected: ' + MESSAGE
   