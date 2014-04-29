import socket
import sys
import time

HOST, PORT = "localhost", 9999
data = " ".join(sys.argv[1:])

for i in xrange(10):
    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((HOST, PORT))
        # Connect to server and send data
        sock.sendall(data + str(i) + "\n")
    
        # Receive data from the server and shut down
        received = sock.recv(1024)
        print "Sent:     {}".format(data)
        print "Received: {}".format(received)
    finally:
        sock.close()
    ##time.sleep(1)
