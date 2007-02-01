
def f():
    import os, stat, shutil, md5
    destdir, options = channel.receive() 
    modifiedfiles = []

    def remove(path):
        assert path.startswith(destdir)
        try:
            os.unlink(path)
        except OSError:
            # assume it's a dir
            shutil.rmtree(path)

    def receive_directory_structure(path, relcomponents):
        try:
            st = os.lstat(path)
        except OSError:
            st = None
        msg = channel.receive()
        if isinstance(msg, list):
            if st and not stat.S_ISDIR(st.st_mode):
                os.unlink(path)
                st = None
            if not st:
                os.makedirs(path)
            entrynames = {}
            for entryname in msg:
                receive_directory_structure(os.path.join(path, entryname),
                    relcomponents + [entryname])
                entrynames[entryname] = True
            if options.get('delete'): 
                for othername in os.listdir(path):
                    if othername not in entrynames:
                        otherpath = os.path.join(path, othername)
                        remove(otherpath)
        elif msg is not None:
            checksum = None
            if st:
                if stat.S_ISREG(st.st_mode):
                    msg_mtime, msg_size = msg
                    if msg_size != st.st_size:
                        pass
                    elif msg_mtime != st.st_mtime:
                        f = open(path, 'rb')
                        checksum = md5.md5(f.read()).digest()
                        f.close()
                    else:
                        return    # already fine
                else:
                    remove(path)
            channel.send(("send", (relcomponents, checksum)))
            modifiedfiles.append((path, msg))
    receive_directory_structure(destdir, [])

    STRICT_CHECK = False    # seems most useful this way for py.test
    channel.send(("list_done", None))

    for path, (time, size) in modifiedfiles:
        data = channel.receive()
        channel.send(("ack", path[len(destdir) + 1:]))
        if data is not None:
            if STRICT_CHECK and len(data) != size:
                raise IOError('file modified during rsync: %r' % (path,))
            f = open(path, 'wb')
            f.write(data)
            f.close()
        try:
            os.utime(path, (time, time))
        except OSError:
            pass
        del data
    channel.send(("links", None))

    msg = channel.receive()
    while msg is not 42:
        # we get symlink
        _type, relpath, linkpoint = msg
        assert _type == "link"
        path = os.path.join(destdir, relpath)
        try:
            remove(path)
        except OSError:
            pass

        os.symlink(os.path.join(destdir, linkpoint), path)
        msg = channel.receive()
    channel.send(("done", None))

