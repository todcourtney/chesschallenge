import curses
import time
import random

from ChessBoard import ChessBoard
chess = ChessBoard()

stdscr = curses.initscr()

curses.noecho()
curses.cbreak()
stdscr.keypad(1)

try:
    ladderPad = curses.newpad(100, 100)
    boardPad  = curses.newpad(30, 30)

    stdscr.addstr("Pretty text\nSecond line")
    stdscr.refresh()

    ask = 5

    moves = "e4 c5 Nf3 e6 d4 cxd4 Nxd4 a6 Bd3 Nf6 O-O Qc7 Qe2 d6 c4 g6 Nc3 Bg7 Nf3 O-O Bf4 Nc6 Rac1 e5 Bg5 h6 Be3 Bg4 Nd5 Qd8 h3 Nxd5 cxd5 Nd4 Bxd4 Bxf3 Qxf3 exd4 Rc4 Rc8 Rfc1 Rxc4 Rxc4 h5 Qd1 Be5 Qc1 Qf6 Rc7 Rb8 a4 Kg7 b4 h4 Kf1 Bf4 Qd1 Qd8 Rc4 Rc8 a5 Rxc4 Bxc4 Qf6 Be2 Be5 Bf3 Qd8 Qc2 b6 axb6 Qxb6 Qc4 d3".split()
    
    while True:
        ask = random.randrange(max(ask-1,1), min(ask+1,9)+1)
        for row,prc in enumerate(reversed(xrange(10+1))):
            bidqty = random.randrange(1,50) if prc <  ask else ""
            askqty = random.randrange(1,50) if prc >= ask else ""
            try:
                ladderPad.addstr(row,10,"%10s %02d %-10s" % (bidqty, int(prc), askqty))
            except curses.error:
                pass
            
        #  Displays a section of the pad in the middle of the screen
        ladderPad.refresh(0,0, 5,5, 20,40)

        boardPad.addstr(0,0,chess.prettyBoardString())
        boardPad.refresh(0,0, 5,45, 35,75)

        # now get input
        c = stdscr.getch()
        if c == ord('q'):
            break

        if len(moves):
            m = moves.pop(0)
            chess.addTextMove(m)

finally:
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()

