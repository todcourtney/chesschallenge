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
from order import Order
from messages import *
import book
import os

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

    def close(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except socket.error:
            pass

class Listener:
    def onGatewayMessage(self, gateway, message):
        pass

class Gateway:
    HOST = os.getenv("CHESS_GATEWAY", "localhost")
    PORT = 9999
    def __init__(self, name=None, sock=None, thread=False, listeners=None):
        self.clientMode = (sock is None)
        self.name = name
        self.liveOrders = None
        self.pos        = None

        self.pendingLock    = threading.Lock()
        self.pendingOrders  = dict()
        self.pendingCancels = set()

        if self.clientMode:
            assert self.name is not None
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((Gateway.HOST, Gateway.PORT))
            self.liveOrders = book.Book()
            self.liveOrders.needRecovery = False
            self.pos = 0
            self.goid = 99000
        else:
            self.socket = sock
            assert not thread

        self.listeners = listeners if listeners is not None else []
        for L in self.listeners:
            assert isinstance(L, Listener)

        self.messenger = Messenger(self.socket)

        self.inboundQueue  = Queue.Queue()
        self.outboundQueue = Queue.Queue()

        self.inboundThread  = threading.Thread(target=self.handleInboundMessages )
        self.outboundThread = threading.Thread(target=self.handleOutboundMessages)

        self.inboundThread.daemon = True
        self.outboundThread.daemon = True

        self.inboundThread.start()
        self.outboundThread.start()

        if thread:
            assert self.clientMode
            self.thread = threading.Thread(target=self.runClient)
            self.thread.daemon = True
            self.thread.start()

        ## now identify ourselves
        if self.clientMode:
            self.outboundQueue.put(LoginMessage(self.name))

    ## client side
    def addOrder(self, gameId, qty, side, price):
        self.goid += 1
        m = GatewaySubmitOrderMessage(gameId, self.goid, qty, side, price)
        with self.pendingLock:
            self.pendingOrders[self.goid] = m
        self.outboundQueue.put(m)

    def cancelOrder(self, oid):
        with self.pendingLock:
            self.pendingCancels.add(oid)
        self.outboundQueue.put(GatewayCancelOrderMessage(oid))

    ## server side
    def send(self, m):
        self.outboundQueue.put(str(m))

    ## internals
    def handleInboundMessages(self):
        if self.name is None: ## TODO: make more robust
            m = self.messenger.recvMessage() ## wait for login message
            self.name = LoginMessage.fromstr(m).name
        while True:
            m = self.messenger.recvMessage()
            print "%s.handleInboundMessages() got message '%s'" % (self.name, m)
            if m is None:
                self.close()
                break
            else:
                try:
                    m = GatewayMessage.fromstr(m)
                except ValueError as e:
                    print "WARNING: conversion problem parsing message '%s'" % m
                else:
                    self.inboundQueue.put(m)

    def handleOutboundMessages(self):
        while True:
            m = self.outboundQueue.get()
            print "%s.handleOutboundMessages() sending message '%s'" % (self.name, m)
            if self.messenger is None: break
            success = self.messenger.sendMessage(str(m))
            if not success:
                self.close()
                break

    def close(self):
        print self, " close" ## TODO
        self.messenger.close()
        del self.messenger
        self.messenger = None
        ## shut down receiver
        ## send all pending notifications
        ## shut down remaining sockets
        pass

    def runClient(self):
        while True:
            m = self.inboundQueue.get()

            ## keep track of position
            if isinstance(m, GatewayTradeMessage):
                self.pos += m.qty * int(m.side)
            elif isinstance(m, GatewaySettleMessage):
                self.pos = 0

            ## keep track of pending, live, and pending cancel
            with self.pendingLock:
                if isinstance(m, GatewayAddOrderMessage) or isinstance(m, GatewayRejectMessage):
                    if m.goid in self.pendingOrders:
                        del self.pendingOrders[m.goid]
                elif isinstance(m, GatewayDeleteOrderMessage):
                    self.pendingCancels.discard(m.goid)
                elif isinstance(m, GatewaySettleMessage):
                    self.pendingOrders.clear()
                    self.pendingCancels.clear()

                ## keep track of live orders
                self.liveOrders.processMessage(m)

                ## trade can also remove pending cancels
                if isinstance(m, GatewayTradeMessage):
                    if m.oid in self.liveOrders.oidToPriceLevel:
                        L = self.liveOrders.oidToPriceLevel[m.oid]
                        if all(o.oid != m.oid for o in L):
                            self.pendingCancels.discard(m.goid)

            ## now that internal state is correct, notify listeners
            for L in self.listeners:
                L.onGatewayMessage(self, m)

class GatewayCollection:
    def __init__(self):
        self.lock = threading.Lock()
        self.gateways = dict()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', Gateway.PORT))
        self.socket.listen(20)

        self.thread = threading.Thread(target=self.acceptGatewayConnections)
        self.thread.daemon = True
        self.thread.start()

    def acceptGatewayConnections(self):
        while True:
            print "accept", self.socket
            (clientsocket, address) = self.socket.accept()
            print clientsocket, address
            ##clientsocket.setblocking(0)
            with self.lock:
                ## first, prune dead gateways
                for s in self.gateways.keys():
                    g = self.gateways[s]
                    if g.messenger is None:
                        print "deleting disconnected gateway '%s'" % g.name
                        del self.gateways[s]
                self.gateways[clientsocket] = Gateway(sock=clientsocket)
            time.sleep(1)

    ## either gets an incoming gateway message, or None if there is nothing to get
    def getIncomingMessage(self):
        with self.lock:
            for g in self.gateways.values(): ## TODO: shuffle for fairness
                if not g.inboundQueue.empty():
                    return g.inboundQueue.get(), g
        return None, None

    def sendToOwner(self, m):
        owner = m.owner
        with self.lock:
            for g in self.gateways.values():
                if g.name == owner and g.messenger is not None:
                    g.send(m)

