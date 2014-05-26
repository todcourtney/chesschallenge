import sys
#sys.path.insert(0, "../common")
#sys.path.insert(0, "../ChessBoard")
#sys.path.insert(0, "../c++/swig/")

import model
import strat
import stockfish
import time
import math

from order import Order
from log import log
from ChessBoard import ChessBoard

from messages import *

from cstrat import *

class CStrategyWrapper(strat.Strategy):
  def __init__(self, name, cname):
    super(CStrategyWrapper, self).__init__(name)
    self.strategy = CFactory.makeStrategy(cname)
    self.stockfish = stockfish.Stockfish()

  def onChessMessage(self,m):
    self.syncGateway()
    self.syncBoard(m)
    self.syncStockfish(m)
    cm = self.makeChessMessage(m)
    self.strategy.onChessMessage(cm)
    self.commitOrders()

  def onExchangeMessage(self,m):
    self.syncGateway()
    self.syncBook(m)
    if not isinstance(m, ExchangeMessage):
      return
    em = self.makeExchangeMessage(m)
    self.strategy.onExchangeMessage(em)
    self.commitOrders()

  def makeOrderVector(self, orders):
    ovec = vector_o()
    for o in orders:
      gameid = o.gameId if o.gameId else ""
      corder = COrder(gameid, int(o.oid), int(o.price), int(o.qty), int(o.side))
      ovec.push_back(corder)
    return ovec

  def syncGateway(self):
    gw = self.strategy.gateway()
    gw.reset()

    gw.setPosition(self.gateway.pos)

    ordersPending, ordersLive, ordersCanceling = self.gateway.orders()
    gw.setOrdersPending(self.makeOrderVector(ordersPending))
    gw.setOrdersLive(self.makeOrderVector(ordersLive))
    gw.setOrdersCanceling(self.makeOrderVector(ordersCanceling))

  def syncBook(self, m):
    self.book.processMessage(m)
    cbook = self.strategy.book()
    cbook.reset()
    for i in xrange(0,CBook.MAX_LEVELS):
      bidLevel = self.book.bidLevel(i)
      askLevel = self.book.askLevel(i)
      if bidLevel:
        qty = 0
        for o in bidLevel.orders: qty += o.qty
        numo = len(bidLevel.orders)
        cbook.setBid(i, bidLevel.price, qty, numo)
      if askLevel:
        qty = 0
        for o in askLevel.orders: qty += o.qty
        numo = len(askLevel.orders)
        cbook.setAsk(i, askLevel.price, qty, numo)

  def syncBoard(self, m):
    if not isinstance(m, ChessMoveMessage):
      return

    chess = ChessBoard()
    if isinstance(m, ChessMoveMessage):
      for move in m.history:
        chess.addTextMove(move)

    board = chess.getBoard()
    cboard = self.strategy.board()

    for row,rank in enumerate(board):
      for col,square in enumerate(rank):
        cboard.setPiece(row, col, square)

  def syncStockfish(self, m):
    if not isinstance(m, ChessMoveMessage) or not self.stockfish:
      return

    chess = ChessBoard()
    algebraicNotationMoves = []
    for move in m.history:
      chess.addTextMove(move)
      algebraicNotationMoves.append(chess.getLastTextMove(ChessBoard.AN))

    fen, legalMoves, scores, pctM, pctE1, pctE2, total = self.stockfish.eval(algebraicNotationMoves)

    sf = self.strategy.stockfish()
    sf.reset()
    sf.setFEN(fen)
    sf.setLegalMoves(legalMoves)
    sf.setTotal(pctM, pctE1, pctE2, total)

    for scoreType, scoreList in scores.iteritems():
      for scoreSubtype, score in scoreList.iteritems():
        if not math.isnan(score):
          sf.setScore(scoreType, scoreSubtype, score)

  def makeChessMessage(self, m):
    if isinstance(m, ChessNewGameMessage):
      cm = ChessMessage(m.code, m.gameId, "", vector_s(), "")
    elif isinstance(m, ChessMoveMessage):
      history = vector_s()
      for h in m.history:
        history.push_back(h)
      cm = ChessMessage(m.code, m.gameId, m.move, history, "")
    elif isinstance(m, ChessResultMessage):
      cm = ChessMessage(m.code, m.gameId, "", vector_s(), m.result)
    return cm

  def makeExchangeMessage(self, m):
    if isinstance(m, ExchangeBookMessage):
      order = COrder(m.gameId, int(m.oid), int(m.price), int(m.qty), int(m.side()))
    else:
      order = COrder(m.gameId, 0, 0, 0, COrder.BUY);
    em = ExchangeMessage(m.code, order)
    return em

  def commitOrders(self):
    gw = self.strategy.gateway()
    addOrderVec = gw.outboundAdds()
    cancelOrderVec = gw.outboundCancels()
    for o in addOrderVec:
      self.gateway.addOrder(o.gameid(), o.quantity(), o.side(), o.price())
    for o in cancelOrderVec:
      self.gateway.cancelOrder(o.gameid(), o.orderid())

if __name__ == "__main__":
  x = CStrategyWrapper("CSW", "MaterialCountStrategy")
  while True:
    time.sleep(1)
    pass
