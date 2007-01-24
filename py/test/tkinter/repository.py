import py
Item = py.test.Item
Collector = py.test.collect.Collector

import copy
import time

import UserDict


class Repository(object):
    '''like a trie'''
    nothing = object()

    def __init__(self):   
        self.root = self.newnode()

    def newnode(self):
        return [self.nothing, OrderedDictMemo()]

    def copy(self):
        newrepos = Repository()
        newrepos.root = copy.deepcopy(self.root)
        return newrepos

    def add(self, key, value):
        node = self.root
        for k in key:
            node = node[1].setdefault(k, self.newnode())
        node[0] = value
        
    def find_tuple(self, key=[]):
        node = self.root
        for k in key:
            node = node[1][k]
        return node

    def find(self, key=[]):
        return self.find_tuple(key)[0]

    def haskey(self, key):
        try:
            value = self.find(key)
        except KeyError:
            return False
        return True

    def haskeyandvalue(self, key):
        if self.haskey(key):
            value = self.find(key)
            return value is not self.nothing
        return False
                    
    def find_children(self, key=[]):
        if self.haskey(key):
            node = self.find_tuple(key)
            return [list(key) + [childname] for childname in node[1].keys()]
        return []

    def keys(self, startkey=[]):
        ret = []
        for key in self.find_children(startkey):
            ret.append(key)
            ret.extend(self.keys(key))
        return ret   

    def removestalekeys(self, key):
        if self.find_children(key) == [] and not self.haskeyandvalue(key):
            if len(key) > 0:
                parent = self.find_tuple(key[:-1])
                del parent[1][key[-1]]
                self.removestalekeys(key[:-1])


    def delete(self, key):
        if self.haskeyandvalue(key):
            node = self.find_tuple(key)
            node[0] = self.newnode()[0]
            self.removestalekeys(key)

    def delete_all(self, key):
        if self.haskeyandvalue(key):
            node = self.find_tuple(key)
            node[0], node[1] = self.newnode()[0], self.newnode()[1]
            self.removestalekeys(key)
        
    def values(self, startkey=[]):
        return [self.find(key) for key in self.keys(startkey)]

    def items(self, startkey=[]):
        return [(key, self.find(key)) for key in self.keys(startkey)]


class OrderedDict(UserDict.DictMixin): 
    '''like a normal dict, but keys are ordered by time of setting'''
    def __init__(self, *args, **kwargs):
        self._dict = dict(*args, **kwargs)
        self._keys = self._dict.keys()

    def __getitem__(self, key):
        return self._dict.__getitem__(key)

    def __setitem__(self, key, value):
        self._dict.__setitem__(key, value)
        try:
            self._keys.remove(key)
        except ValueError:
            pass
        self._keys.append(key)
        
    def __delitem__(self, key):
        self._dict.__delitem__(key)
        self._keys.remove(key)

    def keys(self):
        return self._keys[:]

    def copy(self):
        new = OrderedDict()
        for key, value in self.iteritems():
            new[key] = value
        return new

class OrderedDictMemo(UserDict.DictMixin):
    '''memorize all keys and how they were ordered'''
    def __init__(self, *args, **kwargs):
        self._dict = dict(*args, **kwargs)
        self._keys = self._dict.keys()

    def __getitem__(self, key):
        return self._dict.__getitem__(key)

    def __setitem__(self, key, value):
        self._dict.__setitem__(key, value)
        if key not in self._keys:
            self._keys.append(key)
        
    def __delitem__(self, key):
        self._dict.__delitem__(key)
        
    def keys(self):
        return [key for key in self._keys if key in self._dict]

    def copy(self):
        new = OrderedDict()
        for key, value in self.iteritems():
            new[key] = value
        return new






