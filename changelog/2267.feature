Replace the old introspection code in compat.py that determines the
available arguments of fixtures with inspect.signature on Python 3 and
funcsigs.signature on Python 2.  This should respect __signature__
declarations on functions.
