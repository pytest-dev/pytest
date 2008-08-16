
import py

class ChangeItem:
    def __init__(self, repo, revision, line):
        self.repo = py.path.local(repo)
        self.revision = int(revision)
        self.action = action = line[:4]
        self.path = line[4:].strip()
        self.added = action[0] == "A"
        self.modified = action[0] == "M"
        self.propchanged = action[1] == "U"
        self.deleted = action[0] == "D"

    def svnurl(self):
        return py.path.svnurl("file://%s/%s" %(self.repo, self.path), self.revision)

    def __repr__(self):
        return "<ChangeItem %r>" %(self.action + self.path)

def changed(repo, revision):
    out = py.process.cmdexec("svnlook changed -r %s %s" %(revision, repo))
    l = []
    for line in out.strip().split('\n'):
        l.append(ChangeItem(repo, revision, line))
    return l

def author(repo, revision):         
    out = py.process.cmdexec("svnlook author -r %s %s" %(revision, repo))
    return out.strip()

def youngest(repo): 
    out = py.process.cmdexec("svnlook youngest %s" %(repo,))
    return int(out) 
