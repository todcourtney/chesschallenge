import os
import csv
import threading
import time
import locale
locale.setlocale(locale.LC_ALL, "")

from log import log

class PnlEvents:
    def __init__(self, filename):
        self.events = []

        ## recover from old file
        if os.path.isfile(filename):
            log.info("Reading PnlEvents from file %s" % filename)
            self.f = open(filename, 'r+', 1)
            self.events = [tuple(e) for e in csv.reader(self.f, delimiter=",")]        
            ##print "PnlEvents:", self.events
        else:
            self.f = open(filename, 'w', 1)

        self.writer = csv.writer(self.f, delimiter=",", quoting=csv.QUOTE_MINIMAL)

    def append(self, newEvent):
        self.events.append(newEvent)
        self.writer.writerow(newEvent)

    def extend(self, moreEvents):
        self.events.extend(moreEvents)
        for e in moreEvents:
            self.writer.writerow(e)

    def __str__(self):
        return str(self.events)

class Pnl:
    def __init__(self, filename):
        self.events = []
        self.lock = threading.Lock()
        self.filename = filename
        self.thread = threading.Thread(target=self.keepEventsUpToDate, name="PNL")
        self.thread.daemon = True
        self.thread.start()

    def keepEventsUpToDate(self):
        f = None
        while True:
            if f is None and os.path.isfile(self.filename):
                f = open(self.filename, 'r')

            if f is not None:
                where = f.tell()
                line = f.readline()
                if not line:
                    f.seek(where)
                    time.sleep(0.1)
                else:
                    with self.lock:
                        self.events.append(tuple(line.rstrip().split(",")))
            else:
                time.sleep(1)

    def doSettlement(self, pos, cash, price):
        for owner in pos:
            sqty = -pos[owner]
            if sqty != 0:
                pos [owner] += sqty
                cash[owner] -= sqty*price

    def getPnl(self):
        pos  = dict()
        vol  = dict()
        cash = dict()
        pnl  = dict()

        mark = None
        prevGameId = None
        with self.lock:
            for e in self.events:
                gameId = e[1]
                if gameId != prevGameId:
                    if mark is not None:
                        self.doSettlement(pos, cash, mark) ## settle to mark if we didn't see a settle (mid-game matching engine failure)
                    assert all(p == 0 for p in pos.values()), "at transition from gameId = %s to %s, some positions are not zero" % (prevGameId, gameId)
                    mark = None
                    prevGameId = gameId

                tm = float(e[2])

                if e[0] == "M":
                    mark = float(e[7])
                elif e[0] == "T":
                    owner = e[3]
                    qty   =   int(e[5])
                    side  =   int(e[6])
                    price = float(e[7])
                    pos [owner] = pos .get(owner,0) + qty*side
                    cash[owner] = cash.get(owner,0) - qty*side*price
                    vol [owner] = vol .get(owner,0) + qty
                elif e[0] == "S":
                    price = float(e[7])
                    self.doSettlement(pos, cash, price)

                for owner in pos:
                    mv = 0 if pos[owner] == 0 else pos[owner]*mark
                    if owner not in pnl: pnl[owner] = []
                    pnl[owner].append((gameId,tm,vol[owner],cash[owner]+mv,cash[owner],mv,pos[owner],mark))

        return pnl

def leaderboardFromSummary(pnls):
    lines = []
    for o, r in pnls.iteritems():
        lastLine = r[-1]
        gameId,tm,vol,pnl,cash,mv,pos,mark = lastLine
        pnlIfWhiteWins  = cash + pos*100
        pnlIfWhiteLoses = cash
        o = o[:20]
        pnlStr             = locale.format("%10d", pnl            , grouping=True)
        pnlIfWhiteWinsStr  = locale.format("%10d", pnlIfWhiteWins , grouping=True)
        pnlIfWhiteLosesStr = locale.format("%10d", pnlIfWhiteLoses, grouping=True)
        lines.append((pnl, "%(pnlStr)11s %(o)-10s %(vol)10d %(pnlIfWhiteWinsStr)11s %(pnlIfWhiteLosesStr)11s " % locals()))
    header = "%11s %-10s %10s %11s %11s" % ("pnl", "owner", "volume", "pnl(win)", "pnl(lose)")
    lines = sorted(lines, key = lambda x: -x[0])
    return "\n".join([header] + [l[1] for l in lines])

## for testing
if __name__ == "__main__":
    p = Pnl("pnl.csv")
    while True:
        time.sleep(2)
        z = p.getPnl()
        for k,v in z.iteritems():
            log.info(k)
            for r in v:
                log.info("  " + r)

        log.info(leaderboardFromSummary(z))
