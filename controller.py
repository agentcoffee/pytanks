import socket
import pickle

from multiprocessing import Pipe

from packets import * 
from commands import Input

# Exceptions
from queue import Empty

class ControllerServer:

    def __init__(self, ip, port, window_pipe):
        self.ip     = ip
        self.port   = port
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.socket.bind( (ip, port) )
        print("Socket bound to " + ip + ":" + str(port))

        self.window_pipe = window_pipe
        self.tank_pipes = []

    def loop(self):
        while True:
            print("Listening")
            data, addr = self.socket.recvfrom(2048)
            packet = pickle.loads(data)
            print("Caught packet " + str(type(packet)))

            if type(packet) is InputPacket:
                self.tank_pipes[packet.tank_id].send(packet.key_input)
            elif type(packet) is JoinReqPacket:
                a, b = Pipe()
                self.tank_pipes.append(a)
                self.window_pipe.send(b)
                print("Registering new tank: " + str(len(self.tank_pipes)-1))
                # very hacky:
                self.socket.sendto(
                        pickle.dumps(JoinAckPacket(len(self.tank_pipes)-1)), addr)
        # end while

