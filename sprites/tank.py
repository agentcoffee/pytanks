import math
import random
from Xlib import X, threaded

from maths.vector import Vector
from maths.matrix import RotationMatrix
from maths.interval import Interval

from sprites.movable import Movable
from sprites.drawable import Drawable
from sprites.collidable import Collidable
from sprites.projectile import ProjectileObject, ProjectileState
from sprites.explosion import ExplosionObject, ExplosionState

from commands import Input

# Used to communicate the state to the clients
class TankState:
    def __init__(self, position, angle, speed, health, name, uid):
        self.position = position
        self.angle    = angle
        self.speed    = speed
        self.health   = health
        self.name     = name
        self.uid      = uid

    def getState(self):
        return TankState(self.position, self.angle, self.speed, self.health,
                self.name, self.uid)

    def setState(self, tank_state):
        assert(type(tank_state) == TankState)
        self.position = tank_state.position
        self.angle    = tank_state.angle
        self.speed    = tank_state.speed
        self.health   = tank_state.health
        self.name     = tank_state.name
        self.uid      = tank_state.uid

class TankSprite(Drawable, TankState):
    def __init__(self, screen, window, gc, tank_state):
        # Init the drawable context
        Drawable.__init__(self, screen, window, gc)

        # Init the state
        TankState.setState(self, tank_state)

        self.image = [Vector(5, -5),  Vector(-5, -5), Vector(-5, 5),
                      Vector(5, 5),   Vector(5, 1),   Vector(10, 1),
                      Vector(10, -1), Vector(5, -1),  Vector(5, -5)]

        print("Instantiated TankSprite {}".format(self.name, self.position.x, self.position.y))

    def __str__(self):
        return "TankSprite: " + str(self.uid)

    def drawTank(self, fg_tank, fg_font):
        self.gc.change(foreground = fg_tank)
        placed_image = [self.position + RotationMatrix(self.angle) * dot for dot in self.image]

        self.window.poly_line(self.gc, X.CoordModeOrigin,
                [(int(dot.x), int(dot.y)) for dot in placed_image])

        self.gc.change(foreground = fg_font)
        self.window.point    (self.gc, int(self.position.x), int(self.position.y))
        self.window.draw_text(self.gc, int(self.position.x), int(self.position.y-15), str(self.health))
        self.window.draw_text(self.gc, int(self.position.x-5), int(self.position.y+20), str(self.name))

    def draw(self):
        self.drawTank(self.screen.black_pixel, self.red)

    def erase(self):
        self.drawTank(self.screen.white_pixel, self.screen.white_pixel)

class TankObject(Movable, Collidable, TankState):
    def __init__(self, field, input_pipe, tank_state):
        # Init the movable context
        Movable.__init__(self, field = field,
                acceleration = 0.001,
                deacceleration = 0.0005,
                angular_speed = 0.005,
                drag_coefficient = 0.005)

        # Init the state
        TankState.setState(self, tank_state)

        self.shoot = False
        self.hitbox_radius  = 8 # ~= sqrt(5*5 + 5*5)

        self.input_pipe     = input_pipe

        print("Instantiated TankObject {} : x = {} y = {}"
                .format(self.name, self.position.x, self.position.y))

    def __str__(self):
        return "Tank: " + str(self.uid)

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

    def getCollisionBox(self):
        return (Interval(self.position.x - self.hitbox_radius,
                         self.position.x + self.hitbox_radius),
                Interval(self.position.y - self.hitbox_radius,
                         self.position.y + self.hitbox_radius))

    def collision(self, other):
        if isinstance(other, ProjectileObject):
            self.health -= 10

    def step(self, objects):
        self.update()

        if self.shoot == True:
            self.shoot = False
            start      = self.position + RotationMatrix(self.angle) * Vector(20, 0)
            objects.append(ProjectileObject(
                field = self.field,
                projectile_state = ProjectileState(
                    position = start,
                    angle = self.angle,
                    speed = self.speed+0.7,
                    uid = random.randint(0, 2**16))
                ))

        if self.health <= 0:
            objects.append(ExplosionObject(explosion_state = ExplosionState(
                    position = Vector(self.position.x, self.position.y),
                    counter = 0,
                    color = None,
                    uid = random.randint(0, 2**16))
                ))
            objects.remove(self)
