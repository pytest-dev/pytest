
def test_answer(mysetup): 
    app = mysetup.myapp()
    answer = app.question()
    assert answer == 42

