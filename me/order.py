import order

class Order:
    BUY  =  1
    SELL = -1

    def __init__(self, oid, qty, side, price, owner=None, gameId=None):
        assert side in (Order.BUY, Order.SELL)
        self.oid    = oid
        self.qty    = qty
        self.side   = side
        self.price  = price
        self.owner  = owner
        self.gameId = gameId

    def __str__(self):
        return str(self.qty)

