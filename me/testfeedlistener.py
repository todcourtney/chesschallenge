import feed

f = feed.Feed(send=False, receive=True)
while True:
  msg, seq, drop, m = f.recv()
  print "%08d %1s: %s" % (seq, "*" if drop else " ", m)
