from __future__ import annotations


for i in range(1000):
    exec("def test_func_%d(): pass" % i)
