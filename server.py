import select
import socket
import sys
from utils import *


class Server(object):

    def __init__(self, port):
        self.address = 'localhost'
        self.port = int(port)
        self.server_socket = socket.socket()

        self.channels = [] # list of dicts where key = channel_name, values = list of people in that channel
        self.clients = {} # dict where key = client name, value = address/port of client

        self.server_socket.bind((self.address, self.port))
        self.server_socket.listen(5)

        self.SOCKET_LIST = []
        self.SOCKET_LIST.append(self.server_socket)

        while 1:

            ready_to_read, ready_to_write, in_error = select.select(self.SOCKET_LIST, [], []) # omit timeout to prevent high CPU utilization

            for sock in ready_to_read:

                if sock == self.server_socket:
                    # accept connections from outside
                    # new socket is created for server to communicate with client
                    # this frees up server to listen for more connections
                    (new_socket, address) = self.server_socket.accept()
                    client_name = new_socket.recv(200) # message will contain name of client

                    self.SOCKET_LIST.append(new_socket)
                    self.clients[new_socket.fileno()] = client_name
                    self.broadcast(SERVER_CLIENT_JOINED_CHANNEL.format(client_name), new_socket) # notify other users new user joined channel

                else:
                    try:
                        message = sock.recv(200)
                        if message:
                            name = self.clients.get(sock.fileno())
                            self.broadcast(SERVER_CLIENT_MESSAGE.format(name, message), sock)
                            sys.stdout.write(message) # TODO: COMMENT THIS OUT
                        else:
                            self.remove_socket(sock)
                    except Exception as e:
                        self.remove_socket(sock)

        self.server_socket.close()

    def broadcast(self, message, client_socket):
        for sock in self.SOCKET_LIST:
            if sock != self.server_socket and sock != client_socket:
                try:
                    sock.send(message)
                except Exception as e:
                    self.remove_socket(sock)

    def remove_socket(self, sock):
        self.clients.pop(sock.fileno(), None)
        sock.close()
        if sock in self.SOCKET_LIST:
            self.SOCKET_LIST.remove(sock)


if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        print "Please supply a port."
        sys.exit()
    server = Server(args[1])
