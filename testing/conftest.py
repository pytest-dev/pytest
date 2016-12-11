import sys

collect_ignore = []
if sys.version_info[0] < 3:
    collect_ignore.append("test_compat_3.py")
if sys.version_info < (3, 5):
    collect_ignore.append("test_compat_35.py")
