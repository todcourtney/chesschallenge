import gateway, feed

class Strategy(gateway.Listener, feed.Listener):
    def __init__(self, name):
        self.gateway = Gateway(name=name, listeners=[self])
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
            self.onBookUpdateMessage(message)
        elif isinstance(message, ChessMessage):
            self.onChessUpdateMessage(message)

    def onChessUpdateMessage(self, chessUpdateMessage):
        pass

    def onBookUpdateMessage(self, bookUpdateMessage):
        pass
