import socket
import struct

import feed

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', feed.Feed.MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(feed.Feed.MCAST_GRP), socket.INADDR_ANY)

sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

prev=-1
while True:
  m = sock.recv(feed.Feed.MAX_SIZE)
  seq, m = m.split(" ", 1)
  seq = int(seq)
  print "%08d %1s: %s" % (seq, "*" if seq != prev+1 else " ", m)
  prev = seq
