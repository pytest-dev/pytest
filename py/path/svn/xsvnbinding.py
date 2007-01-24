"""

module defining subversion path objects.

SvnBindingPath    implementation using svn-swig-py-bindings

"""
# import svn swig-c-bindings

if 0:
    #import svn.client, svn.core, svn.util, atexit
    #svn.util.apr_initialize()
    #atexit.register(svn.util.apr_terminate)

    #import os, sys, time, re
    #from common import *
    #from svncommon import _cache, _repocache, SvnPathBase

    class SvnBindingPath(SvnPathBase):
        pool = svn.util.svn_pool_create(None)

        def _make_rev_t(self):
            rev = svn.core.svn_opt_revision_t()
            if self.rev is not None:
                rev.kind = svn.core.svn_opt_revision_number
                rev.value.number = self.rev
            return rev

        def _make_cctx(self):
            cctx = svn.client.svn_client_ctx_t()
            provider = svn.client.svn_client_get_simple_provider(self.pool)
            cctx.auth_baton = svn.util.svn_auth_open([provider], self.pool)
            return cctx

        def open(self, mode='r'):
            assert 'w' not in mode and 'a' not in mode
            assert self.exists()   # svn cat returns an empty file otherwise
            return os.popen("svn cat -r %s '%s'" % (self.rev, self.strpath))
            # XXX we don't know how to make our own stream
            #from svn import client, util, core
            #url = self.strpath
            #rev = self._make_rev_t()
            #cctx = self._make_cctx()
            #stream = core.svn_stream_create(None, self.pool)
            #client.svn_client_cat(stream, url, rev, cctx, self.pool)
            #return stream.get_value()

        def _propget(self, name):
            url = self.strpath
            rev = self._make_rev_t()
            cctx = self._make_cctx()

            table = svn.client.svn_client_propget(name, url, rev, 0, cctx, self.pool)
            return str(table.values()[0])

        def _proplist(self):
            url = self.strpath
            rev = self._make_rev_t()
            cctx = self._make_cctx()
            table = svn.client.svn_client_proplist(url, rev, 0, cctx, self.pool)

            if not table:
                return {}
            content = table[0][1]
            for name, value in content.items():
                content[name] = str(value)
            return content

        def exists(self):
            try:
                self.proplist()
            except RuntimeError, e:
                if e.args[0].lower().find('unknown node')!=-1:
                    return 0
                raise
            return 1

        def _listdir_nameinfo(self):
            """ return a tuple of paths on 'self' as a directory """
            url = self.strpath
            rev = self._make_rev_t()
            cctx = self._make_cctx()
            try:
                dic = svn.client.svn_client_ls(url, rev, 0, cctx, self.pool)
            except RuntimeError, e:
                raise IOError(e.args)

            nameinfo_seq = map(lambda x: (x[0], InfoSvnBinding(x[1])), dic.items())
            return nameinfo_seq

    class InfoSvnBinding:
        def __init__(self, _info):
            self.size = _info.size
            self.time = _info.time
            self.last_author = _info.last_author
            self.created_rev = _info.created_rev
            self.has_props = _info.has_props

            if _info.kind == svn.core.svn_node_dir:
                self.kind = 'dir'
            elif _info.kind == svn.core.svn_node_file:
                self.kind = 'file'
            else:
                raise ValueError, "unknown kind of svn object"

            self.mtime = self.time / 1000000
        def __eq__(self, other):
            return self.__dict__ == other.__dict__

    SvnPath = SvnBindingPath
