#import os
import struct
from collections import deque


class InvalidPacket(Exception):
    pass


FLAG_NAK1 = 0xE0
FLAG_NAK  = 0xE1
FLAG_REG  = 0xE2
FLAG_CFRM = 0xE3

FLAG_RANGE_START  = 0xE0
FLAG_RANGE_STOP   = 0xE4

max_old_packets = 256      # must be <= 256


class PipeLayer(object):
    timeout = 1
    headersize = 4

    def __init__(self):
        #self.localid = os.urandom(4)
        #self.remoteid = None
        self.cur_time = 0
        self.out_queue = deque()
        self.out_nextseqid = 0
        self.out_nextrepeattime = None
        self.in_nextseqid = 0
        self.in_outoforder = {}
        self.out_oldpackets = deque()
        self.out_flags = FLAG_REG
        self.out_resend = 0
        self.out_resend_skip = False

    def queue(self, data):
        if data:
            self.out_queue.appendleft(data)

    def queue_size(self):
        total = 0
        for data in self.out_queue:
            total += len(data)
        return total

    def in_sync(self):
        return not self.out_queue and self.out_nextrepeattime is None

    def settime(self, curtime):
        self.cur_time = curtime
        if self.out_queue:
            if len(self.out_oldpackets) < max_old_packets:
                return 0   # more data to send now
        if self.out_nextrepeattime is not None:
            return max(0, self.out_nextrepeattime - curtime)
        else:
            return None

    def encode(self, maxlength):
        #print ' '*self._dump_indent, '--- OUTQ', self.out_resend, self.out_queue
        if len(self.out_oldpackets) >= max_old_packets:
            # congestion, stalling
            payload = 0
        else:
            payload = maxlength - 4
            if payload <= 0:
                raise ValueError("encode(): buffer too small")
        if (self.out_nextrepeattime is not None and
            self.out_nextrepeattime <= self.cur_time):
            # no ACK received so far, send a packet (possibly empty)
            if not self.out_queue:
                payload = 0
        else:
            if not self.out_queue:   # no more data to send
                return None
            if payload == 0:         # congestion
                return None
        # prepare a packet
        seqid = self.out_nextseqid
        flags = self.out_flags
        self.out_flags = FLAG_REG     # clear out the flags for the next time
        if payload > 0:
            self.out_nextseqid = (seqid + 1) & 0xFFFF
            data = self.out_queue.pop()
            packetlength = len(data)
            if self.out_resend > 0:
                if packetlength > payload:
                    raise ValueError("XXX need constant buffer size for now")
                self.out_resend -= 1
                if self.out_resend_skip:
                    if self.out_resend > 0:
                        self.out_queue.pop()
                        self.out_resend -= 1
                        self.out_nextseqid = (seqid + 2) & 0xFFFF
                    self.out_resend_skip = False
                packetpayload = data
            else:
                packet = []
                while packetlength <= payload:
                    packet.append(data)
                    if not self.out_queue:
                        break
                    data = self.out_queue.pop()
                    packetlength += len(data)
                else:
                    rest = len(data) + payload - packetlength
                    packet.append(data[:rest])
                    self.out_queue.append(data[rest:])
                packetpayload = ''.join(packet)
                self.out_oldpackets.appendleft(packetpayload)
                #print ' '*self._dump_indent, '--- OLDPK', self.out_oldpackets
        else:
            # a pure ACK packet, no payload
            if self.out_oldpackets and flags == FLAG_REG:
                flags = FLAG_CFRM
            packetpayload = ''
        packet = struct.pack("!BBH", flags,
                             self.in_nextseqid & 0xFF,
                             seqid) + packetpayload
        if self.out_oldpackets:
            self.out_nextrepeattime = self.cur_time + self.timeout
        else:
            self.out_nextrepeattime = None
        #self.dump('OUT', packet)
        return packet

    def decode(self, rawdata):
        if len(rawdata) < 4:
            raise InvalidPacket
        #print ' '*self._dump_indent, '------ out %d (+%d) in %d' % (self.out_nextseqid, self.out_resend, self.in_nextseqid)
        #self.dump('IN ', rawdata)
        in_flags, ack_seqid, in_seqid = struct.unpack("!BBH", rawdata[:4])
        if not (FLAG_RANGE_START <= in_flags < FLAG_RANGE_STOP):
            raise InvalidPacket
        in_diff  = (in_seqid  - self.in_nextseqid ) & 0xFFFF
        ack_diff = (self.out_nextseqid + self.out_resend - ack_seqid) & 0xFF
        if in_diff >= max_old_packets:
            return ''    # invalid, but can occur as a late repetition
        if ack_diff != len(self.out_oldpackets):
            # forget all acknowledged packets
            if ack_diff > len(self.out_oldpackets):
                return ''   # invalid, but can occur with packet reordering
            while len(self.out_oldpackets) > ack_diff:
                #print ' '*self._dump_indent, '--- POP', repr(self.out_oldpackets[-1])
                self.out_oldpackets.pop()
            if self.out_oldpackets:
                self.out_nextrepeattime = self.cur_time + self.timeout
            else:
                self.out_nextrepeattime = None   # all packets ACKed
        if in_flags == FLAG_NAK or in_flags == FLAG_NAK1:
            # this is a NAK: resend the old packets as far as they've not
            # also been ACK'ed in the meantime (can occur with reordering)
            while self.out_resend < len(self.out_oldpackets):
                self.out_queue.append(self.out_oldpackets[self.out_resend])
                self.out_resend += 1
                self.out_nextseqid = (self.out_nextseqid - 1) & 0xFFFF
                #print ' '*self._dump_indent, '--- REP', self.out_nextseqid, repr(self.out_queue[-1])
            self.out_resend_skip = in_flags == FLAG_NAK1
        elif in_flags == FLAG_CFRM:
            # this is a CFRM: request for confirmation
            self.out_nextrepeattime = self.cur_time
        # receive this packet's payload if it is the next in the sequence
        if in_diff == 0:
            if len(rawdata) > 4:
                #print ' '*self._dump_indent, 'RECV ', self.in_nextseqid, repr(rawdata[4:])
                self.in_nextseqid = (self.in_nextseqid + 1) & 0xFFFF
                result = [rawdata[4:]]
                while self.in_nextseqid in self.in_outoforder:
                    result.append(self.in_outoforder.pop(self.in_nextseqid))
                    self.in_nextseqid = (self.in_nextseqid + 1) & 0xFFFF
                return ''.join(result)
        else:
            # we missed at least one intermediate packet: send a NAK
            if len(rawdata) > 4:
                self.in_outoforder[in_seqid] = rawdata[4:]
            if ((self.in_nextseqid + 1) & 0xFFFF) in self.in_outoforder:
                self.out_flags = FLAG_NAK1
            else:
                self.out_flags = FLAG_NAK
            self.out_nextrepeattime = self.cur_time
        return ''

    _dump_indent = 0
    def dump(self, dir, rawdata):
        in_flags, ack_seqid, in_seqid = struct.unpack("!BBH", rawdata[:4])
        print ' ' * self._dump_indent, dir,
        if in_flags == FLAG_NAK:
            print 'NAK',
        elif in_flags == FLAG_NAK1:
            print 'NAK1',
        elif in_flags == FLAG_CFRM:
            print 'CFRM',
        #print ack_seqid, in_seqid, '(%d bytes)' % (len(rawdata)-4,)
        print ack_seqid, in_seqid, repr(rawdata[4:])


def pipe_over_udp(udpsock, send_fd=-1, recv_fd=-1,
                  timeout=1.0, inactivity_timeout=None):
    """Example: send all data showing up in send_fd over the given UDP
    socket, and write incoming data into recv_fd.  The send_fd and
    recv_fd are plain file descriptors.  When an EOF is read from
    send_fd, this function returns (after making sure that all data was
    received by the remote side).
    """
    import os
    from select import select
    from time import time
    p = PipeLayer()
    p.timeout = timeout
    iwtdlist = [udpsock]
    if send_fd >= 0:
        iwtdlist.append(send_fd)
    running = True
    while running or not p.in_sync():
        delay = delay1 = p.settime(time())
        if delay is None:
            delay = inactivity_timeout
        iwtd, owtd, ewtd = select(iwtdlist, [], [], delay)
        if iwtd:
            if send_fd in iwtd:
                data = os.read(send_fd, 1500 - p.headersize)
                if not data:
                    # EOF
                    iwtdlist.remove(send_fd)
                    running = False
                else:
                    #print 'queue', len(data)
                    p.queue(data)
            if udpsock in iwtd:
                packet = udpsock.recv(65535)
                #print 'decode', len(packet)
                p.settime(time())
                data = p.decode(packet)
                i = 0
                while i < len(data):
                    i += os.write(recv_fd, data[i:])
        elif delay1 is None:
            break    # long inactivity
        p.settime(time())
        packet = p.encode(1500)
        if packet:
            #print 'send', len(packet)
            #if os.urandom(1) >= '\x08':    # emulate packet losses
            udpsock.send(packet)


class PipeOverUdp(object):

    def __init__(self, udpsock, timeout=1.0):
        import thread, os
        self.os = os
        self.sendpipe = os.pipe()
        self.recvpipe = os.pipe()
        thread.start_new_thread(pipe_over_udp, (udpsock,
                                                self.sendpipe[0],
                                                self.recvpipe[1],
                                                timeout))

    def __del__(self):
        os = self.os
        if self.sendpipe:
            os.close(self.sendpipe[0])
            os.close(self.sendpipe[1])
            self.sendpipe = None
        if self.recvpipe:
            os.close(self.recvpipe[0])
            os.close(self.recvpipe[1])
            self.recvpipe = None

    close = __del__

    def send(self, data):
        if not self.sendpipe:
            raise IOError("I/O operation on a closed PipeOverUdp")
        return self.os.write(self.sendpipe[1], data)

    def sendall(self, data):
        i = 0
        while i < len(data):
            i += self.send(data[i:])

    def recv(self, bufsize):
        if not self.recvpipe:
            raise IOError("I/O operation on a closed PipeOverUdp")
        return self.os.read(self.recvpipe[0], bufsize)

    def recvall(self, bufsize):
        buf = []
        while bufsize > 0:
            data = self.recv(bufsize)
            buf.append(data)
            bufsize -= len(data)
        return ''.join(buf)

    def fileno(self):
        if not self.recvpipe:
            raise IOError("I/O operation on a closed PipeOverUdp")
        return self.recvpipe[0]

    def ofileno(self):
        if not self.sendpipe:
            raise IOError("I/O operation on a closed PipeOverUdp")
        return self.sendpipe[1]
