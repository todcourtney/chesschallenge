import gateway, feed, book
import ChessBoard
from messages import *

class Strategy(object, gateway.Listener, feed.Listener):
    def __init__(self, name):
        self.gateway = gateway.Gateway(name=name, thread=True, listeners=[self])
        self.feed    = feed.Feed(send=False, receive=True, thread=True, listeners=[self])
        self.book    = book.Book()
        self.board   = ChessBoard.ChessBoard()
        self.gameId  = None

    def onGatewayMessage(self, gateway, message):
        print "Strategy.onGatewayMessage('%s')" % message
        pass

    def onFeedMessage(self, rawMessage, seq, drop, message):
        """
        Get feed message, decide whether it is a book update or a chess message,
        and pass to the appropriate callback.
        """

        print rawMessage
        if isinstance(message, ExchangeMessage) or (isinstance(message, str) and message.startswith("B")):
            print "  => ExchangeMessage: ", message
            self.onExchangeMessage(message)
        elif isinstance(message, ChessMessage):
            self.onChessMessage(message)

    def onChessMessage(self, chessMessage):
        print "Strategy.onChessMessage('%s')" % chessMessage
        pass

    def onExchangeMessage(self, exchangeMessage):
        print "Strategy.onExchangeMessage('%s')" % exchangeMessage
        pass
