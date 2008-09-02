from pygreen.pipe.common import BufferedInput


class MeetingPointInput(BufferedInput):

    def __init__(self, accepter):
        self.accepter = accepter

    def wait_input(self):
        while not self.in_buf:
            self.in_buf = self.accepter.accept()

    def shutdown_rd(self):
        self.accepter.close()


class MeetingPointOutput(BufferedInput):

    def __init__(self, giver):
        self.giver = giver

    def wait_output(self):
        self.giver.wait()

    def sendall(self, buffer):
        self.giver.give(buffer)

    def shutdown_wr(self):
        self.giver.close()
