import SocketServer
import time
import threading
import Queue
from book import Order, Book

import gateway
from gateway import AddOrderMessage, CancelOrderMessage

import feed

chessgame = {"moves":"e4 c5 Nf3 e6 d4 cxd4 Nxd4 a6 Bd3 Nf6 O-O Qc7 Qe2 d6 c4 g6 Nc3 Bg7 Nf3 O-O Bf4 Nc6 Rac1 e5 Bg5 h6 Be3 Bg4 Nd5 Qd8 h3 Nxd5 cxd5 Nd4 Bxd4 Bxf3 Qxf3 exd4 Rc4 Rc8 Rfc1 Rxc4 Rxc4 h5 Qd1 Be5 Qc1 Qf6 Rc7 Rb8 a4 Kg7 b4 h4 Kf1 Bf4 Qd1 Qd8 Rc4 Rc8 a5 Rxc4 Bxc4 Qf6 Be2 Be5 Bf3 Qd8 Qc2 b6 axb6 Qxb6 Qc4 d3".split(" "), "result":"1/2-1/2"}
speed = 2
nextMove = time.time() + speed

if __name__ == "__main__":
    gateways = gateway.GatewayCollection()
    f = feed.Feed()
    b = Book()

    newoid = 1
    while True:
        if time.time() > nextMove:
            if len(chessgame['moves']):
                f.send("M," + chessgame['moves'].pop(0))
            else:
                f.send("R," + chessgame['result'])
                f.send("N")
                chessgame = {"moves":"e4 c5 Nf3 e6 d4 cxd4 Nxd4 a6 Bd3 Nf6 O-O Qc7 Qe2 d6 c4 g6 Nc3 Bg7 Nf3 O-O Bf4 Nc6 Rac1 e5 Bg5 h6 Be3 Bg4 Nd5 Qd8 h3 Nxd5 cxd5 Nd4 Bxd4 Bxf3 Qxf3 exd4 Rc4 Rc8 Rfc1 Rxc4 Rxc4 h5 Qd1 Be5 Qc1 Qf6 Rc7 Rb8 a4 Kg7 b4 h4 Kf1 Bf4 Qd1 Qd8 Rc4 Rc8 a5 Rxc4 Bxc4 Qf6 Be2 Be5 Bf3 Qd8 Qc2 b6 axb6 Qxb6 Qc4 d3".split(" "), "result":"1/2-1/2"}
                ## TODO: load new game
                pass
            nextMove = time.time() + speed

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
