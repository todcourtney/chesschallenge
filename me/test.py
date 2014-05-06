import gateway
import sys
import socket
import time
import random

from book import Order

name = sys.argv[1]
test = sys.argv[2] if len(sys.argv) > 2 else "manual"

print "Starting gateway named", name
g = gateway.Gateway(name=name)

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
        side = random.choice((Order.BUY, Order.SELL))
        qty  = random.randint(1,10)

        for gameId in xrange(150,160):
            g.addOrder(gameId, qty, side, prc)

    for m in g.getMessages():
        print "inbound:", m

print "EXIT"
