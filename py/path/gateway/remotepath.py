import py, itertools
from py.__.path import common

COUNTER = itertools.count()

class RemotePath(common.FSPathBase):
    sep = '/'

    def __init__(self, channel, id, basename=None):
        self._channel = channel
        self._id = id
        self._basename = basename
        self._specs = {}

    def __del__(self):
        self._channel.send(('DEL', self._id))

    def __repr__(self):
        return 'RemotePath(%s)' % self.basename

    def listdir(self, *args):
        self._channel.send(('LIST', self._id) + args)
        return [RemotePath(self._channel, id, basename)
                for (id, basename) in self._channel.receive()]

    def dirpath(self):
        id = ~COUNTER.next()
        self._channel.send(('DIRPATH', self._id, id))
        return RemotePath(self._channel, id)

    def join(self, *args):
        id = ~COUNTER.next()
        self._channel.send(('JOIN', self._id, id) + args)
        return RemotePath(self._channel, id)

    def _getbyspec(self, spec):
        parts = spec.split(',')
        ask = [x for x in parts  if x not in self._specs]
        if ask:
            self._channel.send(('GET', self._id, ",".join(ask)))
            for part, value in zip(ask, self._channel.receive()):
                self._specs[part] = value
        return [self._specs[x] for x in parts]

    def read(self):
        self._channel.send(('READ', self._id))
        return self._channel.receive()
