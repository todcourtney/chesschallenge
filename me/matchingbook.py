import time

from order import Order
from book import PriceLevel

from messages import *
from log import log

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

