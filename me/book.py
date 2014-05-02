class Order:
    BUY  =  1
    SELL = -1

    def __init__(self, oid, qty, side, price, owner=None):
        assert side in (Order.BUY, Order.SELL)
        self.oid    = oid
        self.qty    = qty
        self.side   = side
        self.price  = price
        self.owner  = owner

    def __str__(self):
        return str(self.qty)

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
        events = []

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
                    events += self.cancelOrder(ro.oid, owner=o.owner)
                    continue

                ## know we don't have a self-match at this point
                if ro.qty <= o.qty:
                    events.append(("XT", ro.oid, ro.qty, ro.side, ro.price))
                    o.qty  -= ro.qty
                    ro.qty  = 0
                    del l.orders[0]
                else:
                    events.append(("XT", ro.oid,  o.qty, ro.price))
                    ro.qty -= o.qty
                    o.qty   = 0
            else:
                break ## prices don't cross

        ## (2) add this order to the book
        if o.qty > 0:
            L = (self.bids if o.side == Order.BUY else self.asks)[o.price]
            L.orders.append(o)
            events.append(("XA", o.oid, o.qty, o.side, o.price))

            ## track for easy cancels later
            self.oidToPriceLevel[o.oid] = L

        return events

    def cancelOrder(self, oid, owner=None):
        events = []
        if oid in self.oidToPriceLevel:
            restingOrders = self.oidToPriceLevel[oid].orders
            for ro in restingOrders:
                if ro.oid == oid:
                    if owner is None or ro.owner == owner:
                        events.append(("XC", ro.oid, ro.qty, ro.side, ro.price))
                        restingOrders.remove(ro)
                        del self.oidToPriceLevel[oid]
                        break
                    else:
                        pass ## should send cancel reject for trying to cancel other owner's order
        ## TODO: cancel rejects if order is not found (for now silently ignore)
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

class FeedBook:
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
        L = (self.bids if o.side == Order.BUY else self.asks)[o.price]
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
        restingOrders = self.oidToPriceLevel[oid].orders
        for ro in restingOrders:
            if ro.oid == t.oid:
                assert t.qty <= ro.qty
                if t.qty == ro.qty:
                    self.removeOrder(t.oid)
                else:
                    ro.qty -= t.qty
                break

    def __str__(self):
        bs = [str(l) for l in self.bids]
        ss = [str(l) for l in self.asks]
        W = 30
        fmt = "%%%ds %%03d %%-%ds" % (W, W)
        s = ""
        for i in reversed(xrange(self.N)):
            s += fmt % (bs[i][:W], self.prices[i], ss[i][:W]) + "\n"
        return s

