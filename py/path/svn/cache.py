"""
# generic cache mechanism for subversion-related structures
# XXX make mt-safe
"""

import time

proplist = {}
info = {}
entries = {}
prop = {}

#-----------------------------------------------------------
# Caching latest repository revision and repo-paths
# (getting them is slow with the current implementations)
#
# XXX make mt-safe
#-----------------------------------------------------------

class RepoEntry:
    def __init__(self, url, rev, timestamp):
        self.url = url
        self.rev = rev
        self.timestamp = timestamp

    def __str__(self):
        return "repo: %s;%s  %s" %(self.url, self.rev, self.timestamp)

class RepoCache:
    """ The Repocache manages discovered repository paths
    and their revisions.  If inside a timeout the cache
    will even return the revision of the root.
    """
    timeout = 20 # seconds after which we forget that we know the last revision

    def __init__(self):
        self.repos = []

    def clear(self):
        self.repos = []

    def put(self, url, rev, timestamp=None):
        if rev is None:
            return
        if timestamp is None:
            timestamp = time.time()

        for entry in self.repos:
            if url == entry.url:
                entry.timestamp = timestamp
                entry.rev = rev
                #print "set repo", entry
                break
        else:
            entry = RepoEntry(url, rev, timestamp)
            self.repos.append(entry)
            #print "appended repo", entry

    def get(self, url):
        now = time.time()
        for entry in self.repos:
            if url.startswith(entry.url):
                if now < entry.timestamp + self.timeout:
                    #print "returning immediate Etrny", entry
                    return entry.url, entry.rev
                return entry.url, -1
        return url, -1

repositories = RepoCache()
