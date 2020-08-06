import time
from Xlib import X, threaded

from vector import Vector
from drawable import Drawable

EXPANSION_TIME = 100 # in ms

class Explosion(Drawable):
    def __init__(self, x, y, color, screen, window, gc):
        super().__init__(x, y, screen, window, gc)

        self.color   = color
        self.image = [Vector(1, 1),  Vector(1, -1), Vector(-1, -1),
                      Vector(-1, 1), Vector(1, 1)]
        self.counter = 1
        self.timestamp = time.monotonic_ns() / 1000000

    def action(self, sprites):
        if self.counter == 5:
            sprites.remove(self)
            self.drawExplosion(self.screen.white_pixel)

    def drawExplosion(self, fg):
        self.gc.change(foreground = fg)
        placed_image = [self.position + dot for dot in self.image]
        self.window.poly_line(self.gc, X.CoordModeOrigin,
                [(int(dot.x), int(dot.y)) for dot in placed_image])

    def collision(self, other, sprites):
        return

    def draw(self):
        t = time.monotonic_ns() / 1000000
        if t - self.timestamp > EXPANSION_TIME:
            self.timestamp = time.monotonic_ns() / 1000000
            self.drawExplosion(self.white)
            self.image = [self.counter * dot for dot in self.image]
            self.counter += 1
            self.drawExplosion(self.color)
