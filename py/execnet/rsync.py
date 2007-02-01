import py, os, stat, md5
from Queue import Queue


class RSync(object):
    """ This is an example usage of py.execnet - a sample RSync
    protocol, which can perform syncing 1-to-n.

    Sample usage: you instantiate this class, eventually providing a
    callback when rsyncing is done, than add some targets
    (gateway + destdir) by running add_target and finally
    invoking send() which will send provided source tree remotely.

    There is limited support for symlinks, which means that symlinks
    pointing to the sourcetree will be send "as is" while external
    symlinks will be just copied (regardless of existance of such
    a path on remote side)
    """
    def __init__(self, callback=None, **options):
        for name in options:
            assert name in ('delete')
        self.options = options
        self.callback = callback
        self.channels = {}
        self.receivequeue = Queue()
        self.links = []

    def filter(self, path):
        return True

    def add_target(self, gateway, destdir, finishedcallback=None):
        """ Adds a target for to-be-send data
        """
        def itemcallback(req):
            self.receivequeue.put((channel, req))
        channel = gateway.remote_exec(REMOTE_SOURCE)
        channel.setcallback(itemcallback, endmarker = None)
        channel.send((str(destdir), self.options))
        self.channels[channel] = finishedcallback

    def send(self, sourcedir):
        """ Sends a sourcedir to previously prepared targets
        """
        self.sourcedir = str(sourcedir)
        # normalize a trailing '/' away
        self.sourcedir = os.path.dirname(os.path.join(self.sourcedir, 'x'))
        # send directory structure and file timestamps/sizes
        self._send_directory_structure(self.sourcedir)

        # paths and to_send are only used for doing
        # progress-related callbacks
        self.paths = {}
        self.to_send = {}

        # send modified file to clients
        while self.channels:
            channel, req = self.receivequeue.get()
            if req is None:
                # end-of-channel
                if channel in self.channels:
                    # too early!  we must have got an error
                    channel.waitclose()
                    # or else we raise one
                    raise IOError('connection unexpectedly closed: %s ' % (
                        channel.gateway,))
            else:
                command, data = req
                if command == "links":
                    for link in self.links:
                        channel.send(link)
                    # completion marker, this host is done
                    channel.send(42)
                elif command == "done":
                    finishedcallback = self.channels.pop(channel)
                    if finishedcallback:
                        finishedcallback()
                elif command == "ack":
                    if self.callback:
                        self.callback("ack", self.paths[data], channel)
                elif command == "list_done":
                    # sum up all to send
                    if self.callback:
                        s = sum([self.paths[i] for i in self.to_send[channel]])
                        self.callback("list", s, channel)
                elif command == "send":
                    modified_rel_path, checksum = data
                    modifiedpath = os.path.join(self.sourcedir, *modified_rel_path)
                    try:
                        f = open(modifiedpath, 'rb')
                        data = f.read()
                    except IOError:
                        data = None

                    # provide info to progress callback function
                    modified_rel_path = "/".join(modified_rel_path)
                    if data is not None:
                        self.paths[modified_rel_path] = len(data)
                    else:
                        self.paths[modified_rel_path] = 0
                    if channel not in self.to_send:
                        self.to_send[channel] = []
                    self.to_send[channel].append(modified_rel_path)

                    if data is not None:
                        f.close()
                        if checksum is not None and checksum == md5.md5(data).digest():
                            data = None     # not really modified
                        else:
                            # ! there is a reason for the interning:
                            # sharing multiple copies of the file's data
                            data = intern(data)
                            print '%s <= %s' % (
                                channel.gateway.remoteaddress, 
                                modified_rel_path)
                    channel.send(data)
                    del data
                else:
                    assert "Unknown command %s" % command

    def _broadcast(self, msg):
        for channel in self.channels:
            channel.send(msg)
    
    def _send_link(self, basename, linkpoint):
        self.links.append(("link", basename, linkpoint))

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
        elif stat.S_ISLNK(st.st_mode):
            linkpoint = os.readlink(path)
            basename = path[len(self.sourcedir) + 1:]
            if not linkpoint.startswith(os.sep):
                # relative link, just send it
                # XXX: do sth with ../ links
                self._send_link(basename, linkpoint)
            elif linkpoint.startswith(self.sourcedir):
                self._send_link(basename, linkpoint[len(self.sourcedir) + 1:])
            else:
                self._send_link(basename, linkpoint)
            self._broadcast(None)
        else:
            raise ValueError, "cannot sync %r" % (path,)

REMOTE_SOURCE = py.path.local(__file__).dirpath().\
                join('rsync_remote.py').open().read() + "\nf()"

