"""
    Working with multiple channels and gateways

"""
import py
from py.__.execnet.channel import RemoteError

NO_ENDMARKER_WANTED = object()

class MultiGateway:
    RemoteError = RemoteError
    def __init__(self, gateways):
        self.gateways = gateways
    def remote_exec(self, source):
        channels = []
        for gw in self.gateways:
            channels.append(gw.remote_exec(source))
        return MultiChannel(channels)
    def exit(self):
        for gw in self.gateways:
            gw.exit()

class MultiChannel:
    def __init__(self, channels):
        self._channels = channels

    def send_each(self, item):
        for ch in self._channels:
            ch.send(item)

    def receive_each(self, withchannel=False):
        assert not hasattr(self, '_queue')
        l = []
        for ch in self._channels:
            obj = ch.receive()
            if withchannel:
                l.append((ch, obj))
            else:
                l.append(obj)
        return l 

    def make_receive_queue(self, endmarker=NO_ENDMARKER_WANTED):
        try:
            return self._queue
        except AttributeError:
            self._queue = py.std.Queue.Queue()
            for ch in self._channels:
                def putreceived(obj, channel=ch):
                    self._queue.put((channel, obj))
                if endmarker is NO_ENDMARKER_WANTED:
                    ch.setcallback(putreceived)
                else:
                    ch.setcallback(putreceived, endmarker=endmarker)
            return self._queue


    def waitclose(self):
        first = None
        for ch in self._channels:
            try:
                ch.waitclose()
            except ch.RemoteError:
                if first is None:
                    first = py.std.sys.exc_info()
        if first:
            raise first[0], first[1], first[2]


