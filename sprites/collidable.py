from maths.interval import Interval


class Collidable:
    def get_collisionbox(self):
        raise NotImplementedError("You have to provide the get_collisionbox method yourself.")

    def get_hitboxradius(self):
        raise NotImplementedError("You have to provide the get_hitboxradius method yourself.")

    def get_position(self):
        raise NotImplementedError("You have to provide the get_position method yourself.")

    # Check for a collision
    def collides(self, other):
        box      = self.get_collisionbox()
        otherBox = other.get_collisionbox()

        if box[0].overlaps(otherBox[0]) and box[1].overlaps(otherBox[1]):
            # TODO this is just a coarse box checking, we could do the better
            # 'hitcircle'
            return True
        else:
            return False

    # Callback on an actual collision
    def collision(self, other, sprites):
        print("Movable:" + str(self) + " collides with " + str(other))
