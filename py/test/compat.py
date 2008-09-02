import py

from py.test.collect import Function

class TestCaseUnit(Function):
    """ compatibility Unit executor for TestCase methods
        honouring setUp and tearDown semantics.
    """
    def runtest(self, _deprecated=None):
        boundmethod = self.obj 
        instance = boundmethod.im_self 
        instance.setUp()
        try:
            boundmethod()
        finally:
            instance.tearDown()

class TestCase(object):
    """compatibility class of unittest's TestCase. """
    Function = TestCaseUnit

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def fail(self, msg=None):
        """ fail immediate with given message. """
        py.test.fail(msg)

    def assertRaises(self, excclass, func, *args, **kwargs):
        py.test.raises(excclass, func, *args, **kwargs)
    failUnlessRaises = assertRaises

    # dynamically construct (redundant) methods
    aliasmap = [
        ('x',   'not x', 'assert_, failUnless'),
        ('x',   'x',     'failIf'),
        ('x,y', 'x!=y',  'failUnlessEqual,assertEqual, assertEquals'),
        ('x,y', 'x==y',  'failIfEqual,assertNotEqual, assertNotEquals'),
        ]
    items = []
    for sig, expr, names in aliasmap:
        names = map(str.strip, names.split(','))
        sigsubst = expr.replace('y', '%s').replace('x', '%s')
        for name in names:
            items.append("""
                def %(name)s(self, %(sig)s, msg=""):
                    __tracebackhide__ = True
                    if %(expr)s:
                        py.test.fail(msg=msg + (%(sigsubst)r %% (%(sig)s)))
            """ % locals() )

    source = "".join(items)
    exec py.code.Source(source).compile()

__all__ = ['TestCase']
