# Profiling
from pycallgraph2 import PyCallGraph
from pycallgraph2.output import GraphvizOutput

import argparse

from engine.gameloop import GameLoop
from server.tcp_driver import TCPServer

import logging

def start_server():
    parser = argparse.ArgumentParser()

    parser.add_argument("--ip", required=True, type=str)
    parser.add_argument("--port", required=True, type=int)

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)-8s] %(message)s")
    logging.info("IP: " + str(args.ip) + " : " + str(args.port))

    graphviz = GraphvizOutput()
    graphviz.output_file = 'cg_window_server.png'

    with PyCallGraph(output=graphviz):
        GameLoop(TCPServer(args.ip, args.port)).loop()

    #GameLoop(TCPServer(args.ip, args.port)).loop()

if __name__ == "__main__":
    start_server()
