import SocketServer
import time
import threading
import Queue
from book import Order, Book

##if __name__ == "__main__":
##    b = Book()
##
##    print b.addOrder(Order(1, 10,Order.BUY ,67))
##    print b.addOrder(Order(2,200,Order.SELL,68))
##    print b.addOrder(Order(3, 11,Order.BUY ,67))
##    print b.addOrder(Order(4,201,Order.SELL,68))
##    print b.addOrder(Order(5, 15,Order.BUY ,67))
##    print b.addOrder(Order(6, 15,Order.BUY ,68))
##    print b.addOrder(Order(7,500,Order.BUY ,68))
##
##    print b.removeOrder(Order(3, None,Order.BUY ,67))
##    print b
##
##    print b.bid(), "x",  b.ask()

import gateway
from gateway import AddOrderMessage


if __name__ == "__main__":
    gateways = gateway.GatewayCollection()
    b = Book()

    while True:
        m, name = gateways.getIncomingMessage()
        if m is None:
            time.sleep(1)
            continue
        print "MatchingEngine got message from %s: '%s'" % (name, m)
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

        print events
        print b
