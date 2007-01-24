
from py.__.test.tkinter.repository import Repository, OrderedDict, OrderedDictMemo
import py
Item = py.test.Item


import itertools       


class TestRepository:

    def setup_method(self, method):
        self.rep = Repository()

    def test_add_find_single_value(self):
        key = ['key']
        value = 'value'
        self.rep.add(key, value)
        assert self.rep.find(key) == value

    def test_add_works_like_update(self):
        key = 'k e y'.split()
        value = 'value'
        value2 = 'value2'
        self.rep.add(key, value)
        self.rep.add(key, value2)
        assert self.rep.find(key) == value2

    def test_haskeyandvalue(self):
        key = 'first_middle_last'
        value = 'value'
        self.rep.add(key, value)
        assert self.rep.haskeyandvalue(key)
        assert not self.rep.haskeyandvalue('first')
        for index in range(1, len(key[0])):
            assert not self.rep.haskeyandvalue(key[0:index])
        
    def test_add_find_subkey(self):
        key = ('key', 'subkey')
        value = 'subvalue'
        self.rep.add(key, value)
        self.rep.add((key[0],), 'value')
        assert self.rep.find(key) == value

    def test_find_raises_KeyError(self):
        py.test.raises(KeyError, self.rep.find, 'nothing')

    def test_haskey(self):
        self.rep.add('key', 'value')
        assert self.rep.haskey('key') ==  True
        assert self.rep.haskey('katja') == False
        assert self.rep.haskey('ke') == True

    def test_find_children_empyt_repository(self):
        assert self.rep.find_children() == []

    def test_find_children(self):
        self.rep.add(['c'], 'childvalue')
        self.rep.add('c a'.split(), 'a')
        self.rep.add('c b'.split(), 'b')
        assert self.rep.find_children(['c']) == [ ['c','a'], ['c','b']]
        assert self.rep.find_children() == [['c']]

    def test_find_children_with_tuple_key(self):
        key = tuple('k e y'.split())
        value = 'value'
        self.rep.add(key, value)
        assert self.rep.find_children([]) == [['k']]
        assert self.rep.find_children(('k', 'e')) == [['k', 'e', 'y']]

    def test_keys(self):
        keys = [ 'a b c'.split(), 'a b'.split(), ['a']]
        for key in keys:
            self.rep.add(key, 'value')
        assert len(keys) == len(self.rep.keys())
        for key in self.rep.keys():
            assert key in keys
        for key in keys:
            assert key in self.rep.keys()

    def test_delete_simple(self):
        key = 'k'
        value = 'value'
        self.rep.add(key, value)
        self.rep.delete(key)
        assert self.rep.haskeyandvalue(key) == False


    def test_removestallkeys_remove_all(self):
        key = 'k e y'.split()
        value = 'value'
        self.rep.add(key, value)
        node = self.rep.find_tuple(key)
        node[0] = self.rep.newnode()[0]
        self.rep.removestalekeys(key)
        assert self.rep.keys() == []
        
    def test_removestallkeys_dont_remove_parent(self):
        key = 'k e y'.split()
        key2 = 'k e y 2'.split()
        value = 'value'
        self.rep.add(key, value)
        self.rep.add(key2, self.rep.newnode()[0])
        self.rep.removestalekeys(key2)
        assert self.rep.haskey(key2) == False
        assert self.rep.haskeyandvalue(key)

    def test_removestallkeys_works_with_parameter_root(self):
        self.rep.removestalekeys([])
        
    def test_copy(self):
        key = 'k e y'.split()
        key2 = 'k e y 2'.split()
        value = 'value'
        self.rep.add(key, value)
        self.rep.add(key2, value)
        newrep = self.rep.copy()
        assert newrep.root is not self.rep.root
        assert newrep.find(key) == self.rep.find(key)
        


class TestOrderedDict:

    def setup_method(self, method):
        self.dict = OrderedDict()

    def test_add(self):
        self.dict['key'] = 'value'
        assert 'key' in self.dict

    def test_order(self):
        keys = range(3)
        for k in keys:
            self.dict[k] = str(k)
        assert keys == self.dict.keys()

class TestOrderedDictMemo(TestOrderedDict):

    def setup_method(self, method):
        self.dict = OrderedDictMemo()

    def test_insert(self):
        self.dict['key1'] = 1
        self.dict['key2'] = 2
        del self.dict['key1']
        self.dict['key1'] = 1
        assert self.dict.keys() == ['key1', 'key2']
        
        

    
