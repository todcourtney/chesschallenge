import socket

class Feed:
    MCAST_GRP = '224.1.1.1'
    MCAST_PORT = 5007
    MAX_SIZE = 2048

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        self.seq = 0

    def send(self, msg):
        msg = "%08d %s" % (self.seq, msg)
        assert len(msg) < Feed.MAX_SIZE
        self.seq += 1
        self.socket.sendto(msg, (Feed.MCAST_GRP, Feed.MCAST_PORT))

