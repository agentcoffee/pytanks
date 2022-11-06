import pickle
import random
import time

import math
import logging

from server.packets import *
from enum import Enum
from server.clients.state_enum import ClientState

class ObserverClient:
    def __init__(self, connection):
        logging.info("New ObserverClient instantiated")

        self.connection = connection
        self.state      = ClientState.READY
        self.name       = "New Observer Client"

    def get_movables(self):
        return [ ]

    def step(self, field=None, id_generator=None, cmd_id_list=None):
        """
        This function does not do anything, except pass the game state to the
        client.
        """
        pass

    def get(self):
        try:
            return pickle.loads(self.connection.get())
        except (BrokenPipeError, ConnectionResetError):
            logging.info("Observer client '{}' died unexpectedly.".format(self.name))
            self.state = ClientState.DEAD

    def poll(self):
        try:
            return self.connection.poll()
        except (BrokenPipeError, ConnectionResetError):
            logging.info("Observer client '{}' died unexpectedly.".format(self.name))
            self.state = ClientState.DEAD
            return False

    def put(self, msg):
        try:
            return self.connection.put(pickle.dumps(msg))
        except (BrokenPipeError, ConnectionResetError):
            logging.info("Observer client '{}' died unexpectedly.".format(self.name))
            self.state = ClientState.DEAD

    def close(self):
        self.connection.close()
