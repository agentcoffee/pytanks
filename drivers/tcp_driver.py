import socket
import pickle
from client   import TankClient
from telegram import Telegram

class TCPServer:
    def __init__(self, ip, port):
        self.ip        = ip
        self.port      = port
        self.socket    = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.bind( (ip, port) )
        self.socket.listen()
        self.socket.setblocking(False)
        print("Socket bound to " + ip + ":" + str(port))
        print("TCPServer: Connected")

    def accept(self):
        """
        Accept new TCP connections, wrap them in a Client and return them.
        """
        tcp_socket, addr = self.socket.accept()
        telegram         = Telegram(tcp_socket)

        return TankClient(telegram)

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
