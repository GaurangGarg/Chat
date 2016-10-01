import socket
import sys


class BasicServer(object):

    def __init__(self, port):
        self.address = 'localhost'
        self.port = int(port)
        self.socket = socket.socket()

        self.socket.bind((self.address, self.port))
        self.socket.listen(5)

        while 1:
            # accept connections from outside
            # new socket is created for server to communicate with client
            # this frees up server to listen for more connections
            (new_socket, address) = self.socket.accept()
            message = new_socket.recv(1024)
            print message

args = sys.argv
if len(args) != 2:
    print "Please supply a port."
    sys.exit()
server = BasicServer(args[1])