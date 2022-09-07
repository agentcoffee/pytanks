import socket
import pickle

from clients.type_enum   import ClientType
from clients.tank_client import TankClient
from clients.obs_client  import ObserverClient
from telegram import Telegram

from packets import *

class TCPServer:
    def __init__(self, ip, port):
        self.ip        = ip
        self.port      = port
        self.socket    = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.bind( (ip, port) )
        self.socket.listen()
        self.socket.setblocking(False)
        self.pending_clients = []

        print("Socket bound to " + ip + ":" + str(port))
        print("TCPServer: Connected")

    def accept(self):
        """
        Accept new TCP connections, wrap them in a Client and return them.
        """
        tcp_socket, addr = self.socket.accept()
        telegram         = Telegram(tcp_socket)
        print("Accepted connection")

        return telegram

    def step(self, field):
        # Check for new clients
        try:
            self.pending_clients.append(self.accept())
        except BlockingIOError:
            pass

        # Check pending clients
        if len(self.pending_clients) > 0:
            c = self.pending_clients.pop(0)

            if c.poll():
                packet = pickle.loads(c.get())

                if type(packet) is JoinReqPacket:

                    if packet.client_type is ClientType.TANK:
                        client = TankClient(c)
                        client.put(JoinAckPacket(field))
                        return [ client ]

                    elif packet.client_type is ClientType.OBSERVER:
                        client = ObserverClient(c)
                        client.put(JoinAckPacket(field))
                        return [ client ]
                    
                    else:
                        raise Exception("Not supported {}".format(type(packet)))

            self.pending_clients.append(c)
        return []

    def close(self):
        print("Cleaning clients")
        self.socket.close()

class TCPConnection:
    def __init__(self, ip, port):
        self.ip     = ip
        self.port   = port
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.connect( (ip, port) )

        print("TCPConnection: Connected")
        self.telegram = Telegram(self.socket)

    def poll(self):
        return self.telegram.poll()

    def put(self, msg):
        self.telegram.put(pickle.dumps(msg))

    def get(self):
        return pickle.loads(self.telegram.get())

    def blocking_get(self):
        return pickle.loads(self.telegram.blocking_get())

    def get_latest(self):
        return pickle.loads(self.telegram.get_latest())

    def close(self):
        print("Cleaning server connection")
        self.telegram.close()
