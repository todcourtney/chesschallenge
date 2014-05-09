##import strat
##from me import Order ## TODO: will want to factor out actual matching engine code
##from ChessBoard import ChessBoard
##
##class SimpleChessModel(strat.Model):
##    def __init__(self):
##        self.chess = ChessBoard()
##
##    def onChessMove(self,move):
##        self.chess.addTextMove(move)
##        values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 1}
##        board = self.chess.getBoard()
##        W,B = 0,0
##        for rank in board:
##            for square in rank:
##                if square != ".":
##                    if square.isupper():
##                        W += values[square]
##                    else:
##                        B += values[square.upper()]
##        self.materialScore = W-B
##
##    def fairProbabilityEstimate(self):
##        p = 0.50 + (self.materialScore*0.01)
##        if p < 0.01: p = 0.01
##        if p > 0.99: p = 0.99
##        return p
##
##class SimpleExecutor(strat.Executor):
##    def __init__(self):
##        self.model = SimpleChessModel()
##        self.liveOrders = []
##
##    def onChessMove(self,move):
##        ## pass through to model
##        self.model.onChessMove(move)
##
##        ## decide my bid price and ask price
##        fairPrice = self.model.fairProbabilityEstimate()*100
##        buyPrice  = round(fairPrice-2)
##        sellPrice = round(fairPrice+2)
##        print "prices: ", fairPrice, buyPrice, sellPrice
##
##        ## keep desired quantity showing at indicated price
##        desiredQty = 10
##        alreadyHaveBuy  = False
##        alreadyHaveSell = False
##        for o in self.liveOrders:
##            if o.side == Order.BUY:
##                if o.price == buyPrice:
##                    alreadyHaveBuy = True
##                    if o.qty < desiredQty:
##                        self.sendOrder(desiredQty-o.qty, Order.BUY, buyPrice)
##                elif o.price > buyPrice:
##                    self.cancelOrder(o.oid)
##            else:
##                if o.price == sellPrice:
##                    alreadyHaveSell = True
##                    if o.qty < desiredQty:
##                        self.sendOrder(desiredQty-o.qty, Order.SELL, sellPrice)
##                elif o.price < sellPrice:
##                    self.cancelOrder(o.oid)
##
##        if not alreadyHaveBuy : self.sendOrder(desiredQty, Order.BUY , buyPrice)
##        if not alreadyHaveSell: self.sendOrder(desiredQty, Order.SELL, sellPrice)

import strat
import time

from order import Order

class SimpleInventoryMarketMaker(strat.Strategy):
    def __init__(self, name):
        super(SimpleInventoryMarketMaker, self).__init__(name)

        self.maxPos = 5
        self.addQty = 1

    def onExchangeMessage(self, exchangeMessage):
        print "onExchangeMessage('%s')" % exchangeMessage
        ## apply to book (note you could check oid, see if it's yours, and not apply if you don't want to see own orders)
        self.book.processMessage(exchangeMessage)

        if hasattr(exchangeMessage, "gameId") and exchangeMessage.gameId is not None:
            self.gameId = exchangeMessage.gameId

        if self.book.needRecovery or self.gameId is None: return

        ## cooldown
        if not hasattr(self, "nextTime"): self.nextTime = time.time() + 3
        if time.time() > self.nextTime:
            self.nextTime = time.time() + 3
        else:
            return

        bid = self.book.bid()
        ask = self.book.ask()

        if bid is None and ask is not None and ask > 0:
            bid = ask-1
        elif ask is None and bid is not None and bid < 100:
            ask = bid+1

        qtyLong  = max(self.gateway.pos,0)
        qtyShort = min(self.gateway.pos,0)

        print " ", bid, ask, qtyLong, qtyShort

        ## move desired price away from inside price as inventory builds up
        bidPrice = bid - qtyLong
        askPrice = ask + qtyShort

        ## check existing orders that haven't been canceled
        restingBuyQty, restingSellQty = 0,0
        levelsAlreadyPresent = set()
        ordersPending, ordersLive, ordersCanceling = self.gateway.orders()
        for o in ordersLive:
            levelsAlreadyPresent.add((o.side, o.price))

            ## orders that we think are too aggressive
            buyTooHigh = (o.side == Order.BUY  and o.price > bidPrice)
            sellTooLow = (o.side == Order.SELL and o.price < askPrice)

            ## clean up some orders that maybe aren't aggressive enough
            buyTooLow   = (o.side == Order.BUY  and o.price < bidPrice-10)
            sellTooHigh = (o.side == Order.SELL and o.price > askPrice+10)

            print "   ", o.oid, o.qty, o.side, o.price, buyTooHigh, sellTooLow, buyTooLow, sellTooHigh
            if buyTooHigh or sellTooLow or buyTooLow or sellTooHigh:
                self.gateway.cancelOrder(self.gameId, o.oid)
            else:
                ## for orders we want to leave, count up the total quantity
                if o.side == Order.BUY:
                    restingBuyQty  += o.qty
                else:
                    restingSellQty += o.qty

        ## also count pending orders
        for o in ordersPending:
            levelsAlreadyPresent.add((o.side, o.price))
            if o.side == Order.BUY:
                restingBuyQty  += o.qty
            else:
                restingSellQty += o.qty

        ## place new orders
        print " ", qtyLong, restingBuyQty, self.addQty, self.maxPos
        if qtyLong + restingBuyQty + self.addQty <= self.maxPos and (Order.BUY, bidPrice) not in levelsAlreadyPresent:
            self.gateway.addOrder(self.gameId, self.addQty, Order.BUY, price=bidPrice)
        print " ", qtyShort, restingSellQty, self.addQty, self.maxPos
        if qtyShort + restingSellQty + self.addQty <= self.maxPos and (Order.SELL, askPrice) not in levelsAlreadyPresent:
            self.gateway.addOrder(self.gameId, self.addQty, Order.BUY, price=bidPrice)

class MeTooMarketMaker(strat.Strategy):
    def onBookUpdateMessage(self, bookUpdateMessage):
        ## parse out whether it's a buy or sell, and the price, and just do it too if it's not already me
        pass

if __name__ == "__main__":
    import sys
    x = SimpleInventoryMarketMaker("SIMM")
    while True:
        time.sleep(1)
        pass
