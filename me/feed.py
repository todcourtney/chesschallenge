import socket
import struct

class Feed:
    MCAST_GRP = '224.1.1.1'
    MCAST_PORT = 5007
    MAX_SIZE = 2048

    def __init__(self, send=True, receive=False, thread=False):
        self.sendSocket    = None
        self.receiveSocket = None
        self.sendSeq = 0
        self.receiveSeq = None

        if send:
            self.sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.sendSocket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        if receive:
            self.receiveSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.receiveSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.receiveSocket.bind(('', Feed.MCAST_PORT))
            mreq = struct.pack("4sl", socket.inet_aton(Feed.MCAST_GRP), socket.INADDR_ANY)
            self.receiveSocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        if thread:
            raise NotImplementedError("need to add threading")

    def send(self, msg):
        msg = "%08d %s" % (self.sendSeq, msg)
        assert len(msg) < Feed.MAX_SIZE
        self.sendSeq += 1
        self.sendSocket.sendto(msg, (Feed.MCAST_GRP, Feed.MCAST_PORT))

    def recv(self):
        msg = self.receiveSocket.recv(Feed.MAX_SIZE)

        ## check for drops
        seq, m = msg.split(" ", 1)
        seq = int(seq)
        drop = self.receiveSeq is not None and (seq > self.receiveSeq+1)
        self.receiveSeq = seq

        return msg, seq, drop, m
