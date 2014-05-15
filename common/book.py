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
        if m.startswith("CR") or m.startswith("CN"):
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
                elif code == ExchangeNewGameMessage.code:
                    xm = ExchangeNewGameMessage.fromstr(subm)
                    self.clear()
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
        self.needRecovery = False
        self.inRecovery   = False
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

