import socket

class Messenger:
    SIZE = 32
    def __init__(self, socket):
        self.socket     = socket
        self.recvBuffer = ""

    ## block and return one message of indicated size
    def recvMessage(self):
        while len(self.recvBuffer) < Messenger.SIZE:
            data = self.socket.recv(1024)
            print "data: ", data
            if data == "": return None
            self.recvBuffer += data
        if len(self.recvBuffer) >= Messenger.SIZE:
            m = self.recvBuffer[:Messenger.SIZE]
            self.recvBuffer = self.recvBuffer[Messenger.SIZE:]
            return m.rstrip()

    ## send one message (receiver paced)
    def sendMessage(self, msg):
        assert len(msg) <= Messenger.SIZE
        msg = ("%-" + str(Messenger.SIZE) + "s") % msg
        assert len(msg) == Messenger.SIZE
        totalSent = 0
        while totalSent < Messenger.SIZE:
            sent = self.socket.send(msg[totalSent:])
            print "sent: ", sent
            if sent == 0: return False
            totalSent += sent
        return True

