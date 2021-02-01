import time
from Xlib import X, threaded

from maths.vector import Vector
from sprites.drawable import Drawable
from sprites.collidable import Collidable

EXPANSION_TIME = 100 # in ms

class ExplosionState:
    def __init__(self, position, color, counter, uid):
        self.position = position
        self.color    = color
        self.counter  = counter
        self.uid      = uid

    def getState(self):
        return ExplosionState(self.position, self.color, self.counter, self.uid)

    def setState(self, explosion_state):
        assert(type(explosion_state) == ExplosionState)
        self.position = explosion_state.position
        self.color    = explosion_state.color
        self.counter  = explosion_state.counter
        self.uid      = explosion_state.uid

class ExplosionSprite(Drawable, ExplosionState):
    def __init__(self, screen, window, gc, explosion_state):
        Drawable.__init__(self, screen, window, gc)

        ExplosionState.setState(self, explosion_state)

        self.image = [Vector(1, 1),  Vector(1, -1), Vector(-1, -1),
                      Vector(-1, 1), Vector(1, 1)]

    def drawExplosion(self, fg):
        self.image = [self.counter * dot for dot in self.image]

        self.gc.change(foreground = fg)
        placed_image = [self.position + dot for dot in self.image]
        self.window.poly_line(self.gc, X.CoordModeOrigin,
                [(int(dot.x), int(dot.y)) for dot in placed_image])

    def draw(self):
        self.drawExplosion(self.green) # TODO variable explosion color

    def erase(self):
        self.drawExplosion(self.white)

class ExplosionObject(ExplosionState):
    def __init__(self, explosion_state):
        ExplosionState.setState(self, explosion_state)

        self.timestamp = time.monotonic_ns() / 1000000

    def collision(self, other):
        return

    def step(self, objects):
        t = time.monotonic_ns() / 1000000
        if t - self.timestamp > EXPANSION_TIME:
            self.timestamp = time.monotonic_ns() / 1000000
            self.counter += 1

        if self.counter == 5:
            objects.remove(self)
