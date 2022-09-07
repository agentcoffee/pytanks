from enum import Enum
from Xlib import X

class InputPacket:
    class Key(Enum):
        UP      = 0
        DOWN    = 1
        LEFT    = 2
        RIGHT   = 3
        SPACE   = 4
        ESC     = 5

    class Event(Enum):
        PRESS   = 0
        RELEASE = 1

    def __init__(self, uid, key, event, cmd_id = 0, timestamp = 0):
        self.uid       = uid
        self.event     = event
        self.key       = key
        self.cmd_id    = cmd_id
        self.timestamp = timestamp

class StatePacket:
    def __init__(self, round_nr, game_state, cmd_id_list):
        self.round_nr    = round_nr
        self.game_state  = game_state
        self.cmd_id_list = cmd_id_list

class JoinReqPacket:
    def __init__(self, client_type):
        self.client_type = client_type

class JoinAckPacket:
    def __init__(self, field):
        self.field = field

class CreateTankPacket:
    def __init__(self, tank_name):
        self.tank_name = tank_name

class TankAckPacket:
    def __init__(self, uid):
        self.uid = uid

class TankDiedPacket:
    def __init__(self, uid):
        self.uid = uid

class LeavePacket:
    def __init__(self, uid):
        self.uid = uid
