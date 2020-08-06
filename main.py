from Xlib import X, display, threaded

from multiprocessing import Process, Pipe

from window import Window
from controller_server import ControllerServer

# TODO make class forkable
def f(d, p):
    Window(d, p).loop()

# TODO make class forkable
def g(ip, port, pipe):
    ControllerServer(ip, port, pipe).loop()

def main():
    d = display.Display()

    # For adding new tanks
    controller_pipe, window_pipe = Pipe()

    window_p        = Process(target = f, args = (d, window_pipe,))
    window_p.start()

    controller_p    = Process(target = g, args = ("127.0.0.1", 5001, controller_pipe))
    controller_p.start()

    # Finish
    window_p.join()
    controller_p.join()

if __name__ == "__main__":
    main()
