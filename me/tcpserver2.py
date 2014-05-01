import socket
import threading
import select
import time

## send fixed-size messages
class Messenger:
    SIZE = 3
    def __init__(self, socket):
        self.socket = socket
        self.recvBuffer = ""
        self.sendBuffer = ""

    ## may block if socket is not already known to have data
    def recvMessage(self):
        assert len(self.recvBuffer) < SIZE
        part = self.socket.recv(SIZE-len(self.recvBuffer))
        if part == "": raise RuntimeError("connection broken")
        self.recvBuffer += part
        assert len(self.recvBuffer) <= SIZE
        if len(self.recvBuffer) == SIZE:
            m = self.recvBuffer
            self.recvBuffer = ""
            return m
        return None

    def sendMessage(self, msg):
        totalSent = 0
        while totalSent < SIZE:
            part = self.socket.send(msg[totalSent:])
            if part == 0:
                raise RuntimeError("connection broken")
            totalSent += part

class MessengerPool:
    def __init__(self):
        self.lock = threading.Lock()
        self.messengers = dict()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('localhost', 9999))
        self.socket.listen(3)

    def acceptConnections(self):
        while True:
            print "accept", self.socket
            (clientsocket, address) = self.socket.accept()
            print clientsocket, address
            clientsocket.setblocking(0)
            with self.lock:
                self.messengers[clientsocket] = Messenger(clientsocket)
            time.sleep(1)

    def messengers(self):
        with self.lock:
            m = [m for m in self.messengers.values()]
        return m

    def close(self, s):
        with self.lock:
            s.close()
            del self.messengers[s]

if __name__ == "__main__":
    pool = MessengerPool()

    t = threading.Thread(target=pool.acceptConnections)
    t.daemon = True
    t.start()

    i = 0
    while True:
        messengers = pool.messengers()
        if len(messengers):
            sockets = [m.socket for m in messengers]
            print "%04d select from %d sockets" % (i, len(sockets))
            r, w, e = select.select(sockets, sockets, sockets)
            print "  read"
            for s in r:
                print "    ", s
                m = s.recv(3)
                if m == "":
                    pool.close(s)
                    print "CLOSED"
                print "      ", m
            print w
            print e

        i += 1
        time.sleep(2)
