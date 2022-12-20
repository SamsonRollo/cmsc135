import threading
import utils
import socket
import sys
import time #remove later

RECV_BUFFER = 200
RECV_HEADER_LEN = 10

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
        while 1:
            incoming_data = client.socket.recv(RECV_BUFFER)
            if not incoming_data:
                print(utils.CLIENT_SERVER_DISCONNECTED.format(1,1)) #specify server details
                sys.exit()
            else:
                #tell if from server or from other clients
                sys.stdout.write(incoming_data)
                sys.stdout.write(utils.CLIENT_MESSAGE_PREFIX); sys.stdout.flush() 
            
    def client_name(self):
        return "["+self.name+"]"

args = sys.argv
if len(args) != 4:
    print(args)
    print("Please supply a server address and port.")
    sys.exit()

client = BasicClient(args[1], args[2], args[3])

try:
    client.connect_to_server()
except:
    print(utils.CLIENT_CANNOT_CONNECT.format(client.address, client.port))
    sys.exit()

sys.stdout.write(utils.CLIENT_MESSAGE_PREFIX); sys.stdout.flush()
receive_thread = threading.Thread(target=client.receive)
receive_thread.start()

while 1: # thread for writing
    client_input_data = sys.stdin.readline()
    try:
        client.send(client.client_name()+" "+client_input_data)
    except Exception as e:
        sys.stdout.write(str(e))
    sys.stdout.write(utils.CLIENT_MESSAGE_PREFIX); sys.stdout.flush()
