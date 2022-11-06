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
import sys

from server.packets import * 

from players.robots.easy import EasyRobot
from server.tcp_driver import TCPConnection

import logging

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--ip",   required=True, type=str)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--name", required=True, type=str)

    args = parser.parse_args()

    logging.info("IP: " + str(args.ip) + " : " + str(args.port) + " / " + args.name)

    #graphviz = GraphvizOutput()
    #graphviz.output_file = 'cg_window.png'

    #with PyCallGraph(output=graphviz):
    #    Window(display.Display(), TCPConnection(args.ip, args.port), args.name).loop()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)-8s] %(message)s")

    EasyRobot(TCPConnection(args.ip, args.port), args.name).loop()

    #cProfile.run('GameClient(args.ip, args.port, args.name).loop()',
    #        sort=SortKey.CUMULATIVE)
