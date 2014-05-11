import time
import sys
from order import Order
from messages import *
from log import log

class PriceLevel:
    def __init__(self, side, price):
        assert side in (Order.BUY, Order.SELL)
        self.side   = side
        self.price  = price
        self.orders = []

    def __str__(self):
        if self.side == Order.BUY:
            return " ".join(str(o) for o in reversed(self.orders))
        else:
            return " ".join(str(o) for o in          self.orders )

class MatchingBook:
    def __init__(self):
        self.prices = range(0,101)
        self.N      = len(self.prices)

        ## bids and asks, ordered lowest to highest price
        self.bids = [PriceLevel(Order.BUY,  p) for p in self.prices]
        self.asks = [PriceLevel(Order.SELL, p) for p in self.prices]

        ## to speed up cancels
        self.oidToPriceLevel = dict()

    def bidLevel(self, level=0):
        n = -1
        for i in reversed(xrange(self.N)):
            if len(self.bids[i].orders): n += 1
            if n == level:
                return self.bids[i]
        return None

    def askLevel(self, level=0):
        n = -1
        for i in xrange(self.N):
            if len(self.asks[i].orders): n += 1
            if n == level:
                return self.asks[i]
        return None

    def bid(self, level=0):
        b = self.bidLevel(level)
        if b is None: return None
        return b.price

    def ask(self, level=0):
        a = self.askLevel(level)
        if a is None: return None
        return a.price

    def addOrder(self, o):
        feedEvents    = []
        gatewayEvents = []
        pnlTrades     = []

        ## (1) make all trades for resting orders that this new order crosses
        l = None
        while o.qty > 0:
            if l is None or len(l.orders) == 0:
                l = self.askLevel(0) if o.side == Order.BUY else self.bidLevel(0)
                ## if there are no remaining orders, there are definitely no more fills to do
                if l is None: break
            crossingPrice = (o.side == Order.BUY and l.price <= o.price) or (o.side == Order.SELL and l.price >= o.price)
            if crossingPrice:
                ro = l.orders[0]

                ## prevent self-match by canceling resting, move to next order
                if ro.owner == o.owner:
                    newFeedEvents, newGatewayEvents = self.cancelOrder(ro.oid, owner=o.owner)
                    feedEvents.extend(newFeedEvents)
                    gatewayEvents.extend(newGatewayEvents)
                    continue

                ## know we don't have a self-match at this point
                tm = time.time()
                if ro.qty <= o.qty:
                    feedEvents   .append(ExchangeTradeMessage(          ro.gameId,          ro.oid, ro.qty, ro.side, ro.price))
                    gatewayEvents.append( GatewayTradeMessage(ro.owner, ro.gameId, ro.goid, ro.oid, ro.qty, ro.side, ro.price))
                    gatewayEvents.append( GatewayTradeMessage( o.owner,  o.gameId,  o.goid,  o.oid, ro.qty,  o.side, ro.price))
                    pnlTrades.append(("T", ro.gameId, tm, ro.owner, ro.oid, ro.qty, ro.side, ro.price))
                    pnlTrades.append(("T",  o.gameId, tm,  o.owner,  o.oid, ro.qty,  o.side, ro.price))
                    o.qty  -= ro.qty
                    ro.qty  = 0
                    del l.orders[0]
                else:
                    feedEvents   .append(ExchangeTradeMessage(          ro.gameId,          ro.oid,  o.qty, ro.side, ro.price))
                    gatewayEvents.append( GatewayTradeMessage(ro.owner, ro.gameId, ro.goid, ro.oid,  o.qty, ro.side, ro.price))
                    gatewayEvents.append( GatewayTradeMessage( o.owner,  o.gameId,  o.goid,  o.oid,  o.qty,  o.side, ro.price))
                    pnlTrades.append(("T", ro.gameId, tm, ro.owner, ro.oid,  o.qty, ro.side, ro.price))
                    pnlTrades.append(("T",  o.gameId, tm,  o.owner,  o.oid,  o.qty,  o.side, ro.price))
                    ro.qty -= o.qty
                    o.qty   = 0
            else:
                break ## prices don't cross

        ## (2) add this order to the book
        if o.qty > 0:
            L = (self.bids if o.side == Order.BUY else self.asks)[o.price]
            L.orders.append(o)
            feedEvents   .append(ExchangeAddOrderMessage(         o.gameId,         o.oid, o.qty, o.side, o.price))
            gatewayEvents.append( GatewayAddOrderMessage(o.owner, o.gameId, o.goid, o.oid, o.qty, o.side, o.price))

            ## track for easy cancels later
            self.oidToPriceLevel[o.oid] = L

        return feedEvents, gatewayEvents, pnlTrades

    def cancelOrder(self, oid, owner=None):
        feedEvents    = []
        gatewayEvents = []
        if oid in self.oidToPriceLevel:
            restingOrders = self.oidToPriceLevel[oid].orders
            for ro in restingOrders:
                if ro.oid == oid:
                    if owner is None or ro.owner == owner:
                        feedEvents   .append(ExchangeCancelOrderMessage(          ro.gameId,          ro.oid, ro.qty, ro.side, ro.price))
                        gatewayEvents.append( GatewayDeleteOrderMessage(ro.owner, ro.gameId, ro.goid, ro.oid, ro.qty, ro.side, ro.price))
                        restingOrders.remove(ro)
                        del self.oidToPriceLevel[oid]
                        break
                    else:
                        pass ## should send cancel reject for trying to cancel other owner's order
        ## TODO: cancel rejects if order is not found (for now silently ignore)
        return feedEvents, gatewayEvents

    def getStateForRecoveryMessage(self):
        events = []
        for L in self.bids + self.asks:
            for o in L.orders:
                events.append(ExchangeAddOrderMessage(o.gameId, o.oid, o.qty, o.side, o.price))
        return events

    def __str__(self):
        bs = [str(l) for l in self.bids]
        ss = [str(l) for l in self.asks]
        W = 30
        fmt = "%%%ds %%03d %%-%ds" % (W, W)
        s = ""
        for i in reversed(xrange(self.N)):
            s += fmt % (bs[i][:W], self.prices[i], ss[i][:W]) + "\n"
        return s

class Book:
    def __init__(self):
        self.prices = range(0,101)
        self.N      = len(self.prices)
        self.needRecovery = True
        self.inRecovery   = False

        ## bids and asks, ordered lowest to highest price
        self.bids = [PriceLevel(Order.BUY,  p) for p in self.prices]
        self.asks = [PriceLevel(Order.SELL, p) for p in self.prices]

        ## to speed up cancels
        self.oidToPriceLevel = dict()

    def bidLevel(self, level=0):
        n = -1
        for i in reversed(xrange(self.N)):
            if len(self.bids[i].orders): n += 1
            if n == level:
                return self.bids[i]
        return None

    def askLevel(self, level=0):
        n = -1
        for i in xrange(self.N):
            if len(self.asks[i].orders): n += 1
            if n == level:
                return self.asks[i]
        return None

    def bid(self, level=0):
        b = self.bidLevel(level)
        if b is None: return None
        return b.price

    def ask(self, level=0):
        a = self.askLevel(level)
        if a is None: return None
        return a.price


    def processMessage(self, m):
        "Applies message and returns True if this message affected the book (or completed a recovery)."

        ## allow str or message for now by normalizing to string
        m = str(m)
        log.info(m)

        ## when a game starts, we don't need recovery, but we have to clear old orders
        if m.startswith("CR"):
            self.clear()
        elif m.startswith("CN"):
            self.needRecovery = False
            self.clear()

        ## only handle recovery messages if we need them
        if self.needRecovery:
            if m == "BS":
                self.inRecovery = True
                self.clear()
            elif m.startswith("BR") and self.inRecovery:
                header, recoveryMessages = m.split(",",1)
                for msg in recoveryMessages.split(";"):
                    xm = ExchangeAddOrderMessage.fromstr(msg)
                    o = Order(xm.oid, xm.qty, xm.side, xm.price)
                    self.addOrder(o)
            elif m == "BE" and self.inRecovery:
                self.needRecovery = False
                self.inRecovery   = False
                return True
        elif m.startswith("X"):
            for subm in m.split(";"):
                code, rest = subm.split(",", 1)
                if code == ExchangeAddOrderMessage.code:
                    xm = ExchangeAddOrderMessage.fromstr(subm)
                    o = Order(xm.oid, xm.qty, xm.side, xm.price)
                    self.addOrder(o)
                elif code == ExchangeCancelOrderMessage.code:
                    xm = ExchangeCancelOrderMessage.fromstr(subm)
                    self.removeOrder(xm.oid)
                elif code == ExchangeTradeMessage.code:
                    xm = ExchangeTradeMessage.fromstr(subm)
                    self.applyTrade(xm.oid, xm.qty)
            return True
        elif m.startswith("G"):
            code, rest = m.split(",", 1)
            log.info("  code = " + code)
            if code == GatewayAddOrderMessage.code:
                gm = GatewayAddOrderMessage.fromstr(m)
                o = Order(gm.oid, gm.qty, gm.side, gm.price)
                self.addOrder(o)
            elif code == GatewayDeleteOrderMessage.code:
                gm = GatewayDeleteOrderMessage.fromstr(m)
                self.removeOrder(gm.oid)
            elif code == GatewayTradeMessage.code:
                gm = GatewayTradeMessage.fromstr(m)
                self.applyTrade(gm.oid, gm.qty)
            elif code == GatewaySettleMessage.code:
                self.clear()
            else:
                return False
            return True
        return False

    def addOrder(self, o):
        L = (self.bids if o.side == Order.BUY else self.asks)[o.price]
        bid = self.bid()
        ask = self.ask()
        if bid is not None and ask is not None and bid >= ask:
            s = "book just became crossed because of addOrder with oid %d:\n" % o.oid
            s += str(self)
            raise RuntimeError(s)
        L.orders.append(o)

        ## track for easy cancels later
        self.oidToPriceLevel[o.oid] = L

    def removeOrder(self, oid):
        if oid in self.oidToPriceLevel:
            restingOrders = self.oidToPriceLevel[oid].orders
            for ro in restingOrders:
                if ro.oid == oid:
                    restingOrders.remove(ro)
                    del self.oidToPriceLevel[oid]
                    break

    def applyTrade(self, oid, qty):
        ## this should only happen for gateway trades, since the passive
        ## and the aggressive side both get a report, and the aggressor
        ## will have no order to remove
        if oid not in self.oidToPriceLevel:
            return

        restingOrders = self.oidToPriceLevel[oid].orders
        for ro in restingOrders:
            if ro.oid == oid:
                assert qty <= ro.qty
                if qty == ro.qty:
                    self.removeOrder(oid)
                else:
                    ro.qty -= qty
                break

    def clear(self):
        self.oidToPriceLevel = dict()
        for L in self.bids + self.asks:
            L.orders = []

    def __str__(self):
        bs = [str(l) for l in self.bids]
        ss = [str(l) for l in self.asks]
        W = 30
        fmt = "%%%ds %%03d %%-%ds" % (W, W)
        s = ""
        for i in reversed(xrange(self.N)):
            s += fmt % (bs[i][:W], self.prices[i], ss[i][:W]) + "\n"
        return s

