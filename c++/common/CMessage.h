#ifndef __CMESSAGE_H__
#define __CMESSAGE_H__

#include <COrder.h>
#include <cstddef>
#include <string>
#include <vector>

class ExchangeMessage
{
public:
  // Methods for C++ strategy classes.

  enum Type {
    EXCHANGE_UNKNOWN = 0,
    EXCHANGE_NEW_GAME,
    EXCHANGE_ADD_ORDER,
    EXCHANGE_CANCEL_ORDER,
    EXCHANGE_TRADE };

  Type type() const;
  const COrder& order() const;

private:
  Type type_;
  COrder order_;

public:
  // Methods for python controller.
  ExchangeMessage();
  ExchangeMessage(const std::string& type, COrder order);
};

class ChessMessage
{
public:
  // Methods for C++ strategy class.
  
  enum Type {
    CHESS_UNKNOWN = 0,
    CHESS_NEW_GAME,
    CHESS_MOVE,
    CHESS_RESULT };

  Type type() const;
  const std::string& gameid() const;

  // The move just played.
  const std::string& move() const;

  // A history of all moves, including the current move.
  // You can tell if white or black just moved by whether
  // the history vector has an odd or even length.
  const std::vector<std::string>& history() const;

private:
  Type type_;
  std::string gameid_;
  std::string move_;
  std::vector<std::string> history_;
  std::string result_;

public:
  // Methods for python controller.
  ChessMessage();
  ChessMessage(
    const std::string& type,
    const std::string& gid,
    const std::string& move,
    const std::vector<std::string>& history,
    const std::string& result);
};

#endif
