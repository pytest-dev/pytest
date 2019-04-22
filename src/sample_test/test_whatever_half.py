import unittest
import whatever

''' 
Low Quality Test Case
None of the single test cases will trigger else branch 
--> is it possible to produce a mutant that will expose incorrect sorting?
--> maybe instead of replacing function call, replace function args?
--> for assignment operators, maybe we can try assiging it a fixed value?
    e.g. assign it to 14 or something?
'''

class TestHalf(unittest.TestCase):
    def test_single1(self):
        x, y, z = [1], [10], [10]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z, result)

    def test_single2(self):
        x, y, z = [2], [20], [40]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z, result)

    def test_single3(self):
        x, y, z = [3], [30], [90]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z, result)
        
    def test_single4(self):
        x, y, z = [4], [40], [160]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z, result)

    def test_single5(self):
        x, y, z = [5], [6], [30]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z, result)

    def test_single6(self):
        x, y, z = [2], [10], [20]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z, result)

    def test_single7(self):
        x, y, z = [3], [10], [30]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z, result)
        
    def test_single8(self):
        x, y, z = [4], [10], [40]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z, result)





















