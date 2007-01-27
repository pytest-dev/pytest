
import os, sys

if __name__ == '__main__':
    directory = os.path.dirname(os.path.abspath(sys.argv[0]))
    script = os.path.join(directory, 'socketserver.py')
    while 1:
        cmd = "python %s %s" % (script, " ".join(sys.argv[1:]))
        print "starting subcommand:", cmd
        f = os.popen(cmd)
        for line in f:
            print line,
