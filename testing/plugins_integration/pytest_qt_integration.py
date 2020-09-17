def test_hello_world(qtbot):
    import PyQt5.QtWidgets

    w = PyQt5.QtWidgets.QLabel()
    qtbot.add_widget(w)
