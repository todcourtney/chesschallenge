import gateway
import sys
import socket
import time
import random

from book import Order
from log import log

name = sys.argv[1]
test = sys.argv[2] if len(sys.argv) > 2 else "manual"

class TestGatewayListener(gateway.Listener):
    def onGatewayMessage(self, g, message):
        log.info("TestGatewayListener.onGatewayMessage('%s') => pos = %d" % (message, g.pos))
        ##log.info(g.liveOrders)
        log.info("pendingOrders  = %s" % ([oid for oid in g.pendingOrders ]))
        log.info("pendingCancels = %s" % ([oid for oid in g.pendingCancels]))

L = TestGatewayListener()

log.info("Starting gateway named %s", name)
g = gateway.Gateway(name=name, thread=True, listeners=[L])

while True:
    if test == "manual":
        time.sleep(0.1)

        print "input message: ",
        m = sys.stdin.readline().rstrip()
        if m == "": break
        g.outboundQueue.put(m)
    elif test == "random":
        time.sleep(1)
        prc  = random.randint(45,55)
        side = random.choice((Order.BUY, Order.SELL))
        qty  = random.randint(1,10)

        for gameId in xrange(150,160):
            g.addOrder(gameId, qty, side, prc)

    ##for m in g.getMessages():
    ##    print "inbound:", m

print "EXIT"
