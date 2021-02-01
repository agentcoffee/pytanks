import socket
import pickle
import random
import time

from multiprocessing import Pipe

from packets import * 
from telegram import Telegram

import debug

# Communication
from commands import *

# Exceptions
from queue import Empty

class IOController:

    class Connection:
        def __init__(self, input_pipe, address, connection, uid):
            self.input_pipe = input_pipe
            self.address    = address
            self.connection = connection
            self.uid        = uid

    def __init__(self, ip, port, io_gl_pipe, gl_win_pipe, field):
        self.ip     = ip
        self.port   = port
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.bind( (ip, port) )
        self.socket.listen()
        self.socket.setblocking(False)
        print("Socket bound to " + ip + ":" + str(port))

        self.field  = field
        self.io_gl_pipe = io_gl_pipe
        self.gl_win_pipe = gl_win_pipe
        self.connections = {}

    def loop(self):
        try:
            self._loop()
        finally:
            print("Cleaning up")
            for c in self.connections.values():
                c.connection.close()
                self.socket.close()
                self.io_gl_pipe.close()
                self.gl_win_pipe.close()

    def _loop(self):
        while True:
            # Listening for new connections
            try:
                connection, addr = self.socket.accept()
                telegram = Telegram(connection)
                data     = telegram.blocking_get() # TODO a malicious client can stall the server here
                packet   = pickle.loads(data)

                if type(packet) is JoinReqPacket:
                    # Create a new pipe for this tank
                    a, b = Pipe()
                    new_tank = NewTank(pipe = b,
                            name = packet.tank_name,
                            uid = random.randbytes(2))

                    # Save the input pipe in the connections dictionary
                    self.connections[new_tank.uid] = IOController.Connection(
                            input_pipe = a,
                            address = addr,
                            connection = telegram,
                            uid = new_tank.uid)

                    # Register the tank with the game loop
                    self.io_gl_pipe.send(new_tank)
                    print("Registering new tank: " + packet.tank_name)

                    # Acknowledge the join with the requested name
                    self.connections[new_tank.uid].connection.put(
                            pickle.dumps(JoinAckPacket(new_tank.uid, self.field)))
                else:
                    raise Exception("Received garbage via new connection.")
                # end if
            except BlockingIOError:
                pass
            # end try

            # Check existing connections
            for c in self.connections.values():
                while c.connection.poll():
                    data = c.connection.get()
                    packet = pickle.loads(data)
                    if type(packet) is InputPacket:
                        if packet.uid in self.connections:
                            c.input_pipe.send(packet.key_input)
                            debug.latency("Server dispatched Input: {} at {}".format(
                                packet.key_input.cmd_id, (time.monotonic_ns() / 1000000)))
                        # end if
                    # end if
                    else:
                        raise Exception("Received garbage via existing connection")
                # end while
            # end for

            # Listening for game states to distribute
            if self.gl_win_pipe.poll():
                data = self.gl_win_pipe.recv()
                if type(data) == GameState:
                    if len(data.cmd_id_list) != 0:
                        debug.latency("Server broadcasts to Inputs: {} at {}".format(
                            data.cmd_id_list, (time.monotonic_ns() / 1000000)))
                    # Blast state to clients
                    for c in self.connections.values():
                        stream = pickle.dumps(StatePacket(data, c.uid))
                        assert(len(stream) < 4096)
                        c.connection.put( pickle.dumps(StatePacket(data, c.uid)) )
                    # end for
                # end if
            # end if
        # end while
