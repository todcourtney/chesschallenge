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
from book import Order
import re
import os

class GatewayMessage:
    pass

class AddOrderMessage(GatewayMessage):
    code = "GA"
    def __init__(self, gameId, qty, side, price):
        self.gameId = gameId
        self.qty    = qty
        self.side   = side
        self.price  = price

    @classmethod
    def fromstr(cls, s):
        add, gameId, qty, side, price = s.split(",")
        assert add == cls.code
        qty    = int(qty)
        side   = {"B":Order.BUY,"S":Order.SELL}[side]
        price  = int(price)
        return cls(gameId, qty, side, price)

    def __str__(self):
        return "%s,%s,%d,%s,%d" % (AddOrderMessage.code, self.gameId, self.qty, {Order.BUY:"B",Order.SELL:"S"}[self.side], self.price)

class CancelOrderMessage(GatewayMessage):
    code = "GC"
    def __init__(self, oid):
        self.oid = oid

    @classmethod
    def fromstr(cls, s):
        cancel, oid = s.split(",")
        assert cancel == cls.code
        oid = int(oid)
        return cls(oid)

    def __str__(self):
        return "%s,%d" % (CancelOrderMessage.code, self.oid)

class LoginMessage(GatewayMessage):
    code = "GN"
    def __init__(self, name):
        assert re.match("^[0-9A-Za-z]{3,8}$", name), "names must consist of between 3 and 8 characters from [0-9A-Za-z], not '%s'" % name
        self.name = name

    @classmethod
    def fromstr(cls, s):
        login, name = s.split(",")
        assert login == cls.code
        return cls(name)

    def __str__(self):
        return "%s,%s" % (LoginMessage.code, self.name)

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

class Listener:
    def onGatewayMessage(self, message):
        pass

class Gateway:
    HOST = os.getenv("CHESS_GATEWAY", "localhost")
    PORT = 9999
    def __init__(self, name=None, sock=None, thread=False, listeners=None):
        self.clientMode = (sock is None)
        self.name = name
        if self.clientMode:
            assert self.name is not None
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((Gateway.HOST, Gateway.PORT))
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
        self.outboundQueue.put(AddOrderMessage(gameId, qty, side, price))

    def cancelOrder(self, oid):
        self.outboundQueue.put(CancelOrderMessage(oid))

    def getMessages(self):
        messages = []
        while not self.inboundQueue.empty():
            messages.append(self.inboundQueue.get())
        return messages

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
                    if m.startswith("GA"):
                        m = AddOrderMessage.fromstr(m)
                    elif m.startswith("GC"):
                        m = CancelOrderMessage.fromstr(m)
                except ValueError as e:
                    print "WARNING: conversion problem parsing message '%s'" % m
                else:
                    self.inboundQueue.put(m)

    def handleOutboundMessages(self):
        while True:
            m = self.outboundQueue.get()
            print "%s.handleOutboundMessages() sending message '%s'" % (self.name, m)
            success = self.messenger.sendMessage(str(m))
            if not success:
                self.close()
                break

    def close(self):
        print self, " close" ## TODO
        ## shut down receiver
        ## send all pending notifications
        ## shut down remaining sockets
        pass
        
    def runClient(self):
        while True:
            m = self.inboundQueue.get()
            for L in self.listeners:
                L.onGatewayMessage(m)

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
                self.gateways[clientsocket] = Gateway(sock=clientsocket)
            time.sleep(1)

    ## either gets an incoming gateway message, or None if there is nothing to get
    def getIncomingMessage(self):
        with self.lock:
            for g in self.gateways.values(): ## TODO: shuffle for fairness
                if not g.inboundQueue.empty():
                    return g.inboundQueue.get(), g
        return None, None
