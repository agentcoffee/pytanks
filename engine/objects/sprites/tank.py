import math
import random
from Xlib import X, threaded

import debug
from maths.vector import Vector
from maths.matrix import RotationMatrix
from maths.interval import Interval

from sprites.movable import Movable, MovableState
from sprites.drawable import Drawable
from sprites.projectile import ProjectileObject, ProjectileState
from sprites.explosion import ExplosionObject, ExplosionState
from sprites.field import FieldObject

from engine.bounding_box import BoundingBox

from packets import InputPacket

# Used to communicate the state to the clients
class TankState(MovableState):
    def __init__(self, movable_state, health, name, uid):
        MovableState.set_state(self, movable_state)

        self.health   = health
        self.name     = name
        self.uid      = uid

    def get_state(self):
        return TankState(MovableState.get_state(self), self.health, self.name, self.uid)

    def set_state(self, tank_state):
        assert(isinstance(tank_state, TankState))
        MovableState.set_state(self, tank_state)

        self.health   = tank_state.health
        self.name     = tank_state.name
        self.uid      = tank_state.uid

class TankSprite(Drawable):
    def __init__(self, screen, window, gc, tank_state):
        # Init the drawable context
        Drawable.__init__(self, screen, window, gc)

        # Init the state
        self.state = tank_state

        self.image = [Vector(5, -5),  Vector(-5, -5), Vector(-5, 5),
                      Vector(5, 5),   Vector(5, 1),   Vector(10, 1),
                      Vector(10, -1), Vector(5, -1),  Vector(5, -5)]

        tracks = [Vector(0, 0), Vector(0, 1), Vector(1, 0), Vector(1, 1)]
        self.tracks_1  = [v + Vector(-4, 0) for v in tracks]
        self.tracks_1 += [v + Vector(-1, 0) for v in tracks]
        self.tracks_1 += [v + Vector(+3, 0) for v in tracks]

        self.tracks_2  = [v + Vector(-2, 0) for v in tracks]
        self.tracks_2 += [v + Vector(+1, 0) for v in tracks]

        self.track_animation_frames = 20
        self.track_animation_frames_count = self.track_animation_frames

        debug.objects("Instantiated TankSprite {}"
                .format(self.state.name, self.state.position.x, self.state.position.y))

    def __str__(self):
        return "TankSprite: " + str(self.state.uid)

    def drawTank(self, fg_tank, fg_font):
        self.gc.change(foreground = fg_tank)

        placed_tank = [self.state.position + RotationMatrix(self.state.angle) * dot\
                        for dot in self.image]

        if self.track_animation_frames_count > 0:
            placed_tracks  = [self.state.position +\
                    RotationMatrix(self.state.angle) * (dot + Vector(0, 3))\
                    for dot in self.tracks_1]
            placed_tracks += [self.state.position +\
                    RotationMatrix(self.state.angle) * (dot + Vector(0, -4))\
                    for dot in self.tracks_2]
        else:
            placed_tracks  = [self.state.position +\
                    RotationMatrix(self.state.angle) * (dot + Vector(0, -4))\
                    for dot in self.tracks_1]
            placed_tracks += [self.state.position +\
                    RotationMatrix(self.state.angle) * (dot + Vector(0, 3))\
                    for dot in self.tracks_2]

        if self.state.speed > 0:
            self.track_animation_frames_count -= 1
            if self.track_animation_frames_count == -self.track_animation_frames:
                self.track_animation_frames_count = self.track_animation_frames

        self.window.poly_line(self.gc, X.CoordModeOrigin,
                [(int(dot.x), int(dot.y)) for dot in placed_tank])

        for p in placed_tracks:
            self.window.point(self.gc, int(p.x), int(p.y))

        #self.window.poly_line(self.gc, X.CoordModeOrigin,
        #        [(0, 0), (int(self.state.position.x), int(self.state.position.y))])

        self.gc.change(foreground = fg_font)
        self.window.point    (self.gc, int(self.state.position.x), int(self.state.position.y))
        self.window.draw_text(self.gc, int(self.state.position.x), int(self.state.position.y-15),
                str(self.state.health))
        self.window.draw_text(self.gc, int(self.state.position.x-5), int(self.state.position.y+20),
                str(self.state.name))

    def draw(self):
        self.drawTank(self.screen.black_pixel, self.red)

    def erase(self):
        self.drawTank(self.screen.white_pixel, self.screen.white_pixel)

class TankObject(Movable):
    def __init__(self, tank_state, id_generator):
        # Init the state
        self.state = tank_state

        # Init the movable context
        Movable.__init__(self,
                acceleration = 0.001,
                deacceleration = 0.0005,
                angular_speed = 0.005,
                drag_coefficient = 0.005,
                movable_state = self.state)

        self.id_generator   = id_generator
        self.shoot = False
        self.hitbox_radius  = 7 # ~= sqrt(5*5 + 5*5)

        print("Instantiated TankObject {} : x = {} y = {}"
                .format(self.state.name, self.state.position.x, self.state.position.y))

    def __str__(self):
        return f"Tank: {self.state.name} ({str(self.state.uid)})"

    def handler(self, e):
        if e.event == InputPacket.Event.PRESS:
            if e.key == InputPacket.Key.UP:
                self.go(True)
            elif e.key == InputPacket.Key.DOWN:
                self.stop(True)
            elif e.key == InputPacket.Key.LEFT:
                self.rotate(True, -1)
            elif e.key == InputPacket.Key.RIGHT:
                self.rotate(True, 1)
            elif e.key == InputPacket.Key.SPACE:
                self.shoot = True
        elif e.event == InputPacket.Event.RELEASE:
            if e.key == InputPacket.Key.UP:
                self.go(False)
            elif e.key == InputPacket.Key.DOWN:
                self.stop(False)
            elif e.key == InputPacket.Key.LEFT:
                self.rotate(False, -1)
            elif e.key == InputPacket.Key.RIGHT:
                self.rotate(False, 1)

    def get_position(self):
        return self.state.position

    def get_hitboxradius(self):
        return self.hitbox_radius

    def get_collisionbox(self):
        return BoundingBox(self.state.position, self.hitbox_radius)

    def collision(self, other):
        if isinstance(other, ProjectileObject):
            self.state.health -= 10
            return False

        if isinstance(other, FieldObject):
            return True

        if isinstance(other, TankObject):
            return True

    def step(self, objects, movables):
        self.update(objects, movables)

        if self.shoot == True:
            self.shoot = False
            #a = self.angle - 0.5
            #while a < self.angle + 0.5:
            #    start      = self.state.position + RotationMatrix(a) * Vector(20, 0)
            start      = self.state.position + RotationMatrix(self.state.angle) * Vector(15, 0)
            objects.append(ProjectileObject(
                projectile_state = ProjectileState(
                    MovableState(
                        position = start,
                        angle = self.state.angle,
                        #angle = a,
                        speed = self.state.speed+0.7),
                    uid = self.id_generator.get()),
                id_generator = self.id_generator))
            #    a += 0.01

        if self.state.health <= 0:
            objects.append(ExplosionObject(explosion_state = ExplosionState(
                    uid = self.id_generator.get(),
                    position = Vector(self.state.position.x, self.state.position.y),
                    size = 5)
                ))
