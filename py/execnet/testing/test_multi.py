""" 
    tests for 
    - multi channels and multi gateways 

"""

import py

class TestMultiChannelAndGateway:
    def test_multichannel_receive_each(self):
        class pseudochannel:
            def receive(self):
                return 12

        pc1 = pseudochannel()
        pc2 = pseudochannel()
        multichannel = py.execnet.MultiChannel([pc1, pc2])
        l = multichannel.receive_each(withchannel=True)
        assert len(l) == 2
        assert l == [(pc1, 12), (pc2, 12)]
        l = multichannel.receive_each(withchannel=False)
        assert l == [12,12]

    def test_multichannel_send_each(self):
        l = [py.execnet.PopenGateway() for x in range(2)]
        gm = py.execnet.MultiGateway(l)
        mc = gm.remote_exec("""
            import os
            channel.send(channel.receive() + 1)
        """)
        mc.send_each(41)
        l = mc.receive_each() 
        assert l == [42,42]
       
    def test_multichannel_receive_queue_for_two_subprocesses(self):
        l = [py.execnet.PopenGateway() for x in range(2)]
        gm = py.execnet.MultiGateway(l)
        mc = gm.remote_exec("""
            import os
            channel.send(os.getpid())
        """)
        queue = mc.make_receive_queue()
        ch, item = queue.get(timeout=10)
        ch2, item2 = queue.get(timeout=10)
        assert ch != ch2
        assert ch.gateway != ch2.gateway
        assert item != item2
        mc.waitclose()

    def test_multichannel_waitclose(self):
        l = []
        class pseudochannel:
            def waitclose(self):
                l.append(0)
        multichannel = py.execnet.MultiChannel([pseudochannel(), pseudochannel()])
        multichannel.waitclose()
        assert len(l) == 2

