import select
import sys
import socket
import utils
import threading
import re

RECV_BUFFER = 200
RECV_HEADER_LEN = 11
SOCKET_LIST = []

class Server(object):
    channels = []
    clients = [] #[[channel, socket, addr, name]]
    init_clients = [] #list of clients that needs init transmission

    def __init__(self, address, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((address, int(port)))
        self.socket.listen(5)
    
    def add_client(self, client_socket, client_addr, client_name=None, channel=None):
        self.clients.append([channel, client_socket, client_addr, client_name])

    def add_init_client(self, client_socket):
        self.init_clients.append(client_socket)
    
    def remove_init_client(self, client_socket):
        self.init_clients.remove(client_socket)

    def update_client_name(self, client_socket, client_name):
        for cur_client in self.clients:
            if cur_client[1] == client_socket:
                cur_client[3] = client_name
                self.remove_init_client(client_socket)
                break

    def get_client_name(self, client_socket):
        for cur_client in self.clients:
            if cur_client[1] == client_socket:
                return cur_client[3]
    
    def form_broadcast_name(self, client_name):
        return "["+client_name+"]"
    
    def update_client_channel(self, new_channel, client_socket):
        for cur_client in self.clients:

            if cur_client[1] == client_socket:
                old_channel = cur_client[0]
                cur_client[0] = new_channel

                if new_channel != None:
                    new_channel.add_user(client_socket)
                    self.broadcast_to_channel(client_socket, utils.SERVER_CLIENT_JOINED_CHANNEL.format(cur_client[3]), new_channel, True)

                if old_channel != None:
                    old_channel.remove_user(client_socket)
                    self.broadcast_to_channel(client_socket, utils.SERVER_CLIENT_LEFT_CHANNEL.format(cur_client[3]), old_channel, True)
                break

    def add_channel(self, channel_name, client_socket):
        for reg_channel in self.channels:

            if reg_channel.get_channel_name() == channel_name:
                raise Exception(utils.SERVER_CHANNEL_EXISTS.format(channel_name))
                
        new_channel = Channel(channel_name, client_socket)
        self.channels.append(new_channel)
        self.update_client_channel(new_channel, client_socket)

    def join_channel(self, client_socket, data):
        channel_name = data.split()

        if len(channel_name)>1:
            try:
                self.join_channel_aux(channel_name[1], client_socket)
            except Exception as e:
                raise Exception(str(e))
        else:
            raise Exception(utils.SERVER_JOIN_REQUIRES_ARGUMENT)

    def join_channel_aux(self, channel_name, client_socket):
        for reg_channel in self.channels:
            if reg_channel.get_channel_name() == channel_name:
                self.update_client_channel(reg_channel, client_socket)
                return

        raise Exception(utils.SERVER_NO_CHANNEL_EXISTS.format(channel_name))

    def process_for_broadcast(self, client_socket, output_data, channel=None):
        for cur_client in self.clients:
            if cur_client[1] == client_socket:
                channel = cur_client[0]
                client_name = cur_client[3]
                break
        
        self.broadcast_to_channel(client_socket, self.form_broadcast_name(client_name)+" "+output_data, channel)

    def broadcast_to_channel(self, client_socket, output_data, channel, update=False):
        try:
            if channel:
                channel_users = channel.get_users()
            else:               
                channel_users = self.retrive_socket_channel(client_socket)

            for user in channel_users:
                if user == client_socket:
                    continue
                self.send_to_client(user, output_data, update)

        except Exception as e:
            self.handle_server_response(client_socket, e)
 
    def retrive_socket_channel(self, socket):
        for cur_client in self.clients:
            if cur_client and cur_client[1] == socket:

                if cur_client[0] == None:
                    raise Exception(utils.SERVER_CLIENT_NOT_IN_CHANNEL)
                else:
                    return cur_client[0].get_users()
    
    def process_input_data(self, client_socket, data):
        init_trans = False
        if client_socket in self.init_clients:
            init_trans = True
        if re.search("^/", data):
            return init_trans, True
        return init_trans, False

    def process_command(self, client_socket, data):
        command = re.findall("^/\w*", data)

        if command:
            command = command[0].lower()
        try:
            if command == "/list":
                self.send_channel_list(client_socket)

            elif command == "/create":
                self.create_channel(client_socket, data)

            elif command == "/join":
                self.join_channel(client_socket, data)

            else:
                self.invalid_command(command)
        
        except Exception as e:
            self.handle_server_response(client_socket, e)

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

    def send_to_client(self, client, data, update=False):
        new_data = str(len(data))+" "+str(int(update))
        new_data = new_data.ljust(RECV_HEADER_LEN) + data
        client.send(new_data)

    def send_channel_list(self, client):
        self.send_to_client(client, "\n".join(self.get_channel_list()), True)
    
    def handle_server_response(self, client, data):
        self.send_to_client(client, str(data), True)

    def disconnect_client(self, client_socket):
        SOCKET_LIST.remove(client_socket)
        self.update_client_channel(None, client_socket)
        for sock in self.clients:
            if sock[1] == client_socket:
                self.clients.remove(sock)
                break

    def get_channel_list(self):
        channel_list = []
        for channel in self.channels:
            channel_list.append(channel.get_channel_name())
        return channel_list
    
class Channel(object):
    def __init__(self, name, user):
        self.name = name
        self.users = [user]
    
    def add_user(self, user):
        if not user in self.users:
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
            server.add_init_client(client)

        else:
            try:
                data = sock.recv(RECV_BUFFER)
                if data:
                    init_transmission, iscommand = server.process_input_data(sock, data)
                    if init_transmission:
                        server.update_client_name(sock, data)
                        continue

                    if iscommand:
                        server.process_command(sock, data)
                    else:
                        server.process_for_broadcast(sock, data)
                else:
                    if sock in SOCKET_LIST:
                        server.disconnect_client(sock)

            except Exception as e:
                server.disconnect_client(sock)

server.close()
    