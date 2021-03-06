# Profiling
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput

from Xlib import X, display, threaded
import argparse

from multiprocessing import Process, Pipe

from gameloop import GameLoop, Field
from tcp_driver import TCPServer
from xorg.window import Window

def start_server():
    parser = argparse.ArgumentParser()

    parser.add_argument("--ip", required=True, type=str)
    parser.add_argument("--port", required=True, type=int)

    args = parser.parse_args()

    print("IP: " + str(args.ip) + " : " + str(args.port))

    field   = Field(600, 600)

    graphviz = GraphvizOutput()
    graphviz.output_file = 'cg_window_server.png'

    with PyCallGraph(output=graphviz):
        GameLoop(TCPServer(args.ip, args.port), field).loop()

    #GameLoop(TCPServer(args.ip, args.port), field).loop()

if __name__ == "__main__":
    start_server()
