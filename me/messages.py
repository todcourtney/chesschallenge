import re
from order import Order

class ExchangeMessage:
    def __init__(self, gameId, oid, qty, side, price):
        assert hasattr(self,'code'), "you cannot instantiate ExchangeMessage directly"
        self.gameId = gameId
        self.oid    = oid
        self.qty    = qty
        self.side   = side
        self.price  = price

    @classmethod
    def fromstr(cls, s):
        code, gameId, oid, qty, side, price = s.split(",")
        assert code == cls.code
        oid    = int(oid)
        qty    = int(qty)
        side   = {"B":Order.BUY,"S":Order.SELL}[side]
        price  = int(price)
        return cls(gameId, oid, qty, side, price)

    def __str__(self):
        return "%s,%s,%d,%d,%s,%d" % (self.code, self.gameId, self.oid, self.qty, {Order.BUY:"B",Order.SELL:"S"}[self.side], self.price)

class ExchangeAddOrderMessage(ExchangeMessage):
    code = "XA"

class ExchangeCancelOrderMessage(ExchangeMessage):
    code = "XC"

class ExchangeTradeMessage(ExchangeMessage):
    code = "XT"




class GatewayMessage:
    def __init__(self):
        raise NotImplementedError("cannot instantiate GatewayMessage base class")

    @classmethod
    def fromstr(cls, s):
        code, rest = s.split(",", 1)
        if   code ==              LoginMessage.code: return              LoginMessage.fromstr(s)
        elif code == GatewaySubmitOrderMessage.code: return GatewaySubmitOrderMessage.fromstr(s)
        elif code == GatewayCancelOrderMessage.code: return GatewayCancelOrderMessage.fromstr(s)
        elif code ==    GatewayAddOrderMessage.code: return    GatewayAddOrderMessage.fromstr(s)
        elif code == GatewayDeleteOrderMessage.code: return GatewayDeleteOrderMessage.fromstr(s)
        elif code ==       GatewayTradeMessage.code: return       GatewayTradeMessage.fromstr(s)
        elif code ==      GatewaySettleMessage.code: return      GatewaySettleMessage.fromstr(s)
        elif code ==      GatewayRejectMessage.code: return      GatewayRejectMessage.fromstr(s)
        else:
            raise ValueError("no message type has code '%s'" % s)

class GatewaySubmitOrderMessage(GatewayMessage):
    code = "GS"
    def __init__(self, gameId, goid, qty, side, price):
        self.gameId = gameId
        self.goid   = goid
        self.qty    = qty
        self.side   = side
        self.price  = price

    @classmethod
    def fromstr(cls, s):
        add, gameId, goid, qty, side, price = s.split(",")
        assert add == cls.code
        goid   = int(goid)
        qty    = int(qty)
        side   = {"B":Order.BUY,"S":Order.SELL}[side]
        price  = int(price)
        return cls(gameId, goid, qty, side, price)

    def __str__(self):
        return "%s,%s,%d,%d,%s,%d" % (GatewaySubmitOrderMessage.code, self.gameId, self.goid, self.qty, {Order.BUY:"B",Order.SELL:"S"}[self.side], self.price)

class GatewayCancelOrderMessage(GatewayMessage):
    code = "GC"
    def __init__(self, oid):
        self.oid = oid

    @classmethod
    def fromstr(cls, s):
        cancel, oid = s.split(",")
        assert cancel == cls.code
        oid = int(oid)
        return cls(oid)

    def __str__(self):
        return "%s,%d" % (GatewayCancelOrderMessage.code, self.oid)

class LoginMessage(GatewayMessage):
    code = "GN"
    def __init__(self, name):
        assert re.match("^[0-9A-Za-z]{3,8}$", name), "names must consist of between 3 and 8 characters from [0-9A-Za-z], not '%s'" % name
        self.name = name

    @classmethod
    def fromstr(cls, s):
        login, name = s.split(",")
        assert login == cls.code
        return cls(name)

    def __str__(self):
        return "%s,%s" % (LoginMessage.code, self.name)

class GatewayResponseMessage(GatewayMessage):
    def __init__(self, owner, gameId, goid, oid, qty, side, price):
        assert hasattr(self,'code'), "you cannot instantiate GatewayResponseMessage directly"
        self.owner  = owner
        self.gameId = gameId
        self.goid   = goid
        self.oid    = oid
        self.qty    = qty
        self.side   = side
        self.price  = price

    @classmethod
    def fromstr(cls, s):
        code, owner, gameId, goid, oid, qty, side, price = s.split(",")
        assert code == cls.code
        goid   = int(goid)
        oid    = int(oid)
        qty    = int(qty)
        side   = {"B":Order.BUY,"S":Order.SELL}[side]
        price  = int(price)
        return cls(owner, gameId, goid, oid, qty, side, price)

    def __str__(self):
        return "%s,%s,%s,%d,%d,%d,%s,%d" % (self.code, self.owner, self.gameId, self.goid, self.oid, self.qty, {Order.BUY:"B",Order.SELL:"S"}[self.side], self.price)

class GatewayAddOrderMessage(GatewayResponseMessage):
    code = "GA"

class GatewayDeleteOrderMessage(GatewayResponseMessage):
    code = "GD"

class GatewayTradeMessage(GatewayResponseMessage):
    code = "GT"

class GatewaySettleMessage(GatewayResponseMessage):
    code = "GX"
    def __init__(self, gameId, price):
        self.gameId = gameId
        self.price  = price

    @classmethod
    def fromstr(cls, s):
        code, gameId, price = s.split(",")
        assert code == cls.code
        price  = int(price)
        return cls(gameId, price)

    def __str__(self):
        return "%s,%s,%d" % (self.code, self.gameId, self.price)

class GatewayRejectMessage(GatewayResponseMessage):
    code = "GR"
    def __init__(self, owner, gameId, goid, reason=""):
        self.owner  = owner
        self.gameId = gameId
        self.goid   = goid
        self.reason = reason

    @classmethod
    def fromstr(cls, s):
        code, owner, gameId, goid, reason = s.split(",")
        assert code == cls.code
        goid = int(goid)
        return cls(owner, gameId, goid, reason)

    def __str__(self):
        return "%s,%s,%s,%d,%s" % (self.code, self.owner, self.gameId, self.goid, self.reason)
