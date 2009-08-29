import sys

fn = sys.argv[1]
print("Testing %s" % (fn,))
fp = open(fn, "rb")
try:
    source = fp.read()
finally:
    fp.close()
compile(source, fn, "exec")
