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

    boardPad.addstr(chess.prettyBoardString())
    boardPad.refresh(0,0, 5,45, 35,75)

    ask = 5
    
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

        # now get input
        c = stdscr.getch()
        if c == ord('q'):
            break

finally:
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()

