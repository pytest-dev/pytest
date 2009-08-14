import py

def pytest_runtest_call(item, __multicall__):
    cap = py.io.StdCapture()
    try:
        return __multicall__.execute()
    finally:
        outerr = cap.reset() 
