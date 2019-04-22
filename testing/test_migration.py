"""Test that collection order same for 2.7 and 3.7"""
import pytest
import sys
import os

def main():
    test_input = sys.argv[1]
    cmd = "pytest --collect-only {} > migration_test_out".format(test_input)
    os.system(cmd)
    with open('migration_test_out', 'r') as test_output:
        res = test_output.readlines()
    print(''.join(res))

if __name__ == "__main__":
    main()
