"""
Simple script that actually executes py.test runner when passed "--pytest" as
first argument; in this case, all other arguments are forwarded to pytest's
main().
"""

if __name__ == '__main__':
    import sys
    import pytest
    sys.exit(pytest.main())