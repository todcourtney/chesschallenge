import curses
import time
import random
import sys

import book, feed ##, pnl
from ChessBoard import ChessBoard

import logging
from log import log
log.setLevel(logging.CRITICAL)

prettyBoard = True
if prettyBoard:
    try:
        import pygame
        import inspect, os
        chessboardDirectory = os.path.dirname(inspect.getfile(ChessBoard))

        pygame.init()
        pygameScreen = pygame.display.set_mode((480, 480),1)
        pygame.display.set_caption('')

        # load all images
        pieces = [{},{}]
        pieces[0]["r"] = pygame.image.load(chessboardDirectory + "/img/brw.png")
        pieces[0]["n"] = pygame.image.load(chessboardDirectory + "/img/bnw.png")
        pieces[0]["b"] = pygame.image.load(chessboardDirectory + "/img/bbw.png")
        pieces[0]["k"] = pygame.image.load(chessboardDirectory + "/img/bkw.png")
        pieces[0]["q"] = pygame.image.load(chessboardDirectory + "/img/bqw.png")
        pieces[0]["p"] = pygame.image.load(chessboardDirectory + "/img/bpw.png")
        pieces[0]["R"] = pygame.image.load(chessboardDirectory + "/img/wrw.png")
        pieces[0]["N"] = pygame.image.load(chessboardDirectory + "/img/wnw.png")
        pieces[0]["B"] = pygame.image.load(chessboardDirectory + "/img/wbw.png")
        pieces[0]["K"] = pygame.image.load(chessboardDirectory + "/img/wkw.png")
        pieces[0]["Q"] = pygame.image.load(chessboardDirectory + "/img/wqw.png")
        pieces[0]["P"] = pygame.image.load(chessboardDirectory + "/img/wpw.png")
        pieces[0]["."] = pygame.image.load(chessboardDirectory + "/img/w.png")
        pieces[1]["r"] = pygame.image.load(chessboardDirectory + "/img/brb.png")
        pieces[1]["n"] = pygame.image.load(chessboardDirectory + "/img/bnb.png")
        pieces[1]["b"] = pygame.image.load(chessboardDirectory + "/img/bbb.png")
        pieces[1]["k"] = pygame.image.load(chessboardDirectory + "/img/bkb.png")
        pieces[1]["q"] = pygame.image.load(chessboardDirectory + "/img/bqb.png")
        pieces[1]["p"] = pygame.image.load(chessboardDirectory + "/img/bpb.png")
        pieces[1]["R"] = pygame.image.load(chessboardDirectory + "/img/wrb.png")
        pieces[1]["N"] = pygame.image.load(chessboardDirectory + "/img/wnb.png")
        pieces[1]["B"] = pygame.image.load(chessboardDirectory + "/img/wbb.png")
        pieces[1]["K"] = pygame.image.load(chessboardDirectory + "/img/wkb.png")
        pieces[1]["Q"] = pygame.image.load(chessboardDirectory + "/img/wqb.png")
        pieces[1]["P"] = pygame.image.load(chessboardDirectory + "/img/wpb.png")
        pieces[1]["."] = pygame.image.load(chessboardDirectory + "/img/b.png")
    except ImportError:
        prettyBoard = False

def drawPrettyBoard(board):
    for y, rank in enumerate(board):
        for x, p in enumerate(rank):
            pygameScreen.blit(pieces[(x+y)%2][p],(x*60,y*60))
    pygame.display.flip()

chess = ChessBoard()

b = book.Book()
prevSeq = None
drops = 0

f = feed.Feed()

##p = pnl.Pnl(sys.argv[1])

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
    ##pnlPad    = curses.newpad(20, 72)

    stdscr.addstr("Chess Trading GUI")
    stdscr.refresh()

    move = ""
    while True:
        msg, seq, drop, m = f.recv()
        messages.append(msg)
        drops += drop

        stdscr.addstr(0,40, "Drops: %d needRecovery: %-5s" % (drops, b.needRecovery))

        stdscr.addstr(38,0, "Feed Messages:")
        logPad.addstr(0,0, "\n".join("%-50s" % msg[:50] for msg in messages[-20:]))
        messages = messages[-20:] ## discard old
        logPad.refresh(0,0, 40,0, 60,52)

        ##pnlPad.addstr(0,0, pnl.leaderboardFromSummary(p.getPnl()))
        ##pnlPad.refresh(0,0, 40,55, 60,55+72)

        stdscr.refresh()

        if m.startswith("CN") or drop:
            if m.startswith("CN"):
                header, gameId = m.split(",")
            b = book.Book()
            chessResult = ""
        elif m.startswith("CM"):
            header, gameId, move, history = m.split(",")
            chess = ChessBoard()
            for h in history.split(" "):
                chess.addTextMove(h)
            chessResult = ""
        elif m.startswith("CR"):
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

        if prettyBoard:
            drawPrettyBoard(chess.getBoard())
            pygame.display.set_caption('%s %s %s' % (gameId, move, chessResult))

        prevSeq = seq

finally:
    curses.curs_set(2)
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()
    if prettyBoard: pygame.quit()
