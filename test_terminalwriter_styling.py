from typing import Any
import pytest
import warnings

@pytest.fixture()
def test_terminal_formatter_styling_one():
    # Check assert with message
    assert 1 + 1 == 2 
    assert 2 + 2 == 5, "This assertion has a failure message"
    
@pytest.fixture()
def test_terminal_formatter_styling_two():
    # Check fail with message
    pytest.fail("Test fails with pytest.fail()")  
    
@pytest.fixture()
def test_terminal_formatter_styling_three():  
    # Check xfail with message  
    pytest.xfail("Test is expected to fail with pytest.xfail()")  
    
@pytest.fixture()
def test_terminal_formatter_styling_four(): 
    # Check skip with message   
    pytest.skip("Test skipped with pytest.skip()") 

@pytest.fixture()
def test_terminal_formatter_styling_five():
    # Check raise with message
    with pytest.raises(ValueError, match="Custom error message"):
        raise ValueError("Custom error message")

@pytest.fixture()
def test_terminal_formatter_styling_six():
    # Check warning with message
    with pytest.warns(UserWarning, match="Custom warning message"):
        warnings.warn("Custom warning message", UserWarning)

@pytest.fixture()
def test_terminal_formatter_styling_seven():
    @pytest.mark.custom_mark
    def test_custom_mark():
        pass

    # Check for the custom mark
    config = pytest.config
    if hasattr(config, 'getini'):
        config.getini("markers")  

    # Check ouput with message
    captured_output = "This should be captured"
    with pytest.raises(AssertionError, match=captured_output):
        assert captured_output == "This should not be captured"

@pytest.fixture
def test_terminal_formatter_styling_eight():
    # Check printing of function
    @pytest.mark.parametrize("input, expected", [("input1", "expected1"), ("input2", "expected2")])
    def test_parameterized(input, expected):
        assert input == expected

    # Guarantee fail and output
    assert False, "This test should fail for styling demonstration purposes"

# Call all tests
def test_one(test_terminal_formatter_styling_one):
    ...

def test_two(test_terminal_formatter_styling_two):
    ...

def test_three(test_terminal_formatter_styling_three):
    ...

def test_four(test_terminal_formatter_styling_four):
    ...

def test_five(test_terminal_formatter_styling_five):
    ...

def test_six(test_terminal_formatter_styling_six):
    ...

def test_seven(test_terminal_formatter_styling_seven):
    ...

def test_eight(test_terminal_formatter_styling_eight):
    ...
    