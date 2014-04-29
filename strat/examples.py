import strat
from ChessBoard import ChessBoard

class SimpleChessModel(strat.Model):
    def __init__(self):
        self.chess = ChessBoard()

    def onChessMove(self,move):
        self.chess.addTextMove(move)
        values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 1}
        board = self.chess.getBoard()
        W,B = 0,0
        for rank in board:
            for square in rank:
                if square != ".":
                    if square.isupper():
                        W += values[square]
                    else:
                        B += values[square.upper()]
        self.materialScore = W-B

    def fairProbabilityEstimate(self):
        p = 0.50 + (self.materialScore*0.01)
        if p < 0.01: p = 0.01
        if p > 0.99: p = 0.99
        return p
