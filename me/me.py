import sys
import time
import threading
import Queue

from order import Order
from messages import *
from book import MatchingBook, Book
import gateway
import feed
import pnl
import chessgame

game = chessgame.ChessGame(gameId = 150, result = "1/2-1/2", moves="e4 c5 Nf3 e6 d4 cxd4 Nxd4 a6 Bd3 Nf6 O-O Qc7 Qe2 d6 c4 g6 Nc3 Bg7 Nf3 O-O Bf4 Nc6 Rac1 e5 Bg5 h6 Be3 Bg4 Nd5 Qd8 h3 Nxd5 cxd5 Nd4 Bxd4 Bxf3 Qxf3 exd4 Rc4 Rc8 Rfc1 Rxc4 Rxc4 h5 Qd1 Be5 Qc1 Qf6 Rc7 Rb8 a4 Kg7 b4 h4 Kf1 Bf4 Qd1 Qd8 Rc4 Rc8 a5 Rxc4 Bxc4 Qf6 Be2 Be5 Bf3 Qd8 Qc2 b6 axb6 Qxb6 Qc4 d3".split(" "))
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
                rs = str(r)
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
            return recoveryMessageList

if __name__ == "__main__":
    pnlFilename = sys.argv[1]

    debugFeedBook = True

    gateways = gateway.GatewayCollection()
    f = feed.Feed()
    b = MatchingBook()
    newMsg = game.newMessage()
    f.send(newMsg)
    if debugFeedBook:
        fb = Book()
        fb.processMessage(newMsg)
    r = RecoveryBuilder(b,f)
    pnlEvents = pnl.PnlEvents(pnlFilename)
    oldMark = None

    newoid = 1
    while True:
        if time.time() > nextMove:
            if n < len(game.moves):
                moveMessage = game.moveMessage(n)
                print "moveMessage = '%s'" % moveMessage
                f.send(moveMessage)
                n += 1
            else:
                resultMsg = game.resultMessage()
                settlePrice = 100 if resultMsg.whiteWins() else 0
                pnlEvents.append(("S", game.gameId, time.time(), "", "", "", "", settlePrice))
                for g in gateways.gateways.values():
                    g.send(GatewaySettleMessage(game.gameId, settlePrice))

                ##print pnlEvents
                f.send(resultMsg)
                if debugFeedBook: fb.processMessage(resultMsg)
                print "Waiting 5 sec to start next game..."
                time.sleep(5)

                ## TODO: load new game
                game = chessgame.ChessGame(gameId = str(int(game.gameId)+1), result = "1/2-1/2", moves="e4 c5 Nf3 e6 d4 cxd4 Nxd4 a6 Bd3 Nf6 O-O Qc7 Qe2 d6 c4 g6 Nc3 Bg7 Nf3 O-O Bf4 Nc6 Rac1 e5 Bg5 h6 Be3 Bg4 Nd5 Qd8 h3 Nxd5 cxd5 Nd4 Bxd4 Bxf3 Qxf3 exd4 Rc4 Rc8 Rfc1 Rxc4 Rxc4 h5 Qd1 Be5 Qc1 Qf6 Rc7 Rb8 a4 Kg7 b4 h4 Kf1 Bf4 Qd1 Qd8 Rc4 Rc8 a5 Rxc4 Bxc4 Qf6 Be2 Be5 Bf3 Qd8 Qc2 b6 axb6 Qxb6 Qc4 d3".split(" "))
                n = 0

                newMsg = game.newMessage()
                f.send(newMsg)
                b = MatchingBook() ## TODO: should send out cancels for everybody's orders?
                if debugFeedBook: fb.processMessage(newMsg)
                r = RecoveryBuilder(b,f)
                oldMark = None
            nextMove = time.time() + speed

        ## send recovery messages if needed
        recoveryMessages = r.sendIfNeeded()
        if debugFeedBook:
            if recoveryMessages is not None:
                for rm in recoveryMessages:
                    print "FB REPLAY:", rm
                    fb.processMessage(rm)

        ## try to get and process one message
        m, g = gateways.getIncomingMessage()
        if m is None:
            time.sleep(0.1)
            continue
        elif m.gameId != game.gameId:
            print "WARNING: MatchingEngine dropping message not for this game (%s) from %s: '%s'" % (game.gameId, g.name, m)
            if m.code == GatewayAddOrderMessage.code:
                g.send(GatewayRejectMessage(g.name, m.gameId, m.goid, reason="BAD_GAME_ID"))
            continue
        print "MatchingEngine got message from %s: '%s'" % (g.name, m)
        events = []
        gatewayEvents = []
        if isinstance(m, GatewaySubmitOrderMessage):
            o = Order(newoid,m.qty,m.side,m.price,owner=g.name,gameId=m.gameId,goid=m.goid)
            newoid += 1
            newEvents, newGatewayEvents, newPnlEvents = b.addOrder(o)
            events       .extend(newEvents)
            gatewayEvents.extend(newGatewayEvents)
            pnlEvents    .extend(newPnlEvents)
        elif isinstance(m, GatewayCancelOrderMessage):
            oid = m.oid
            newEvents, newGatewayEvents = b.cancelOrder(oid,owner=g.name)
            events       .extend(newEvents)
            gatewayEvents.extend(newGatewayEvents)

        ## now that messages have been processed, record new mark price
        bid = b.bid()
        ask = b.ask()
        if   bid is None and ask is None: mark = oldMark if oldMark is not None else 50
        elif bid is None                : mark = ask
        elif ask is None                : mark = bid
        else                            : mark = (bid+ask)/2.0

        if mark != oldMark:
            pnlEvents.append(("M", game.gameId, time.time(), "", "", "", "", mark))
            oldMark = mark

        ## responses for gateways
        for e in gatewayEvents:
            gateways.sendToOwner(e)

        ## feed handler
        msg = ";".join(str(e) for e in events)
        f.send(msg)
        if debugFeedBook:
            print "FB MESSAGE:", msg
            fb.processMessage(msg)

        ## now check that the local book and reconstructed book look the same
        if debugFeedBook:
            x = str(b ).split("\n")
            y = str(fb).split("\n")
            assert len(x) == len(y)
            z = "\n".join(xx + "  " + (" " if xx == yy else "X") + "   " + yy for xx,yy in zip(x,y))
            print z
            assert x == y or (fb.bid() is None and fb.ask() is None)
