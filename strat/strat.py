##from me import Order ## factor out
##import socket
##
##class MarketListener:
##    def onMarketActivity(self,book,trade):
##        pass
##
##class ChessListener:
##    def onChessMove(self,move):
##        pass
##
##    def onResult(self,move):
##        pass
##
##class Model(MarketListener, ChessListener):
##    def fairProbabilityEstimate(self):
##        pass
##
##class Executor(MarketListener, ChessListener):
##    def onOrderUpdate(self,update):
##        pass
##
##    def sendOrder(self,qty,side,price):
##        data = "A,%d,%s,%d\n" % (qty, "B" if side == Order.BUY else "S", price)
##        print data
##        HOST, PORT = "localhost", 9999
##        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##        try:
##            sock.connect((HOST, PORT))
##            sock.sendall(data)
##        finally:
##            sock.close()
##
##    def cancelOrder(self,oid):
##        pass

## TODO: how to interleave gateway and feed traffic to avoid multithreading issues

class Strategy(gateway.Listener, feed.Listener):
    def __init__(self, name):
        self.gateway = Gateway(name, self) ## TODO: will need to move socket creation inside, and sending of initial identification message
        self.feed    = Feed(self) ## TODO: rename existing Feed to FeedPublisher, handle multicast setup in constructor, handle drops
        self.book    = Book() ## TODO: rename Book -> MatchingEngineBook
        self.board   = ChessBoard()

    def onGatewayMessage(self, message):
        pass

    def onFeedMessage(self, message):
        """
        Get feed message, decide whether it is a book update or a chess message,
        and pass to the appropriate callback.
        """
        if isinstance(message, BookUpdateMessage):
            self.onBookUpdateMessage(message)
        elif isinstance(message, ChessUpdateMessage):
            self.onChessUpdateMessage(message)

    def onChessUpdateMessage(self, chessUpdateMessage):
        pass

    def onBookUpdateMessage(self, bookUpdateMessage):
        pass
