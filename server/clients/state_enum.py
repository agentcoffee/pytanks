from enum import Enum

class ClientState(Enum):
    WAITING = 1
    READY   = 2
    DEAD    = 3
