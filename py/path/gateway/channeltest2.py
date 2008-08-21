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
gw.remote_init_threads(5)
c = gw.remote_exec(SRC, stdout=py.std.sys.stdout, stderr=py.std.sys.stderr)
subchannel = gw._channelfactory.new()
c.send(subchannel)

p = RemotePath(subchannel, c.receive())
