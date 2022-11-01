import time
import math

from maths.vector import Vector
from maths.matrix import Matrix
from maths.matrix import RotationMatrix
from maths.interval import Interval

from sprites.drawable import Drawable
from sprites.collidable import Collidable, CollidableType

from engine.bounding_box import BoundingBox


class MovableState:
    def __init__(self, position, angle, speed):
        self.position = position
        self.angle    = angle
        self.speed    = speed

    def get_state(self):
        return MovableState(self.position, self.angle, self.speed)

    def set_state(self, movable_state):
        assert(isinstance(movable_state, MovableState))

        self.position = movable_state.position
        self.angle    = movable_state.angle
        self.speed    = movable_state.speed

class Movable(Collidable):
    def __init__(self, acceleration, deacceleration,
            angular_speed, drag_coefficient, movable_state):
        assert(isinstance(movable_state, MovableState))
        self.state          = movable_state

        Collidable.__init__(self, CollidableType.CIRCLE)

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
        return "pos: " + str(self.state.position) + \
               " speed: " + str(self.state.speed)

    def update(self, objects):
        t = ((time.monotonic_ns() / 1000000) - self.timestamp)
        self.timestamp = time.monotonic_ns() / 1000000

        self.state.speed -= self.drag_coefficient * self.state.speed * t

        if self.accelerate == True:
            self.state.speed += self.acceleration * t

        if self.deaccelerate == True:
            self.state.speed -= self.deacceleration * t
            if self.state.speed < 0:
                self.state.speed = 0

        if self.turn == True:
            self.state.angle += self.angular_speed * self.angular_sign * t

        direction = RotationMatrix(self.state.angle) * Vector(1, 0)

        old_position = self.state.position
        old_boundingbox = self.get_collisionbox()

        self.state.position += (self.state.speed * t * direction)
        new_boundingbox = self.get_collisionbox()

        # Construct bounding box of the projected trajectory
        xmin = min(old_boundingbox.xrange.a, new_boundingbox.xrange.a)
        xmax = max(old_boundingbox.xrange.b, new_boundingbox.xrange.b)

        ymin = min(old_boundingbox.yrange.a, new_boundingbox.yrange.a)
        ymax = max(old_boundingbox.yrange.b, new_boundingbox.yrange.b)

        trajectory_boundingbox = BoundingBox(Interval(xmin, xmax), Interval(ymin, ymax))

        first_collision = None
        opponent        = None
        collided        = False

        for o in objects:
            # Obviously we collide with ourselves
            if o is not self and isinstance(o, Collidable):
                # Coarse check if we collide
                if o.get_collisionbox().overlaps( trajectory_boundingbox ):
                    # The factor for the calculated new position
                    x = (self.state.speed * t)

                    # Check if we collide circles and circles
                    if self.get_collidabletype() == CollidableType.CIRCLE and\
                        o.get_collidabletype() == CollidableType.CIRCLE:

                        # ( Opponent Position - Old Position ) * d / (d * d)
                        # Note: Since d is normalized, we can simplify
                        # Calculate the factor x on the trajectory where the
                        # opponent is the closest, i.e., the normal vector on the
                        # trajectory through the opponent.
                        x = ((o.get_position() - old_position) * direction ) #/ (direction * direction)

                        # Q is the normal point of the opponent position on the trajectory.
                        Q = old_position + (x * direction)
                        # l is the distance of the opponent position to Q.
                        l = (Q - o.get_position()).length()
                        # Calculate the factor x on the trajectory where we would hit the opponent.
                        x = math.sqrt((o.get_hitboxradius() + self.get_hitboxradius())**2 - l**2)

                        collided = True

                    # Or we collide with a square
                    elif self.get_collidabletype() == CollidableType.CIRCLE and\
                        o.get_collidabletype() == CollidableType.SQUARE:
                        other_box = o.get_collisionbox()

                        if self.state.position.x in other_box.xrange:
                            if other_box.xrange.inverted:
                                if self.state.position.x <= other_box.xrange.a:
                                    #print(f"1 correcting x from {x}")
                                    x = (other_box.xrange.a - old_position.x) / direction.x
                                    #print(f" to {x}")
                                elif self.state.position.x >= other_box.xrange.b:
                                    #print(f"2 correcting x from {x}")
                                    x = (other_box.xrange.b - old_position.x) / direction.x
                                    #print(f" to {x}")
                                else:
                                    raise RuntimeError
                            else:
                                raise NotImplementedError("Not yet implemented.")
                            collided = True

                        if self.state.position.y in other_box.yrange:
                            if other_box.yrange.inverted:
                                if self.state.position.y <= other_box.yrange.a:
                                    #print(f"3 correcting x from {x}")
                                    x = (other_box.yrange.a - old_position.y) / direction.y
                                    #print(f" to {x}")
                                elif self.state.position.y >= other_box.yrange.b:
                                    #print(f"4 correcting x from {x}")
                                    x = (other_box.yrange.b - old_position.y) / direction.y
                                    #print(f" to {x}")
                                else:
                                    raise RuntimeError
                            else:
                                raise NotImplementedError("Not yet implemented.")
                            collided = True

                    else:
                        raise NotImplementedError(("A SQUARE collidable"
                                "shouldn't be movable, and two SQUARE's"
                                "shouldn't be able to collide"))

                    if first_collision is None:
                        first_collision = x
                        opponent = o
                    elif x < first_collision:
                        first_collision = x
                        opponent = o

        if collided and first_collision is not None:
            opponent.collision(self)
            if self.collision(opponent):
                print(f"correcting position from {self.state.position} to {old_position + x * direction}")
                self.state.position = old_position + x * direction

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
