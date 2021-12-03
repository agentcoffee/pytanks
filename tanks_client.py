# Profiling
#from pycallgraph import PyCallGraph
#from pycallgraph.output import GraphvizOutput

#import cProfile
#from pstats import SortKey

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

from xorg.window import Window
#from telegram import Telegram
from drivers.tcp_driver import TCPConnection

# Exceptions
from queue import Empty

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

        #graphviz = GraphvizOutput()
        #graphviz.output_file = 'cg_window.png'

        #with PyCallGraph(output=graphviz):
        #    Window(display.Display(), TCPConnection(args.ip, args.port), args.name).loop()

        Window(display.Display(), TCPConnection(args.ip, args.port), args.name).loop()

        #cProfile.run('GameClient(args.ip, args.port, args.name).loop()',
        #        sort=SortKey.CUMULATIVE)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
