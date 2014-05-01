import socket
import sys
import time

HOST, PORT = "localhost", 9999

# Create a socket (SOCK_STREAM means a TCP socket)
while True:
    print "Message: ",
    data = sys.stdin.readline()

    try:
        # Connect to server and send data
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        sock.sendall(data + "\n")
        print "Sent: ", data
    finally:
        sock.close()
    time.sleep(1)
