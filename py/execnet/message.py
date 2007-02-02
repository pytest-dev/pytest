import struct
#import marshal

# ___________________________________________________________________________
#
# Messages
# ___________________________________________________________________________
# the header format
HDR_FORMAT = "!hhii"
HDR_SIZE   = struct.calcsize(HDR_FORMAT)

class Message:
    """ encapsulates Messages and their wire protocol. """
    _types = {}
    def __init__(self, channelid=0, data=''):
        self.channelid = channelid
        self.data = data

    def writeto(self, io):
        # XXX marshal.dumps doesn't work for exchanging data across Python
        # version :-(((  There is no sane solution, short of a custom
        # pure Python marshaller
        data = self.data
        if isinstance(data, str):
            dataformat = 1
        else:
            data = repr(self.data)  # argh
            dataformat = 2
        header = struct.pack(HDR_FORMAT, self.msgtype, dataformat,
                                         self.channelid, len(data))
        io.write(header + data)

    def readfrom(cls, io):
        header = io.read(HDR_SIZE)
        (msgtype, dataformat,
         senderid, stringlen) = struct.unpack(HDR_FORMAT, header)
        data = io.read(stringlen)
        if dataformat == 1:
            pass
        elif dataformat == 2:
            data = eval(data, {})   # reversed argh
        else:
            raise ValueError("bad data format")
        msg = cls._types[msgtype](senderid, data)
        return msg
    readfrom = classmethod(readfrom)

    def post_sent(self, gateway, excinfo=None):
        pass

    def __repr__(self):
        r = repr(self.data)
        if len(r) > 50:
            return "<Message.%s channelid=%d len=%d>" %(self.__class__.__name__,
                        self.channelid, len(r))
        else:
            return "<Message.%s channelid=%d %r>" %(self.__class__.__name__,
                        self.channelid, self.data)


def _setupmessages():

    class CHANNEL_OPEN(Message):
        def received(self, gateway):
            channel = gateway._channelfactory.new(self.channelid)
            gateway._local_schedulexec(channel=channel, sourcetask=self.data)

    class CHANNEL_NEW(Message):
        def received(self, gateway):
            """ receive a remotely created new (sub)channel. """
            newid = self.data
            newchannel = gateway._channelfactory.new(newid)
            gateway._channelfactory._local_receive(self.channelid, newchannel)

    class CHANNEL_DATA(Message):
        def received(self, gateway):
            gateway._channelfactory._local_receive(self.channelid, self.data)

    class CHANNEL_CLOSE(Message):
        def received(self, gateway):
            gateway._channelfactory._local_close(self.channelid)

    class CHANNEL_CLOSE_ERROR(Message):
        def received(self, gateway):
            remote_error = gateway._channelfactory.RemoteError(self.data)
            gateway._channelfactory._local_close(self.channelid, remote_error)

    class CHANNEL_LAST_MESSAGE(Message):
        def received(self, gateway):
            gateway._channelfactory._local_last_message(self.channelid)

    classes = [x for x in locals().values() if hasattr(x, '__bases__')]
    classes.sort(lambda x,y : cmp(x.__name__, y.__name__))
    i = 0
    for cls in classes:
        Message._types[i] = cls
        cls.msgtype = i
        setattr(Message, cls.__name__, cls)
        i+=1

_setupmessages()

