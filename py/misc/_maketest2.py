""" create a py/test2 hierarchy copied from py/test. 
    useful for refactoring py.test itself and still 
    use py.test itself. 
"""

from _findpy import py

def change_init(initfile):
    l = []
    for line in initfile.readlines():
        newline = line 
        l.append(line) 
        newline = newline.replace("'test.", "'test2.") 
        newline = newline.replace("'./test/", "'./test2/")
        if newline != line: 
            l.append(newline) 
    initfile.write("".join(l))

def perform_replace(directory):
    for x in directory.visit("*.py", 
                             rec=lambda x: x.check(dir=1, dotfile=0)):
        s = n = x.read()
        n = n.replace("py.test", "py.test2")
        n = n.replace("py.__.test.", "py.__.test2.")
        n = n.replace("py.__.test ", "py.__.test2 ")
        if s != n:
            print "writing modified", x
            x.write(n) 

def cmd(command):
    print "* executing:", command
    return py.process.cmdexec(command) 

if __name__ == '__main__':
    basedir = py.path.local(py.__file__).dirpath()
    #st = py.path.svnwc(basedir).status() 
    #assert not st.modified
    olddir = basedir.chdir()
    try:
        initfile = basedir.join("__init__.py")
        cmd("svn revert %s" % initfile)
        change_init(initfile) 

        test2dir = basedir.join("test2")
        cmd("svn revert -R test2") 
        cmd("rm -rf test2") 
        cmd("svn cp test test2") 
        perform_replace(test2dir)

    finally:
        olddir.chdir()
    
    
