"""
example

reading results from possibly blocking code running in sub processes. 
"""
import py

NUM_PROCESSES = 5

channels = []
for i in range(NUM_PROCESSES):
    gw = execnet.PopenGateway() # or use SSH or socket gateways 
    channel = gw.remote_exec("""
        import time
        secs = channel.receive()
        time.sleep(secs)
        channel.send("waited %d secs" % secs)
    """)
    channels.append(channel)
    print "*** instantiated subprocess", gw

mc = execnet.MultiChannel(channels)
queue = mc.make_receive_queue()

print "***", "verifying that timeout on receiving results from blocked subprocesses works"
try:
    queue.get(timeout=1.0) 
except Exception:
    pass

print "*** sending subprocesses some data to have them unblock"
mc.send_each(1) 

print "*** receiving results asynchronously"
for i in range(NUM_PROCESSES):
    channel, result = queue.get(timeout=2.0)
    print "result", channel.gateway, result
