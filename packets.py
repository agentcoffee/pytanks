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

    def __init__(self, uid, key_event, cmd_id, timestamp = 0):
        self.uid       = uid
        self.cmd_id    = cmd_id
        self.timestamp = timestamp

        if key_event.type is X.KeyPress:
            self.event = self.Event.PRESS
        elif key_event.type is X.KeyRelease:
            self.event = self.Event.RELEASE
        else:
            raise NotImplementedError

        if key_event.detail == 111:
            self.key = self.Key.UP

        elif key_event.detail == 116:
            self.key = self.Key.DOWN

        elif key_event.detail == 113:
            self.key = self.Key.LEFT

        elif key_event.detail == 114:
            self.key = self.Key.RIGHT

        elif key_event.detail == 65:
            self.key = self.Key.SPACE

        elif key_event.detail == 66:
            self.key = self.Key.ESC

        else:
            raise KeyError

class StatePacket:
    def __init__(self, round_nr, game_state, cmd_id_list):
        #self.uid         = uid
        self.round_nr    = round_nr
        self.game_state  = game_state
        self.cmd_id_list = cmd_id_list

class JoinReqPacket:
    def __init__(self, tank_name):
        self.tank_name  = tank_name

class JoinAckPacket:
    def __init__(self, uid, field):
        self.uid    = uid
        self.field  = field
