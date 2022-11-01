# Profiling
from pycallgraph3 import PyCallGraph
from pycallgraph3.output import GraphvizOutput

import argparse

from gameloop import GameLoop
from drivers.tcp_driver import TCPServer

def start_server():
    parser = argparse.ArgumentParser()

    parser.add_argument("--ip", required=True, type=str)
    parser.add_argument("--port", required=True, type=int)

    args = parser.parse_args()

    print("IP: " + str(args.ip) + " : " + str(args.port))

    graphviz = GraphvizOutput()
    graphviz.output_file = 'cg_window_server.png'

    with PyCallGraph(output=graphviz):
        GameLoop(TCPServer(args.ip, args.port)).loop()

    #GameLoop(TCPServer(args.ip, args.port)).loop()

if __name__ == "__main__":
    start_server()
