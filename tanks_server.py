from Xlib import X, display, threaded
import argparse

from multiprocessing import Process, Pipe

from window import Window
from controller import ControllerServer

# TODO make class forkable
def f(d, p):
    Window(d, p).loop()

# TODO make class forkable
def g(ip, port, pipe):
    ControllerServer(ip, port, pipe).loop()

def tanks_server():
    parser = argparse.ArgumentParser()

    parser.add_argument("--ip", required=True, type=str)
    parser.add_argument("--port", required=True, type=int)

    args = parser.parse_args()

    print("IP: " + str(args.ip) + " : " + str(args.port))

    d = display.Display()

    # For adding new tanks
    controller_pipe, window_pipe = Pipe()

    window_p        = Process(target = f, args = (d, window_pipe))
    window_p.start()

    controller_p    = Process(target = g, args = (args.ip, args.port, controller_pipe))
    controller_p.start()

    # Finish
    window_p.join()
    controller_p.join()

if __name__ == "__main__":
    tanks_server()
