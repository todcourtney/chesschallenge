import curses
import time
import random
import socket, struct

import book, feed
from ChessBoard import ChessBoard
chess = ChessBoard()

b = book.FeedBook()

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
        stdscr.addstr(0,40, m)
        seq, m = m.split(" ", 1)

        if m.startswith("N"):
            chess = ChessBoard()
            b = book.FeedBook()
        elif m.startswith("M"):
            header, move = m.split(",")
            chess.addTextMove(move)
        elif m.startswith("XA"):
            header, oid, qty, side, price = m.split(",")
            o = book.Order(int(oid), int(qty), int(side), int(price))
            b.addOrder(o)
        elif m.startswith("XC"):
            header, oid, qty, side, price = m.split(",")
            b.removeOrder(int(oid))
        elif m.startswith("XT"):
            header, oid, qty, side, price = m.split(",")
            b.applyTrade(int(oid), int(qty))
        else:
            stdscr.addstr(1,0,"UNKNOWN MESSAGE")
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

        boardPad.addstr(0,0,chess.prettyBoardString())
        boardPad.refresh(0,0, 5,5, 5+15,5+25)

finally:
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()

