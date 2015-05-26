#include "MaterialCountStrategy.h"
#include <cctype>

MaterialCountStrategy::MaterialCountStrategy()
  : maxPosition_(100)
  , maxOrderQuantity_(10)
{
  // nothing
}

MaterialCountStrategy::~MaterialCountStrategy()
{
  // nothing
}

void MaterialCountStrategy::onExchangeMessage(const CExchangeMessage& em)
{
  // This strategy does nothing with exchange messages.
}

void MaterialCountStrategy::onChessMessage(const CChessMessage& cm)
{
  // If unknown message type, do nothing.
  if (cm.type() == CChessMessage::CHESS_UNKNOWN)
    return;

  // If not move (is new game or result) cancel all outstanding orders.
  if (cm.type() != CChessMessage::CHESS_MOVE) {
    cancelAllOrders();
    return;
  }

  // Otherwise we have a chess move.

  // If pending orders, do nothing.
  CGateway& gw = this->gateway();
  if (gw.ordersPending().size() > 0)
    return;

  // No pending orders. Let's compute a fair price.
  unsigned fairPrice = computeFairPrice();

  // We want to market make 2 ticks around fair price.
  unsigned buyPrice = std::max(fairPrice - 2, (unsigned)1);
  unsigned sellPrice = std::min(fairPrice + 2, (unsigned)99);

  const std::vector<COrder> ordersLive = gw.ordersLive();
  unsigned position = gw.position();

  unsigned activeBuyQuantity = 0;
  unsigned activeSellQuantity = 0;

  // Cancel live orders at wrong prices.
  // Record active quanity at desired prices.
  for (size_t i=0; i < ordersLive.size(); ++i) {
    const COrder& o = ordersLive[i];
    if (o.side() == COrder::BUY && o.price() == buyPrice)
      activeBuyQuantity += o.quantity();
    else if (o.side() == COrder::SELL && o.price() == sellPrice)
      activeSellQuantity += o.quantity();
    else
      gw.cancelOrder(cm.gameid(), o.orderid());
  }

  // Buy and sell subject to maxOrderQuantity_ and maxPosition_ constraints.
  int buyQuantity = maxOrderQuantity_ - activeBuyQuantity;
  int sellQuantity = maxOrderQuantity_ - activeSellQuantity;
  if (buyQuantity > 0 && position + buyQuantity <= maxPosition_)
    gw.addOrder(cm.gameid(), buyPrice, buyQuantity, COrder::BUY);
  if (sellQuantity > 0 && position - sellQuantity >= -maxPosition_)
    gw.addOrder(cm.gameid(), sellPrice, sellQuantity, COrder::SELL);
}

void MaterialCountStrategy::cancelAllOrders()
{
  // Cancel all outstanding orders. First get the
  // list of live orders from the gateway, then
  // tell the gateway to cancel each of them.
  CGateway& gw = this->gateway();
  const std::vector<COrder> ordersLive = gw.ordersLive();
  for (size_t i=0; i < ordersLive.size(); ++i) {
    const COrder order = ordersLive[i];
    gw.cancelOrder(order.gameid(), order.orderid());
  }
}

unsigned MaterialCountStrategy::computeFairPrice() const
{
  // We define the fair price as the difference
  // between the white score and the black score, then
  // scale the result.

  int whiteScore = 0;
  int blackScore = 0;

  const CBoard& board = this->board();
  for (unsigned r = 0; r < CHESS_BOARD_DIM; ++r) {
    for (unsigned c = 0; c < CHESS_BOARD_DIM; ++c) {
      char piece = board.getPiece(r, c);
      int score = getScore(piece);
      if (isupper(piece))
        whiteScore += score;
      else
        blackScore += score;
    }
  }

  int score = whiteScore - blackScore;
  unsigned price = getPrice(score);
  return price;
}

int MaterialCountStrategy::getScore(char piece) const
{
  // We asssign some reasonable looking weights to each piece.
  char p = tolower(piece);
  switch (p) {
    case 'p': return 1;
    case 'n': return 3;
    case 'b': return 3;
    case 'r': return 5;
    case 'q': return 9;
    case 'k': return 1;
    default:  return 0;
  }
}

unsigned MaterialCountStrategy::getPrice(int score) const
{
  // Scale the score to a price between 1 and 99.
  double price = 0.50 + (score*0.01);
  if (price < 0.01) price = 0.01;
  if (price > 0.99) price = 0.99;
  return price * 100;
}

