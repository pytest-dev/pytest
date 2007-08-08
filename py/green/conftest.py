import py, os

if os.name == 'nt':
    py.test.skip("Cannot test green layer on windows")
