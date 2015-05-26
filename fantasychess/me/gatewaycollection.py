import time
import Queue
import threading
import socket
from gateway import Gateway
from log import log

class GatewayCollection:
    def __init__(self):
        self.lock = threading.Lock()
        self.gateways = dict()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', Gateway.PORT))
        self.socket.listen(20)

        self.thread = threading.Thread(target=self.acceptGatewayConnections, name="GWAccept")
        self.thread.daemon = True
        self.thread.start()

    def acceptGatewayConnections(self):
        while True:
            log.info("accept" + str(self.socket))
            (clientsocket, address) = self.socket.accept()
            log.info("%s:%s" % (clientsocket, address))
            ##clientsocket.setblocking(0)
            with self.lock:
                ## first, prune dead gateways
                for s in self.gateways.keys():
                    g = self.gateways[s]
                    if g.messenger is None:
                        log.info("deleting disconnected gateway '%s'" % g.name)
                        del self.gateways[s]
                self.gateways[clientsocket] = Gateway(sock=clientsocket)
            time.sleep(1)

    ## either gets an incoming gateway message, or None if there is nothing to get
    def getIncomingMessage(self):
        with self.lock:
            for g in self.gateways.values(): ## TODO: shuffle for fairness
                if not g.inboundQueue.empty():
                    return g.inboundQueue.get(), g
        return None, None

    def sendToOwner(self, m):
        owner = m.owner
        with self.lock:
            for g in self.gateways.values(): ## TODO: randomize?
                if g.name == owner and g.messenger is not None:
                    g.send(m)

