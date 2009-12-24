import os, sys, subprocess, urllib

BUILDNAME=os.environ.get('BUILD_NUMBER', "1")
BIN=os.path.abspath(os.path.join(BUILDNAME, 'bin'))
PYTHON=os.path.join(BIN, 'python')

def call(*args):
    ret = subprocess.call(list(args))
    assert ret == 0

def bincall(*args):
    args = list(args)
    args[0] = os.path.join(BIN, args[0])
    call(*args)

call("virtualenv", os.path.abspath(BUILDNAME), '--no-site-packages')
bincall("python", "setup.py", "develop", "-q")
bincall("pip", "install", "-r", "testing/pip-reqs1.txt", 
               "-q", "--download-cache=download")
bincall("py.test", "--ignore", BUILDNAME, 
        "-p", "xmlresult", "--xmlresult=junit.xml", 
        "--report=skipped", "--runslowtest", *sys.argv[1:])
