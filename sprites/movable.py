import time

from maths.vector import Vector
from maths.matrix import Matrix
from maths.matrix import RotationMatrix
from maths.interval import Interval
from sprites.drawable import Drawable


class Movable(Drawable):
    def __init__(self, field, x, y, angle, acceleration, deacceleration,
            angular_speed, drag_coefficient, speed, screen, window, gc):
        super().__init__(x, y, screen, window, gc)

        self.field          = field

        self.angle          = angle

        self.acceleration       = acceleration
        self.deacceleration     = deacceleration
        self.angular_speed      = angular_speed
        self.drag_coefficient   = drag_coefficient

        self.speed          = speed

        self.accelerate     = False;
        self.deaccelerate   = False;
        self.turn           = False;
        self.angular_sign   = 1;

        self.timestamp      = 0

    def __str__(self):
        return "pos: " + str(self.position) + \
               " speed: " + str(self.speed)

    def update(self):
        t = ((time.monotonic_ns() / 1000000) - self.timestamp)
        self.timestamp = time.monotonic_ns() / 1000000

        self.speed -= self.drag_coefficient * self.speed * t

        if self.accelerate == True:
            self.speed += self.acceleration * t

        if self.deaccelerate == True:
            self.speed -= self.deacceleration * t
            if self.speed < 0:
                self.speed = 0

        if self.turn == True:
            self.angle += self.angular_speed * self.angular_sign * t

        direction = RotationMatrix(self.angle) * Vector(1, 0)
        self.position += (self.speed * t * direction)

        if self.position.x > self.field.width:
            self.position.x = self.field.width
        elif self.position.x < 0:
            self.position.x = 0

        if self.position.y > self.field.height:
            self.position.y = self.field.height
        elif self.position.y < 0:
            self.position.y = 0

    def rotate(self, v, d):
        self.turn           = v
        self.angular_sign   = d

    def go(self, v):
        self.accelerate = v
        self.timestamp = time.monotonic_ns() / 1000000

    def stop(self, v):
        self.deaccelerate = v
        self.timestamp = time.monotonic_ns() / 1000000

    def handler(self, e):
        return

    def action(self, sprites):
        return
