import sys

def main(fn):
    print("Testing %s" % (fn,))
    fp = open(fn, "rb")
    try:
        source = fp.read()
    finally:
        fp.close()
    compile(source, fn, "exec")

if __name__ == "__main__":
    main(sys.argv[1])
