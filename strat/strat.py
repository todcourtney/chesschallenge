

class MarketListener:
    def onMarketActivity(self,book,trade):
        pass

class ChessListener:
    def onChessMove(self,move):
        pass

    def onResult(self,move):
        pass

class Model(MarketListener, ChessListener):
    def fairProbabilityEstimate(self):
        pass

class Executor(MarketListener, ChessListener):
    def onOrderUpdate(self,update):
        pass

    def sendOrder(self,qty,side,price):
        pass









