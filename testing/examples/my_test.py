def test_():
    m = [
        "This is some dummy test which shows the strange way in which Pycharm"
        " displays the full diff."
    ]
    assert m == []


def test2_():
    m = [
        "This is another check"
        " This line and the line above should be fine"
        " Same with this line"
        " But we should not see the '- ,' appear"
        " But rather we should see a '- []' appear"
    ]
    assert m == []


def test3_():
    m = ["This is some dummy test which shows the strange way in which Pycharm"]
    assert m == []
