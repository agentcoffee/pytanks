import socket
import pickle
import argparse
import termios
import sys

from packets import * 

from pynput import keyboard
from commands import Input

# Exceptions
from queue import Empty

class Controller():

    def __init__(self, ip, port):
        self.ip     = ip
        self.port   = port
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        self.socket.sendto(pickle.dumps(JoinReqPacket()), (ip, port))
        print("Listening")
        data, address = self.socket.recvfrom(2048)
        print("Caught packet")

        packet = pickle.loads(data)

        print(packet)

        if type(packet) is not JoinAckPacket:
            raise SystemError
        self.tank_id = packet.tank_id

        self.map   = dict( (x, Input.Event.RELEASE) for x in Input.Key ) 

    def autoRepeatDetection(self, events):

        try:
            e = events.get(0.01)
        except Empty:
            e = None

        while e is not None:
            try:
                k = Input(e)
            except KeyError:
                k = None

            if k is not None:
                if k.event is Input.Event.PRESS:
                    if self.map[k.key] == Input.Event.RELEASE:
                        print(k.key.name)
                        self.map[k.key] = Input.Event.PRESS
                        self.socket.sendto(pickle.dumps(
                            InputPacket(k, self.tank_id)), (self.ip, self.port))
                else:
                    #self.on_release(e.key)
                    self.map[k.key] = Input.Event.RELEASE
                    self.socket.sendto(pickle.dumps(
                        InputPacket(k, self.tank_id)), (self.ip, self.port))

                if k.key == Input.Key.ESC:
                    return False

            try:
                e = events.get(0.01)
            except Empty:
                e = None

        return True

    def loop(self):
        with keyboard.Events() as events:
            while True:
                if not self.autoRepeatDetection(events):
                    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--ip", required=True, type=str)
    parser.add_argument("--port", required=True, type=int)

    args = parser.parse_args()

    print("IP: " + str(args.ip) + " : " + str(args.port))

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)

    new[3] = new[3] & ~termios.ECHO

    try:
        termios.tcsetattr(fd, termios.TCSADRAIN, new)

        Controller(args.ip, args.port).loop()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
