import gateway
import sys
import socket
import time
import random

host = sys.argv[1]
name = sys.argv[2]
test = sys.argv[3] if len(sys.argv) > 3 else "manual"
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host, 9999))

print "Starting gateway named", name
g = gateway.Gateway(sock, name)

g.outboundQueue.put(g.name)
while True:
    if test == "manual":
        time.sleep(0.1)

        print "input message: ",
        m = sys.stdin.readline().rstrip()
        if m == "": break
        g.outboundQueue.put(m)
    elif test == "random":
        time.sleep(0.5)
        prc  = random.randint(45,55)
        side = random.choice(("B","S"))
        qty  = random.randint(1,10)

        for gameId in xrange(150,160):
            m = "GA,%(gameId)d,%(qty)d,%(side)s,%(prc)d" % locals()
            g.outboundQueue.put(m)

    while not g.inboundQueue.empty():
        print "inbound: ",
        m = g.inboundQueue.get()
        print m

print "EXIT"
