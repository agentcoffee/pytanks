from maths.interval import Interval


class Collidable:
    def getCollisionBox(self):
        raise NotImplementedError("You have to provide the getCollisionBox method yourself.")

    def getHitboxRadius(self):
        raise NotImplementedError("You have to provide the getHitboxRadius method yourself.")

    def getPosition(self):
        raise NotImplementedError("You have to provide the getPosition method yourself.")

    # Check for a collision
    def collides(self, other):
        box      = self.getCollisionBox()
        otherBox = other.getCollisionBox()

        if box[0].overlaps(otherBox[0]) and box[1].overlaps(otherBox[1]):
            return True
        else:
            return False

    # Callback on an actual collision
    def collision(self, other, sprites):
        print("Movable:" + str(self) + " collides with " + str(other))
