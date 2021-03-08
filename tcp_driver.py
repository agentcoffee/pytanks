import socket
import pickle
from telegram import Telegram

class TCPServer:
    # TODO: the client pickles here, do the same for the server
    def __init__(self, ip, port):
        self.ip        = ip
        self.port      = port
        self.socket    = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.bind( (ip, port) )
        self.socket.listen()
        self.socket.setblocking(False)
        print("Socket bound to " + ip + ":" + str(port))
        self.connections      = []

        print("TCPServer: Connected")
        self.telegram = Telegram(self.socket)

    def __iter__(self):
        return iter(self.connections)

    def accept(self):
        tcp_socket, addr = self.socket.accept()
        telegram         = Telegram(tcp_socket)
        self.connections.append(telegram)
        return telegram

    def drop(self):
        pass

    def close(self):
        print("Cleaning clients")
        for c in self.connections:
            c.close()
        self.socket.close()

class TCPClient:
    def __init__(self, ip, port):
        self.ip     = ip
        self.port   = port
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.connect( (ip, port) )

        print("TCPClient: Connected")
        self.telegram = Telegram(self.socket)

    def send(self, msg):
        self.telegram.put(pickle.dumps(msg))

    def recv(self):
        return pickle.loads(self.telegram.get())

    def blocking_recv(self):
        return pickle.loads(self.telegram.blocking_get())

    def recv_latest(self):
        return pickle.loads(self.telegram.get_latest())

    def close(self):
        print("Cleaning server connection")
        self.telegram.close()
