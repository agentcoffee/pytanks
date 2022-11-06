from maths.interval import Interval
from enum import Enum


class CollidableType(Enum):
    CIRCLE = 1
    SQUARE = 2

class Collidable:
    def __init__(self, collidabletype):
        self.collidabletype = collidabletype

    def get_collidabletype(self):
        return self.collidabletype

    def get_collisionbox(self):
        raise NotImplementedError("You have to provide the get_collisionbox method yourself.")

    def get_hitboxradius(self):
        raise NotImplementedError("You have to provide the get_hitboxradius method yourself.")

    def get_position(self):
        raise NotImplementedError("You have to provide the get_position method yourself.")

    # Check for a collision
    def collides(self, other):
        # TODO this is just a coarse box checking, we could do the better
        # 'hitcircle'
        return self.get_collisionbox().overlaps( other.get_collisionbox() )

    # Callback on an actual collision
    def collision(self, other, k=None):
        print(f"Movable: {str(self)} collides with {str(other)} after k {k}")
