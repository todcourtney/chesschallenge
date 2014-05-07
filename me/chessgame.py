class ChessMessage:
    pass

class ChessNewGameMessage(ChessMessage):
    code = "CN"
    def __init__(self, gameId):
        self.gameId  = gameId

    @classmethod
    def fromstr(cls, s):
        msgType, gameId = s.split(",")
        assert msgType == cls.code
        return cls(gameId)

    def __str__(self):
        return "%s,%s" % (self.code, self.gameId)

class ChessMoveMessage(ChessMessage):
    code = "CM"
    def __init__(self, gameId, move, history):
        self.gameId  = gameId
        self.move    = move
        self.history = history

    @classmethod
    def fromstr(cls, s):
        msgType, gameId, move, history = s.split(",")
        assert msgType == cls.code
        history = history.split(" ")
        return cls(gameId, move, history)

    def __str__(self):
        return "%s,%s,%s,%s" % (self.code, self.gameId, self.move, " ".join(self.history))


class ChessResultMessage(ChessMessage):
    code = "CR"
    def __init__(self, gameId, result):
        self.gameId  = gameId
        self.result  = result

    def whiteWins(self):
        return self.result == "1-0"

    @classmethod
    def fromstr(cls, s):
        msgType, gameId, result = s.split(",")
        assert msgType == cls.code
        return cls(gameId, result)

    def __str__(self):
        return "%s,%s,%s" % (self.code, self.gameId, self.result)


class ChessGame:
    def __init__(self, gameId, moves, result):
        self.gameId = str(gameId)
        self.moves  = moves
        self.result = result

    def newMessage(self):
        return ChessNewGameMessage(self.gameId)

    def moveMessage(self, i):
        return ChessMoveMessage(self.gameId, self.moves[i], self.moves[:(i+1)])

    def resultMessage(self):
        return ChessResultMessage(self.gameId, self.result)

