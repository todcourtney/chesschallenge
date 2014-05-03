import SocketServer
import time
import threading
import Queue
from book import Order, Book

import gateway
from gateway import AddOrderMessage, CancelOrderMessage

import feed

chessgame = {"moves":"e4 c5 Nf3 e6 d4 cxd4 Nxd4 a6 Bd3 Nf6 O-O Qc7 Qe2 d6 c4 g6 Nc3 Bg7 Nf3 O-O Bf4 Nc6 Rac1 e5 Bg5 h6 Be3 Bg4 Nd5 Qd8 h3 Nxd5 cxd5 Nd4 Bxd4 Bxf3 Qxf3 exd4 Rc4 Rc8 Rfc1 Rxc4 Rxc4 h5 Qd1 Be5 Qc1 Qf6 Rc7 Rb8 a4 Kg7 b4 h4 Kf1 Bf4 Qd1 Qd8 Rc4 Rc8 a5 Rxc4 Bxc4 Qf6 Be2 Be5 Bf3 Qd8 Qc2 b6 axb6 Qxb6 Qc4 d3".split(" "), "result":"1/2-1/2"}
speed = 0.5
nextMove = time.time() + speed
n = 0

nextRecovery = time.time() + 5

class RecoveryBuilder:
    def __init__(self, b, f, freq=5):
        self.b = b
        self.f = f
        self.freq = freq
        self.reset()

    def reset(self):
        self.nextTime = time.time() + self.freq

    def sendIfNeeded(self):
        ## send recovery message every so often (may be very large)
        if time.time() > nextRecovery:
            recoveryMessageList = []
            recoveryMessage = None
            messages = self.b.getStateForRecoveryMessage()
            for r in messages:
                rs = ",".join(str(field) for field in r)
                recoveryMessageExpanded = recoveryMessage + ";" + rs if recoveryMessage is not None else rs
                if len(recoveryMessageExpanded) + 15 < feed.Feed.MAX_SIZE:
                    recoveryMessage = recoveryMessageExpanded
                else:
                    recoveryMessageList.append(recoveryMessage)
                    recoveryMessage = rs
            if recoveryMessage is not None:
                recoveryMessageList.append(recoveryMessage)
            recoveryMessageList = ["BS"] + ["BR," + rm for rm in recoveryMessageList] + ["BE"]
            for rm in recoveryMessageList:
                self.f.send(rm)
            self.reset()

if __name__ == "__main__":
    gateways = gateway.GatewayCollection()
    f = feed.Feed()
    f.send("N")
    b = Book()
    r = RecoveryBuilder(b,f)

    newoid = 1
    while True:
        if time.time() > nextMove:
            if n < len(chessgame['moves']):
                moveMessage = "M,%s,%s" % (chessgame['moves'][n], " ".join(chessgame['moves'][:(n+1)]))
                print "moveMessage = '%s'" % moveMessage
                f.send(moveMessage)
                n += 1
            else:
                f.send("R," + chessgame['result'])
                time.sleep(10)
                f.send("N")
                ## TODO: load new game
                chessgame = {"moves":"e4 c5 Nf3 e6 d4 cxd4 Nxd4 a6 Bd3 Nf6 O-O Qc7 Qe2 d6 c4 g6 Nc3 Bg7 Nf3 O-O Bf4 Nc6 Rac1 e5 Bg5 h6 Be3 Bg4 Nd5 Qd8 h3 Nxd5 cxd5 Nd4 Bxd4 Bxf3 Qxf3 exd4 Rc4 Rc8 Rfc1 Rxc4 Rxc4 h5 Qd1 Be5 Qc1 Qf6 Rc7 Rb8 a4 Kg7 b4 h4 Kf1 Bf4 Qd1 Qd8 Rc4 Rc8 a5 Rxc4 Bxc4 Qf6 Be2 Be5 Bf3 Qd8 Qc2 b6 axb6 Qxb6 Qc4 d3".split(" "), "result":"1/2-1/2"}
                n = 0
                b = Book() ## TODO: should send out cancels for everybody's orders?
                r = RecoveryBuilder(b,f)
                ## TODO: need to clear gateway queues
                pass
            nextMove = time.time() + speed

        ## send recovery messages if needed
        r.sendIfNeeded()

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
