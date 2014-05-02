class Order:
    BUY  =  1
    SELL = -1

    def __init__(self, oid, qty, side, price):
        assert side in (Order.BUY, Order.SELL)
        self.oid    = oid
        self.qty    = qty
        self.side   = side
        self.price  = price

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
                if ro.qty <= o.qty:
                    events.append(("eTradeOrder", ro.oid, ro.qty, ro.price))
                    o.qty  -= ro.qty
                    ro.qty  = 0
                    del l.orders[0]
                else:
                    events.append(("eTradeOrder", ro.oid,  o.qty, ro.price))
                    ro.qty -= o.qty
                    o.qty   = 0
            else:
                break ## prices don't cross

        ## (2) add this order to the book
        if o.qty > 0:
            (self.bids if o.side == Order.BUY else self.asks)[o.price].orders.append(o)
            events.append(("eAddOrder", o.oid, o.qty, o.side, o.price))

        return events

    def removeOrder(self, o):
        events = []
        restingOrders = (self.bids if o.side == Order.BUY else self.asks)[o.price].orders
        for ro in restingOrders:
            if ro.oid == o.oid:
                events.append(("eCancelOrder", ro.oid, ro.qty, ro.side, ro.price))
                restingOrders.remove(ro)
                break
        assert len(events) ## for now TODO: cancel rejects
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

