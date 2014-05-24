#include <COrder.h>

unsigned COrder::gameid() const
{
  return gameid_;
}

unsigned COrder::orderid() const
{
  return orderid_;
}

unsigned COrder::price() const
{
  return price_;
}

unsigned COrder::quantity() const
{
  return quantity_;
}

int COrder::side() const
{
  return side_;
}

COrder::COrder()
{
  gameid_ = 0;
  orderid_ = 0;
  price_ = 0;
  quantity_ = 0;
  side_ = BUY;
}

COrder::COrder(unsigned gid, unsigned oid, unsigned price, unsigned qty, int side)
{
  gameid_ = gid;
  orderid_ = oid;
  price_ = price;
  quantity_ = qty;
  side_ = side;
}
