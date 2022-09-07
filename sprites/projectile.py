import math
import random
from Xlib import X, threaded

import debug
import sprites.tank
from maths.vector import Vector
from maths.matrix import RotationMatrix
from maths.interval import Interval
from sprites.movable import Movable
from sprites.drawable import Drawable
from sprites.collidable import Collidable
from sprites.explosion import ExplosionObject, ExplosionState


class ProjectileState:
    def __init__(self, position, angle, speed, uid):
        self.position = position
        self.angle    = angle
        self.speed    = speed
        self.uid      = uid

    def getState(self):
        return ProjectileState(self.position, self.angle, self.speed, self.uid)

    def setState(self, projectile_state):
        self.position = projectile_state.position
        self.angle    = projectile_state.angle
        self.speed    = projectile_state.speed
        self.uid      = projectile_state.uid

class ProjectileSprite(Drawable, ProjectileState):
    def __init__(self, screen, window, gc, projectile_state):
        Drawable.__init__(self, screen, window, gc)

        ProjectileState.setState(self, projectile_state)

        self.image = [Vector(2, 2),  Vector(2, -2), Vector(-2, -2),
                      Vector(-2, 2), Vector(2, 2)]

    def drawProjectile(self, fg_color):
        self.gc.change(foreground = fg_color)
        #placed_image = [self.position + RotationMatrix(self.angle) * dot for dot in self.image]

        #self.window.poly_line(self.gc, X.CoordModeOrigin,
        #        [(int(dot.x), int(dot.y)) for dot in placed_image])
        self.window.poly_line(self.gc, X.CoordModeOrigin,
                [ ( int(self.position.x), int(self.position.y) ),
                  ( int(self.position.x + 4 * math.cos(self.angle)),
                    int(self.position.y + 4 * math.sin(self.angle)) )])

    def draw(self):
        self.drawProjectile(self.red)

    def erase(self):
        self.drawProjectile(self.screen.white_pixel)

class ProjectileObject(Movable, Collidable, ProjectileState):
    def __init__(self, field, projectile_state, id_generator):
        Movable.__init__(self, field = field,
                acceleration = 0,
                deacceleration = 0.0005,
                angular_speed = 0.005,
                drag_coefficient = 0.0001)

        ProjectileState.setState(self, projectile_state)

        self.hitbox_radius = 3 # ~= sqrt(2*2 + 2*2)
        self.go(True)
        self.explode = False
        self.id_generator = id_generator

        debug.objects("Instantiated Projectile x = {} y = {}".format(self.position.x, self.position.y))

    def __str__(self):
        return "Projectile: " + self.uid

    def getPosition(self):
        return self.position

    def getHitboxRadius(self):
        return self.hitbox_radius

    def getCollisionBox(self):
        return (Interval(self.position.x - self.hitbox_radius,
                         self.position.x + self.hitbox_radius),
                Interval(self.position.y - self.hitbox_radius,
                         self.position.y + self.hitbox_radius))

    def collision(self, other):
        if isinstance(other, sprites.tank.TankObject):
            self.explode = True

    def step(self, objects):
        remove = False
        self.update()

        if self.position.x >= self.field.x_sup or self.position.x <= self.field.x_inf or \
           self.position.y >= self.field.y_sup or self.position.y <= self.field.y_inf:
            remove = True

        if self.explode == True:
            objects.append(ExplosionObject(explosion_state = ExplosionState(
                    uid = self.id_generator.get(),
                    position = Vector(self.position.x, self.position.y),
                    size = 4)
                ))
            remove = True

        if remove:
            objects.remove(self)
