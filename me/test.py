import gateway
import sys
import socket
import time

host = sys.argv[1]
name = sys.argv[2]
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host, 9999))

print "Starting gateway named", name
g = gateway.Gateway(sock, name)

g.outboundQueue.put(g.name)
while True:
    time.sleep(0.1)
    print "input message: ",
    m = sys.stdin.readline().rstrip()
    if m == "": break
    g.outboundQueue.put(m)

    while not g.inboundQueue.empty():
        print "inbound: ",
        m = g.inboundQueue.get()
        print m

print "EXIT"
