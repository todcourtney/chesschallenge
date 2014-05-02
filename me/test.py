##import sys
##import time
##import socket
##import messenger
##from gateway import GatewayCollection
##
##if sys.argv[1] == "server":
##    print "building GatewayCollection()"
##    gs = GatewayCollection()
##    print "GatewayCollection() running"
##    while True: time.sleep(1)
##else:
##    name = sys.argv[1]
##    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##    sock.connect(('localhost', 9999))
##    c = messenger.Messenger(sock)
##    c.sendMessage(name)
##    c.sendMessage("message1")
##    c.sendMessage("message2")


import gateway
import sys
import socket

name = sys.argv[1]
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 9999))
g = gateway.Gateway(sock, name)

g.outboundQueue.put(g.name)
while True:
    print "input message: ",
    m = sys.stdin.readline().rstrip()
    g.outboundQueue.put(m)

    while not g.inboundQueue.empty():
        print "inbound: ",
        m = g.inboundQueue.get()
        print m
