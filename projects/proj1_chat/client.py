import select
import utils
import socket
import sys

RECV_BUFFER = 200
RECV_HEADER_LEN = 11

class BasicClient(object):
    name = ""

    def __init__(self, name, address, port):
        self.name = name
        self.address = address
        self.port = int(port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self):
        self.socket.connect((self.address, self.port))
        
    def send(self, message):
        self.socket.send(message)

    def receive(self):
        full_data = ""
        new_data = True
        update = False

        while 1:
            incoming_data = client.socket.recv(RECV_BUFFER)

            if not incoming_data:
                print(utils.CLIENT_SERVER_DISCONNECTED.format(self.socket.address, self.socket.port))
                sys.exit()

            if new_data:
                header = incoming_data[:RECV_HEADER_LEN].split()
                data_len = int(header[0])
                update = header[1] == "1"
                new_data = False
            full_data += incoming_data

            if len(full_data)-RECV_HEADER_LEN == data_len:
                sys.stdout.write(utils.CLIENT_WIPE_ME+"\r")
                sys.stdout.write(full_data[RECV_HEADER_LEN:]); sys.stdout.flush()
                if update:
                    sys.stdout.write("\n")
                sys.stdout.write(utils.CLIENT_MESSAGE_PREFIX); sys.stdout.flush() 
                break
            
    def client_name(self):
        return self.name

args = sys.argv
if len(args) != 4:
    print("Please supply a server address and port.")
    sys.exit()

client = BasicClient(args[1], args[2], args[3])

try:
    client.connect_to_server()
except:
    print(utils.CLIENT_CANNOT_CONNECT.format(client.address, client.port))
    sys.exit()

client.send(client.client_name())
sys.stdout.write(utils.CLIENT_MESSAGE_PREFIX); sys.stdout.flush()

while 1: 
    socket_list = [sys.stdin, client.socket]

    ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])
         
    for sock in ready_to_read:             
        if sock == client.socket:
            client.receive()
        else:
            client_input_data = sys.stdin.readline()
            try:
                client.send(client_input_data)
            except Exception as e:
                print(e)
                sys.stdout.write(str(e))
            sys.stdout.write(utils.CLIENT_MESSAGE_PREFIX); sys.stdout.flush()
