import select
import sys
import socket
import utils

RECV_BUFFER = 200
SOCKET_LIST = [] #for nonblocking use
NEW_CLIENTS = [] #for naming use

class Server(object):
    channels_clients = [[]] #[[channel_name, [socket]], [channel_name1, [socket]]]
    clients = [[]] #[[name, socket, addr],[..,..,..]]

    def __init__(self, address, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((address, int(port)))
        self.socket.listen(5)
    
    def add_client(self, client_socket, client_addr):
        self.clients.append([None, client_socket, client_addr])

    def update_client_name(self, client_name, client_socket):
        for client in self.clients:
            if client[1] == client_socket:
                client[0] = client_name
                return

    def add_channel(self, channel_name, client_socket):
        for reg_channel in self.channels_clients:
            if reg_channel[0] == channel_name:
                raise Exception(utils.SERVER_CHANNEL_EXISTS)
        self.channels_clients.append([channel_name, [client_socket]])
    
    def broadcast_to_channel(self, socket, msg):
        channel_sockets = self.retrive_socket_channel(self, socket)
        for socket in channel_sockets:
            self.socket.send(msg)

    def retrive_socket_channel(self, socket): #return sockets in a channel of current socket
        for channel in self.channels_clients:
            for cur_socket in channel[1]:
                if cur_socket == socket:
                    return channel[1]
        return []

args = sys.argv
if len(args) != 3:
    print("Please supply a server address and port.")
    sys.exit()

server = Server(args[1], args[2])
SOCKET_LIST.append(server.socket)

print("Server running")

while 1:
    ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)
    
    for sock in ready_to_read:
        if sock == server.socket: 
            client, addr = server.socket.accept()
            SOCKET_LIST.append(client)
            NEW_CLIENTS.append(client)
            server.add_client(client, addr)
        #make a way to retrieve name before messages
        else:
            try:
                msg = sock.recv(RECV_BUFFER)
                print(msg)
            except:
                print("errorororor")

server.close()
    