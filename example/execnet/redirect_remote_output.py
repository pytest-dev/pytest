"""
redirect output from remote to a local function 
showcasing features of the channel object:

- sending a channel over a channel 
- adapting a channel to a file object 
- setting a callback for receiving channel data 

"""

import py

gw = execnet.PopenGateway()

outchan = gw.remote_exec("""
    import sys
    outchan = channel.gateway.newchannel()
    sys.stdout = outchan.makefile("w")
    channel.send(outchan) 
""").receive()

# note: callbacks execute in receiver thread! 
def write(data):
    print "received:", repr(data)
outchan.setcallback(write)

gw.remote_exec("""
    print 'hello world'
    print 'remote execution ends'
""").waitclose()

