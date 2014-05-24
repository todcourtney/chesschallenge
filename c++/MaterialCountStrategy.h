#ifndef __MATERIAL_COUNT_STRATEGY_H__
#define __MATERIAL_COUNT_STRATEGY_H__

#include <CStrategy.h>
#include <map>

class MaterialCountStrategy : public CStrategy
{
public:
  MaterialCountStrategy();
  virtual ~MaterialCountStrategy();

  void onExchangeMessage(const ExchangeMessage& em);
  void onChessMessage(const ChessMessage& cm);

private:
  void cancelAllOrders();
  unsigned computeFairPrice() const;
  int getScore(char piece) const;
  unsigned getPrice(int score) const;

  const unsigned maxPosition_;
  const unsigned maxOrderQuantity_;
};

#endif
