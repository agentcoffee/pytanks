import time

from maths.vector import Vector
from maths.matrix import Matrix
from maths.matrix import RotationMatrix
from maths.interval import Interval
from sprites.drawable import Drawable


class Movable:
    def __init__(self, field, acceleration, deacceleration,
            angular_speed, drag_coefficient):
        self.field          = field

        self.acceleration       = acceleration
        self.deacceleration     = deacceleration
        self.angular_speed      = angular_speed
        self.drag_coefficient   = drag_coefficient

        self.accelerate     = False
        self.deaccelerate   = False
        self.turn           = False
        self.angular_sign   = 1

        self.timestamp      = 0

    def __str__(self):
        return "pos: " + str(self.position) + \
               " speed: " + str(self.speed)

    def update(self, objects):
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

        for o in objects:
            if o.collides(self):
                o.collision(self)
                self.collsision(o)

    def rotate(self, v, d):
        self.turn         = v
        self.angular_sign = d

    def go(self, v):
        self.accelerate = v
        self.timestamp  = time.monotonic_ns() / 1000000

    def stop(self, v):
        self.deaccelerate = v
        self.timestamp    = time.monotonic_ns() / 1000000

    def handler(self, e):
        raise NotImplementedError("You have to provide the handler method yourself.")

    def action(self, sprites):
        return
