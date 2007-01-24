import py
try:
    from py.magic import greenlet
except (ImportError, RuntimeError), e:
    py.test.skip(str(e))


class RGreenletBunch:

    def __init__(self, gateway):
        self.channel = gateway.remote_exec('''
            from py.magic import greenlet
            glob = {"greenlet": greenlet}
            gids = {}
            while True:
                key, code, args = channel.receive()
                if args is not None:
                    if code is not None:
                        def run(code=code):
                            exec code in glob, {}
                        gids[key] = greenlet(run)
                    result = gids[key].switch(*args)
                    channel.send(result)
                else:
                    del gids[key]
        ''')

    def greenlet(self, code):
        return RGreenlet(self, code)


class RGreenlet:

    def __init__(self, bunch, code):
        self.channel = bunch.channel
        self.code    = str(py.code.Source(code))

    def switch(self, *args):
        self.channel.send((id(self), self.code, args))
        self.code = None     # only send over the code the first time
        return self.channel.receive()

    def __del__(self):
        if self.code is None:
            self.channel.send((id(self), None, None))


def test_rgreenlet():
    gw = py.execnet.PopenGateway()
    bunch = RGreenletBunch(gw)
    g = bunch.greenlet('''
        x = greenlet.getcurrent().parent.switch(42)
        y = greenlet.getcurrent().parent.switch(x+1)
        greenlet.getcurrent().parent.switch(y+2)
        import os
        greenlet.getcurrent().parent.switch(os.getpid())
    ''')
    result = g.switch()
    assert result == 42
    result = g.switch(102)
    assert result == 103
    result = g.switch(-93)
    assert result == -91
    import os
    result = g.switch()
    assert result != os.getpid()
