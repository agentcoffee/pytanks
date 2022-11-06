import time
from Xlib import X, threaded

from engine.maths.vector import Vector
from engine.objects.generics.drawable import Drawable
from engine.objects.generics.collidable import Collidable

EXPANSION_TIME = 100 # in ms

class ExplosionState:
    def __init__(self, uid, position, color=None, counter=0, size=5):
        self.uid      = uid
        self.position = position
        self.color    = color
        self.counter  = counter
        self.size     = size

    def get_state(self):
        return ExplosionState(self.uid, self.position, self.color, self.counter, self.size)

    def set_state(self, explosion_state):
        assert(isinstance(explosion_state, ExplosionState))
        self.uid      = explosion_state.uid
        self.position = explosion_state.position
        self.color    = explosion_state.color
        self.counter  = explosion_state.counter
        self.size     = explosion_state.size

class ExplosionSprite(Drawable):
    def __init__(self, screen, window, gc, explosion_state):
        Drawable.__init__(self, screen, window, gc)

        self.state = explosion_state

        self.image = [Vector(1, 1),  Vector(1, -1), Vector(-1, -1),
                      Vector(-1, 1), Vector(1, 1)]

    def drawExplosion(self, fg):
        self.gc.change(foreground = fg)
        placed_image = [self.state.position + self.state.counter * dot for dot in self.image]
        self.window.poly_line(self.gc, X.CoordModeOrigin,
                [(int(dot.x), int(dot.y)) for dot in placed_image])

    def draw(self):
        self.drawExplosion(self.red) # TODO variable explosion color

    def erase(self):
        self.drawExplosion(self.white)

class ExplosionObject:
    def __init__(self, explosion_state):
        self.state = explosion_state

        self.timestamp = time.monotonic_ns() / 1000000

    def collision(self, other):
        return False

    def step(self, objects, movables):
        t = time.monotonic_ns() / 1000000
        if t - self.timestamp > EXPANSION_TIME:
            self.timestamp = time.monotonic_ns() / 1000000
            self.state.counter += 1

        if self.state.counter == self.state.size:
            objects.remove(self)
