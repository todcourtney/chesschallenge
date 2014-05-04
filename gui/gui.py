import curses
import time
import random
import socket, struct
import sys

import book, feed, pnl
from ChessBoard import ChessBoard
chess = ChessBoard()

b = book.FeedBook()
prevSeq = None
drops = 0

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', feed.Feed.MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(feed.Feed.MCAST_GRP), socket.INADDR_ANY)

sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

stdscr = curses.initscr()

curses.noecho()
curses.cbreak()
curses.curs_set(0)
stdscr.keypad(1)

gameId = ""
chessResult=""
messages = []

p = pnl.Pnl(sys.argv[1])

try:
    ladderPad = curses.newpad(105, 70)
    boardPad  = curses.newpad(15, 25)
    logPad    = curses.newpad(20, 52)
    pnlPad    = curses.newpad(20, 72)

    stdscr.addstr("Chess Trading GUI")
    stdscr.refresh()

    while True:
        m = sock.recv(feed.Feed.MAX_SIZE)
        messages.append(m)
        seq, m = m.split(" ", 1)
        seq = int(seq)

        drop = prevSeq is not None and (seq > prevSeq+1)
        drops += drop
        stdscr.addstr(0,40, "Drops: %d needRecovery: %s" % (drops, b.needRecovery))

        stdscr.addstr(38,0, "Feed Messages:")
        logPad.addstr(0,0, "\n".join("%-50s" % msg[:50] for msg in messages[-20:]))
        messages = messages[-20:] ## discard old
        logPad.refresh(0,0, 40,0, 60,52)

        stdscr.addstr(38,55, "Pnl Events:")
        with p.lock:
            pnlPad.addstr(0,0, "\n".join("%-70s" % str(e)[:70] for e in p.events[-20:]))
        pnlPad.refresh(0,0, 40,55, 60,55+72)

        stdscr.refresh()


        if m.startswith("N") or drop:
            if m.startswith("N"):
                header, gameId = m.split(",")
            b = book.FeedBook()
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

