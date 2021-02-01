from Xlib import X, display, threaded
import argparse

from multiprocessing import Process, Pipe

from gameloop import GameLoop, Field
from tank_server import IOController
from xorg.window import Window

# TODO make class forkable
def f(gameloop_pipe, window_pipe, field):
    GameLoop(gameloop_pipe, window_pipe, field).loop()

# TODO make class forkable
def g(ip, port, gameloop_pipe, window_pipe, field):
    IOController(ip, port, gameloop_pipe, window_pipe, field).loop()

# TODO make class forkable
#def h(display, gameloop_pipe, field):
#    Window(display, gameloop_pipe, field).loop()

def start_server():
    parser = argparse.ArgumentParser()

    parser.add_argument("--ip", required=True, type=str)
    parser.add_argument("--port", required=True, type=int)

    args = parser.parse_args()

    print("IP: " + str(args.ip) + " : " + str(args.port))

    field   = Field(600, 600)

    # Communication between IO controller (receiving inputs via UDP)
    # and the game loop.
    io_gl_pipe, gl_io_pipe      = Pipe()
    # Communication between the game loop and the window
    win_gl_pipe, gl_win_pipe    = Pipe()

    gameloop_p       = Process(target = f, args = (gl_io_pipe, gl_win_pipe, field))
    gameloop_p.start()

    io_controller_p  = Process(target = g, args = (args.ip, args.port, io_gl_pipe, win_gl_pipe, field))
    io_controller_p.start()

    #window_p         = Process(target = h, args = (display.Display(), win_gl_pipe, field))
    #window_p.start()

    # Finish
    gameloop_p.join()
    io_controller_p.join()

if __name__ == "__main__":
    start_server()
