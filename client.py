import socket
import sys
import select


class Client(object):

    def __init__(self, name, address, port):
        self.name = name
        self.address = address
        self.port = int(port)
        self.socket = socket.socket()
        # connect to server
        # send name to server
        self.socket.connect((self.address, self.port))
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
                        sys.exit()
                    else:
                        sys.stdout.write(data)
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
