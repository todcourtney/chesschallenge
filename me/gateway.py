## main class has accept => creates new gateways on demand
##
## gateway operates on own threads:
##   (a) blocking read, buffers and populates message queue
##   (b) notification and logging thread: block on something to notify, then notify all sockets that listen (note is receiver paced, so always send to drop copy first)
##   (c) disconnect will shut down receiver socket, send all pending notifications, and kill the gateway
##
## matching engine will poll in random order and grab a message from a non-empty queue (non-blocking)

import threading
import socket
import Queue
import time
import messenger


class Gateway:
    def __init__(self, socket, name=None):
        self.name = name
        self.messenger = messenger.Messenger(socket)

        self.inboundQueue  = Queue.Queue()
        self.outboundQueue = Queue.Queue()

        self.inboundThread  = threading.Thread(target=self.handleInboundMessages )
        self.outboundThread = threading.Thread(target=self.handleOutboundMessages)

        self.inboundThread.start()
        self.outboundThread.start()

    def handleInboundMessages(self):
        m = self.messenger.recvMessage()
        self.name = m ## for now
        while True:
            m = self.messenger.recvMessage()
            print "%s.handleInboundMessages() got message '%s'" % (self.name, m)
            if m is None:
                self.close()
                break
            else:
                self.inboundQueue.put(m)

    def handleOutboundMessages(self):
        while True:
            m = self.outboundQueue.get()
            print "%s.handleOutboundMessages() sending message '%s'" % (self.name, m)
            success = self.messenger.sendMessage(m)
            if not success:
                self.close()
                break

    def close(self):
        print self, " close"
        ## shut down receiver
        ## send all pending notifications
        ## shut down remaining sockets
        pass
        
class GatewayCollection:
    def __init__(self):
        self.lock = threading.Lock()
        self.gateways = dict()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('localhost', 9999))
        self.socket.listen(20)

        self.thread = threading.Thread(target=self.acceptGatewayConnections)
        self.thread.start()

    def acceptGatewayConnections(self):
        while True:
            print "accept", self.socket
            (clientsocket, address) = self.socket.accept()
            print clientsocket, address
            ##clientsocket.setblocking(0)
            with self.lock:
                self.gateways[clientsocket] = Gateway(clientsocket)
            time.sleep(1)

    ## either gets an incoming gateway message, or None if there is nothing to get
    def getIncomingMessage(self):
        with self.lock:
            for g in self.gateways.values(): ## TODO: shuffle for fairness
                if not g.inboundQueue.empty():
                    return g.inboundQueue.get(), g.name
        return None, None
