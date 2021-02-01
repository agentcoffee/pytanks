# Profiling
import cProfile
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
from pstats import SortKey
import time

# Includes
import socket
import pickle
import argparse
import termios
import sys

from multiprocessing import Process, Pipe

from Xlib import X, display, threaded

from packets import * 

from commands import Input
from xorg.window import Window
#from telegram import Telegram
from tcp_driver import TCPDriver

# Exceptions
from queue import Empty

# TODO make class forkable
def f(ip, port, name):
    graphviz = GraphvizOutput()
    graphviz.output_file = 'cg_window.png'

    #with PyCallGraph(output=graphviz):
    Window(display.Display(), TCPDriver(ip, port), name).loop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--ip",   required=True, type=str)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--name", required=True, type=str)

    args = parser.parse_args()

    print("IP: " + str(args.ip) + " : " + str(args.port) + " / " + args.name)

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)

    new[3] = new[3] & ~termios.ECHO

    try:
        termios.tcsetattr(fd, termios.TCSADRAIN, new)

        window_p = Process(target = f, args = (args.ip, args.port, args.name))
        window_p.start()

        #cProfile.run('GameClient(args.ip, args.port, args.name).loop()',
        #        sort=SortKey.CUMULATIVE)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
