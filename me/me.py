import SocketServer
import time
import threading
import Queue
from book import Order, Book

import gateway
from gateway import AddOrderMessage, CancelOrderMessage

import feed

if __name__ == "__main__":
    gateways = gateway.GatewayCollection()
    f = feed.Feed()
    b = Book()

    newoid = 1
    while True:
        m, g = gateways.getIncomingMessage()
        if m is None:
            time.sleep(0.1)
            continue
        print "MatchingEngine got message from %s: '%s'" % (g.name, m)
        events = []
        if isinstance(m, AddOrderMessage):
            o = Order(newoid,m.qty,m.side,m.price,owner=g.name)
            newoid += 1
            events += b.addOrder(o)
        elif isinstance(m, CancelOrderMessage):
            oid = m.oid
            events += b.cancelOrder(oid,owner=g.name)

        print b
        print events

        ## response for gateway
        for e in events:
            g.outboundQueue.put(",".join(str(f) for f in e))

        ## feed handler
        msg = ";".join(",".join(str(f) for f in e) for e in events)
        f.send(msg)
