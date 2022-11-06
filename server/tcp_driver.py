import socket
import pickle

from server.clients.type_enum   import ClientType
from server.clients.tank_client import TankClient
from server.clients.obs_client  import ObserverClient
from server.telegram import Telegram

from server.packets import *

import logging

class TCPServer:
    def __init__(self, ip, port):
        self.ip        = ip
        self.port      = port
        self.socket    = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.bind( (ip, port) )
        self.socket.listen()
        self.socket.setblocking(False)
        self.pending_clients = []

        logging.info("Socket bound to " + ip + ":" + str(port))
        logging.info("TCPServer: Connected")

    def accept(self):
        """
        Accept new TCP connections, wrap them in a Client and return them.
        """
        tcp_socket, addr = self.socket.accept()
        telegram         = Telegram(tcp_socket)
        logging.info("Accepted connection")

        return telegram

    def step(self):
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
                        client.put(JoinAckPacket())
                        return [ client ]

                    elif packet.client_type is ClientType.OBSERVER:
                        client = ObserverClient(c)
                        client.put(JoinAckPacket())
                        return [ client ]
                    
                    else:
                        raise Exception("Not supported {}".format(type(packet)))

            self.pending_clients.append(c)
        return []

    def close(self):
        logging.info("Cleaning clients")
        self.socket.close()

class TCPConnection:
    def __init__(self, ip, port):
        self.ip     = ip
        self.port   = port
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.connect( (ip, port) )

        logging.info("TCPConnection: Connected")
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
        logging.info("Cleaning server connection")
        self.telegram.close()
