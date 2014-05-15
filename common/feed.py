import socket
import struct
import threading
from messages import *
from log import log

class Listener:
    def onFeedMessage(rawMessage, seq, drop, message):
        pass

class Feed:
    MCAST_GRP = '224.1.1.1'
    MCAST_PORT = 5007
    MAX_SIZE = 2048

    def __init__(self, send=True, receive=False, thread=False, listeners=None):
        self.sendSocket    = None
        self.receiveSocket = None
        self.sendSeq = 0
        self.receiveSeq = None
        self.listeners = listeners if listeners is not None else []
        for L in self.listeners:
            assert isinstance(L, Listener)

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
            self.thread = threading.Thread(target=self.run, name="Feed")
            self.thread.daemon = True
            self.thread.start()

    def send(self, msg):
        msg = "%08d %s" % (self.sendSeq, msg)
        assert len(msg) < Feed.MAX_SIZE
        log.info(msg)
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

    def run(self):
        while True:
            msg, seq, drop, m = self.recv()

            if   m.startswith("C"): msgs = [   ChessMessage.fromstr(m)                      ]
            elif m.startswith("X"): msgs = [ExchangeMessage.fromstr(m) for m in m.split(";")]
            else:                   msgs = [m]

            for m in msgs:
                for L in self.listeners:
                    L.onFeedMessage(msg, seq, drop, m)
