import gateway, feed

class Strategy(gateway.Listener, feed.Listener):
    def __init__(self, name):
        self.gateway = Gateway(name=name, thread=True, listeners=[self])
        self.feed    = Feed(send=False, receive=True, thread=True, listeners=[self])
        self.book    = Book()
        self.board   = ChessBoard()

    def onGatewayMessage(self, message):
        pass

    def onFeedMessage(self, rawMessage, seq, drop, message):
        """
        Get feed message, decide whether it is a book update or a chess message,
        and pass to the appropriate callback.
        """
        if isinstance(message, ExchangeMessage):
            self.onExchangeMessage(message)
        elif isinstance(message, ChessMessage):
            self.onChessMessage(message)

    def onChessMessage(self, chessMessage):
        pass

    def onExchangeMessage(self, exchangeMessage):
        pass
