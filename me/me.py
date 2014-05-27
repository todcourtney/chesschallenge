import sys
import time
import threading
import Queue

from order import Order
from messages import *
from book import Book
from matchingbook import MatchingBook
from gatewaycollection import GatewayCollection
import feed
import pnl
import chessgame

from log import log

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
    pnlFilename = sys.argv[2]

    gamelines = open(sys.argv[1], 'r').readlines()

    speed = 1
    nextMove = time.time() + speed
    ##game = chessgame.ChessGame(gameId = 150, result = "1/2-1/2", moves="e4 c5 Nf3 e6 d4 cxd4 Nxd4 a6 Bd3 Nf6 O-O Qc7 Qe2 d6 c4 g6 Nc3 Bg7 Nf3 O-O Bf4 Nc6 Rac1 e5 Bg5 h6 Be3 Bg4 Nd5 Qd8 h3 Nxd5 cxd5 Nd4 Bxd4 Bxf3 Qxf3 exd4 Rc4 Rc8 Rfc1 Rxc4 Rxc4 h5 Qd1 Be5 Qc1 Qf6 Rc7 Rb8 a4 Kg7 b4 h4 Kf1 Bf4 Qd1 Qd8 Rc4 Rc8 a5 Rxc4 Bxc4 Qf6 Be2 Be5 Bf3 Qd8 Qc2 b6 axb6 Qxb6 Qc4 d3".split(" "))
    game = chessgame.ChessGame.fromstr(gamelines.pop(0))
    n = 0

    debugFeedBook = True

    gateways = GatewayCollection()
    f = feed.Feed(send=True)
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
                log.info("moveMessage = '%s'" % moveMessage)
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
                log.info("Waiting 5 sec to start next game...")
                time.sleep(5)

                ## TODO: load new game
                game = chessgame.ChessGame.fromstr(gamelines.pop(0))
                n = 0

                newMsg = game.newMessage()
                f.send(newMsg)

                bookClearMessage = ExchangeNewGameMessage(game.gameId)
                f.send(bookClearMessage)

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
                    log.info("FB REPLAY: " + rm)
                    fb.processMessage(rm)

        ## try to get and process one message
        m, g = gateways.getIncomingMessage()
        if m is None:
            time.sleep(0.1)
            continue

        log.info("MatchingEngine got message from %s: '%s'" % (g.name, m))

        ## settings for checks
        MAX_POTENTIAL_POS   = 100
        MAX_TOTAL_ORDER_QTY = 100
        MAX_TOTAL_ORDER_NUM = 10
        MAX_ORDER_QTY       = 100

        ## check gameid, position, order qty, and num orders
        if isinstance(m, GatewaySubmitOrderMessage):
            reason = None
            if m.gameId != game.gameId:
                reason="BAD_GAME_ID"
            elif m.price < 0 or m.price > 100:
                reason="BAD_PRICE"
            elif m.qty < 1 or m.qty > MAX_ORDER_QTY:
                reason="BAD_QTY"
            else:
                bids = [o for L in b.bids for o in L.orders if o.owner == g.name]
                asks = [o for L in b.asks for o in L.orders if o.owner == g.name]
                totalOrders = len(bids+asks)
                totalQty    = sum(o.qty for o in bids+asks)
                pos = b.pos.get(g.name, 0)
                posL =  pos if pos > 0 else 0
                posS = -pos if pos < 0 else 0
                potL = posL + sum(o.qty for o in bids)
                potS = posS + sum(o.qty for o in asks)

                if totalOrders + 1 > MAX_TOTAL_ORDER_NUM:
                    reason="TOO_MANY_ORD"
                elif totalQty + m.qty > MAX_TOTAL_ORDER_QTY:
                    reason="BAD_TOT_QTY"
                elif m.side == Order.BUY  and potL + m.qty > MAX_POTENTIAL_POS:
                    reason="TOO_LONG"
                elif m.side == Order.SELL and potS + m.qty > MAX_POTENTIAL_POS:
                    reason="TOO_SHORT"

                log.info("owner = %s, totalOrders = %d, totalQty = %d, pos = %d, posL/potL = %d/%d, posS/potS = %d/%d" % (g.name, totalOrders, totalQty, pos, posL, potL, posS, potS))

            if reason is not None:
                g.send(GatewayRejectMessage(g.name, m.gameId, m.goid, reason=reason))
                continue

        ## ignore non-submits that are not for this gameid too, but no reject message (TODO: pending cancels?)
        if m.gameId != game.gameId:
            log.warning("MatchingEngine dropping message not for this game (%s) from %s: '%s'" % (game.gameId, g.name, m))
            continue

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
            log.info("FB MESSAGE:" + msg)
            fb.processMessage(msg)

        ## now check that the local book and reconstructed book look the same
        if debugFeedBook:
            x = str(b ).split("\n")
            y = str(fb).split("\n")
            assert len(x) == len(y)
            z = "\n".join(xx + "  " + (" " if xx == yy else "X") + "   " + yy for xx,yy in zip(x,y))
            log.info("Book:\n"+z)
            assert x == y or (fb.bid() is None and fb.ask() is None)
