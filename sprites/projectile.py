import math
import random
from Xlib import X, threaded

import debug
import sprites.tank

from maths.vector import Vector
from maths.matrix import RotationMatrix
from maths.interval import Interval

from sprites.movable import Movable, MovableState
from sprites.drawable import Drawable
from sprites.collidable import Collidable
from sprites.explosion import ExplosionObject, ExplosionState
from sprites.field import FieldObject

from engine.bounding_box import BoundingBox


class ProjectileState(MovableState):
    def __init__(self, movable_state, uid):
        MovableState.set_state(self, movable_state)
        self.uid = uid

    def get_state(self):
        return ProjectileState(MovableState.get_state(self), self.uid)

    def set_state(self, projectile_state):
        assert(isinstance(projectile_state, ProjectileState))
        MovableState.set_state(self, projectile_state)
        self.uid = projectile_state.uid

class ProjectileSprite(Drawable):
    def __init__(self, screen, window, gc, projectile_state):
        Drawable.__init__(self, screen, window, gc)

        self.state = projectile_state

        self.image = [Vector(2, 2),  Vector(2, -2), Vector(-2, -2),
                      Vector(-2, 2), Vector(2, 2)]

    def drawProjectile(self, fg_color):
        self.gc.change(foreground = fg_color)
        #placed_image = [self.state.position + RotationMatrix(self.state.angle) * dot for dot in self.image]

        #self.window.poly_line(self.gc, X.CoordModeOrigin,
        #        [(int(dot.x), int(dot.y)) for dot in placed_image])
        self.window.poly_line(self.gc, X.CoordModeOrigin,
                [ ( int(self.state.position.x), int(self.state.position.y) ),
                  ( int(self.state.position.x + 4 * math.cos(self.state.angle)),
                    int(self.state.position.y + 4 * math.sin(self.state.angle)) )])

    def draw(self):
        self.drawProjectile(self.red)

    def erase(self):
        self.drawProjectile(self.screen.white_pixel)

class ProjectileObject(Movable):
    def __init__(self, projectile_state, id_generator):
        self.state = projectile_state

        Movable.__init__(self,
                acceleration = 0,
                deacceleration = 0.0005,
                angular_speed = 0.005,
                drag_coefficient = 0.0001,
                movable_state = self.state)

        self.hitbox_radius = 3 # ~= sqrt(2*2 + 2*2)
        self.go(True)
        self.explode = False
        self.id_generator = id_generator

        debug.objects("Instantiated Projectile x = {} y = {}"
                .format(self.state.position.x, self.state.position.y))

    def __str__(self):
        return "Projectile: " + self.uid

    def get_position(self):
        return self.state.position

    def get_hitboxradius(self):
        return self.hitbox_radius

    def get_collisionbox(self):
        return BoundingBox(self.state.position, self.hitbox_radius)

    def collision(self, other):
        if isinstance(other, sprites.tank.TankObject):
            self.explode = True
            return False

        if isinstance(other, FieldObject):
            self.explode = True
            return True

    def step(self, objects):
        remove = False
        self.update(objects)

        if self.explode == True:
            objects.append(ExplosionObject(
                explosion_state = ExplosionState(
                    uid = self.id_generator.get(),
                    position = Vector(self.state.position.x, self.state.position.y),
                    size = 4)
                ))
            remove = True

        if remove:
            objects.remove(self)
