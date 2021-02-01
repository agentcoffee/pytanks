from enum import Enum
from Xlib import X

# Client > Server
class Input:
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

    def __init__(self, key_event, cmd_id, timestamp = 0):
        self.cmd_id = cmd_id
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

# Client > Server
class NewTank:
    def __init__(self, pipe, name, uid):
        self.pipe = pipe
        self.name = name
        self.uid  = uid

# Server > Client
class GameState:
    def __init__(self, round_nr, game_state, cmd_id_list):
        self.round_nr   = round_nr
        self.game_state = game_state
        self.cmd_id_list = cmd_id_list
