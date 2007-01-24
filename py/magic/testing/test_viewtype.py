from py.__.magic.viewtype import View

def test_class_dispatch():
    ### Use a custom class hierarchy with existing instances

    class Picklable(View):
        pass

    class Simple(Picklable):
        __view__ = object
        def pickle(self):
            return repr(self.__obj__)

    class Seq(Picklable):
        __view__ = list, tuple, dict
        def pickle(self):
            return ';'.join([Picklable(item).pickle() for item in self.__obj__])

    class Dict(Seq):
        __view__ = dict
        def pickle(self):
            return Seq.pickle(self) + '!' + Seq(self.values()).pickle()

    assert Picklable(123).pickle() == '123'
    assert Picklable([1,[2,3],4]).pickle() == '1;2;3;4'
    assert Picklable({1:2}).pickle() == '1!2'


def test_custom_class_hierarchy():
    ### Use a custom class hierarchy based on attributes of existing instances

    class Operation:
        "Existing class that I don't want to change."
        def __init__(self, opname, *args):
            self.opname = opname
            self.args = args

    existing = [Operation('+', 4, 5),
                Operation('getitem', '', 'join'),
                Operation('setattr', 'x', 'y', 3),
                Operation('-', 12, 1)]

    class PyOp(View):
        def __viewkey__(self):
            return self.opname
        def generate(self):
            return '%s(%s)' % (self.opname, ', '.join(map(repr, self.args)))

    class PyBinaryOp(PyOp):
        __view__ = ('+', '-', '*', '/')
        def generate(self):
            return '%s %s %s' % (self.args[0], self.opname, self.args[1])

    codelines = [PyOp(op).generate() for op in existing]
    assert codelines == ["4 + 5", "getitem('', 'join')", "setattr('x', 'y', 3)", "12 - 1"]
