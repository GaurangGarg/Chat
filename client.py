import socket
import sys
import select
from utils import *


class Client(object):

    def __init__(self, name, address, port):
        self.name = name
        self.address = address
        self.port = int(port)
        self.socket = socket.socket()

        try:
            self.socket.connect((self.address, self.port))
        except Exception as e:
            print CLIENT_CANNOT_CONNECT.format(self.address, self.port)
            sys.exit()

        self.socket.send(self.name)
        self.FD_LIST = [self.socket, sys.stdin]

        sys.stdout.write('[Me] ')
        sys.stdout.flush()

        while 1:

            ready_to_read, ready_to_write, in_error = select.select(self.FD_LIST, [], [])

            for fd in ready_to_read:
                if fd == self.socket:
                    data = self.socket.recv(200)
                    if not data:
                        sys.stdout.write(CLIENT_WIPE_ME)
                        sys.stdout.write('\r' + CLIENT_SERVER_DISCONNECTED.format(self.address, self.port) + '\n')
                        sys.exit()
                    else:
                        data = data.strip('\n')
                        sys.stdout.write(CLIENT_WIPE_ME)
                        sys.stdout.write('\r'+data+'\n')
                        sys.stdout.write('[Me] ')
                        sys.stdout.flush()
                else:
                    message = sys.stdin.readline()
                    self.socket.send(message)
                    sys.stdout.write('[Me] ')
                    sys.stdout.flush()


if __name__ == "__main__":
    args = sys.argv
    if len(args) != 4:
        print "Please supply a name, server address, and port."
        sys.exit()
    client = Client(args[1], args[2], args[3])
