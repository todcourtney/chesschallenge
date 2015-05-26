from messages import *

class ChessGame:
    def __init__(self, gameId, moves, result):
        self.gameId = str(gameId)
        self.moves  = moves
        self.result = result

    @classmethod
    def fromstr(cls, l):
        srcfile, line, result, moves = l.split(",")
        gameId = "%s:%s" % (srcfile, line)
        moves = moves.rstrip().split(" ")

        return cls(gameId, moves, result)

    def newMessage(self):
        return ChessNewGameMessage(self.gameId)

    def moveMessage(self, i):
        return ChessMoveMessage(self.gameId, self.moves[i], self.moves[:(i+1)])

    def resultMessage(self):
        return ChessResultMessage(self.gameId, self.result)

