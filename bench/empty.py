import six

for i in range(1000):
    six.exec_("def test_func_%d(): pass" % i)
