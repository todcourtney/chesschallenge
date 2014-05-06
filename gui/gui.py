import curses
import time
import random
import sys

import book, feed, pnl
from ChessBoard import ChessBoard
chess = ChessBoard()

b = book.Book()
prevSeq = None
drops = 0

f = feed.Feed(send=False, receive=True)

p = pnl.Pnl(sys.argv[1])

stdscr = curses.initscr()

curses.noecho()
curses.cbreak()
curses.curs_set(0)
stdscr.keypad(1)

gameId = ""
chessResult=""
messages = []

try:
    ladderPad = curses.newpad(105, 70)
    boardPad  = curses.newpad(15, 25)
    logPad    = curses.newpad(20, 52)
    pnlPad    = curses.newpad(20, 72)

    stdscr.addstr("Chess Trading GUI")
    stdscr.refresh()

    while True:
        msg, seq, drop, m = f.recv()
        messages.append(msg)
        drops += drop

        stdscr.addstr(0,40, "Drops: %d needRecovery: %-5s" % (drops, b.needRecovery))

        stdscr.addstr(38,0, "Feed Messages:")
        logPad.addstr(0,0, "\n".join("%-50s" % msg[:50] for msg in messages[-20:]))
        messages = messages[-20:] ## discard old
        logPad.refresh(0,0, 40,0, 60,52)

        pnlPad.addstr(0,0, pnl.leaderboardFromSummary(p.getPnl()))
        pnlPad.refresh(0,0, 40,55, 60,55+72)

        stdscr.refresh()

        if m.startswith("N") or drop:
            if m.startswith("N"):
                header, gameId = m.split(",")
            b = book.Book()
            chessResult = ""
        elif m.startswith("M"):
            header, gameId, move, history = m.split(",")
            chess = ChessBoard()
            for h in history.split(" "):
                chess.addTextMove(h)
            chessResult = ""
        elif m.startswith("R"):
            header, gameId, chessResult = m.split(",")
        else:
            ## all other messages are to update the book
            b.processMessage(m)

        bid = b.bid()
        ask = b.ask()
        if ask is None and bid is None:
            center = 50
        elif ask is None:
            center = bid
        elif bid is None:
            center = ask
        else:
            center = int((bid+ask)/2.0)

        ladderPad.addstr(0,0,str(b))

        #  Displays a section of the pad in the middle of the screen
        H = 20
        ladderPad.refresh(100-center-H/2,0, 5,5+5+25, 5+H,5+5+25+70)

        boardPad.addstr(0,3,"%-10s"%chessResult)
        boardPad.addstr(1,0,chess.prettyBoardString())
        boardPad.refresh(0,0, 5,5, 5+15,5+25)

        stdscr.addstr(1,0,"Game ID: %s" % gameId)
        stdscr.refresh()
        prevSeq = seq

finally:
    curses.curs_set(2)
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()

