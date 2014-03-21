#/usr/bin/env python

from ChessBoard import ChessBoard
import sys
import re

def loadMovesAndResult(filename):
    with open(filename, 'r') as f:
        lines = [l.strip() for l in f.readlines() if "[" not in l and l.strip() != ""]
    
    movesline = (" ".join(lines))
    moves = re.sub("([0-9]+\\.) *", "\n\\1", movesline).lstrip()

    moves = [m.strip().split(".") for m in moves.split("\n")]
    n = len(moves)

    turnNumbers = [int(m[0]) for m in moves]
    assert turnNumbers == range(1,n+1)

    moves = [m[1].split(" ") for m in moves]

    assert len(moves[n-1]) in [2,3] ## black may not have moved, and result should be last
    result = moves[n-1][-1]
    assert result in ["1-0", "0-1", "1/2-1/2"]
    moves[n-1] = moves[n-1][:-1]

    assert all(len(m) in [1,2] for m in moves)

    return moves, result

def main():
    assert len(sys.argv) == 2
    filename = sys.argv[1]
    verbose = True

    print filename, " ",
    moves, result = loadMovesAndResult(filename)
    if verbose: print moves, result

    chess = ChessBoard()

    for turn in moves:
        for i, m in enumerate(turn):
            if verbose: print "WB"[i], ":", m
            assert chess.addTextMove(m), chess.getReason()

            if verbose: chess.printBoard()

    print result

#this calls the 'main' function when this script is executed
if __name__ == '__main__': main()
