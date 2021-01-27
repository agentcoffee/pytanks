import math
from Xlib import X, threaded

from maths.vector import Vector
from maths.matrix import RotationMatrix
from sprites.movable import Movable
from sprites.projectile import Projectile
from sprites.explosion import Explosion
from commands import Input


class Tank(Movable):
    def __init__(self, field, x, y, screen, window, gc, input_pipe):
        super().__init__(field = field,
                x = x, y = y,
                angle = math.pi * 1/2,
                acceleration = 0.001,
                deacceleration = 0.0005,
                angular_speed = 0.005,
                drag_coefficient = 0.005,
                speed = 0,
                screen = screen,
                window = window,
                gc = gc)

        self.shoot = False
        self.image = [Vector(5, -5),  Vector(-5, -5), Vector(-5, 5),
                      Vector(5, 5),   Vector(5, 1),   Vector(10, 1),
                      Vector(10, -1), Vector(5, -1),  Vector(5, -5)]
        self.hitbox_radius  = 8 # ~= sqrt(5*5 + 5*5)
        self.health         = 100
        #self.tank_name      = tank_name

        self.input_pipe       = input_pipe

        print("Instantiated Tank x = {} y = {}".format(self.position.x, self.position.y))

    def __str__(self):
        return "Tank: " + super().__str__()

    def handler(self, e):
        if e.event == Input.Event.PRESS:
            if e.key == Input.Key.UP:
                self.go(True)
            elif e.key == Input.Key.DOWN:
                self.stop(True)
            elif e.key == Input.Key.LEFT:
                self.rotate(True, -1)
            elif e.key == Input.Key.RIGHT:
                self.rotate(True, 1)
            elif e.key == Input.Key.SPACE:
                self.shoot = True
        elif e.event == Input.Event.RELEASE:
            if e.key == Input.Key.UP:
                self.go(False)
            elif e.key == Input.Key.DOWN:
                self.stop(False)
            elif e.key == Input.Key.LEFT:
                self.rotate(False, -1)
            elif e.key == Input.Key.RIGHT:
                self.rotate(False, 1)

    def drawTank(self, fg_tank, fg_font):
        self.gc.change(foreground = fg_tank)
        placed_image = [self.position + RotationMatrix(self.angle) * dot for dot in self.image]

        self.window.poly_line(self.gc, X.CoordModeOrigin,
                [(int(dot.x), int(dot.y)) for dot in placed_image])

        self.gc.change(foreground = fg_font)
        self.window.point    (self.gc, int(self.position.x), int(self.position.y))
        self.window.draw_text(self.gc, int(self.position.x), int(self.position.y-15), str(self.health))

    def collision(self, other, sprites):
        if isinstance(other, Projectile):
            self.gc.change(foreground = self.screen.white_pixel)
            self.window.draw_text(self.gc, int(self.position.x), int(self.position.y-15), str(self.health))
            self.health -= 10

            if self.health == 0:
                self.drawTank(self.screen.white_pixel, self.screen.white_pixel)
                sprites.append(Explosion(self.position.x, self.position.y, self.green,
                    self.screen, self.window, self.gc))
                sprites.remove(self)

    def action(self, sprites):
        if self.shoot == True:
            self.shoot = False
            start      = self.position + RotationMatrix(self.angle) * Vector(20, 0)
            sprites.append(Projectile(self.field, start.x, start.y,
                    self.angle, self.speed, self.screen, self.window, self.gc))

    def draw(self):
        self.drawTank(self.screen.white_pixel, self.screen.white_pixel)
        self.update()
        self.drawTank(self.screen.black_pixel, self.red)
