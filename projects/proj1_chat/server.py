import select
import sys
import socket
import utils
import threading
import re

RECV_BUFFER = 200
SOCKET_LIST = [] #for nonblocking use

class Server(object):
    channels = []
    clients = [] #[[channel, socket, addr]]

    def __init__(self, address, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((address, int(port)))
        self.socket.listen(5)
    
    def add_client(self, client_socket, client_addr):
        self.clients.append([None, client_socket, client_addr])

    def add_channel(self, channel_name, client_socket):
        for reg_channel in self.channels:
            if reg_channel.get_channel_name() == channel_name:
                raise Exception(utils.SERVER_CHANNEL_EXISTS)
        self.channels.append(Channel(channel_name, client_socket))
    
    def broadcast_to_channel(self, socket, msg):
        try:
            channel_users = self.retrive_socket_channel(socket)
            for user in channel_users:
                if user == socket:
                    continue
                self.socket.send(msg)
        except Exception as e:
            socket.send(str(e))
 
    def retrive_socket_channel(self, socket): #return sockets in a channel of current socket
        for client in self.clients:
            if client and client[1] == socket:
                if client[0] == None:
                    raise Exception(utils.SERVER_CLIENT_NOT_IN_CHANNEL)
                else:
                    return client[0].get_users()
    
    def process_input_data(self, data):
        data1 = self.trim_name(data)
        if re.search("^/", data1):
            return True, data1
        return False, data

    def process_command(self, client, data):
        command = (re.search("^/\w* ", data)).casefold()
        print("command is "+command)

        if command == "/list":
            client.send("\n".join(self.get_channel_list()))
        elif command == "/create":
            1
        elif command == "/join":
            1
        else:
            raise Exception(utils.SERVER_INVALID_CONTROL_MESSAGE.format())

    def trim_name(self, data):
        return (re.sub("^\[\w*\]","",data,1)).strip()

    def get_channel_list(self):
        channel_list = []
        for channel in self.channels:
            channel_list.append(channel.get_channel_name())
        return channel_list
    
class Channel(object):
    users = []

    def __init__(self, name, user):
        self.name = name
        self.users.append(user)
    
    def add_user(self, user):
        self.users.append(user)

    def remove_user(self, user):
        self.users.remove(user)
    
    def get_channel_name(self):
        return self.name
    
    def get_users(self):
        return self.users

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
            server.add_client(client, addr)

        else:
            try:
                data = sock.recv(RECV_BUFFER) # do as if recieving beyond 200 bytes consider name is included, buffer the msg. i.e. name+msg
                #trim header and recieve all data before continue
                print(data)
                #check message is command or data; assuming header is removed
                iscommand, proc_data = server.process_input_data(data)
                if iscommand:
                    server.process_command(sock, proc_data)
                else:
                    server.broadcast_to_channel(sock, proc_data)
            except Exception as e:
                SOCKET_LIST.remove(sock)
                print(e)
                sock.close()

server.close()
    