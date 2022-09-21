import math
import random
from Xlib import X, threaded

import debug
from maths.vector import Vector
from maths.matrix import RotationMatrix
from maths.interval import Interval

from sprites.drawable import Drawable
from sprites.collidable import Collidable
from sprites.explosion import ExplosionObject, ExplosionState

from packets import InputPacket

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

    def getState(self):
        return FieldState(self.width, self.height, self.uid)

    def setState(self, field_state):
        assert(type(field_state) == FieldState)
        self.x_inf  = field_state.x_inf
        self.x_sup  = field_state.x_sup
        self.y_inf  = field_state.y_inf
        self.y_sup  = field_state.y_sup
        self.width  = field_state.width
        self.height = field_state.height
        self.uid    = field_state.uid

class FieldSprite(Drawable, FieldState):
    def __init__(self, screen, window, gc, field_state):
        # Init the drawable context
        Drawable.__init__(self, screen, window, gc)

        # Init the state
        TankState.setState(self, field_state)

        self.image = [Vector(5, -5),  Vector(-5, -5), Vector(-5, 5),
                      Vector(5, 5),   Vector(5, 1),   Vector(10, 1),
                      Vector(10, -1), Vector(5, -1),  Vector(5, -5)]

        debug.objects("Instantiated TankSprite {}".format(self.name, self.position.x, self.position.y))

    def __str__(self):
        return "TankSprite: " + str(self.uid)

    def draw_field(self, fg_border, fg_font):
        self.gc.change(foreground = fg_border)
        self.window.rectangle(self.gc, 0, 0, int(self.width), int(self.height))

    def draw(self):
        self.draw_field(self.screen.black_pixel, self.red)

    def erase(self):
        self.draw_field(self.screen.white_pixel, self.screen.white_pixel)

class FieldObject(Collidable, FieldState):
    def __init__(self, field_state, id_generator):
        # Init the state
        FieldState.setState(self, field_state)

        self.id_generator   = id_generator

        print(f"Instantiated Field {self.id} : x = {self.width} y = {self.height}")

    def __str__(self):
        return "Field: " + str(self.uid)

    def handler(self, e):
        pass

    def get_position(self):
        raise NotImplementedError(f"Called get_position on Field {self.id}")

    def get_hitboxradius(self):
        raise NotImplementedError(f"Called get_hitboxradius on Field {self.id}")

    def get_collisionbox(self):
        return = (Interval(self.x_inf, self.x_sup, inverted = True),
                  Interval(self.y_inf, self.y_sup, inverted = True))

    def collision(self, other):
        pass

    def step(self, objects):
        pass
