import select
import utils
import socket
import sys

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


while 1:
    #change the recieving and senfing of message
    msg = raw_input(utils.CLIENT_MESSAGE_PREFIX)
    if msg == "exit":
        break
    try:
        client.send( client.client_name()+" "+msg)
    except Exception as e:
        print(e)

    msg = client.socket.recv(RECV_BUFFER)
    print(msg)   
