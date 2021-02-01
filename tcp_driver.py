import socket
import pickle
from telegram import Telegram

class TCPDriver:
    def __init__(self, ip, port):
        self.ip     = ip
        self.port   = port
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.connect( (ip, port) )

        print("TCPDriver: Connected")
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
        self.socket.close()
