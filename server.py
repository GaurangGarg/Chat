import select
import socket
import sys
from utils import MESSAGE_LENGTH, SERVER_INVALID_CONTROL_MESSAGE, SERVER_NO_CHANNEL_EXISTS, SERVER_JOIN_REQUIRES_ARGUMENT, \
    SERVER_CLIENT_JOINED_CHANNEL, SERVER_CLIENT_LEFT_CHANNEL, SERVER_CHANNEL_EXISTS, SERVER_CREATE_REQUIRES_ARGUMENT, SERVER_CLIENT_NOT_IN_CHANNEL


class Server(object):

    def __init__(self, port):
        self.address = 'localhost'
        self.port = int(port)
        self.server_socket = socket.socket()

        self.channels = {} # dict where key = channel_name, values = list of fd of sockets in that channel
        self.clients = {} # dict where key = fd of socket, value = dict with name of client, channel currently a part of, buffer

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

                    self.SOCKET_LIST.append(new_socket)
                    self.clients[new_socket.fileno()] = {'name': '', 'channel': '', 'buffer': []}

                else:
                    try:
                        data = sock.recv(MESSAGE_LENGTH)
                        if data:
                            msg_length = len(data)
                            output_str = ''
                            if self.clients[sock.fileno()].get('buffer', []):
                                cached_msg = self.clients[sock.fileno()].get('buffer', []).pop()
                                cached_len = len(cached_msg)
                                if cached_len + msg_length > MESSAGE_LENGTH:
                                    output_str = cached_msg + data[:MESSAGE_LENGTH-cached_len]
                                    self.clients[sock.fileno()].get('buffer', []).append(data[MESSAGE_LENGTH-cached_len:])
                                elif cached_len + msg_length == MESSAGE_LENGTH:
                                    output_str = cached_msg + data
                                else:
                                    self.clients[sock.fileno()].get('buffer', []).append(cached_msg + data)
                            else:
                                if msg_length < MESSAGE_LENGTH:
                                    self.clients[sock.fileno()].get('buffer', []).append(data)
                                else:
                                    output_str = data

                            if output_str:
                                output_str = output_str.rstrip()
                                if not self.clients[sock.fileno()].get('name', ''):
                                    self.clients[sock.fileno()]['name'] = output_str
                                else:
                                    name = self.clients.get(sock.fileno(), {}).get('name')
                                    msg_lst = output_str.split(' ')
                                    if msg_lst[0].startswith('/'):
                                        if msg_lst[0].startswith('/join'):
                                            self.join_channel(msg_lst, sock)
                                        elif msg_lst[0].startswith('/create'):
                                            self.create_channel(msg_lst, sock)
                                        elif msg_lst[0].startswith('/list'):
                                            self.list_channel(sock)
                                        else:
                                            self.send(SERVER_INVALID_CONTROL_MESSAGE.format(output_str), sock)
                                    else:
                                        channel = self.clients.get(sock.fileno(), {}).get('channel')
                                        if channel:
                                            self.broadcast("[{}] {}".format(name, output_str), sock, self.channels.get(channel, []))
                                        else:
                                            self.send(SERVER_CLIENT_NOT_IN_CHANNEL, sock)
                        else:
                            self.remove_socket(sock)
                    except Exception as e:
                        self.remove_socket(sock)

        self.server_socket.close()

    def send(self, message, sock):
        try:
            sock.send(message.ljust(MESSAGE_LENGTH))
        except Exception as e:
            self.remove_socket(sock)

    def broadcast(self, message, client_socket, sock_lst=None):
        if sock_lst is not None:
            sock_lst = self.SOCKET_LIST
        for sock in sock_lst:
            if sock != self.server_socket and sock != client_socket:
                self.send(message, sock)

    def remove_socket(self, sock):
        channel = self.clients.get(sock.fileno(), {}).get('channel')
        if channel:
            name = self.clients.get(sock.fileno(), {}).get('name')
            self.channels.get(channel, []).remove(sock)
            self.broadcast(SERVER_CLIENT_LEFT_CHANNEL.format(name), sock, self.channels.get(channel, []))
        self.clients.pop(sock.fileno(), None)
        if sock in self.SOCKET_LIST:
            self.SOCKET_LIST.remove(sock)
        sock.close()

    def join_channel(self, message, sock):
        if len(message) == 2:
            channel = message[1]
            if channel not in self.channels.keys():
                self.send(SERVER_NO_CHANNEL_EXISTS.format(channel), sock)
            else:
                name = self.clients.get(sock.fileno(), {}).get('name', '')
                prev_channel = self.clients.get(sock.fileno(), {}).get('channel', '')
                if prev_channel:
                    self.broadcast(SERVER_CLIENT_LEFT_CHANNEL.format(name), sock, self.channels.get(prev_channel, []))
                    self.channels.get(prev_channel, []).remove(sock)

                self.broadcast(SERVER_CLIENT_JOINED_CHANNEL.format(name), sock, self.channels.get(channel, []))
                self.clients.get(sock.fileno(), {})['channel'] = channel
                self.channels[channel].append(sock)
        else:
            self.send(SERVER_JOIN_REQUIRES_ARGUMENT, sock)

    def create_channel(self, message, sock):
        if len(message) == 2:
            channel = message[1]
            if channel in self.channels.keys():
                self.send(SERVER_CHANNEL_EXISTS.format(channel), sock)
            else:
                name = self.clients.get(sock.fileno(), {}).get('name', '')
                prev_channel = self.clients.get(sock.fileno(), {}).get('channel', '')
                if prev_channel:
                    self.broadcast(SERVER_CLIENT_LEFT_CHANNEL.format(name), sock, self.channels.get(prev_channel, []))
                    self.channels.get(prev_channel, []).remove(sock)

                self.clients.get(sock.fileno(), {})['channel'] = channel
                self.channels[channel] = [sock]
        else:
            self.send(SERVER_CREATE_REQUIRES_ARGUMENT, sock)

    def list_channel(self, sock):
        reply = ''
        for channel in self.channels:
            reply += channel + '\n'
        self.send(reply, sock)


if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        print "Please supply a port."
        sys.exit()
    server = Server(args[1])
