import strat
from me import Order ## TODO: will want to factor out actual matching engine code
from ChessBoard import ChessBoard

class SimpleChessModel(strat.Model):
    def __init__(self):
        self.chess = ChessBoard()

    def onChessMove(self,move):
        self.chess.addTextMove(move)
        values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 1}
        board = self.chess.getBoard()
        W,B = 0,0
        for rank in board:
            for square in rank:
                if square != ".":
                    if square.isupper():
                        W += values[square]
                    else:
                        B += values[square.upper()]
        self.materialScore = W-B

    def fairProbabilityEstimate(self):
        p = 0.50 + (self.materialScore*0.01)
        if p < 0.01: p = 0.01
        if p > 0.99: p = 0.99
        return p

class SimpleExecutor(strat.Executor):
    def __init__(self):
        self.model = SimpleChessModel()
        self.liveOrders = []

    def onChessMove(self,move):
        ## pass through to model
        self.model.onChessMove(move)

        ## decide my bid price and ask price
        fairPrice = self.model.fairProbabilityEstimate()*100
        buyPrice  = round(fairPrice-2)
        sellPrice = round(fairPrice+2)
        print "prices: ", fairPrice, buyPrice, sellPrice

        ## keep desired quantity showing at indicated price
        desiredQty = 10
        alreadyHaveBuy  = False
        alreadyHaveSell = False
        for o in self.liveOrders:
            if o.side == Order.BUY:
                if o.price == buyPrice:
                    alreadyHaveBuy = True
                    if o.qty < desiredQty:
                        self.sendOrder(desiredQty-o.qty, Order.BUY, buyPrice)
                elif o.price > buyPrice:
                    self.cancelOrder(o.oid)
            else:
                if o.price == sellPrice:
                    alreadyHaveSell = True
                    if o.qty < desiredQty:
                        self.sendOrder(desiredQty-o.qty, Order.SELL, sellPrice)
                elif o.price < sellPrice:
                    self.cancelOrder(o.oid)

        if not alreadyHaveBuy : self.sendOrder(desiredQty, Order.BUY , buyPrice)
        if not alreadyHaveSell: self.sendOrder(desiredQty, Order.SELL, sellPrice)

if __name__ == "__main__":
    import sys
    x = SimpleExecutor()
    while True:
        print "Move: ",
        move = sys.stdin.readline().rstrip()
        x.onChessMove(move)
