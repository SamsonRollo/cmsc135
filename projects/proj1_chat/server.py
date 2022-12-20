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
    
    def add_client(self, client_socket, client_addr, channel=None):
        self.clients.append([channel, client_socket, client_addr])

    def add_channel(self, channel_name, client_socket):
        for reg_channel in self.channels:

            if reg_channel.get_channel_name() == channel_name:
                raise Exception(utils.SERVER_CHANNEL_EXISTS)
                
        new_channel = Channel(channel_name, client_socket)
        self.channels.append(new_channel)
        self.update_client_channel(client_socket, new_channel)

    def join_channel_aux(self, channel_name, client_socket):
        for reg_channel in self.channels:

            if reg_channel.get_channel_name() == channel_name:
                self.update_client_channel(client_socket, reg_channel)
                return

        raise Exception(utils.SERVER_NO_CHANNEL_EXISTS.format(channel_name, channel_name))
    
    def update_client_channel(self, client, new_channel):
        for cur_client in self.clients:

            if cur_client[1] == client:
                old_channel = cur_client[0]
                cur_client[0] = new_channel
                new_channel.add_user(client)
                self.broadcast_to_channel(client, utils.SERVER_CLIENT_JOINED_CHANNEL, new_channel)

                if old_channel != None:
                    old_channel.remove_user(client)
                    self.broadcast_to_channel(client, utils.SERVER_CLIENT_LEFT_CHANNEL, old_channel)

    def broadcast_to_channel(self, socket, msg, channel):
        try:
            if channel:
                channel_users = channel.get_users()
            else:               
                channel_users = self.retrive_socket_channel(socket)

            for user in channel_users:
                if user == socket:
                    continue
                self.send_to_client(user, msg)

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
        command = re.findall("^/\w* ", data+" ")

        if command:
            command = (command[0].lower()).strip()
        try:
            if command == "/list":
                print("list")
                self.send_channel_list(client)

            elif command == "/create":
                print("create")
                self.create_channel(client, data)

            elif command == "/join":
                print("join")
                self.join_channel(client, data)

            else:
                self.invalid_command(command)
        
        except Exception as e:
            self.send_to_client(client, str(e))

    def invalid_command(self, command):
        raise Exception(utils.SERVER_INVALID_CONTROL_MESSAGE.format(command))

    def create_channel(self, client, data):
        channel_name = data.split()

        if len(channel_name)>1:
            try:
                self.add_channel(channel_name[1], client)
            except Exception as e:
                raise Exception(str(e))
        else:
            raise Exception(utils.SERVER_CREATE_REQUIRES_ARGUMENT)

    def join_channel(self, client, data):
        channel_name = data.split()

        if len(channel_name)>1:
            try:
                self.join_channel_aux(channel_name[1], client)
            except Exception as e:
                raise Exception(str(e))
        else:
            raise Exception(utils.SERVER_JOIN_REQUIRES_ARGUMENT)

    def send_to_client(self, client, data):
        client.send(data)

    def send_channel_list(self, client):
        self.send_to_client(client, "\n".join(self.get_channel_list()))

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
                    print("done")
                else:
                    server.broadcast_to_channel(sock, proc_data, None)
            except Exception as e:
                #check this if valid
                SOCKET_LIST.remove(sock)
                print(e)
                sock.close()

server.close()
    