import math
from Xlib import X, threaded

import tank
from vector import Vector
from matrix import RotationMatrix
from movable import Movable
from explosion import Explosion


class Projectile(Movable):
    def __init__(self, field, x, y, angle, speed, screen, window, gc):
        super().__init__(field = field,
                x = x, y = y,
                angle = angle,
                acceleration = 0.001,
                deacceleration = 0.0005,
                angular_speed = 0.005,
                drag_coefficient = 0.001,
                speed = speed,
                screen = screen,
                window = window,
                gc = gc)

        self.image         = [Vector(2, 2),  Vector(2, -2), Vector(-2, -2),
                              Vector(-2, 2), Vector(2, 2)]
        self.hitbox_radius = 3 # ~= sqrt(2*2 + 2*2)

        self.go(True)

        print("Instantiated Projectile x = {} y = {}".format(self.position.x, self.position.y))

    def __str__(self):
        return "Projectile: " + super().__str__()

    def drawProjectile(self, fg_color):
        self.gc.change(foreground = fg_color)
        placed_image = [self.position + RotationMatrix(self.angle) * dot for dot in self.image]

        self.window.poly_line(self.gc, X.CoordModeOrigin,
                [(int(dot.x), int(dot.y)) for dot in placed_image])

    def removeProjectile(self, sprites):
        sprites.remove(self)
        self.drawProjectile(self.screen.white_pixel)

    def collision(self, other, sprites):
        if isinstance(other, tank.Tank):
            sprites.append(Explosion(self.position.x, self.position.y, self.red,
                self.screen, self.window, self.gc))
            self.removeProjectile(sprites)

    def action(self, sprites):
        if self.position.x >= self.field.width or self.position.x <= 0 or \
           self.position.y >= self.field.height or self.position.y <= 0:
            self.removeProjectile(sprites)

    def draw(self):
        self.drawProjectile(self.screen.white_pixel)
        self.update()
        self.drawProjectile(self.red)
