import py
from remotepath import RemotePath


SRC = open('channeltest.py', 'r').read()

SRC += '''
import py
srv = PathServer(channel.receive())
channel.send(srv.p2c(py.path.local("/tmp")))
'''


#gw = py.execnet.SshGateway('codespeak.net')
gw = py.execnet.PopenGateway()
c = gw.remote_exec(SRC)
subchannel = gw.channelfactory.new()
c.send(subchannel)

p = RemotePath(subchannel, c.receive())
