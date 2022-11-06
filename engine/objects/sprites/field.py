import math
import random
from Xlib import X, threaded

import logging
from engine.maths.vector import Vector
from engine.maths.matrix import RotationMatrix
from engine.maths.interval import Interval

from engine.objects.generics.drawable import Drawable
from engine.objects.generics.collidable import Collidable, CollidableType
from engine.objects.sprites.explosion import ExplosionObject, ExplosionState

from engine.bounding_box import BoundingBox


# Used to communicate the state to the clients
class FieldState:
    def __init__(self, width, height, uid):
        self.x_inf  = 1
        self.x_sup  = width
        self.y_inf  = 1
        self.y_sup  = height
        self.width  = width
        self.height = height
        self.uid    = uid

    def get_state(self):
        return FieldState(self.width, self.height, self.uid)

    def set_state(self, field_state):
        assert(type(field_state) == FieldState)
        self.x_inf  = field_state.x_inf
        self.x_sup  = field_state.x_sup
        self.y_inf  = field_state.y_inf
        self.y_sup  = field_state.y_sup
        self.width  = field_state.width
        self.height = field_state.height
        self.uid    = field_state.uid

class FieldSprite(Drawable):
    def __init__(self, screen, window, gc, field_state):
        # Init the drawable context
        Drawable.__init__(self, screen, window, gc)

        # Init the state
        self.state = field_state

        logging.info(f"Instantiated Field {self.state.width} x {self.state.height}")

    def __str__(self):
        return "FieldSprite: " + str(self.state.uid)

    def draw_field(self, fg_border, fg_font):
        self.gc.change(foreground = fg_border)
        self.window.rectangle(self.gc, 0, 0, int(self.state.width), int(self.state.height))

    def draw(self):
        self.draw_field(self.screen.black_pixel, self.red)

    def erase(self):
        self.draw_field(self.screen.white_pixel, self.screen.white_pixel)

class FieldObject(Collidable):
    def __init__(self, field_state, id_generator):
        # Init the state
        self.state = field_state
        self.id_generator = id_generator

        Collidable.__init__(self, CollidableType.SQUARE)

        logging.info((f"Instantiated Field {self.state.uid} : "
            f"x = {self.state.width} y = {self.state.height}"))

    def __str__(self):
        return "Field: " + str(self.state.uid)

    def handler(self, e):
        pass

    def get_position(self):
        raise NotImplementedError(f"Called get_position on Field {self.id}")

    def get_hitboxradius(self):
        raise NotImplementedError(f"Called get_hitboxradius on Field {self.id}")

    def get_collisionbox(self):
        return BoundingBox(Interval(1, self.state.width, True), Interval(1, self.state.height, True))

    def collision(self, other):
        pass

    def step(self, objects, movables):
        pass
