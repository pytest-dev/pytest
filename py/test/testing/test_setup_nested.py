
#
# test correct setup/teardowns at
# module, class, and instance level

modlevel = []
def setup_module(module):
    assert not modlevel
    module.modlevel.append(42)

def teardown_module(module):
    modlevel.pop()

def setup_function(function):
    function.answer = 17

def teardown_function(function):
    del function.answer

def test_modlevel():
    assert modlevel[0] == 42
    assert test_modlevel.answer == 17

class TestSimpleClassSetup:
    clslevel = []
    def setup_class(cls):
        cls.clslevel.append(23)

    def teardown_class(cls):
        cls.clslevel.pop()

    def test_classlevel(self):
        assert self.clslevel[0] == 23

    def test_modulelevel(self):
        print modlevel
        assert modlevel == [42]

class TestInheritedClassSetupStillWorks(TestSimpleClassSetup):
    def test_classlevel_anothertime(self):
        assert self.clslevel == [23]

class TestSetupTeardownOnInstance(TestSimpleClassSetup):
    def setup_method(self, method):
        self.clslevel.append(method.__name__)

    def teardown_method(self, method):
        x = self.clslevel.pop()
        assert x == method.__name__

    def test_setup(self):
        assert self.clslevel[-1] == 'test_setup'

    def test_generate(self):
        assert self.clslevel[-1] == 'test_generate'
        yield self.generated, 5
        assert self.clslevel[-1] == 'test_generate'

    def generated(self, value):
        assert value == 5
        assert self.clslevel[-1] == 'test_generate'

def test_teardown_method_worked(): 
    assert not TestSetupTeardownOnInstance.clslevel 
