import curses
import time
import random
import socket, struct

import book, feed
from ChessBoard import ChessBoard
chess = ChessBoard()

b = book.FeedBook()
needRecovery = True
inRecovery = False
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
stdscr.keypad(1)

try:
    ladderPad = curses.newpad(105, 70)
    boardPad  = curses.newpad(15, 25)

    stdscr.addstr("Chess Trading GUI")
    stdscr.refresh()

    while True:
        m = sock.recv(feed.Feed.MAX_SIZE)
        seq, m = m.split(" ", 1)
        seq = int(seq)

        drop = prevSeq is not None and (seq > prevSeq+1)
        drops += drop
        stdscr.addstr(0,40, "Drops: %d needRecovery: %s" % (drops, needRecovery))
        stdscr.refresh()

        if m.startswith("N") or drop:
            b = book.FeedBook()
            needRecovery = False
            inRecovery = False
            chessResult = ""
        elif m.startswith("M"):
            header, move, history = m.split(",")
            chess = ChessBoard()
            for h in history.split(" "):
                chess.addTextMove(h)
            chessResult = ""
        elif m.startswith("R"):
            header, chessResult = m.split(",")
        elif m == "BS":
            if needRecovery:
                inRecovery = True
        elif m.startswith("BR"):
            if needRecovery and inRecovery:
                header, recoveryMessages = m.split(",",1)
                for msg in recoveryMessages.split(";"):
                    header, oid, qty, side, price = msg.split(",")
                    o = book.Order(int(oid), int(qty), int(side), int(price))
                    b.addOrder(o)
        elif m == "BE":
            if needRecovery and inRecovery:
                needRecovery = False
                inRecovery = False
        elif m.startswith("XA"):
            if not needRecovery:
                header, oid, qty, side, price = m.split(",")
                o = book.Order(int(oid), int(qty), int(side), int(price))
                b.addOrder(o)
        elif m.startswith("XC"):
            if not needRecovery:
                header, oid, qty, side, price = m.split(",")
                b.removeOrder(int(oid))
        elif m.startswith("XT"):
            if not needRecovery:
                header, oid, qty, side, price = m.split(",")
                b.applyTrade(int(oid), int(qty))
        else:
            stdscr.addstr(1,0,"UNKNOWN MESSAGE: '%s'" % m)
            stdscr.refresh()
            time.sleep(5)

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

        boardPad.addstr(1,5,chessResult)
        boardPad.addstr(1,0,chess.prettyBoardString())
        boardPad.refresh(0,0, 5,5, 5+15,5+25)

        prevSeq = seq

finally:
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()

