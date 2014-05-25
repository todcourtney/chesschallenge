#ifndef __CSTRATEGY_H__
#define __CSTRATEGY_H__

#include <CMessage.h>
#include <CGateway.h>
#include <CBook.h>
#include <CBoard.h>

class CStrategy
{
public:
  // Callbacks to be implemented by subclasses.
  virtual void onExchangeMessage(const ExchangeMessage& em) = 0;
  virtual void onChessMessage(const ChessMessage& cm) = 0;

  // Methods for C++ strategy classes.
  CGateway& gateway();
  const CGateway& gateway() const;
  const CBook& book() const;
  const CBoard& board() const;

private:
  CGateway gateway_;
  CBook book_;
  CBoard board_;
  // TODO: board
  // TODO: stockfish

public:
  // Accessors for python controller.
  CStrategy() {}
  virtual ~CStrategy() {}
  CBook& book();
  CBoard& board();
};

#endif