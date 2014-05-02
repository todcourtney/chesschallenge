import SocketServer
import time
import threading
import Queue
from book import Order, Book

import gateway
from gateway import AddOrderMessage

import feed

if __name__ == "__main__":
    gateways = gateway.GatewayCollection()
    f = feed.Feed()
    b = Book()

    while True:
        m, g = gateways.getIncomingMessage()
        if m is None:
            time.sleep(1)
            continue
        print "MatchingEngine got message from %s: '%s'" % (g.name, m)
        events = []
        if isinstance(m, AddOrderMessage):
            o = Order(m.oid,m.qty,m.side,m.price)
            events += b.addOrder(o)
        elif m.startswith("C"):
            action, oid, qty, side, price = m.split(",")
            oid   = int(oid)
            qty   = int(qty)
            side  = {"B":Order.BUY, "S":Order.SELL}[side]
            price = int(price)
            events += b.removeOrder(Order(oid,qty,side,price))

        print b
        print events

        ## response for gateway
        for e in events:
            g.outboundQueue.put(",".join(str(f) for f in e))

        ## feed handler
        msg = ";".join(",".join(str(f) for f in e) for e in events)
        f.send(msg)
