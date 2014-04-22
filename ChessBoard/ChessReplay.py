#/usr/bin/env python

## downloader:
## ~/code/chess/games/www.chessgames.com$ for ID in {1500319..1500700}; do echo $ID; test -f $ID || wget -O $ID "http://www.chessgames.com/perl/nph-chesspgn?text=1&gid=$ID"; sleep 1; done

## even better (5M games):
## http://icofy-blog.de/icofy-base/

## bulk play:
## ~/code/chess$ find games/www.chessgames.com/ -maxdepth 1 -type f | sort | xargs -L1 python ChessBoard/ChessReplay.py

## TODO:
##
## double-check that three
##

STOCKFISH = "/home/mschubmehl/code/chess/stockfish-dd-src/src_c11/stockfish"

from ChessBoard import ChessBoard
import sys
import re
import subprocess

def stockfishEval(moves):
    p = subprocess.Popen([STOCKFISH], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p.communicate("position startpos moves " + " ".join(moves) + "\nd\neval\n")
    assert p.returncode == 0
    #print [l for l in out.split("\n") if "Total evaluation:" in l]
    print out

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
    verbose = True #False

    print filename, " ",
    moves, result = loadMovesAndResult(filename)
    if verbose: print moves, result

    chess = ChessBoard()

    textMoves = []
    for turn in moves:
        for i, m in enumerate(turn):
            if verbose: print "WB"[i], ":", m
            assert chess.addTextMove(m), chess.getReason()
            textMoves.append(chess.getLastTextMove(ChessBoard.AN))

            if verbose:
                chess.printBoard()
                print "moves/2 = ", len(textMoves)/2
                #print chess.getFEN(), "\n"
            if chess.isGameOver():
                resultReplay = chess.getGameResult()
                print "GAME OVER resultReplay =", resultReplay,
            else:
                stockfishEval(textMoves)

    print result

#this calls the 'main' function when this script is executed
if __name__ == '__main__': main()
