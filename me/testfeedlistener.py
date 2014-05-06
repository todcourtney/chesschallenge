import feed
import time

useThread = True

class FeedPrinter(feed.Listener):
  def onFeedMessage(self, rawMessage, seq, drop, message):
    print "%08d %1s: %s" % (seq, "*" if drop else " ", message)

if useThread:
  L = FeedPrinter()
  f = feed.Feed(send=False, receive=True, thread=True, listeners=[L])
  while True:
    time.sleep(1)
else:  
  f = feed.Feed(send=False, receive=True)
  while True:
    msg, seq, drop, m = f.recv()
    print "%08d %1s: %s" % (seq, "*" if drop else " ", m)
