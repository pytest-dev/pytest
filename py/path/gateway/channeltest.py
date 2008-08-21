import threading


class PathServer:

    def __init__(self, channel):
        self.channel = channel
        self.C2P = {}
        self.next_id = 0
        threading.Thread(target=self.serve).start()

    def p2c(self, path):
        id = self.next_id
        self.next_id += 1
        self.C2P[id] = path
        return id

    def command_LIST(self, id, *args):
        path = self.C2P[id]
        answer = [(self.p2c(p), p.basename) for p in path.listdir(*args)]
        self.channel.send(answer)

    def command_DEL(self, id):
        del self.C2P[id]

    def command_GET(self, id, spec):
        path = self.C2P[id]
        self.channel.send(path._getbyspec(spec))

    def command_READ(self, id):
        path = self.C2P[id]
        self.channel.send(path.read())

    def command_JOIN(self, id, resultid, *args):
        path = self.C2P[id]
        assert resultid not in self.C2P
        self.C2P[resultid] = path.join(*args)

    def command_DIRPATH(self, id, resultid):
        path = self.C2P[id]
        assert resultid not in self.C2P
        self.C2P[resultid] = path.dirpath()

    def serve(self):
        try:
            while 1:
                msg = self.channel.receive()
                meth = getattr(self, 'command_' + msg[0])
                meth(*msg[1:])
        except EOFError:
            pass

if __name__ == '__main__':
    import py
    gw = py.execnet.PopenGateway()
    channel = gw._channelfactory.new()
    srv = PathServer(channel)
    c = gw.remote_exec("""
        import remotepath
        p = remotepath.RemotePath(channel.receive(), channel.receive())
        channel.send(len(p.listdir()))
    """)
    c.send(channel)
    c.send(srv.p2c(py.path.local('/tmp')))
    print c.receive()
