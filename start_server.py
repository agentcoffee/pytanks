# Profiling
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput

import argparse

from gameloop import GameLoop, Field
from drivers.tcp_driver import TCPServer

def start_server():
    parser = argparse.ArgumentParser()

    parser.add_argument("--ip", required=True, type=str)
    parser.add_argument("--port", required=True, type=int)

    args = parser.parse_args()

    print("IP: " + str(args.ip) + " : " + str(args.port))

    field   = Field(400, 400)

    graphviz = GraphvizOutput()
    graphviz.output_file = 'cg_window_server.png'

    with PyCallGraph(output=graphviz):
        GameLoop(TCPServer(args.ip, args.port), field).loop()

    #GameLoop(TCPServer(args.ip, args.port), field).loop()

if __name__ == "__main__":
    start_server()
