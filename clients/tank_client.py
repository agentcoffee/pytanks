import pickle
import random
import time

import math
import debug
from enum import Enum

from packets import *
from maths.vector import Vector
from sprites.tank import TankObject, TankState
from clients.state_enum import ClientState

class TankClient:
    def __init__(self, connection):
        print("New TankClient instantiated")

        self.connection = connection
        self.state      = ClientState.WAITING
        self.name       = "New Client"

    def get_movables(self):
        if self.state is ClientState.READY:
            return [ self.tank ]
        else:
            return [ ]

    def step(self, field=None, id_generator=None, cmd_id_list=None):
        """
        Function to advance the client through its state machine. After any
        invocation the function returns the clients current state. The states
        are:

        WAITING: The client is still waiting for the JoinReqPacket. Upon
            reception of the JoinReqPacket it instantiates a Tank and moves to the
            READY state.

        READY: The client has its tank initialised and is ready to handle
            inputs and move the tank.

        DEAD: The player closed the connection. The client is dead and ready to
            be removed.
        """

        if self.state is ClientState.WAITING:
            self.state_waiting(field, id_generator)

        elif self.state is ClientState.READY:
            self.state_ready(cmd_id_list)

        elif self.state is ClientState.DEAD:
            self.state_dead()

    def state_waiting(self, field, id_generator):
        """
        Function to step through initial handshake of this client. This
        function is called by the server class until it returns CLIENT_READY,
        after which it will be handed to the gameloop.
        """

        if self.poll():
            packet = self.get()

            if type(packet) is CreateTankPacket:
                self.name = packet.tank_name
                self.tank = TankObject(
                                field = field,
                                tank_state = TankState(
                                    position = Vector(
                                        x = field.x_inf +
                                            random.random() * (field.x_sup - field.x_inf + 1),
                                        y = field.y_inf +
                                            random.random() * (field.y_sup - field.y_inf + 1)),
                                    angle = math.pi/2,
                                    speed = 0,
                                    health = 100,
                                    name = self.name,
                                    uid = id_generator.get()),
                                id_generator = id_generator)

                self.put(TankAckPacket(self.tank.uid))
                self.state = ClientState.READY
                print("Client {} moves to READY".format(self.name))

            elif type(packet) is LeavePacket:
                self.state = ClientState.DEAD
                print("Client {} left".format(self.name))

    def state_ready(self, cmd_id_list=None):
        """
        This function is called by the gameloop to process whatever inputs this
        client sent (and received) and whatever this does to its movables.

        @cmd_id_list: Is a list of commands which are currently in process.
        Used for debugging the latency of the gameloop.
        """

        # check if the tank died
        if self.tank.health <= 0:
            self.put(TankDiedPacket(self.tank.uid))
            self.state = ClientState.WAITING
            self.tank = None # remove reference, let garbage collector do its job
        else:
            # else process inputs
            # TODO: bound this, this shouldn't be a while
            while self.poll():
                packet = self.get()

                if type(packet) is InputPacket:
                    if cmd_id_list is not None:
                        cmd_id_list.append(packet.cmd_id)
                        debug.latency("Gameloop handled Input: {} at {}".format(
                            packet.cmd_id, (time.monotonic_ns() / 1000000)))

                    self.tank.handler(packet)

                    if packet.event == InputPacket.Event.PRESS:
                        debug.input("> " + str(packet.key.name))
                    if packet.event == InputPacket.Event.RELEASE:
                        debug.input("< " + str(packet.key.name))

                elif type(packet) is LeavePacket:
                    self.state = ClientState.DEAD
                    print("Client {} left".format(self.name))

    def state_dead(self):
        pass

    def get(self):
        try:
            return pickle.loads(self.connection.get())
        except (BrokenPipeError, ConnectionResetError):
            print("Client '{}' died unexpectedly.".format(self.name))
            self.state = ClientState.DEAD

    def poll(self):
        try:
            return self.connection.poll()
        except (BrokenPipeError, ConnectionResetError):
            print("Client '{}' died unexpectedly.".format(self.name))
            self.state = ClientState.DEAD
            return False

    def put(self, msg):
        try:
            return self.connection.put(pickle.dumps(msg))
        except (BrokenPipeError, ConnectionResetError):
            print("Client '{}' died unexpectedly.".format(self.name))
            self.state = ClientState.DEAD

    def close(self):
        self.connection.close()
