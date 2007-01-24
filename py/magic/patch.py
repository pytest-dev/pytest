
patched = {}

def patch(namespace, name, value):
    """ rebind the 'name' on the 'namespace'  to the 'value',
        possibly and remember the original value. Multiple
        invocations to the same namespace/name pair will
        remember a list of old values.
    """
    nref = (namespace, name)
    orig = getattr(namespace, name)
    patched.setdefault(nref, []).append(orig)
    setattr(namespace, name, value)
    return orig

def revert(namespace, name):
    """ revert to the orginal value the last patch modified.
        Raise ValueError if no such original value exists.
    """
    nref = (namespace, name)
    if nref not in patched or not patched[nref]:
        raise ValueError, "No original value stored for %s.%s" % nref
    current = getattr(namespace, name)
    orig = patched[nref].pop()
    setattr(namespace, name, orig)
    return current
