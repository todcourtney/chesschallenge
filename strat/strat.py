from me import Order ## factor out
import socket

class MarketListener:
    def onMarketActivity(self,book,trade):
        pass

class ChessListener:
    def onChessMove(self,move):
        pass

    def onResult(self,move):
        pass

class Model(MarketListener, ChessListener):
    def fairProbabilityEstimate(self):
        pass

class Executor(MarketListener, ChessListener):
    def onOrderUpdate(self,update):
        pass

    def sendOrder(self,qty,side,price):
        data = "A,%d,%s,%d\n" % (qty, "B" if side == Order.BUY else "S", price)
        print data
        HOST, PORT = "localhost", 9999
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((HOST, PORT))
            sock.sendall(data)
        finally:
            sock.close()

    def cancelOrder(self,oid):
        pass

