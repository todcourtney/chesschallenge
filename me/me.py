import sys
import time
import threading
import Queue

from book import Order, MatchingBook
import gateway
from gateway import AddOrderMessage, CancelOrderMessage
import feed
import pnl

chessgame = {"moves":"e4 c5 Nf3 e6 d4 cxd4 Nxd4 a6 Bd3 Nf6 O-O Qc7 Qe2 d6 c4 g6 Nc3 Bg7 Nf3 O-O Bf4 Nc6 Rac1 e5 Bg5 h6 Be3 Bg4 Nd5 Qd8 h3 Nxd5 cxd5 Nd4 Bxd4 Bxf3 Qxf3 exd4 Rc4 Rc8 Rfc1 Rxc4 Rxc4 h5 Qd1 Be5 Qc1 Qf6 Rc7 Rb8 a4 Kg7 b4 h4 Kf1 Bf4 Qd1 Qd8 Rc4 Rc8 a5 Rxc4 Bxc4 Qf6 Be2 Be5 Bf3 Qd8 Qc2 b6 axb6 Qxb6 Qc4 d3".split(" "), "result":"1/2-1/2", "gameId":'150'}
n = 0
speed = 1
nextMove = time.time() + speed

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
        if time.time() > self.nextTime:
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
    pnlFilename = sys.argv[1]

    gateways = gateway.GatewayCollection()
    f = feed.Feed()
    f.send("N,%s" % chessgame['gameId'])
    b = MatchingBook()
    r = RecoveryBuilder(b,f)
    pnlEvents = pnl.PnlEvents(pnlFilename)
    oldMark = None

    newoid = 1
    while True:
        if time.time() > nextMove:
            if n < len(chessgame['moves']):
                moveMessage = "M,%s,%s,%s" % (chessgame['gameId'], chessgame['moves'][n], " ".join(chessgame['moves'][:(n+1)]))
                print "moveMessage = '%s'" % moveMessage
                f.send(moveMessage)
                n += 1
            else:
                pnlEvents.append(("S", chessgame['gameId'], time.time(), "", "", "", "", 100 if chessgame['result'] == '1-0' else 0))
                print pnlEvents
                f.send("R,%s,%s" % (chessgame['gameId'], chessgame['result']))
                print "Waiting 10 sec to start next game..."
                time.sleep(10)

                ## TODO: load new game
                chessgame = {"moves":"e4 c5 Nf3 e6 d4 cxd4 Nxd4 a6 Bd3 Nf6 O-O Qc7 Qe2 d6 c4 g6 Nc3 Bg7 Nf3 O-O Bf4 Nc6 Rac1 e5 Bg5 h6 Be3 Bg4 Nd5 Qd8 h3 Nxd5 cxd5 Nd4 Bxd4 Bxf3 Qxf3 exd4 Rc4 Rc8 Rfc1 Rxc4 Rxc4 h5 Qd1 Be5 Qc1 Qf6 Rc7 Rb8 a4 Kg7 b4 h4 Kf1 Bf4 Qd1 Qd8 Rc4 Rc8 a5 Rxc4 Bxc4 Qf6 Be2 Be5 Bf3 Qd8 Qc2 b6 axb6 Qxb6 Qc4 d3".split(" "), "result":"1/2-1/2", "gameId":str(int(chessgame['gameId'])+1)}
                n = 0

                f.send("N,%s" % chessgame['gameId'])
                b = MatchingBook() ## TODO: should send out cancels for everybody's orders?
                r = RecoveryBuilder(b,f)
                oldMark = None
            nextMove = time.time() + speed

        ## send recovery messages if needed
        r.sendIfNeeded()

        ## try to get and process one message
        m, g = gateways.getIncomingMessage()
        if m is None:
            time.sleep(0.1)
            continue
        elif m.gameId != chessgame['gameId']:
            print "WARNING: MatchingEngine dropping message not for this game (%s) from %s: '%s'" % (chessgame['gameId'], g.name, m)
            continue
        print "MatchingEngine got message from %s: '%s'" % (g.name, m)
        events = []
        if isinstance(m, AddOrderMessage):
            o = Order(newoid,m.qty,m.side,m.price,owner=g.name,gameId=m.gameId)
            newoid += 1
            newEvents, newPnlEvents = b.addOrder(o)
            events   .extend(newEvents)
            pnlEvents.extend(newPnlEvents)
        elif isinstance(m, CancelOrderMessage):
            oid = m.oid
            events += b.cancelOrder(oid,owner=g.name)

        ## now that messages have been processed, record new mark price
        bid = b.bid()
        ask = b.ask()
        if   bid is None and ask is None: mark = oldMark if oldMark is not None else 50
        elif bid is None                : mark = ask
        elif ask is None                : mark = bid
        else                            : mark = (bid+ask)/2.0

        if mark != oldMark:
            pnlEvents.append(("M", chessgame['gameId'], time.time(), "", "", "", "", mark))
            oldMark = mark

        print b
        print events
        print pnlEvents

        ## response for gateway
        for e in events:
            g.outboundQueue.put(",".join(str(f) for f in e))

        ## feed handler
        msg = ";".join(",".join(str(f) for f in e) for e in events)
        f.send(msg)
