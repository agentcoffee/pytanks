from enum import Enum
from pynput import keyboard


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

    def __init__(self, key_event):
        if type(key_event) is keyboard.Events.Press:
            self.event = self.Event.PRESS
        elif type(key_event) is keyboard.Events.Release:
            self.event = self.Event.RELEASE
        else:
            raise NotImplementedError

        if key_event.key == keyboard.Key.up:
            self.key = self.Key.UP
        elif key_event.key == keyboard.Key.down:
            self.key = self.Key.DOWN
        elif key_event.key == keyboard.Key.left:
            self.key = self.Key.LEFT
        elif key_event.key == keyboard.Key.right:
            self.key = self.Key.RIGHT
        elif key_event.key == keyboard.Key.space:
            self.key = self.Key.SPACE
        elif key_event.key == keyboard.Key.esc:
            self.key = self.Key.ESC
        else:
            raise KeyError
