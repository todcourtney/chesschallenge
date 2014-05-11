import model
import strat
import time

from order import Order
from log import log

from ChessBoard import ChessBoard
from messages import *

import stockfish

class SimpleMaterialCountChessModel(model.FairPriceModel):
    def __init__(self):
        self.materialScore = 0

    def onChessMessage(self,m):
        log.info(str(m))
        chess = ChessBoard()
        if not isinstance(m, ChessMoveMessage):
            self.materialScore = 0
            return

        for move in m.history:
            chess.addTextMove(move)

        values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 1}
        board = chess.getBoard()
        W,B = 0,0
        for rank in board:
            for square in rank:
                if square != ".":
                    if square.isupper():
                        W += values[square]
                    else:
                        B += values[square.upper()]
        self.materialScore = W-B
        log.info("materialScore = %d" % self.materialScore)

    def fairPrice(self):
        p = 0.50 + (self.materialScore*0.01)
        if p < 0.01: p = 0.01
        if p > 0.99: p = 0.99
        return p*100

class StockfishChessModel(model.FairPriceModel):
    def __init__(self):
        self.stockfish = stockfish.Stockfish()
        self.fp = 50

    def onChessMessage(self,m):
        log.info(str(m))
        chess = ChessBoard()
        if not isinstance(m, ChessMoveMessage):
            self.fp = 50
            return

        algebraicNotationMoves = []
        for move in m.history:
            chess.addTextMove(move)
            algebraicNotationMoves.append(chess.getLastTextMove(ChessBoard.AN))

        stockfishFEN, legalMoves, scores, pctM, pctE1, pctE2, total = self.stockfish.eval(algebraicNotationMoves)

        ## Call:
        ## lm(formula = whiteWins ~ s, data = a, na.action = na.exclude)
        ##
        ## Residuals:
        ##     Min      1Q  Median      3Q     Max
        ## -0.7457 -0.4437 -0.1217  0.4577  0.8783
        ##
        ## Coefficients:
        ##              Estimate Std. Error t value Pr(>|t|)
        ## (Intercept) 0.4337105  0.0012811   338.5   <2e-16 ***
        ## s           0.1247885  0.0008928   139.8   <2e-16 ***
        ## ---
        ## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
        ##
        ## Residual standard error: 0.4669 on 137618 degrees of freedom
        ##   (70 observations deleted due to missingness)
        ## Multiple R-squared:  0.1243,	Adjusted R-squared:  0.1243
        ## F-statistic: 1.953e+04 on 1 and 137618 DF,  p-value: < 2.2e-16

        log.info(scores)
        s = total
        s = min(s,  2.5)
        s = max(s, -2.5)
        self.fp = (0.4337105 + 0.1247885 * s)*100
        self.fp = min(self.fp, 100)
        self.fp = max(self.fp,   0)

    def fairPrice(self):
        return self.fp

class SimpleChessMoveExecutor(strat.Strategy):
    def __init__(self, name):
        super(SimpleChessMoveExecutor, self).__init__(name)
        ##self.model = SimpleMaterialCountChessModel()
        self.model = StockfishChessModel()

    def onChessMessage(self,m):
        ## pass through to model
        self.model.onChessMessage(m)

        ## decide my bid price and ask price
        fairPrice = self.model.fairPrice()
        buyPrice  = round(fairPrice-2)
        sellPrice = round(fairPrice+2)
        log.info("fairPrice = %d buyPrice = %d sellPrice = %d" % (fairPrice, buyPrice, sellPrice))

        ## keep desired quantity showing at indicated price
        desiredQty = 10
        alreadyHaveBuy  = False
        alreadyHaveSell = False
        ordersPending, ordersLive, ordersCanceling = self.gateway.orders()
        if len(ordersPending):
            log.info("already have %d pending orders" % len(ordersPending))
            return

        for o in ordersLive:
            log.info("oid=%d qty=%d side=%d price=%d" % (o.oid, o.qty, o.side, o.price))
            if o.side == Order.BUY:
                if o.price == buyPrice:
                    alreadyHaveBuy = True
                    if o.qty < desiredQty:
                        self.addOrder(m.gameId, desiredQty-o.qty, Order.BUY, buyPrice)
                elif True or o.price > buyPrice:
                    self.gateway.cancelOrder(m.gameId, o.oid)
            else:
                if o.price == sellPrice:
                    alreadyHaveSell = True
                    if o.qty < desiredQty:
                        self.addOrder(m.gameId, desiredQty-o.qty, Order.SELL, sellPrice)
                elif True or o.price < sellPrice:
                    self.gateway.cancelOrder(m.gameId, o.oid)

        if not alreadyHaveBuy : self.gateway.addOrder(m.gameId, desiredQty, Order.BUY , buyPrice)
        if not alreadyHaveSell: self.gateway.addOrder(m.gameId, desiredQty, Order.SELL, sellPrice)


class SimpleInventoryMarketMaker(strat.Strategy):
    def __init__(self, name):
        super(SimpleInventoryMarketMaker, self).__init__(name)

        self.maxPos = 10
        self.addQty = 1
        self.cooldown = 2

    def onExchangeMessage(self, exchangeMessage):
        log.info("onExchangeMessage('%s')" % exchangeMessage)
        ## apply to book (note you could check oid, see if it's yours, and not apply if you don't want to see own orders)
        self.book.processMessage(exchangeMessage)

        if hasattr(exchangeMessage, "gameId") and exchangeMessage.gameId is not None:
            self.gameId = exchangeMessage.gameId

        if self.book.needRecovery or self.gameId is None: return

        ## cooldown
        if not hasattr(self, "nextTime"): self.nextTime = time.time() + self.cooldown
        if time.time() > self.nextTime:
            self.nextTime = time.time() + self.cooldown
        else:
            return

        bid = self.book.bid()
        ask = self.book.ask()

        if bid is None and ask is not None and ask > 0:
            bid = ask-1
        elif ask is None and bid is not None and bid < 100:
            ask = bid+1
        elif bid is None and ask is None:
            return

        qtyLong  =     max(self.gateway.pos,0)
        qtyShort = abs(min(self.gateway.pos,0))

        ## move desired price away from inside price as inventory builds up
        bidPrice = bid - qtyLong
        askPrice = ask + qtyShort

        log.info("ask = %(ask)3d qtyShort = %(qtyShort)3d askPrice = %(askPrice)3d" % locals())
        log.info("bid = %(bid)3d qtyLong  = %(qtyLong)3d bidPrice = %(bidPrice)3d" % locals())

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

            log.info("oid=%d qty=%d side=%d price=%d bad=%d%d%d%d" % (o.oid, o.qty, o.side, o.price, buyTooHigh, sellTooLow, buyTooLow, sellTooHigh))
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
        log.info("qtyLong + restingBuyQty + self.addQty = %d + %d + %d with self.maxPos = %d %s" % (qtyLong, restingBuyQty, self.addQty, self.maxPos, "NEW" if (Order.BUY, bidPrice) not in levelsAlreadyPresent else ""))
        if qtyLong + restingBuyQty + self.addQty <= self.maxPos and (Order.BUY, bidPrice) not in levelsAlreadyPresent:
            self.gateway.addOrder(self.gameId, self.addQty, Order.BUY, price=bidPrice)
        log.info("qtyShort + restingSellQty + self.addQty = %d + %d + %d with self.maxPos = %d %s" % (qtyShort, restingSellQty, self.addQty, self.maxPos, "NEW" if (Order.SELL, askPrice) not in levelsAlreadyPresent else ""))
        if qtyShort + restingSellQty + self.addQty <= self.maxPos and (Order.SELL, askPrice) not in levelsAlreadyPresent:
            self.gateway.addOrder(self.gameId, self.addQty, Order.SELL, price=askPrice)

class MeTooMarketMaker(strat.Strategy):
    def onBookUpdateMessage(self, bookUpdateMessage):
        ## parse out whether it's a buy or sell, and the price, and just do it too if it's not already me
        pass

if __name__ == "__main__":
    import sys
    x = SimpleChessMoveExecutor("SCX")
    ##x = SimpleInventoryMarketMaker("SIMM")
    while True:
        time.sleep(1)
        pass
