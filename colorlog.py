import logging
import threading
import time

class ColorThread(logging.Formatter):
    def __init__(self, msg):
        logging.Formatter.__init__(self, msg)

    def format(self, record):
        t = threading.current_thread()
        if t.name == "a": color = 31
        elif t.name == "b": color = 32
        else: color = 30
        return "\033[1;%dm" % color + t.name + "\033[0m" + ": " + logging.Formatter.format(self, record)


def printList():
    for i in xrange(10):
        logging.getLogger("test").info(str(i))
        if threading.current_thread().name == "a" and i == 5:
            raise RuntimeError("uh oh")
        time.sleep(1)

ct = ColorThread("%(asctime)s %(levelname)s %(name)s %(message)s")

logger = logging.getLogger("test")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setFormatter(ct)
logger.addHandler(ch)

a = threading.Thread(target=printList, name="a")
a.daemon = True
b = threading.Thread(target=printList, name="b")
b.daemon = True

a.start()
b.start()



while True:
    logger.info("waiting...")
    time.sleep(1)
