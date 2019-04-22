import unittest
import whatever

''' High Quality Test Case '''

class TestFull(unittest.TestCase):
    def test_single1(self):
        x, y, z = [1],[2],[2]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z, result)
    
    def test_single2(self):
        x, y, z = [2],[1],[4]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z,result)

    def test_single3(self):
        x, y, z = [],[],[]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z,result)

    def test_single4(self):
        x, y, z = [1],[1],[4]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z,result)

    def test_single5(self):
        x, y, z = [0], [0], [3]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z,result)

    def test_double1(self):
        x, y, z = [1,100], [130,50], [50, 13000]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z,result)

    def test_double2(self):
        x, y, z = [130,50], [1,100], [4, 103]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z,result)
    
    def test_tripple1(self):
        x, y, z = [30,15,1], [5,10,20], [5,13,23]
        result = whatever.whatever_ok(x,y)
        self.assertEqual(z,result)

