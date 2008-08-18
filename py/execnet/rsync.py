import py, os, stat
from Queue import Queue
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

class RSync(object):
    """ This class allows to send a directory structure (recursively)
        to one or multiple remote filesystems.

        There is limited support for symlinks, which means that symlinks
        pointing to the sourcetree will be send "as is" while external
        symlinks will be just copied (regardless of existance of such
        a path on remote side). 
    """
    def __init__(self, sourcedir, callback=None, verbose=True): 
        self._sourcedir = str(sourcedir)
        self._verbose = verbose 
        assert callback is None or callable(callback)
        self._callback = callback
        self._channels = {}
        self._receivequeue = Queue()
        self._links = []

    def filter(self, path):
        return True

    def _end_of_channel(self, channel):
        if channel in self._channels:
            # too early!  we must have got an error
            channel.waitclose()
            # or else we raise one
            raise IOError('connection unexpectedly closed: %s ' % (
                channel.gateway,))

    def _process_link(self, channel):
        for link in self._links:
            channel.send(link)
            # completion marker, this host is done
        channel.send(42)

    def _done(self, channel):
        """ Call all callbacks
        """
        finishedcallback = self._channels.pop(channel)
        if finishedcallback:
            finishedcallback()

    def _list_done(self, channel):
        # sum up all to send
        if self._callback:
            s = sum([self._paths[i] for i in self._to_send[channel]])
            self._callback("list", s, channel)

    def _send_item(self, channel, data):
        """ Send one item
        """
        modified_rel_path, checksum = data
        modifiedpath = os.path.join(self._sourcedir, *modified_rel_path)
        try:
            f = open(modifiedpath, 'rb')
            data = f.read()
        except IOError:
            data = None

        # provide info to progress callback function
        modified_rel_path = "/".join(modified_rel_path)
        if data is not None:
            self._paths[modified_rel_path] = len(data)
        else:
            self._paths[modified_rel_path] = 0
        if channel not in self._to_send:
            self._to_send[channel] = []
        self._to_send[channel].append(modified_rel_path)

        if data is not None:
            f.close()
            if checksum is not None and checksum == md5.md5(data).digest():
                data = None     # not really modified
            else:
                # ! there is a reason for the interning:
                # sharing multiple copies of the file's data
                data = intern(data)
                self._report_send_file(channel.gateway, modified_rel_path)
        channel.send(data)

    def _report_send_file(self, gateway, modified_rel_path):
        if self._verbose:
            print '%s <= %s' % (gateway.remoteaddress, modified_rel_path)

    def send(self, raises=True):
        """ Sends a sourcedir to all added targets. Flag indicates
        whether to raise an error or return in case of lack of
        targets
        """
        if not self._channels:
            if raises:
                raise IOError("no targets available, maybe you "
                              "are trying call send() twice?")
            return
        # normalize a trailing '/' away
        self._sourcedir = os.path.dirname(os.path.join(self._sourcedir, 'x'))
        # send directory structure and file timestamps/sizes
        self._send_directory_structure(self._sourcedir)

        # paths and to_send are only used for doing
        # progress-related callbacks
        self._paths = {}
        self._to_send = {}

        # send modified file to clients
        while self._channels:
            channel, req = self._receivequeue.get()
            if req is None:
                self._end_of_channel(channel)
            else:
                command, data = req
                if command == "links":
                    self._process_link(channel)
                elif command == "done":
                    self._done(channel)
                elif command == "ack":
                    if self._callback:
                        self._callback("ack", self._paths[data], channel)
                elif command == "list_done":
                    self._list_done(channel)
                elif command == "send":
                    self._send_item(channel, data)
                    del data
                else:
                    assert "Unknown command %s" % command

    def add_target(self, gateway, destdir, 
                   finishedcallback=None, **options):
        """ Adds a remote target specified via a 'gateway'
            and a remote destination directory. 
        """
        assert finishedcallback is None or callable(finishedcallback)
        for name in options:
            assert name in ('delete',)
        def itemcallback(req):
            self._receivequeue.put((channel, req))
        channel = gateway.remote_exec(REMOTE_SOURCE)
        channel.setcallback(itemcallback, endmarker = None)
        channel.send((str(destdir), options))
        self._channels[channel] = finishedcallback

    def _broadcast(self, msg):
        for channel in self._channels:
            channel.send(msg)
    
    def _send_link(self, basename, linkpoint):
        self._links.append(("link", basename, linkpoint))

    def _send_directory(self, path):
        # dir: send a list of entries
        names = []
        subpaths = []
        for name in os.listdir(path):
            p = os.path.join(path, name)
            if self.filter(p):
                names.append(name)
                subpaths.append(p)
        self._broadcast(names)
        for p in subpaths:
            self._send_directory_structure(p)

    def _send_link_structure(self, path):
        linkpoint = os.readlink(path)
        basename = path[len(self._sourcedir) + 1:]
        if not linkpoint.startswith(os.sep):
            # relative link, just send it
            # XXX: do sth with ../ links
            self._send_link(basename, linkpoint)
        elif linkpoint.startswith(self._sourcedir):
            self._send_link(basename, linkpoint[len(self._sourcedir) + 1:])
        else:
            self._send_link(basename, linkpoint)
        self._broadcast(None)

    def _send_directory_structure(self, path):
        try:
            st = os.lstat(path)
        except OSError:
            self._broadcast((0, 0))
            return
        if stat.S_ISREG(st.st_mode):
            # regular file: send a timestamp/size pair
            self._broadcast((st.st_mtime, st.st_size))
        elif stat.S_ISDIR(st.st_mode):
            self._send_directory(path)
        elif stat.S_ISLNK(st.st_mode):
            self._send_link_structure(path)
        else:
            raise ValueError, "cannot sync %r" % (path,)

REMOTE_SOURCE = py.path.local(__file__).dirpath().\
                join('rsync_remote.py').open().read() + "\nf()"

