#ifndef __CORDER_H__
#define __CORDER_H__

class COrder
{
public:
  // Methods for C++ strategy classes.

  // Order field accessors.
  unsigned gameid() const;
  unsigned orderid() const;
  unsigned price() const;
  unsigned quantity() const;
  int side() const;

  static const int BUY  =  1;
  static const int SELL = -1;

private:
  unsigned gameid_;
  unsigned orderid_;
  unsigned price_;
  unsigned quantity_;
  int side_;

public:
  // Methods for python controller.
  COrder();
  COrder(unsigned gid, unsigned oid, unsigned price, unsigned qty, int side);
};

#endif
