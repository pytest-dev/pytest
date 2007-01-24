import sys
import os

def setup_module(mod=None):
    if mod is None:
        f = __file__
    else:
        f = mod.__file__
    sys.path.append(os.path.dirname(os.path.dirname(f)))

def teardown_module(mod=None):
    if mod is None:
        f = __file__
    else:
        f = mod.__file__
    sys.path.remove(os.path.dirname(os.path.dirname(f)))

def test_import():
    global shared_lib, module_that_imports_shared_lib
    import shared_lib
    from package import shared_lib as shared_lib2
    import module_that_imports_shared_lib
    import absolute_import_shared_lib
    all_modules = [
        ('shared_lib', shared_lib),
        ('shared_lib2', shared_lib2),
        ('module_that_imports_shared_lib',
         module_that_imports_shared_lib.shared_lib),
        ('absolute_import_shared_lib',
         absolute_import_shared_lib.shared_lib),
        ]
    bad_matches = []
    while all_modules:
        name1, mod1 = all_modules[0]
        all_modules = all_modules[1:]
        for name2, mod2 in all_modules:
            if mod1 is not mod2:
                bad_matches.append((name1, mod1, name2, mod2))
    for name1, mod1, name2, mod2 in bad_matches:
        print "These modules should be identical:"
        print "  %s:" % name1
        print "   ", mod1
        print "  %s:" % name2
        print "   ", mod2
        print
    if bad_matches:
        assert False

if __name__ == "__main__":
    setup_module()
    test_import
    teardown_module()
