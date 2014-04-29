import socket
import sys
import time

HOST, PORT = "localhost", 9999
data = " ".join(sys.argv[1:])

# Create a socket (SOCK_STREAM means a TCP socket)
for i in xrange(10):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))

        # Connect to server and send data
        sock.sendall(data + str(i) + "\n")
        print "Sent:     {}".format(data)
    finally:
        sock.close()
    time.sleep(1)
