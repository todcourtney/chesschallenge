import model
import strat
import time
import math

from order import Order
from log import log

from messages import *

from example_models import *

class SimpleChessMoveExecutor(strat.Strategy):
    def __init__(self, name, model):
        super(SimpleChessMoveExecutor, self).__init__(name)
        self.model = model
        self.maxPos = 100

    def onChessMessage(self,m):
        ## pass through to model
        self.model.onChessMessage(m)

        ## decide my bid price and ask price
        fairPrice = self.model.fairPrice()
        if fairPrice is None or math.isnan(fairPrice):
            ordersPending, ordersLive, ordersCanceling = self.gateway.orders()
            for o in ordersLive:
                self.gateway.cancelOrder(m.gameId, o.oid)
            return

        buyPrice  = int(round(fairPrice-2))
        sellPrice = int(round(fairPrice+2))
        log.info("fairPrice = %f buyPrice = %d sellPrice = %d" % (fairPrice, buyPrice, sellPrice))

        ## keep desired quantity showing at indicated price
        desiredQty = 10
        alreadyHaveBuy  = False
        alreadyHaveSell = False
        ordersPending, ordersLive, ordersCanceling = self.gateway.orders()
        if len(ordersPending):
            log.info("already have %d pending orders: %s" % (len(ordersPending), [(o.owner, o.oid) for o in ordersPending]))
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

        if not alreadyHaveBuy  and self.gateway.pos + desiredQty <  self.maxPos: self.gateway.addOrder(m.gameId, desiredQty, Order.BUY , buyPrice)
        if not alreadyHaveSell and self.gateway.pos - desiredQty > -self.maxPos: self.gateway.addOrder(m.gameId, desiredQty, Order.SELL, sellPrice)


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
    if "SCO"  in sys.argv: SCO  = SimpleChessMoveExecutor("SCO", OpeningChessModel("OpeningChessModel"))
    if "SCM"  in sys.argv: SCM  = SimpleChessMoveExecutor("SCM", SimpleMaterialCountChessModel("SimpleMaterialCountChessModel"))
    if "SCS"  in sys.argv: SCS  = SimpleChessMoveExecutor("SCS", StockfishChessModel("StockfishChessModel"))
    if "SIMM" in sys.argv: SIMM = SimpleInventoryMarketMaker("SIMM")
    ##x = SimpleInventoryMarketMaker("SIMM")
    while True:
        time.sleep(1)
        pass
